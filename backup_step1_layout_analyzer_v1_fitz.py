"""
PyMuPDF (fitz) 기반 PDF 레이아웃 분석기

기능:
1. 페이지별 텍스트/테이블/이미지 위치 파악
2. 테이블 구조 추출 (컬럼 수, bbox, 셀 데이터)
3. Continuation 테이블 자동 감지
4. 파싱 전략 결정 (fitz vs QWEN)
"""
import os
import fitz
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from common_parameter import PDF_PATH, OUTPUT_DIR

@dataclass
class TableInfo:
    """테이블 정보"""
    table_id: int
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    row_count: int
    col_count: int
    cells: List[List[str]]  # 2D array
    is_simple: bool  # fitz로 처리 가능한지
    title: Optional[str] = None  # 테이블 제목
    
    def to_dict(self):
        return {
            'table_id': self.table_id,
            'bbox': self.bbox,
            'row_count': self.row_count,
            'col_count': self.col_count,
            'cell_count': len(self.cells) * len(self.cells[0]) if self.cells else 0,
            'is_simple': self.is_simple,
            'title': self.title
        }


@dataclass
class PageLayout:
    """페이지 레이아웃 정보"""
    page_num: int  # 1-based
    width: float
    height: float
    has_text: bool
    has_table: bool
    has_image: bool
    tables: List[TableInfo]
    text_blocks: List[Dict]
    strategy: str  # 'fitz-only', 'qwen-simple', 'qwen-continuation'
    
    def to_dict(self):
        return {
            'page_num': self.page_num,
            'width': self.width,
            'height': self.height,
            'has_text': self.has_text,
            'has_table': self.has_table,
            'has_image': self.has_image,
            'table_count': len(self.tables),
            'tables': [t.to_dict() for t in self.tables],
            'text_block_count': len(self.text_blocks),
            'strategy': self.strategy
        }


