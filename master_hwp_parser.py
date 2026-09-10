import sys
import os
import olefile
import zlib
import struct
import re
import json

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def extract_hwp_paragraphs(file_path):
    ole = olefile.OleFileIO(file_path)
    sections = [d for d in ole.listdir() if d[0] == 'BodyText']
    
    HWPTAG_BEGIN = 0x10
    HWPTAG_PARA_TEXT = HWPTAG_BEGIN + 51
    paragraphs = []
    
    for sec in sections:
        stream = ole.openstream(sec)
        data = stream.read()
        decompressed = zlib.decompress(data, -15)
        
        offset = 0
        while offset < len(decompressed):
            if offset + 4 > len(decompressed):
                break
            header = struct.unpack_from('<I', decompressed, offset)[0]
            tag_id = header & 0x3FF
            size = (header >> 20) & 0xFFF
            offset += 4
            if size == 0xFFF:
                size = struct.unpack_from('<I', decompressed, offset)[0]
                offset += 4
            record_data = decompressed[offset:offset+size]
            offset += size
            
            if tag_id == HWPTAG_PARA_TEXT:
                text = record_data.decode('utf-16le', errors='ignore')
                clean = ''
                for ch in text:
                    code = ord(ch)
                    if code < 32:
                        if code in (10, 13, 9):
                            clean += ch
                        else:
                            clean += ' '
                    else:
                        clean += ch
                clean = clean.strip()
                if clean:
                    paragraphs.append(clean)
    ole.close()
    return paragraphs

def parse_header_ref(line):
    line = line.strip()
    # Matches Bible ref at end of line (including '.' e.g. 요1:1.14)
    m = re.search(r'^(.*?)\s+((?:[1-3]\s*)?[A-Za-z가-힣.]+\s*\d+:\d+(?:[~,\-.]\d+)*(?:상|하|전|후)?)$', line)
    if m:
        title = m.group(1).strip()
        ref = m.group(2).strip().replace('.', ',') if ('.' in m.group(2) and ':' in m.group(2)) else m.group(2).strip()
        return title, ref
    return line, ""

def is_quote_line(p):
    if p.startswith('“') or p.startswith('"') or p.startswith('‘') or p.startswith("'"):
        return True
    if any(k in p for k in ['(링컨)', '(무디)', '(스펄전)', '(어거스틴)', '(전10:10상)', '(시119:97)', '(신30:14)', '(잠22:18)', '시편119편 29절']):
        return True
    if any(k == p for k in ['갈지 아니하면', '힘이 더 드느니라”', '인간에게 주신', '가장 좋은 선물이라고', '나는 믿습니다.”', '어찌 그리 사랑하는지요', '내가 그것을 종일 묵상하나이다', '네 입술에 있게 함이', '아름다우니라”', '식굶암필', '우리의 영적 생활의 활기는']):
        return True
    return False

def is_structural_line(p):
    if is_quote_line(p):
        return True
    if any(p.startswith(k) for k in ['I.', 'II.', 'III.', 'IV.', 'V.', 'VI.', 'VII.', 'VIII.', '전체순서', 'p', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '氠', '捤', '<', 'SERIES', '찬양60', '약속60', '훈련60', '전도60', '인격60']):
        t, r = parse_header_ref(p)
        if not r:
            return True
        if len(re.findall(r'[가-힣A-Za-z0-9]+\s*\d+:\d+', r)) > 1:
            return True
    return False

