import fitz
import json
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from common_parameter import PDF_PATH, OUTPUT_DIR
from logger import setup_advanced_logger # error 시 Archive/logger.py 사용할 것 
import logging

logger = setup_advanced_logger(name="step2_section_extractor", log_dir=OUTPUT_DIR, log_level=logging.INFO)



# Fallback 로직을 위해 필요한 정규식 및 타입 임포트
import re

class SectionExtractor:
    def __init__(self, pdf_path: str):
        self.doc = fitz.open(str(pdf_path))
        
        # DeepSeek Layout 로드
        ds_layout_path = Path(OUTPUT_DIR) / "deepseek_layout.json"
        if not ds_layout_path.exists():
            logger.error(f"DeepSeek layout not found at {ds_layout_path}")
            raise FileNotFoundError(f"DeepSeek layout not found at {ds_layout_path}")
            
        with open(ds_layout_path, 'r', encoding='utf-8') as f:
            self.deepseek_layout = json.load(f)
            
        logger.info(f"Loaded DeepSeek layout for {len(self.deepseek_layout)} pages")
        
    def _convert_bbox(self, page_num: int, ds_bbox: List[float]) -> List[float]:
        """DeepSeek bbox (1000-based) -> PDF bbox (pt)"""
        if page_num > len(self.doc):
            return [0, 0, 0, 0]
            
        page = self.doc[page_num - 1]
        width, height = page.rect.width, page.rect.height
        
        return [
            ds_bbox[0] * width / 1000.0,
            ds_bbox[1] * height / 1000.0,
            ds_bbox[2] * width / 1000.0,
            ds_bbox[3] * height / 1000.0
        ]
    
    def _get_text_content(self, page_num: int, ds_bbox: List[float]) -> tuple[str, float]:
        """PDF에서 해당 영역의 텍스트와 폰트 크기 추출 (Fallback용)"""
        pdf_bbox = self._convert_bbox(page_num, ds_bbox)
        page = self.doc[page_num - 1]
        text = page.get_text("text", clip=pdf_bbox).strip()
        
        if not text:
            return "", 0.0
            
        return self._clean_text(text), self._get_avg_font_size(page, pdf_bbox)

    def _get_avg_font_size(self, page: fitz.Page, bbox: List[float]) -> float:
        """해당 영역의 평균 폰트 크기 계산 (Fallback용)"""
        try:
            blocks = page.get_text("dict", clip=bbox)["blocks"]
            total_size = 0.0
            char_count = 0
            for b in blocks:
                for l in b.get("lines", []):
                    for s in l.get("spans", []):
                        total_size += s["size"] * len(s["text"].strip())
                        char_count += len(s["text"].strip())
            
            if char_count > 0:
                return total_size / char_count
            return 0.0
        except Exception:
            return 0.0

    def _clean_text(self, text: str) -> str:
        lines = text.split('\n')
        cleaned = [line.strip() for line in lines if line.strip()]
        return "\n".join(cleaned)

    def _is_valid_section_title(self, text: str) -> bool:
        """섹션 제목 검증 (Fallback용)"""
        if len(text) < 3: return False
        if re.match(r'^\d+$', text): return False
        if text.lower() in ['table of contents', 'contents']: return False
        if re.search(r'\.{3,}\s*\d+$', text) or re.search(r'\.{5,}', text): return False
        if re.search(r'\n\s*\d+$', text): return False
        if re.match(r'^(Figure|Table)\s*\d+', text, re.IGNORECASE): return False
        return True

    def _parse_section_id(self, text: str) -> str:
        """섹션 번호 추출 (Fallback용)"""
        match = re.match(r'^([\d\.]+)', text)
        if match:
            return match.group(1).rstrip('.')
        return ""

    def _normalize_title(self, title: str) -> str:
        """제목 비교를 위한 정규화 (소문자, 공백 제거, 특수문자 제거)"""
        # 섹션 번호 제거 (예: "1.2 Scope" -> "Scope")
        title = re.sub(r'^[\d\.]+\s+', '', title)
        return re.sub(r'[^a-zA-Z0-9]', '', title.lower())

    def _find_matching_layout_item(self, page_num: int, toc_title: str) -> Optional[Dict]:
        """TOC 제목과 매칭되는 DeepSeek Layout 아이템 찾기"""
        if str(page_num) not in self.deepseek_layout:
            return None
            
        items = self.deepseek_layout[str(page_num)]['items']
        toc_norm = self._normalize_title(toc_title)
        
        candidates = []
        
        for item in items:
            if item['type'] == 'title':
                layout_text, _ = self._get_text_content(page_num, item['bbox']) # 폰트사이즈 무시
                layout_norm = self._normalize_title(layout_text)
                
                # 1. 정확 매칭
                if toc_norm == layout_norm:
                    return {'item': item, 'text': layout_text, 'score': 100}
                
                # 2. 부분 매칭 (Layout 텍스트가 TOC 텍스트를 포함하거나 그 반대)
                if toc_norm in layout_norm or layout_norm in toc_norm:
                    if len(layout_norm) > 3:
                        candidates.append({'item': item, 'text': layout_text, 'score': 50})
        
        if candidates:
            return candidates[0]
            
        return None

    def _parse_section_id_from_toc(self, title: str) -> str:
        """TOC 타이틀에서 섹션 번호 추출 (예: "1.2 Scope" -> "1.2")"""
        match = re.match(r'^([\d\.]+)', title)
        if match:
            return match.group(1).rstrip('.')
        return ""

    
    def _assign_attributes_to_content(self, section_items: List[Dict]):
        """
        아이템들을 분석하여 Table/Figure에 Title을 할당하고,
        연속된 Table 사이에 텍스트가 존재하는지 확인하여 플래그 설정.
        
        Refined Logic:
        - Separate matching for Tables (Title Above) and Figures (Title Below).
        - Prevents "shifting" and cross-type assignment errors.
        """
        table_title_pattern = re.compile(r'^Table\s*\d+', re.IGNORECASE)
        figure_title_pattern = re.compile(r'^Figure\s*\d+', re.IGNORECASE)
        
        # 1. Classify Candidates and Content
        tables_content = []
        figures_content = []
        
        table_titles_cand = []
        figure_titles_cand = []
        
        for i, item in enumerate(section_items):
            dtype = item['data']['type']
            
            # Reset attributes
            if 'detected_title' in item['data']: del item['data']['detected_title']
            if 'has_intervening_text' in item['data']: del item['data']['has_intervening_text']
            
            # Content Classification
            if dtype == 'table':
                tables_content.append((i, item))
            elif dtype in ['figure', 'image']:
                figures_content.append((i, item))
            
            # Title Candidate Classification
            elif dtype in ['title', 'text', 'image_caption', 'table_caption']:
                txt, _ = self._get_text_content(item['page'], item['data']['bbox'])
                if not txt: continue
                txt = txt.strip()
                
                bbox = item['data']['bbox']
                y_mid = (bbox[1] + bbox[3]) / 2.0
                
                info = {
                    'index': i,
                    'text': txt,
                    'page': item['page'],
                    'y_mid': y_mid,
                    'bbox': bbox
                }
                
                if table_title_pattern.match(txt):
                    table_titles_cand.append(info)
                elif figure_title_pattern.match(txt):
                    figure_titles_cand.append(info)

        # 2. Match Function
        def match_pairs(content_list, title_list, prefer_title_above=True):
            pairs = []
            for c_idx, (i, content) in enumerate(content_list):
                c_page = content['page']
                c_bbox = content['data']['bbox']
                c_y_mid = (c_bbox[1] + c_bbox[3]) / 2.0
                
                for t_info in title_list:
                    t_page = t_info['page']
                    t_y = t_info['y_mid']
                    
                    # 1. Check Page Distance (Must be same or adjacent)
                    page_diff = t_page - c_page
                    if abs(page_diff) > 1: continue 
                    
                    # 2. Directionality Check
                    # Table (prefer_title_above=True): Title should be visually ABOVE content
                    # Figure (prefer_title_above=False): Title should be visually BELOW content
                    
                    is_above = (t_page < c_page) or (t_page == c_page and t_y < c_y_mid)
                    is_below = (t_page > c_page) or (t_page == c_page and t_y > c_y_mid)
                    
                    penalty = 0
                    if prefer_title_above:
                        if not is_above: penalty = 1000 # Heavy penalty for wrong side
                    else: # prefer below
                        if not is_below: penalty = 1000
                    
                    # 3. Calculate Visual Distance
                    # If separate pages, add large constant but allow typical header/footer spacing
                    dist = abs(t_y - c_y_mid) 
                    if page_diff != 0:
                        dist += 800 # Assume page height ~1000
                        
                    score = dist + penalty
                    
                    # Max distance threshold (e.g. 500 units on same page)
                    if page_diff == 0 and dist > 600: continue
                    
                    pairs.append({
                        'content_idx': i,
                        'title_idx': t_info['index'],
                        'score': score,
                        'text': t_info['text']
                    })
            
            # Sort by score (min distance first)
            pairs.sort(key=lambda x: x['score'])
            
            assigned_c = set()
            assigned_t = set()
            
            for p in pairs:
                if p['content_idx'] in assigned_c: continue
                if p['title_idx'] in assigned_t: continue
                
                # Assign
                section_items[p['content_idx']]['data']['detected_title'] = p['text']
                assigned_c.add(p['content_idx'])
                assigned_t.add(p['title_idx'])
                
            return assigned_c # Return assigned content indices
            
        # 3. Execute Matching
        # Tables -> Titles ABOVE
        match_pairs(tables_content, table_titles_cand, prefer_title_above=True)
        
        # Figures -> Titles BELOW
        match_pairs(figures_content, figure_titles_cand, prefer_title_above=False)
        
        # 4. Intervening Text Check (For Tables)
        # Only check between TABLE items
        table_indices = [i for i, item in enumerate(section_items) if item['data']['type'] == 'table']
        
        for idx_in_list, i in enumerate(table_indices):
            if idx_in_list == 0: continue
            
            prev_i = table_indices[idx_in_list - 1]
            
            # Check range [prev_i + 1, i - 1]
            has_text = False
            for k in range(prev_i + 1, i):
                mid_item = section_items[k]
                m_type = mid_item['data']['type']
                
                # Check text content
                txt, _ = self._get_text_content(mid_item['page'], mid_item['data']['bbox'])
                if not txt: continue
                txt = txt.strip()
                
                # Ignore if it looks like a caption or page number
                if table_title_pattern.match(txt) or figure_title_pattern.match(txt):
                    continue
                    
                if m_type in ['text', 'list']:
                    if len(txt) > 20: 
                        has_text = True
                        break
            
            if has_text:
                section_items[i]['data']['has_intervening_text'] = True

    def process(self, output_dir: Path):
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. TOC 로드
        toc_list = self.doc.get_toc(simple=False) # [[lvl, title, page, dest], ...]
        logger.info(f"PDF TOC loaded: {len(toc_list)} entries")
        
        if not toc_list:
            logger.warning("No TOC found in PDF! Switching to Layout-based extraction (Fallback).")
            self.process_without_toc(output_dir)
            return

        sections = []
        
        # 2. TOC 순회하며 매칭
        for idx, entry in enumerate(toc_list):
            lvl, title, page, dest = entry
            
            # [Filter] Skip invalid TOC entries
            # TCG spec specific: "Bit", "Description" often appear as TOC items incorrectly
            if title.strip() in ["Bit", "Description", "Bytes", "R/W", "Reset"]:
                logger.info(f"Skipping invalid TOC entry: {title}")
                continue

            # 섹션 ID 추출 (TOC 타이틀에 포함되어 있다고 가정)
            # TOC가 "1. Introduction" 형태라면 ID는 "1"
            sec_id = self._parse_section_id_from_toc(title)
            
            # ID가 없다면? (예: "Appendix A") -> 그냥 타이틀 사용하거나 별도 로직
            # 여기서는 편의상 ID가 없으면 빈 문자열
            
            # DeepSeek Layout 매칭
            match_info = self._find_matching_layout_item(page, title)
            
            # 매칭되면 그 좌표 사용, 안되면 페이지 상단으로 가정?
            # 또는 DeepSeek가 못 찾은 섹션은 TOC 정보만으로 생성 (좌표=None)
            
            bbox = match_info['item']['bbox'] if match_info else None
            
            sections.append({
                'index': idx,
                'id': sec_id, # TOC에서 가져온 정확한 ID (예: 3.1.3.1)
                'title': title, # TOC 제목 (예: 3.1.3.1 I/O Controller)
                'level': lvl,
                'start_page': page,
                'bbox': bbox,
                'matched_layout': bool(match_info),
                'items': [] # 나중에 채움
            })
            
        logger.info(f"Initial sections mapped: {len(sections)}")
        
        # 3. Content Allocation (Layout Items -> Sections)
        # 섹션 간의 경계를 기준으로 Content 할당
        # 단순화: 섹션 S의 Content는 S.bbox(top) ~ S+1.bbox(top) 사이의 아이템들
        
        # 전체 딥식 아이템 플래트닝
        all_layout_items = []
        for page_num in range(1, len(self.doc) + 1):
            if str(page_num) in self.deepseek_layout:
                for item in self.deepseek_layout[str(page_num)]['items']:
                    # Title 타입인데 매칭에 사용된 녀석은 제외해야 함 (중복 방지)
                    # 하지만 비교하기 복잡하니 일단 다 넣고 나중에 타입 필터링
                    all_layout_items.append({'page': page_num, 'data': item})

        # 섹션별 아이템 할당 로직
        # 매우 단순화: 아이템의 페이지/Y좌표가 섹션의 범위 내에 있으면 할당
        # 섹션 범위: 
        #   Start: (StartPage, Y_top)
        #   End: (NextSection_StartPage, NextSection_Y_top)
        
        curr_sec_idx = 0
        total_secs = len(sections)
        
        for item_entry in all_layout_items:
            i_page = item_entry['page']
            i_data = item_entry['data']
            i_bbox = i_data['bbox']
            i_y1 = i_bbox[1]
            
            # 현재 섹션 찾기
            # 아이템이 속할 수 있는 가장 마지막 섹션을 찾아야 함 (순차적이니까)
            # 조건: 섹션 시작 위치 <= 아이템 위치
            
            # 최적화: curr_sec_idx 부터 검색
            target_sec = None
            
            # 1. 아이템 위치보다 늦게 시작하는 첫 번째 섹션의 바로 앞 섹션이 타겟
            found = False
            for s_idx in range(curr_sec_idx, total_secs):
                sec = sections[s_idx]
                s_page = sec['start_page']
                
                # BBox 있는 경우만 비교 가능 (없는 경우 페이지 단위로 대충 처리)
                s_y1 = sec['bbox'][1] if sec['bbox'] else 0 
                
                # 아이템 위치 비교
                # 페이지 비교
                if i_page < s_page:
                    # 섹션 시작 페이지보다 이전 -> 이 섹션보다 앞쪽 섹션에 속함
                    target_sec = sections[s_idx - 1] if s_idx > 0 else sections[0] # Front matter 처리 필요
                    curr_sec_idx = s_idx - 1 if s_idx > 0 else 0
                    found = True
                    break
                elif i_page == s_page:
                    # 같은 페이지 -> Y좌표 비교
                    if i_y1 < s_y1:
                        # 섹션 시작보다 위에 있음 -> 앞 섹션
                        target_sec = sections[s_idx - 1] if s_idx > 0 else sections[0]
                        curr_sec_idx = s_idx - 1 if s_idx > 0 else 0
                        found = True
                        break
                
                # 아직 못 찾았으면 다음 섹션 확인 (현재 섹션이 후보가 됨)
                
            if not found:
                # 마지막 섹션까지 검색했는데 break 안 걸림 -> 마지막 섹션에 속함
                target_sec = sections[-1]
                curr_sec_idx = total_secs - 1
            
            # 할당 (Title은 제외? 아니면 포함? 여기선 내용물이므로 포함하되, 섹션 헤더 자체는 
            # 중복으로 들어갈 수 있음. 나중에 정제)
            # 여기서는 단순히 다 넣음.
            if target_sec:
                # 섹션 헤더(Title) 자체는 Content에 포함시키지 않는게 깔끔함
                # 매칭된 녀석인지 확인?
                # BBox 일치 여부로 판단 (약간 오차 허용)
                if target_sec['bbox'] and i_data['type'] == 'title':
                     # 같은 페이지, Y좌표 차이 작음
                     if i_page == target_sec['start_page'] and abs(i_y1 - target_sec['bbox'][1]) < 10:
                         continue # 헤더 스킵

                target_sec['items'].append(item_entry)

        # 4. 저장
        index_data = {
            "total_sections": len(sections),
            "sections": []
        }
        
        for sec in sections:
            # Add Title/Intervening Text Logic
            self._assign_attributes_to_content(sec['items'])

            # 파일명 생성
            raw_title = sec['title']
            sec_id_str = sec['id'] if sec['id'] else "NoID"
            
            # Title이 ID로 시작하는 경우 제거
            # 예: sec['id']="3.1.3", title="3.1.3 Controller Types" -> safe_title="Controller_Types"
            if sec['id'] and raw_title.startswith(sec['id']):
                # ID 뒤의 공백이나 점 등도 같이 제거
                clean_title = raw_title[len(sec['id']):].lstrip(" .-_")
            else:
                clean_title = raw_title
                
            safe_title = re.sub(r'[\\/*?:"<>| \n]', '_', clean_title)[:50]
            # 연속된 _ 제거
            safe_title = re.sub(r'_+', '_', safe_title).strip('_')
            
            filename = f"{sec['index']:03d}_{sec_id_str}_{safe_title}.json"
            
            # Content Text 조합
            content_text = ""
            tables = []
            figures = []
            
            for item in sec['items']:
                itype = item['data']['type']
                if itype in ['text', 'list', 'code']:
                    txt, _ = self._get_text_content(item['page'], item['data']['bbox'])
                    # Cleaning: Remove isolated single characters (artifacts)
                    # e.g., "p", "y" on separate lines
                    cleaned_lines = []
                    for line in txt.split('\n'):
                        line_stripped = line.strip()
                        if len(line_stripped) == 1 and line_stripped.isalpha():
                            continue # Skip single char lines
                        cleaned_lines.append(line)
                    txt = "\n".join(cleaned_lines)
                    
                    if txt.strip():
                        content_text += txt + "\n"
                        
                elif itype == 'table':
                    t_id = f"table_{item['page']}_{int(item['data']['bbox'][1])}"
                    t_data = {
                        'id': t_id,
                        'page': item['page'], 
                        'bbox': item['data']['bbox']
                    }
                    detected_title = item['data'].get('detected_title', '')
                    if detected_title:
                        t_data['detected_title'] = detected_title
                    if item['data'].get('has_intervening_text'):
                        t_data['has_intervening_text'] = True
                        
                    # Rule: If 'table' has a title starting with 'Figure', treat as 'figure'
                    if detected_title and detected_title.lower().startswith("figure"):
                         # Move to figures
                         f_id = t_id.replace('table', 'figure')
                         t_data['id'] = f_id
                         t_data['title'] = detected_title # Set title explicitly
                         figures.append(t_data)
                    else:
                         if detected_title: t_data['title'] = detected_title
                         tables.append(t_data)
                         
                elif itype in ['figure', 'image']:
                    f_id = f"figure_{item['page']}_{int(item['data']['bbox'][1])}"
                    f_data = {
                        'id': f_id, 
                        'page': item['page'], 
                        'bbox': item['data']['bbox']
                    }
                    if item['data'].get('detected_title'):
                        f_data['title'] = item['data']['detected_title']
                    figures.append(f_data)

            sec_data = {
                "section_index": sec['index'],
                "section_id": sec['id'],
                "title": sec['title'],
                "level": sec['level'],
                "pages": {
                    "start": sec['start_page'],
                    "end": sec['items'][-1]['page'] if sec['items'] else sec['start_page'],
                    "count": (sec['items'][-1]['page'] - sec['start_page'] + 1) if sec['items'] else 1
                },
                "content": {
                    "text": content_text.strip(),
                    "tables": tables,
                    "figures": figures
                },
                "statistics": {
                    "table_count": len(tables),
                    "figure_count": len(figures)
                }
            }
            
            with open(output_dir / filename, 'w', encoding='utf-8') as f:
                json.dump(sec_data, f, indent=2, ensure_ascii=False)
                
            index_data['sections'].append({
                "index": sec['index'],
                "id": sec['id'],
                "title": sec['title'],
                "level": sec['level'],
                "file": filename
            })
            
        with open(output_dir / "section_index.json", 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
            
        logger.info("Saved all sections based on TOC.")

    def process_without_toc(self, output_dir: Path):
        """Fallback System: Layout & Font based extraction"""
        logger.info("Starting Fallback Extraction (Rule-based + Visual Hierarchy)...")
        
        # Flatten Items
        all_items = []
        for page_num in range(1, len(self.doc) + 1):
            if str(page_num) in self.deepseek_layout:
                for item in self.deepseek_layout[str(page_num)]['items']:
                    all_items.append({'page': page_num, 'data': item})
        
        sections = []
        current_section = {
            'index': 0, 'id': '', 'title': 'Front Matter', 'level': 1, 
            'start_page': 1, 'items': []
        }
        
        self.level_font_map = {}
        
        for entry in all_items:
            page = entry['page']
            item = entry['data']
            itype = item['type']
            bbox = item['bbox']
            
            # Content accumulation
            if itype != 'title':
                if current_section:
                    current_section['items'].append(entry)
                continue
                
            # Title handling
            text, font_size = self._get_text_content(page, bbox)
            
            if not self._is_valid_section_title(text):
                if current_section:
                    current_section['items'].append(entry)
                continue
                
            sec_id = self._parse_section_id(text)
            is_special = any(k in text.lower() for k in ['references', 'appendix', 'introduction'])
            
            is_new = False
            
            if sec_id or is_special:
                # [New Explicit Section]
                # Save previous
                if current_section:
                    current_section['end_page'] = page if not current_section['items'] else current_section['items'][-1]['page']
                    sections.append(current_section)
                
                level = sec_id.count('.') + 1 if sec_id else 1
                self.level_font_map[level] = font_size
                
                current_section = {
                    'index': len(sections),
                    'id': sec_id,
                    'title': text,
                    'level': level,
                    'start_page': page,
                    'items': []
                }
                
                self.last_numbered_id = sec_id
                self.last_numbered_level = level
                self.last_font_size = font_size
                self.inferred_sub_count = 0
                is_new = True
                
            elif hasattr(self, 'last_numbered_id') and self.last_numbered_id:
                # [Inferred Subsection]
                # Font size check
                # Smaller font -> Child (most likely)
                # Same/Larger -> Sibling? Or Child? 
                # Strategy: If no number, ASSUME CHILD to be safe (avoid skipping siblings)
                
                self.inferred_sub_count += 1
                inferred_id = f"{self.last_numbered_id}.{self.inferred_sub_count}"
                inferred_level = self.last_numbered_level + 1
                
                if current_section:
                    current_section['end_page'] = page if not current_section['items'] else current_section['items'][-1]['page']
                    sections.append(current_section)
                    
                current_section = {
                    'index': len(sections),
                    'id': inferred_id,
                    'title': text,
                    'level': inferred_level,
                    'start_page': page,
                    'items': []
                }
                is_new = True
            
            if not is_new and current_section:
                current_section['items'].append(entry) # Should not happen if logic covers all titles
                
        # Save last section
        if current_section:
            current_section['end_page'] = current_section['items'][-1]['page'] if current_section['items'] else current_section['start_page']
            sections.append(current_section)
            
        # Saving Logic (Duplicate from process_toc but adapted)
        index_data = {"total_sections": len(sections), "sections": []}
        
        for sec in sections:
            # Add Title/Intervening Text Logic
            self._assign_attributes_to_content(sec['items'])
            
            safe_title = re.sub(r'[\\/*?:"<>| \n]', '_', sec['title'])[:50]
            sec_id_str = sec['id'] if sec['id'] else "NoID"
            filename = f"{sec['index']:03d}_{sec_id_str}_{safe_title}.json"
            
            content_text = ""
            tables = []
            figures = []
            
            for item in sec['items']:
                itype = item['data']['type']
                if itype in ['text', 'list', 'code']:
                    txt, _ = self._get_text_content(item['page'], item['data']['bbox'])
                    content_text += txt + "\n"
                elif itype == 'table':
                    t_id = f"table_{item['page']}_{int(item['data']['bbox'][1])}" # Add ID for consistency
                    t_data = {
                        'id': t_id,
                        'page': item['page'], 
                        'bbox': item['data']['bbox']
                    }
                    if item['data'].get('detected_title'):
                        t_data['title'] = item['data']['detected_title']
                    if item['data'].get('has_intervening_text'):
                        t_data['has_intervening_text'] = True
                    tables.append(t_data)
                elif itype == 'figure':
                    f_id = f"figure_{item['page']}_{int(item['data']['bbox'][1])}"
                    f_data = {
                        'id': f_id,
                        'page': item['page'], 
                        'bbox': item['data']['bbox']
                    }
                    if item['data'].get('detected_title'):
                        f_data['title'] = item['data']['detected_title']
                    figures.append(f_data)
            
            sec_data = {
                "section_index": sec['index'],
                "section_id": sec['id'],
                "title": sec['title'],
                "level": sec['level'],
                "pages": {"start": sec['start_page'], "end": sec.get('end_page', sec['start_page']), "count": 1},
                "content": {"text": content_text.strip(), "tables": tables, "figures": figures},
                "statistics": {"table_count": len(tables), "figure_count": len(figures)}
            }
            
            with open(output_dir / filename, 'w', encoding='utf-8') as f:
                json.dump(sec_data, f, indent=2, ensure_ascii=False)
                
            index_data['sections'].append({
                "index": sec['index'], "id": sec['id'], "title": sec['title'], "level": sec['level'], "file": filename
            })
            
        with open(output_dir / "section_index.json", 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
            
        logger.info("Saved all sections based on Fallback (Rule-based).")

def main():
    extractor = SectionExtractor(PDF_PATH)

    extractor.process(Path(OUTPUT_DIR) / "section_data_v2")

if __name__ == "__main__":
    main()
