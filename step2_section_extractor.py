"""
Section 추출기 V2

전략:
1. Page별 MD 파일 생성 (전체 텍스트)
2. Section list에서 순서대로:
   - 현재 섹션 제목 찾기
   - 다음 섹션 제목 나올 때까지 텍스트 복사
   - 페이지 넘어가도 계속
3. 테이블/그림 정보 매핑
"""

import fitz,os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from common_parameter import PDF_PATH, OUTPUT_DIR


@dataclass
class TableInfo:
    """테이블 정보"""
    table_id: str
    title: Optional[str]
    page: int
    bbox: List[float]
    image_path: str
    markdown: Optional[str] = None
    
    def to_dict(self):
        return {
            "table_id": self.table_id,
            "title": self.title,
            "page": self.page,
            "bbox": self.bbox,
            "image_path": self.image_path,
            "markdown": self.markdown
        }


@dataclass
class FigureInfo:
    """그림 정보"""
    figure_id: str
    title: Optional[str]
    page: int
    bbox: List[float]
    image_path: str
    description: Optional[str] = None
    
    def to_dict(self):
        return {
            "figure_id": self.figure_id,
            "title": self.title,
            "page": self.page,
            "bbox": self.bbox,
            "image_path": self.image_path,
            "description": self.description
        }


@dataclass
class SectionData:
    """섹션 데이터"""
    section_index: int
    section_id: str
    title: str
    level: int
    start_page: int
    end_page: int
    text_content: str
    tables: List[TableInfo]
    figures: List[FigureInfo]
    
    def to_dict(self):
        return {
            "section_index": self.section_index,
            "section_id": self.section_id,
            "title": self.title,
            "level": self.level,
            "pages": {
                "start": self.start_page,
                "end": self.end_page,
                "count": self.end_page - self.start_page + 1
            },
            "content": {
                "text": self.text_content,
                "tables": [t.to_dict() for t in self.tables],
                "figures": [f.to_dict() for f in self.figures]
            },
            "statistics": {
                "table_count": len(self.tables),
                "figure_count": len(self.figures)
            }
        }