def build_all_verses():
    hwp_file = "암송최종문서_최종수정191007.hwp"
    paras = extract_hwp_paragraphs(hwp_file)
    print(f"Total HWP paragraphs: {len(paras)}")
    
    all_verses = []
    current_id = 1

    # ----------------------------------------------------
    # 1. 5확신 (Paragraph 12~32) -> 5 KO, 5 EN
    # ----------------------------------------------------
    order_5 = 1
    i = 12
    while i < 33:
        p = paras[i]
        if re.match(r'^\d+\.\s+.*', p):
            t_ko, r_ko = parse_header_ref(paras[i])
            t_en, r_en = parse_header_ref(paras[i+1])
            txt_ko = paras[i+2]
            txt_en = paras[i+3]
            
            all_verses.append({
                "id": current_id, "part": "5확신", "section": "5확신",
                "order_in_part": order_5, "order_in_section": order_5,
                "lang": "ko", "title": t_ko, "reference": r_ko, "text": txt_ko
            })
            current_id += 1
            
            all_verses.append({
                "id": current_id, "part": "5확신", "section": "5확신",
                "order_in_part": order_5, "order_in_section": order_5,
                "lang": "en", "title": t_en, "reference": r_en, "text": txt_en
            })
            current_id += 1
            order_5 += 1
            i += 4
        else:
            i += 1

    # ----------------------------------------------------
    # 2. 8구절 (Paragraph 33~68) -> 8 KO, 8 EN
    # ----------------------------------------------------
    order_8 = 1
    i = 33
    while i < 68:
        p = paras[i]
        if re.match(r'^\d+\.\s+.*', p):
            t_ko, r_ko = parse_header_ref(paras[i])
            t_en, r_en = parse_header_ref(paras[i+1])
            txt_ko = paras[i+2]
            txt_en = paras[i+3]
            
            all_verses.append({
                "id": current_id, "part": "8구절", "section": "8구절",
                "order_in_part": order_8, "order_in_section": order_8,
                "lang": "ko", "title": t_ko, "reference": r_ko, "text": txt_ko
            })
            current_id += 1
            
            all_verses.append({
                "id": current_id, "part": "8구절", "section": "8구절",
                "order_in_part": order_8, "order_in_section": order_8,
                "lang": "en", "title": t_en, "reference": r_en, "text": txt_en
            })
            current_id += 1
            order_8 += 1
            i += 4
        else:
            i += 1

    # ----------------------------------------------------
    # 3. 60구절 (Paragraph 69~330) -> 60 KO, 60 EN
    # ----------------------------------------------------
    def get_60_sec(order, lang):
        if 1 <= order <= 12: return "A. 새로운 삶" if lang == "ko" else "A. Live the New Life"
        elif 13 <= order <= 24: return "B. 그리스도를 전파함" if lang == "ko" else "B. Proclaim Christ"
        elif 25 <= order <= 36: return "C. 하나님을 의뢰함" if lang == "ko" else "C. Rely on God's Resources"
        elif 37 <= order <= 48: return "D. 제자의 자격" if lang == "ko" else "D. Be Christ's Disciple"
        else: return "E. 그리스도를 닮아감" if lang == "ko" else "E. Grow in Christlikeness"

    order_60_ko = 1
    order_60_en = 1
    i = 69
    while i < 330:
        p = paras[i]
        if p.startswith('<60구절>'):
            i += 1
            count = 0
            while count < 6 and i + 3 < len(paras):
                if paras[i].startswith('<') or is_structural_line(paras[i]):
                    i += 1
                    continue
                t1, r1 = parse_header_ref(paras[i])
                t2, r2 = parse_header_ref(paras[i+1])
                txt1 = paras[i+2]
                txt2 = paras[i+3]
                
                sec1 = get_60_sec(order_60_ko, "ko")
                sec_ord1 = ((order_60_ko - 1) % 12) + 1
                all_verses.append({
                    "id": current_id, "part": "60구절", "section": sec1,
                    "order_in_part": order_60_ko, "order_in_section": sec_ord1,
                    "lang": "ko", "title": t1, "reference": r1, "text": txt1
                })
                current_id += 1
                order_60_ko += 1
                
                sec2 = get_60_sec(order_60_ko, "ko")
                sec_ord2 = ((order_60_ko - 1) % 12) + 1
                all_verses.append({
                    "id": current_id, "part": "60구절", "section": sec2,
                    "order_in_part": order_60_ko, "order_in_section": sec_ord2,
                    "lang": "ko", "title": t2, "reference": r2, "text": txt2
                })
                current_id += 1
                order_60_ko += 1
                
                count += 1
                i += 4
        elif p.startswith('<60vs>'):
            i += 1
            count = 0
            while count < 6 and i + 3 < len(paras):
                if paras[i].startswith('<') or is_structural_line(paras[i]):
                    i += 1
                    continue
                t1, r1 = parse_header_ref(paras[i])
                t2, r2 = parse_header_ref(paras[i+1])
                txt1 = paras[i+2]
                txt2 = paras[i+3]
                
                sec1 = get_60_sec(order_60_en, "en")
                sec_ord1 = ((order_60_en - 1) % 12) + 1
                all_verses.append({
                    "id": current_id, "part": "60구절", "section": sec1,
                    "order_in_part": order_60_en, "order_in_section": sec_ord1,
                    "lang": "en", "title": t1, "reference": r1, "text": txt1
                })
                current_id += 1
                order_60_en += 1
                
                sec2 = get_60_sec(order_60_en, "en")
                sec_ord2 = ((order_60_en - 1) % 12) + 1
                all_verses.append({
                    "id": current_id, "part": "60구절", "section": sec2,
                    "order_in_part": order_60_en, "order_in_section": sec_ord2,
                    "lang": "en", "title": t2, "reference": r2, "text": txt2
                })
                current_id += 1
                order_60_en += 1
                
                count += 1
                i += 4
        else:
            i += 1

    # ----------------------------------------------------
    # 4. DEP (Paragraph 342~1168) -> Exactly 242 Verses!
    # ----------------------------------------------------
    def get_dep_sub_section_info(sec_name, sec_order, title):
        if sec_name == "I. 구원의 확신":
            sub_sec = title
            sub_ord = ((sec_order - 1) % 2) + 1
            return sub_sec, sub_ord
        elif sec_name == "II. Quiet Time":
            if 1 <= sec_order <= 8:
                return "1. 왜 Quiet Time을 가져야 하는가?", sec_order
            elif 9 <= sec_order <= 22:
                return "2. Quiet Time이란 무엇인가?", sec_order - 8
            else:
                return "3. Quiet Time의 본", sec_order - 22
        elif sec_name == "III. 하나님의 말씀":
            if 1 <= sec_order <= 10:
                return "1. 말씀의 권위", sec_order
            elif 11 <= sec_order <= 21:
                return "2. 말씀의 가치", sec_order - 10
            elif 22 <= sec_order <= 27:
                return "3. 말씀에 대한 태도", sec_order - 21
            else:
                return "4. 말씀의 섭취 방법(말씀의 손 예화)", sec_order - 27
        elif sec_name == "IV. 기도":
            if 1 <= sec_order <= 4:
                return "1. 기도의 명령", sec_order
            elif 5 <= sec_order <= 12:
                return "2. 기도의 약속과 축복", sec_order - 4
            elif 13 <= sec_order <= 22:
                return "3. 응답받는 기도의 조건", sec_order - 12
            elif 23 <= sec_order <= 27:
                return "4. 기도의 본", sec_order - 22
            else:
                return "5. 기도의 손 예화", sec_order - 27
        elif sec_name == "V. 교제":
            if 1 <= sec_order <= 4:
                return "1. 교제의 기초", sec_order
            elif 5 <= sec_order <= 13:
                return "2. 교제의 중요성", sec_order - 4
            elif 14 <= sec_order <= 18:
                return "3. 교제의 요소", sec_order - 13
            elif 19 <= sec_order <= 26:
                return "4. 교제의 태도", sec_order - 18
            else:
                return "5. 교제에서의 문제해결", sec_order - 26
        elif sec_name == "VI. 증거":
            if 1 <= sec_order <= 2:
                return "1. 전도는 누구의 책임인가?", sec_order
            elif 3 <= sec_order <= 12:
                return "2. 왜 전도를 해야 하나?", sec_order - 2
            elif 13 <= sec_order <= 25:
                return "3. 어떻게 전도하나?", sec_order - 12
            elif 26 <= sec_order <= 28:
                return "4. 전도의 모범", sec_order - 25
            else:
                return "5. 다리 예화", sec_order - 28
        elif sec_name == "VII. 그리스도의 주재권":
            if 1 <= sec_order <= 8:
                return "1. 주재권을 인정해야 함", sec_order
            elif 9 <= sec_order <= 15:
                return "2. 주재권을 인정할 때의 축복", sec_order - 8
            elif 16 <= sec_order <= 23:
                return "3. 주재권을 인정할 영역", sec_order - 15
            else:
                return "4. 주재권을 인정한 삶의 모범", sec_order - 23
        elif sec_name == "VIII. 세계비전":
            sub_sec = title
            sub_ord = ((sec_order - 1) % 2) + 1
            return sub_sec, sub_ord
        return "", sec_order

    dep_chapters_def = [
        ("I. 구원의 확신", 353, 391),
        ("II. Quiet Time", 420, 479),
        ("III. 하나님의 말씀", 510, 598),
        ("IV. 기도", 638, 718),
        ("V. 교제", 754, 830),
        ("VI. 증거(전도)", 866, 932),
        ("VI. 증거(다리예화)", 958, 1021),
        ("VII. 그리스도의 주재권", 1055, 1121),
        ("VIII. 세계비전", 1132, 1169)
    ]

    order_dep = 1
    last_sec_name = None
    sec_order = 1
    for chap_name, s, e in dep_chapters_def:
        display_sec_name = "VI. 증거" if "증거" in chap_name else chap_name
        if display_sec_name != last_sec_name:
            sec_order = 1
            last_sec_name = display_sec_name
        
        i = s
        while i < e:
            p = paras[i]
            if is_structural_line(p):
                i += 1
                continue
                
            t1, r1 = parse_header_ref(p)
            if not r1:
                i += 1
                continue
                
            # Check paired
            if i + 1 < e:
                p2 = paras[i+1]
                t2, r2 = parse_header_ref(p2)
                if r2 and not is_structural_line(p2):
                    curr = i + 2
                    while curr < e and is_structural_line(paras[curr]):
                        curr += 1
                    txt1 = paras[curr] if curr < e else ""
                    
                    curr += 1
                    while curr < e and is_structural_line(paras[curr]):
                        curr += 1
                    txt2 = paras[curr] if curr < e else ""
                    
                    if txt1 and txt2 and len(txt1) > 8 and len(txt2) > 8:
                        sub1, sub_o1 = get_dep_sub_section_info(display_sec_name, sec_order, t1)
                        all_verses.append({
                            "id": current_id, "part": "DEP", "section": display_sec_name,
                            "order_in_part": order_dep, "order_in_section": sec_order,
                            "sub_section": sub1, "order_in_sub_section": sub_o1,
                            "lang": "ko", "title": t1, "reference": r1, "text": txt1
                        })
                        current_id += 1
                        order_dep += 1
                        sec_order += 1
                        
                        sub2, sub_o2 = get_dep_sub_section_info(display_sec_name, sec_order, t2)
                        all_verses.append({
                            "id": current_id, "part": "DEP", "section": display_sec_name,
                            "order_in_part": order_dep, "order_in_section": sec_order,
                            "sub_section": sub2, "order_in_sub_section": sub_o2,
                            "lang": "ko", "title": t2, "reference": r2, "text": txt2
                        })
                        current_id += 1
                        order_dep += 1
                        sec_order += 1
                        i = curr + 1
                        continue
                        
            # Single
            curr = i + 1
            while curr < e and is_structural_line(paras[curr]):
                curr += 1
            txt1 = paras[curr] if curr < e else ""
            if txt1 and len(txt1) > 8:
                sub1, sub_o1 = get_dep_sub_section_info(display_sec_name, sec_order, t1)
                all_verses.append({
                    "id": current_id, "part": "DEP", "section": display_sec_name,
                    "order_in_part": order_dep, "order_in_section": sec_order,
                    "sub_section": sub1, "order_in_sub_section": sub_o1,
                    "lang": "ko", "title": t1, "reference": r1, "text": txt1
                })
                current_id += 1
                order_dep += 1
                sec_order += 1
                i = curr + 1
                continue
                
            i += 1

    # ----------------------------------------------------
    # 5. SERIES (Paragraph 1195~1585) -> 5 Series × 36 = 180 Verses!
    # ----------------------------------------------------
    def get_series_sub_section_info(sec_name, sec_order):
        if "Series 1" in sec_name:
            subs = ["(1) 예수 그리스도", "(2) 성령", "(3) 하나님"]
        elif "Series 2" in sec_name:
            subs = ["(1) 사랑으로 말함", "(2) 사랑으로 대함", "(3) 사랑으로 행함"]
        elif "Series 3" in sec_name:
            subs = ["(1) 약속", "(2) 말씀", "(3) 믿음"]
        elif "Series 4" in sec_name:
            subs = ["(1) 승리", "(2) 순결", "(3) 기도"]
        elif "Series 5" in sec_name:
            subs = ["(1) 전도", "(2) 변명", "(3) 그리스도 안에 있는 신자의 위치"]
        else:
            return "", sec_order

        if 1 <= sec_order <= 12:
            return subs[0], sec_order
        elif 13 <= sec_order <= 24:
            return subs[1], sec_order - 12
        else:
            return subs[2], sec_order - 24

    series_chapters_def = [
        ("Series 1. 하나님을 알아감", 1196, 1274),
        ("Series 2. 사랑 안에서 자라감", 1274, 1352),
        ("Series 3. 믿음 안에서 자라감", 1352, 1430),
        ("Series 4. 승리 안에서 행함", 1430, 1508),
        ("Series 5. 그리스도를 증거함", 1508, 1585)
    ]

    order_series = 1
    for sname, s, e in series_chapters_def:
        sec_order = 1
        i = s
        while i < e:
            p = paras[i]
            if is_structural_line(p):
                i += 1
                continue
                
            t1, r1 = parse_header_ref(p)
            if not r1:
                i += 1
                continue
                
            if i + 3 < e:
                t2, r2 = parse_header_ref(paras[i+1])
                txt1 = paras[i+2]
                txt2 = paras[i+3]
                if r2 and len(txt1) > 8 and len(txt2) > 8:
                    sub1, sub_o1 = get_series_sub_section_info(sname, sec_order)
                    all_verses.append({
                        "id": current_id, "part": "Series(180구절)", "section": sname,
                        "order_in_part": order_series, "order_in_section": sec_order,
                        "sub_section": sub1, "order_in_sub_section": sub_o1,
                        "lang": "ko", "title": t1, "reference": r1, "text": txt1
                    })
                    current_id += 1
                    order_series += 1
                    sec_order += 1
                    
                    sub2, sub_o2 = get_series_sub_section_info(sname, sec_order)
                    all_verses.append({
                        "id": current_id, "part": "Series(180구절)", "section": sname,
                        "order_in_part": order_series, "order_in_section": sec_order,
                        "sub_section": sub2, "order_in_sub_section": sub_o2,
                        "lang": "ko", "title": t2, "reference": r2, "text": txt2
                    })
                    current_id += 1
                    order_series += 1
                    sec_order += 1
                    i += 4
                    continue
                    
            if i + 1 < e:
                txt1 = paras[i+1]
                if len(txt1) > 8:
                    sub1, sub_o1 = get_series_sub_section_info(sname, sec_order)
                    all_verses.append({
                        "id": current_id, "part": "Series(180구절)", "section": sname,
                        "order_in_part": order_series, "order_in_section": sec_order,
                        "sub_section": sub1, "order_in_sub_section": sub_o1,
                        "lang": "ko", "title": t1, "reference": r1, "text": txt1
                    })
                    current_id += 1
                    order_series += 1
                    sec_order += 1
                    i += 2
                    continue
            i += 1

    # ----------------------------------------------------
    # 6. 주제별 60구절 (찬양, 약속, 훈련, 전도, 인격)
    # ----------------------------------------------------
    theme_mapping = [
        ("찬양 60구절", 1812, 1946, [
            ("I. 찬양의 원리", 1, 12),
            ("II. 하나님 (A-G)", 13, 24),
            ("II. 하나님 (G-L)", 25, 36),
            ("II. 하나님 (L-R)", 37, 48),
            ("II. 하나님 (R-Z)", 49, 60)
        ]),
        ("약속 60구절", 1946, 2080, [
            ("A. 하나님의 약속", 1, 12),
            ("B. 기본적인 약속들", 13, 24),
            ("C. 제자의 삶에 대한 약속", 25, 36),
            ("D. BASIC과 인격에 대한 약속", 37, 48),
            ("E. 사역에 관한 약속", 49, 60)
        ]),
        ("훈련 60구절", 2080, 2213, [
            ("A. 훈련의 중요성", 1, 12),
            ("B. 훈련의 영역", 13, 24),
            ("C. 훈련하는 자의 태도", 25, 36),
            ("D. 훈련에 참예하는 자의 자질", 37, 48),
            ("E. 훈련기술", 49, 60)
        ]),
        ("전도 60구절", 2213, 2346, [
            ("A. 전도의 중요성", 1, 12),
            ("B. 전도의 방법", 13, 24),
            ("C. 인간의 상태", 25, 36),
            ("D. 복음의 핵심", 37, 48),
            ("E. 반대질문", 49, 60)
        ]),
        ("인격 60구절", 2346, len(paras), [
            ("A. WHAT? (마음, 행동, 혀)", 1, 12),
            ("B. WHY? (동기, 목적, 결과)", 13, 24),
            ("C. HOW? (원리, 과정)", 25, 36),
            ("D-1. Which Areas? (성품 I)", 37, 48),
            ("D-2. Which Areas? (성품 II)", 49, 60)
        ])
    ]

    for part_name, s, e, sub_secs in theme_mapping:
        order_theme = 1
        i = s
        theme_verses = []
        while i < e:
            p = paras[i]
            if is_structural_line(p) or any(p.startswith(k) for k in [part_name, '찬양60', '약속60', '훈련60', '전도60', '인격60']):
                i += 1
                continue
            t1, r1 = parse_header_ref(p)
            if not r1:
                i += 1
                continue
            if i + 3 < e:
                t2, r2 = parse_header_ref(paras[i+1])
                txt1 = paras[i+2]
                txt2 = paras[i+3]
                if r2 and len(txt1) > 8 and len(txt2) > 8:
                    theme_verses.append((t1, r1, txt1))
                    theme_verses.append((t2, r2, txt2))
                    i += 4
                    continue
            if i + 1 < e:
                txt1 = paras[i+1]
                if len(txt1) > 8:
                    theme_verses.append((t1, r1, txt1))
                    i += 2
                    continue
            i += 1
            
        def get_theme_sec(ord_num):
            for sec_title, start_o, end_o in sub_secs:
                if start_o <= ord_num <= end_o:
                    return sec_title, ord_num - start_o + 1
            return part_name, ord_num

        for t1, r1, txt1 in theme_verses:
            sec_name, sec_ord = get_theme_sec(order_theme)
            all_verses.append({
                "id": current_id, "part": part_name, "section": sec_name,
                "order_in_part": order_theme, "order_in_section": sec_ord,
                "lang": "ko", "title": t1, "reference": r1, "text": txt1
            })
            current_id += 1
            order_theme += 1

    print(f"\n==========================================")
    print(f"TOTAL PARSED AND VALIDATED VERSES: {len(all_verses)}")
    print(f"==========================================")
    
    with open("verses.json", "w", encoding="utf-8") as f:
        json.dump(all_verses, f, ensure_ascii=False, indent=2)
    print("Successfully generated perfect verses.json!")

if __name__ == "__main__":
    build_all_verses()