class FitzLayoutAnalyzer:
    """fitz 기반 PDF 레이아웃 분석기"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.doc = fitz.open(str(pdf_path))
        self.layouts: Dict[int, PageLayout] = {}
        self.continuations: Dict[int, int] = {}  # {current_page: previous_page}
        
    def analyze_all_pages(self) -> Dict[int, PageLayout]:
        """전체 페이지 분석"""
        print(f"\n{'='*70}")
        print(f"Analyzing PDF: {self.pdf_path.name}")
        print(f"Total pages: {len(self.doc)}")
        print(f"{'='*70}\n")
        
        # 1단계: 각 페이지 레이아웃 분석
        for page_num in range(len(self.doc)):
            layout = self._analyze_single_page(page_num)
            self.layouts[page_num] = layout
            
            print(f"Page {page_num + 1:3d}: ", end="")
            if layout.has_table:
                print(f"Tables={len(layout.tables)}", end=" ")
            if layout.has_image:
                print(f"Images=Yes", end=" ")
            if layout.has_text and not layout.has_table and not layout.has_image:
                print(f"Text-only", end=" ")
            print()
        
        # 2단계: Continuation 관계 파악
        print(f"\n{'='*70}")
        print("Detecting table continuations...")
        print(f"{'='*70}\n")
        
        self.continuations = self._detect_continuations()
        
        for curr_page, prev_page in self.continuations.items():
            print(f"Page {curr_page + 1} continues from Page {prev_page + 1}")
            # 전략 업데이트
            self.layouts[curr_page].strategy = 'qwen-continuation'
            # Continuation 테이블은 제목을 null로 설정 (이전 페이지와 동일한 테이블)
            if self.layouts[curr_page].tables:
                for table in self.layouts[curr_page].tables:
                    table.title = None
        
        # 3단계: 파싱 전략 결정
        self._decide_strategies()
        
        return self.layouts
    
    def _analyze_single_page(self, page_num: int) -> PageLayout:
        """단일 페이지 분석"""
        page = self.doc[page_num]
        
        layout = PageLayout(
            page_num=page_num + 1,  # 1-based
            width=page.rect.width,
            height=page.rect.height,
            has_text=False,
            has_table=False,
            has_image=False,
            tables=[],
            text_blocks=[],
            strategy='unknown'
        )
        
        # 텍스트 블록
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block['type'] == 0:  # 텍스트
                layout.has_text = True
                layout.text_blocks.append({
                    'bbox': block['bbox'],
                    'text': ' '.join([
                        span['text'] 
                        for line in block['lines'] 
                        for span in line['spans']
                    ])[:100]  # 처음 100자만
                })
        
        # 테이블 (fitz의 자동 감지)
        try:
            tables = page.find_tables()
            # tables 객체는 항상 truthy하지만, 실제 테이블이 있는지 확인 필요
            if tables and tables.tables:  # tables.tables 리스트가 비어있지 않은지 확인
                layout.has_table = True
                
                for i, table in enumerate(tables):
                    cells = table.extract()
                    
                    # 테이블 제목 추출
                    title = self._extract_table_title(
                        page, table.bbox, layout.text_blocks, 
                        layout.height, is_continuation=False
                    )
                    
                    table_info = TableInfo(
                        table_id=i,
                        bbox=table.bbox,
                        row_count=table.row_count,
                        col_count=table.col_count,
                        cells=cells,
                        is_simple=self._is_simple_table(cells),
                        title=title
                    )
                    
                    layout.tables.append(table_info)
        except Exception as e:
            print(f"  Warning: Table detection failed on page {page_num + 1}: {e}")
        
        # 이미지
        images = page.get_images()
        if images:
            layout.has_image = True
        
        return layout
    
    def _extract_table_title(self, page, table_bbox: Tuple[float, float, float, float], 
                            text_blocks: List[Dict], page_height: float, 
                            is_continuation: bool = False) -> Optional[str]:
        """테이블 위의 제목 텍스트 추출
        
        Args:
            page: PyMuPDF page object
            table_bbox: 테이블 bounding box (x0, y0, x1, y1)
            text_blocks: 페이지의 텍스트 블록들
            page_height: 페이지 높이
            is_continuation: continuation 테이블인지 여부
        
        Returns:
            테이블 제목 또는 None
        """
        # Continuation 테이블은 제목을 추출하지 않음 (이전 페이지와 동일한 테이블)
        if is_continuation:
            return None
        
        table_x0, table_y0, table_x1, table_y1 = table_bbox
        
        # 헤더/푸터 영역 정의
        header_threshold = 80  # 상단 80pt는 헤더로 간주
        footer_threshold = page_height - 50  # 하단 50pt는 푸터로 간주
        
        # 테이블 위쪽에서 제목을 찾을 범위 (테이블 상단으로부터 최대 150pt 위)
        search_y_min = max(header_threshold, table_y0 - 150)
        search_y_max = table_y0
        
        # 후보 제목들 (테이블 위에 있는 텍스트 블록들)
        table_title_candidates = []  # "Table X -" 패턴
        section_title_candidates = []  # 섹션 제목
        
        for block in text_blocks:
            block_x0, block_y0, block_x1, block_y1 = block['bbox']
            
            # 헤더/푸터 영역은 제외
            if block_y0 < header_threshold or block_y1 > footer_threshold:
                continue
            
            # 테이블 위쪽 범위에 있는지 확인
            if search_y_min <= block_y1 <= search_y_max:
                # 테이블과 수평적으로 겹치는지 확인 (제목은 보통 테이블 위에 위치)
                horizontal_overlap = not (block_x1 < table_x0 or block_x0 > table_x1)
                
                if horizontal_overlap:
                    text = block.get('text', '').strip()
                    
                    # 너무 짧거나 숫자만 있는 것 제외
                    if not text or len(text) < 3 or text.isdigit():
                        continue
                    
                    # 너무 긴 텍스트는 본문으로 간주 (100자 이상)
                    if len(text) > 100:
                        continue
                    
                    # 테이블과의 거리 계산
                    distance = table_y0 - block_y1
                    
                    # "Table X -" 패턴이 있으면 명시적 테이블 제목
                    if text.lower().startswith('table ') and '-' in text:
                        table_title_candidates.append({
                            'text': text,
                            'distance': distance,
                            'y': block_y1
                        })
                    # 짧고 대문자가 많으면 섹션 제목일 가능성
                    elif len(text) < 60:
                        # 대문자 비율 계산
                        alpha_chars = [c for c in text if c.isalpha()]
                        if alpha_chars:
                            upper_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
                            # 대문자 비율이 높거나 (>30%) 숫자로 시작하면 (예: "1.7 Definition") 섹션 제목
                            if upper_ratio > 0.3 or (text[0].isdigit() and '.' in text[:5]):
                                section_title_candidates.append({
                                    'text': text,
                                    'distance': distance,
                                    'y': block_y1
                                })
        
        # 1순위: "Table X -" 패턴이 있는 명시적 테이블 제목
        if table_title_candidates:
            table_title_candidates.sort(key=lambda x: x['distance'])
            closest = table_title_candidates[0]
            if closest['distance'] <= 50:
                return closest['text']
        
        # 2순위: 섹션 제목 (테이블 제목이 없는 경우)
        # 섹션 제목은 참고용으로만 사용하거나 null 반환
        # 사용자 요청에 따라 섹션 제목을 반환할 수도 있음
        # if section_title_candidates:
        #     section_title_candidates.sort(key=lambda x: x['distance'])
        #     closest = section_title_candidates[0]
        #     if closest['distance'] <= 100:
        #         return f"[{closest['text']}]"  # 섹션 제목임을 표시
        
        # 제목을 찾지 못함
        return None
    
    def _is_simple_table(self, cells: List[List[str]]) -> bool:
        """단순 테이블 판단 (fitz로 처리 가능)"""
        if not cells or not cells[0]:
            return False
        
        # 빈 셀 비율 체크
        total_cells = sum(len(row) for row in cells)
        if total_cells == 0:
            return False
        
        empty_cells = sum(
            1 for row in cells 
            for cell in row 
            if not cell or not str(cell).strip()
        )
        
        empty_ratio = empty_cells / total_cells
        
        # 30% 미만 빈 셀이면 단순 테이블
        return empty_ratio < 0.3
    
    def _detect_continuations(self) -> Dict[int, int]:
        """페이지 넘어가는 테이블 감지"""
        continuations = {}
        
        for page_num in range(1, len(self.doc)):
            prev_layout = self.layouts[page_num - 1]
            curr_layout = self.layouts[page_num]
            
            if self._is_continuation(prev_layout, curr_layout):
                continuations[page_num] = page_num - 1
        
        return continuations
    
    def _is_continuation(self, prev_layout: PageLayout, curr_layout: PageLayout) -> bool:
        """테이블 continuation 판단 (간단한 2가지 조건)"""
        # 둘 다 테이블이 있어야 함
        if not prev_layout.has_table or not curr_layout.has_table:
            return False
        
        # 이전 페이지 마지막 테이블
        prev_table = prev_layout.tables[-1]
        
        # 현재 페이지 첫 테이블
        curr_table = curr_layout.tables[0]
        
        # ===== 핵심 조건 2가지 =====
        
        # 조건 1: 컬럼/행 구조가 동일한가?
        # 같은 테이블이라면 구조가 동일해야 함 (회전된 경우도 고려)
        col_match = prev_table.col_count == curr_table.col_count
        
        # Non-empty 헤더 컬럼 수로도 비교 (병합된 셀 처리)
        prev_non_empty = self._get_non_empty_column_count(prev_table)
        curr_non_empty = self._get_non_empty_column_count(curr_table)
        non_empty_match = prev_non_empty == curr_non_empty
        
        rotated_match = (prev_table.col_count == curr_table.row_count or 
                        prev_table.row_count == curr_table.col_count)
        
        if not (col_match or non_empty_match or rotated_match):
            return False
        
        # 조건 2: 테이블 사이에 의미있는 텍스트가 있는가?
        # 텍스트가 있으면 별개의 테이블
        if self._has_text_between_tables(prev_layout, curr_layout, prev_table, curr_table):
            return False
        
        # 두 조건을 모두 만족하면 continuation
        return True
    
    def _get_non_empty_column_count(self, table: TableInfo) -> int:
        """테이블 헤더의 non-empty 컬럼 수 반환"""
        if not table.cells or len(table.cells) == 0:
            return 0
        
        # 첫 번째 행(헤더)에서 비어있지 않은 셀 개수
        # PyMuPDF가 2줄 헤더를 2개 셀로 파싱하지만, 양쪽 페이지 모두 동일하게 파싱되므로
        # 필터링 없이 그대로 카운트하는 것이 더 정확함
        header_row = table.cells[0]
        non_empty_count = sum(
            1 for cell in header_row 
            if cell and str(cell).strip()
        )
        return non_empty_count
    
    def _has_text_between_tables(self, prev_layout: PageLayout, curr_layout: PageLayout, 
                                   prev_table: TableInfo, curr_table: TableInfo) -> bool:
        """테이블 사이에 의미있는 텍스트가 있는지 확인"""
        
        # 1. 이전 페이지: 테이블 끝(y1) 아래에 텍스트가 있는가?
        prev_table_bottom = prev_table.bbox[3]  # y1
        prev_page_height = prev_layout.height
        
        # 페이지 하단 여백 (헤더/푸터 영역 제외)
        prev_footer_threshold = prev_page_height - 50  # 하단 50pt는 푸터로 간주
        
        for block in prev_layout.text_blocks:
            block_top = block['bbox'][1]  # y0
            block_bottom = block['bbox'][3]  # y1
            
            # 테이블 아래 & 푸터 위에 있는 텍스트
            if block_top > prev_table_bottom and block_bottom < prev_footer_threshold:
                text = block.get('text', '').strip()
                # 의미있는 텍스트인지 확인 (페이지 번호 등 제외)
                if len(text) > 10 and not text.isdigit():
                    return True
        
        # 2. 현재 페이지: 테이블 시작(y0) 위에 텍스트가 있는가?
        curr_table_top = curr_table.bbox[1]  # y0
        
        # 페이지 상단 여백 (헤더 영역 제외)
        curr_header_threshold = 50  # 상단 50pt는 헤더로 간주
        
        for block in curr_layout.text_blocks:
            block_top = block['bbox'][1]  # y0
            block_bottom = block['bbox'][3]  # y1
            
            # 헤더 아래 & 테이블 위에 있는 텍스트
            if block_top > curr_header_threshold and block_bottom < curr_table_top:
                text = block.get('text', '').strip()
                # 의미있는 텍스트인지 확인
                if len(text) > 10 and not text.isdigit():
                    return True
        
        # 텍스트가 없으면 continuation 가능성 높음
        return False

    
    def _decide_strategies(self):
        """각 페이지의 파싱 전략 결정"""
        for page_num, layout in self.layouts.items():
            # Continuation은 이미 결정됨
            if layout.strategy == 'qwen-continuation':
                continue
            
            # 텍스트만 → fitz로 처리
            if layout.has_text and not layout.has_table and not layout.has_image:
                layout.strategy = 'fitz-only'
            
            # 테이블이 있고 단순한 경우 → fitz 시도
            elif layout.has_table and not layout.has_image:
                # 모든 테이블이 단순한가?
                if all(t.is_simple for t in layout.tables):
                    layout.strategy = 'fitz-only'
                else:
                    layout.strategy = 'qwen-simple'
            
            # 복잡한 경우 → QWEN
            else:
                layout.strategy = 'qwen-simple'
    
    def get_header_info(self, page_num: int) -> Optional[Dict]:
        """특정 페이지 테이블의 헤더 정보 추출 (continuation용)"""
        if page_num not in self.layouts:
            return None
        
        layout = self.layouts[page_num]
        if not layout.has_table:
            return None
        
        # 마지막 테이블의 헤더 (보통 첫 행)
        table = layout.tables[-1]
        
        if not table.cells or len(table.cells) == 0:
            return None
        
        return {
            'column_names': table.cells[0],  # 첫 행 = 헤더
            'col_count': table.col_count,
            'bbox': table.bbox
        }
    
    def export_to_json(self, output_path: str):
        """분석 결과를 JSON으로 저장"""
        output = {
            'pdf_name': self.pdf_path.name,
            'total_pages': len(self.doc),
            'layouts': {
                page_num: layout.to_dict() 
                for page_num, layout in self.layouts.items()
            },
            'continuations': {
                str(curr): prev 
                for curr, prev in self.continuations.items()
            },
            'statistics': self._get_statistics()
        }
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Layout analysis saved to: {output_path}")
    
    def _get_statistics(self) -> Dict:
        """통계 정보"""
        strategies = {}
        for layout in self.layouts.values():
            strategies[layout.strategy] = strategies.get(layout.strategy, 0) + 1
        
        return {
            'total_pages': len(self.layouts),
            'pages_with_tables': sum(1 for l in self.layouts.values() if l.has_table),
            'pages_with_images': sum(1 for l in self.layouts.values() if l.has_image),
            'total_tables': sum(len(l.tables) for l in self.layouts.values()),
            'continuation_count': len(self.continuations),
            'strategies': strategies
        }
    
    def print_summary(self):
        """분석 결과 요약 출력"""
        stats = self._get_statistics()
        
        print(f"\n{'='*70}")
        print("Analysis Summary")
        print(f"{'='*70}")
        print(f"Total pages:         {stats['total_pages']}")
        print(f"Pages with tables:   {stats['pages_with_tables']}")
        print(f"Pages with images:   {stats['pages_with_images']}")
        print(f"Total tables:        {stats['total_tables']}")
        print(f"Continuations found: {stats['continuation_count']}")
        print(f"\nParsing strategies:")
        for strategy, count in stats['strategies'].items():
            print(f"  {strategy:20s}: {count:3d} pages")
        print(f"{'='*70}\n")
    
    def close(self):
        """문서 닫기"""
        if self.doc:
            self.doc.close()


def main(pdf_path: str):
    """테스트 실행"""
    import sys
    
    try:
        pdf_path = sys.argv[1]
    except IndexError:
        pdf_path = PDF_PATH
    print(f"\nAnalyzing PDF: {pdf_path}")
    # 분석 실행
    analyzer = FitzLayoutAnalyzer(pdf_path)
    
    try:
        # 전체 분석
        layouts = analyzer.analyze_all_pages()
        
        # 요약 출력
        analyzer.print_summary()
        
        # JSON 저장
        output_path = Path(OUTPUT_DIR)/(Path(pdf_path).stem + "_layout.json")
        analyzer.export_to_json(output_path)
        
        # Continuation 상세 정보
        if analyzer.continuations:
            print("\nContinuation Details:")
            print("="*70)
            for curr_page, prev_page in analyzer.continuations.items():
                print(f"\nPage {curr_page + 1} ← Page {prev_page + 1}")
                
                # 이전 페이지 헤더 정보
                header_info = analyzer.get_header_info(prev_page)
                if header_info:
                    # 빈 문자열 제거하고 실제 컬럼명만 표시
                    non_empty_columns = [col for col in header_info['column_names'] if col and str(col).strip()]
                    print(f"  Header columns: {non_empty_columns}")
                    print(f"  Column count (total): {header_info['col_count']}")
                    print(f"  Column count (non-empty): {len(non_empty_columns)}")
        
    finally:
        analyzer.close()


if __name__ == '__main__':
    main(PDF_PATH)