class SectionExtractorV2:
    """섹션 추출기 V2"""
    
    def __init__(self, pdf_path: str, layout_json_path: Optional[str] = None):
        self.pdf_path = Path(pdf_path)
        self.doc = fitz.open(str(pdf_path))
        
        # 레이아웃 JSON 로드
        if layout_json_path is None:
            layout_json_path = Path(OUTPUT_DIR) / (self.pdf_path.stem + "_layout.json")
        
        with open(layout_json_path, 'r', encoding='utf-8') as f:
            self.layout_data = json.load(f)
        
        # Page별 MD 캐시
        self.page_md_cache = {}
    
    def generate_page_md(self, page_num: int, header_height: float = 50.0, footer_height: float = 50.0) -> str:
        """
        페이지 전체를 MD로 변환 (테이블, 헤더, 푸터 영역 제외)
        
        Args:
            page_num: 페이지 번호 (1-based)
            header_height: 상단 헤더 영역 높이 (pt)
            footer_height: 하단 푸터 영역 높이 (pt)
        """
        if page_num in self.page_md_cache:
            return self.page_md_cache[page_num]
        
        page = self.doc[page_num - 1]
        page_idx = str(page_num - 1)
        page_height = page.rect.height
        
        # 테이블 bbox 정보 가져오기
        table_bboxes = []
        if page_idx in self.layout_data['layouts']:
            page_layout = self.layout_data['layouts'][page_idx]
            for table in page_layout.get('tables', []):
                # 테이블 영역을 약간 확장하여 텍스트 마스킹 강화
                bbox = fitz.Rect(table['bbox'])
                bbox.x0 -= 2
                bbox.y0 -= 2
                bbox.x1 += 2
                bbox.y1 += 2
                table_bboxes.append(bbox)
        
        # 텍스트 블록별로 추출 (테이블 및 헤더/푸터 영역 제외)
        text_parts = []
        blocks = page.get_text("dict")["blocks"]
        
        for block in blocks:
            if block.get("type") == 0:  # 텍스트 블록
                block_rect = fitz.Rect(block["bbox"])
                
                # 1. 헤더/푸터 영역 체크
                center_y = (block_rect.y0 + block_rect.y1) / 2
                if center_y < header_height or center_y > (page_height - footer_height):
                    continue

                # 2. 테이블과 겹치는지 확인
                overlaps = False
                for table_bbox in table_bboxes:
                    if block_rect.intersects(table_bbox):
                        overlaps = True
                        break
                
                # 테이블과 겹치지 않으면 텍스트 추가
                if not overlaps:
                    for line in block.get("lines", []):
                        line_text = ""
                        for span in line.get("spans", []):
                            line_text += span.get("text", "")
                        if line_text.strip():
                            text_parts.append(line_text)
        
        text = "\n".join(text_parts)
        
        # 캐시에 저장
        self.page_md_cache[page_num] = text
        return text

    # ... (methods omitted)

    def extract_all_sections(self, output_dir: Optional[str] = None):
        # ... (implementation omitted to focus on replacement target)
        # We need to target the filename generation part inside this method, 
        # but since replace_file_content works on contiguous blocks, 
        # I'll replace the generate_page_md method first, then the filename logic in a separate call 
        # or I need to include the whole block if I want to do it in one go.
        # Given the "Single Contiguous Block" rule, I will split this into two tool calls if needed, 
        # but here I will focus on generate_page_md first as requested in the plan
        pass
        
    # Wait, the instruction says "Re-apply ... AND Update filename generation". 
    # Since they are far apart in the file (lines 117 and 444), I must use multi_replace.

    
    def extract_toc_from_text(self) -> List[Dict]:
        """
        문서 텍스트를 스캔하여 TOC(목차) 정보 생성
        PDF 내부 TOC를 신뢰할 수 없으므로 직접 텍스트 패턴으로 추출
        강화된 알고리즘: 폰트 크기 및 Bold 여부 활용
        """
        toc_items = []
        index = 0
        
        print("MOCK TOC 생성 중 (텍스트 스캔 & 구조 분석)...")
        
        # 섹션 번호 패턴 (강화됨): 
        # - 0으로 시작하는 섹션 번호 제외 (예: 00 00 ...)
        # - 1.2.3 형태 허용
        # - 마지막이 점으로 끝나거나 공백으로 이어짐
        section_pattern = re.compile(r'^([1-9]\d*(?:\.\d+)*\.?)\s+(.+)$')
        
        whitelist = [
            "disclaimer", "notices", "license terms", "acknowledgement", 
            "list of tables", "list of figures", "index", 
            "references", "appendix", "abstract", "foreword",
            "introduction", "bibliography", "glossary", "revision history"
        ]
        
        # 1. 문서 전체의 기본 폰트 크기(본문) 파악을 위한 샘플링
        font_sizes = {}
        sample_pages = min(20, len(self.doc))
        for i in range(sample_pages):
            blocks = self.doc[i].get_text("dict")["blocks"]
            for block in blocks:
                if block.get("type") == 0:
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            size = round(span.get("size", 0), 1)
                            font_sizes[size] = font_sizes.get(size, 0) + len(span.get("text", ""))
        
        if font_sizes:
            # 가장 많이 쓰인 폰트 크기를 본문 크기로 간주
            body_font_size = max(font_sizes.items(), key=lambda x: x[1])[0]
        else:
            body_font_size = 10.0 # 기본값
            
        print(f"  Deduced Body Font Size: {body_font_size} pt")

        for page_num in range(1, len(self.doc) + 1):
            page = self.doc[page_num - 1]
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if block.get("type") != 0: continue
                
                # 블록 내 라인 검사
                for line in block.get("lines", []):
                    line_text = ""
                    max_size = 0.0
                    is_bold = False
                    
                    spans = line.get("spans", [])
                    if not spans: continue
                    
                    # 텍스트 재구성 및 Span 간 거리 정보 수집
                    # 섹션 번호와 제목 사이의 간격을 확인하기 위함
                    full_text_spans = [] # (text, end_x, start_x_of_next)
                    
                    for i, span in enumerate(spans):
                        text = span.get("text", "")
                        line_text += text
                        if span.get("size", 0) > max_size:
                            max_size = span.get("size", 0)
                        if "bold" in span.get("font", "").lower():
                            is_bold = True
                        
                        # Span 정보 저장 (text, bbox)
                        # bbox: [x0, y0, x1, y1]
                        full_text_spans.append({
                            "text": text,
                            "bbox": span["bbox"]
                        })
                            
                    line_text = line_text.strip()
                    if not line_text: continue
                    
                    # 제목이 너무 길면 제외 (300자 이상)
                    if len(line_text) > 300: continue

                    # 1. 화이트리스트 체크 (폰트 크기 무관)
                    is_whitelisted = False
                    lower_text = line_text.lower()
                    
                    for item in whitelist:
                        if lower_text == item or (lower_text.startswith(item) and len(lower_text) < 50):
                             if toc_items and toc_items[-1]['title'] == line_text and toc_items[-1]['start_page'] == page_num:
                                 is_whitelisted = False 
                                 break
                             
                             toc_items.append({
                                'index': index,
                                'level': 1,
                                'title': line_text,
                                'start_page': page_num
                             })
                             index += 1
                             is_whitelisted = True
                             break
                    
                    if is_whitelisted: continue
                    
                    # 2. 번호 패턴 체크 + 폰트 검증
                    match = section_pattern.match(line_text)
                    if match:
                        sec_id = match.group(1)
                        sec_title = match.group(2).strip()
                        
                        # [Gap Check] 섹션 번호와 제목 사이의 시각적 간격 확인
                        # 섹션 번호가 포함된 span과 그 다음 span 사이의 거리를 계산
                        # 예: Span1("1.2"), Span2("Scope") -> Span2.x0 - Span1.x1 > Threshold
                        
                        # 매칭된 sec_id("1.2")가 어느 span에 속하는지, 
                        # 그리고 그 뒤의 텍스트가 어느 span에서 시작하는지 찾아야 함.
                        
                        # 간단한 로직: 첫 번째 span이 번호를 포함하고, 그 다음 span이 제목을 포함하는 경우
                        # 또는 번호와 제목이 같은 span에 있다면(드문 경우) 띄어쓰기 개수 확인
                        
                        is_gap_sufficient = False
                        
                        # Case A: 번호와 제목이 서로 다른 span에 있는 경우 (대부분의 PDF 헤더)
                        if len(full_text_spans) >= 2:
                            # 첫 번째 span이 번호만 가지고 있거나 번호로 끝나는 경우
                            first_span_text = full_text_spans[0]["text"].strip()
                            if first_span_text.startswith(sec_id):
                                # 첫 번째 span(번호)의 끝과 두 번째 span(제목)의 시작 사이 거리
                                gap = full_text_spans[1]["bbox"][0] - full_text_spans[0]["bbox"][2]
                                
                                # 5pt 이상이면 충분한 간격으로 간주 (약 스페이스 2개)
                                # 사용자 요청 "Space 10개"는 텍스트상의 표현일 수 있으나, 
                                # PDF 레이아웃상 10~20pt 정도면 확실한 탭 간격임.
                                if gap > 5.0:
                                    is_gap_sufficient = True
                        
                        # Case B: 같은 span에 있는 경우 (예: "1.2    Title")
                        if not is_gap_sufficient:
                            # 텍스트 상에서 번호 뒤에 공백이 2개 이상 있는지 확인
                            if re.match(r'^\d+(\.\d+)*\s{2,}', line_text):
                                is_gap_sufficient = True
                                
                        # [조건 완화] 
                        # 간격이 충분하지 않더라도, 시각적으로 강조된(Bold 혹은 본문보다 큰 폰트) 경우라면 헤더로 인정
                        is_visually_emphasized = False
                        
                        # 본문 폰트보다 0.5pt 이상 크면 강조된 것으로 간주
                        if max_size > body_font_size + 0.5:
                            is_visually_emphasized = True
                        
                        # 혹은 Bold 속성이 있으면 강조된 것으로 간주
                        if is_bold:
                            is_visually_emphasized = True

                        # 최종 판정: 간격이 충분하거나 시각적으로 강조되었어야 함
                        if not is_gap_sufficient and not is_visually_emphasized:
                            continue

                        # 예외 필터링 (False Positive 제거)
                        if len(sec_title) < 2: continue
                        if re.match(r'^\d+(\s+\d+)*$', sec_title): continue 
                        if "..." in line_text: continue
                        
                        # 2-0. 섹션 번호 형식 검증 (추가)
                        # - "666.666" 처럼 숫자가 비정상적으로 크거나 소수점이 많은 경우
                        # - 통상적인 섹션 깊이는 5~6레벨(점 5개) 이내
                        if sec_id.count('.') > 6: continue
                        # - 각 파트가 4자리 이상(예: 2025년 제외하면 드묾)이면 의심
                        if any(len(part) > 3 for part in sec_id.split('.')): continue

                        # 2-1. 숫자 범위 필터링 (예: "5 - 11", "1.2 - 1.5")
                        if re.search(r'\d+\s*-\s*\d+', sec_title): continue

                        # 2-2. 리스트 아이템 및 문장 파편 필터링
                        # 소문자로 시작하면 섹션 제목 아님
                        if sec_title[0].islower(): continue
                        
                        # 2-3. 문장형 시작 단어 필터링 (Stopwords)
                        stopwords = ["If ", "The ", "This ", "When ", "Note"]
                        if any(sec_title.startswith(w) for w in stopwords): continue
                        
                        # 2-4. 서술어 포함 여부 (문장일 확률 높음)
                        verbs = [" is ", " are ", " shall ", " should ", " must ", " will "]
                        if any(v in sec_title.lower() for v in verbs): continue
                        
                        # 2-5. 값 정의/할당 필터링
                        msg_without_parens = re.sub(r'\(.*?\)', '', sec_title)
                        if '=' in msg_without_parens: continue
                        
                        # 2-6. 문장 종료 부호 및 접속사 필터링
                        # 세미콜론, 콤마, 마침표, 콜론 등으로 끝나거나
                        # and, or 등으로 끝나면 문장이 잘린 것으로 간주
                        if sec_title.rstrip().endswith((';', ',', '.', ':')): continue
                        if sec_title.rstrip().lower().endswith((' and', ' or', ' but')): continue
                            
                        # 2-7. 특정 키워드 필터링
                        if "minimum" in sec_title.lower() or "maximum" in sec_title.lower():
                            continue
                        
                        # 폰트 검증: 본문보다 작으면 헤더 아닐 확률 높음
                        if round(max_size, 1) < body_font_size:
                             continue

                        # 레벨 계산
                        level = sec_id.count('.') + 1
                        if sec_id.endswith('.'): level -= 1
                        
                        # 중복 방지
                        if toc_items and toc_items[-1]['title'] == line_text and toc_items[-1]['start_page'] == page_num:
                            continue
                            
                        toc_items.append({
                            'index': index,
                            'level': level,
                            'title': line_text,
                            'start_page': page_num
                        })
                        index += 1
                        
        return toc_items

    def extract_section_id(self, title: str) -> str:
        """섹션 제목에서 섹션 ID 추출"""
        match = re.match(r'^([\d.]+)\s+', title)
        if match:
            return match.group(1)
        return ""
    
    def find_text_between_sections(self, current_section: Dict, 
                                   next_section: Optional[Dict],
                                   all_pages_text: Dict[int, str]) -> str:
        """
        현재 섹션과 다음 섹션 사이의 텍스트 추출
        """
        current_title = current_section['title']
        current_id = self.extract_section_id(current_title)
        start_page = current_section['start_page']
        
        # 다음 섹션 정보
        if next_section:
            next_title = next_section['title']
            next_id = self.extract_section_id(next_title)
            end_page = next_section['start_page']
        else:
            next_title = None
            next_id = None
            end_page = len(self.doc)
        
        # 텍스트 수집
        collected_text = []
        found_start = False
        
        for page_num in range(start_page, end_page + 1):
            if page_num not in all_pages_text:
                continue
            
            page_text = all_pages_text[page_num]
            lines = page_text.split('\n')
            
            for line in lines:
                # 현재 섹션 시작 찾기
                if not found_start:
                    if current_id and current_id in line:
                        found_start = True
                        collected_text.append(line)
                    continue
                
                # 다음 섹션 시작 찾기 (종료 조건)
                if next_id and next_id in line:
                    # 다음 섹션 시작이므로 여기서 중단
                    return '\n'.join(collected_text)
                
                # 텍스트 수집
                collected_text.append(line)
        
        return '\n'.join(collected_text)
    
    def find_section_y_on_page(self, page_num: int, section_id: str) -> Optional[float]:
        """페이지에서 섹션 ID의 Y 좌표 찾기"""
        if not section_id:
            return None
        
        # 페이지 텍스트 블록 가져오기
        page = self.doc[page_num - 1]
        blocks = page.get_text("dict")["blocks"]
        
        for block in blocks:
            if block.get("type") == 0:  # 텍스트 블록
                text = ""
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text += span.get("text", "")
                
                # 섹션 ID가 텍스트에 포함되어 있으면
                if section_id in text:
                    return block["bbox"][1]  # Y 좌표 (top)
        
        return None

    def get_tables_in_section(self, section_info: Dict, 
                            next_section_page: Optional[int] = None, 
                            next_section_y: Optional[float] = None,
                            max_pages: int = 10) -> List[TableInfo]:
        """섹션 내 테이블 정보 추출 (Y 좌표 기반, continuation 포함)"""
        tables = []
        start_page = section_info['start_page']
        current_page = start_page
        
        # 섹션 시작 Y 좌표 찾기 (시작 페이지 필터링용)
        section_id = self.extract_section_id(section_info['title'])
        start_section_y = self.find_section_y_on_page(start_page, section_id)
        
        # 문서 끝 페이지
        doc_end_page = len(self.doc)
        
        # 다음 섹션 시작을 만날 때까지, 혹은 max_pages 만큼 테이블 수집
        while current_page <= doc_end_page and (current_page - start_page) < max_pages:
            page_idx = str(current_page - 1)
            
            # 레이아웃 정보가 없으면 다음 페이지로
            if page_idx not in self.layout_data['layouts']:
                current_page += 1
                continue
            
            page_layout = self.layout_data['layouts'][page_idx]
            
            # 페이지에 테이블이 없으면
            if not page_layout.get('has_table', False):
                pass 
            
            # 이 페이지의 테이블 탐색
            for table in page_layout.get('tables', []):
                table_bbox = table['bbox']
                table_y = table_bbox[1]  # Y 좌표 (top)
                
                # 1. 시작 페이지인 경우: 섹션 시작 위치보다 위에 있는 테이블 제외 (이전 섹션의 continuation)
                if current_page == start_page and start_section_y is not None:
                    if table_y < start_section_y:
                        continue

                # 2. 다음 섹션 시작 페이지인 경우, Y 좌표 체크
                if next_section_page and current_page == next_section_page:
                    if next_section_y is not None:
                        # 테이블이 다음 섹션 시작 위치보다 아래(같거나 큼)에 있으면 중단
                        if table_y >= next_section_y:
                            return tables
                
                # 테이블 추가
                table_id = f"Table_{current_page}_{table['table_id']}"
                tables.append(TableInfo(
                    table_id=table_id,
                    title=table.get('title'),
                    page=current_page,
                    bbox=table_bbox,
                    image_path=f"table_{current_page:03d}_{table['table_id']}.png",
                    markdown=None
                ))
            
            # 종료 조건 체크
            
            # 1. 다음 섹션 페이지에 도달했고, 위 루프에서 return되지 않았다면
            #    (즉, 다음 섹션 시작 Y좌표 이전의 테이블들은 다 담았거나, 테이블이 없었음)
            #    이제 루프 종료
            if next_section_page and current_page == next_section_page:
                break
            
            # 2. 다음 섹션 페이지를 넘어섰으면 종료
            if next_section_page and current_page > next_section_page:
                break
                
            current_page += 1
            
        return tables
    
    def get_figures_in_section(self, section_info: Dict) -> List[FigureInfo]:
        """섹션 내 그림 정보 추출"""
        figures = []
        start_page = section_info['start_page']
        end_page = section_info['end_page']
        
        for page_num in range(start_page, end_page + 1):
            page_idx = str(page_num - 1)
            
            if page_idx not in self.layout_data['layouts']:
                continue
            
            page_layout = self.layout_data['layouts'][page_idx]
            
            if not page_layout.get('has_figure', False):
                continue
            
            for figure in page_layout.get('figures', []):
                fig_id = figure.get('figure_id', 'unknown')
                figure_id = f"Figure_{page_num}_{fig_id}"
                
                figures.append(FigureInfo(
                    figure_id=figure_id,
                    title=figure.get('title'),
                    page=page_num,
                    bbox=figure['bbox'],
                    image_path=f"figure_{page_num:03d}_{fig_id}.png",
                    description=None
                ))
        
        return figures

    def extract_all_sections(self, output_dir: Optional[str] = None):
        """모든 섹션 추출"""
        if output_dir is None:
            output_dir = str(OUTPUT_DIR / "section_data_v2")
            
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # TOC 생성 (직접 추출)
        sections_info = self.extract_toc_from_text()
        
        # 종료 페이지 계산
        for i in range(len(sections_info)):
            if i < len(sections_info) - 1:
                next_start = sections_info[i + 1]['start_page']
                sections_info[i]['end_page'] = max(sections_info[i]['start_page'], next_start - 1)
            else:
                sections_info[i]['end_page'] = len(self.doc)
        
        print(f"\n총 {len(sections_info)}개 섹션 처리 시작...\n")
        
        # 1단계: 모든 페이지의 텍스트 생성
        print("\n[1/2] 페이지별 텍스트 생성 중...")
        all_pages_text = {}
        for page_num in range(1, len(self.doc) + 1):
            all_pages_text[page_num] = self.generate_page_md(page_num)
            if page_num % 10 == 0:
                print(f"  {page_num}/{len(self.doc)} 페이지 완료")
        
        # 2단계: 섹션별로 텍스트 추출
        print("\n[2/2] 섹션별 데이터 추출 중...")
        for i, section_info in enumerate(sections_info):
            # 다음 섹션 정보 미리 확보
            next_section = sections_info[i+1] if i < len(sections_info) - 1 else None
            
            # 다음 섹션 시작정보 계산
            next_section_page = None
            next_section_y = None
            
            if next_section:
                next_section_page = next_section['start_page']
                # 다음 섹션 ID 추출 및 Y좌표 탐색
                next_section_id = self.extract_section_id(next_section['title'])
                next_section_y = self.find_section_y_on_page(next_section_page, next_section_id)
            
            # 텍스트 추출
            text_content = self.find_text_between_sections(
                section_info,
                next_section,
                all_pages_text
            )
            
            # 테이블 정보 추출
            tables = self.get_tables_in_section(
                section_info, 
                next_section_page=next_section_page,
                next_section_y=next_section_y
            )
            
            # 그림 정보
            figures = self.get_figures_in_section(section_info)
            
            if len(tables) > 0 or len(figures) > 0:
                 print(f"[{i+1}/{len(sections_info)}] {section_info['title']}")
                 print(f"  텍스트: {len(text_content)} 문자")
                 print(f"  테이블: {len(tables)}개, 그림: {len(figures)}개")
            else:
                 pass 
            
            # SectionData 생성
            section_data = SectionData(
                section_index=section_info['index'],
                section_id=self.extract_section_id(section_info['title']),
                title=section_info['title'],
                level=section_info['level'],
                start_page=section_info['start_page'],
                end_page=section_info['end_page'],
                text_content=text_content,
                tables=tables,
                figures=figures
            )
            
            # JSON 저장
            # 파일명 생성: {index:03d}_{id}_{title}.json (title에서 id 제거)
            safe_title = section_info['title']
            if safe_title.startswith(section_data.section_id):
                safe_title = safe_title[len(section_data.section_id):].strip()
            
            safe_title = "".join([c if c.isalnum() or c in (' ', '.', '_', '-') else '_' for c in safe_title]).strip()
            safe_title = re.sub(r'\s+', '_', safe_title)  # 공백 -> _
            
            section_filename = f"{section_info['index']:03d}_{section_data.section_id}_{safe_title}.json"
            section_file = output_path / section_filename
            
            with open(section_file, 'w', encoding='utf-8') as f:
                json.dump(section_data.to_dict(), f, ensure_ascii=False, indent=2)
    
        # 인덱스 파일 생성
        index_sections = []
        for s in sections_info:
            section_id = self.extract_section_id(s['title'])
            
            safe_title = s['title']
            if safe_title.startswith(section_id):
                safe_title = safe_title[len(section_id):].strip()
                
            safe_title = "".join([c if c.isalnum() or c in (' ', '.', '_', '-') else '_' for c in safe_title]).strip()
            safe_title = re.sub(r'\s+', '_', safe_title)
            
            index_sections.append({
                "index": s['index'],
                "section_id": section_id,
                "title": s['title'],
                "level": s['level'],
                "pages": f"{s['start_page']}-{s['end_page']}",
                "file": f"{s['index']:03d}_{section_id}_{safe_title}.json"
            })
            
        index_data = {
            "pdf_name": self.pdf_path.name,
            "total_sections": len(sections_info),
            "sections": index_sections
        }
        
        index_file = output_path / "section_index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 완료! 출력: {output_path}")
    
    def close(self):
        """문서 닫기"""
        if self.doc:
            self.doc.close()


def main():
    print("=" * 80)
    print("Section Extractor V2 - 텍스트 패턴 기반 섹션 추출")
    print("=" * 80)
    
    from common_parameter import PDF_PATH, OUTPUT_DIR
    
    # 출력 경로 생성

    os.makedirs(os.path.join(OUTPUT_DIR, "section_data_v2"), exist_ok=True)
    extractor = SectionExtractorV2(
        pdf_path=PDF_PATH,
        layout_json_path=None  # 자동으로 OUTPUT_DIR에서 찾음
    )
    
    try:
        extractor.extract_all_sections(
            output_dir=Path(OUTPUT_DIR) / "section_data_v2"
        )
    finally:
        extractor.close()


if __name__ == '__main__':
    main()
