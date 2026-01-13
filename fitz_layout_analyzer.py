"""
PyMuPDF (fitz) 기반 PDF 레이아웃 분석기

기능:
1. 페이지별 텍스트/테이블/이미지 위치 파악
2. 테이블 구조 추출 (컬럼 수, bbox, 셀 데이터)
3. Continuation 테이블 자동 감지
4. 파싱 전략 결정 (fitz vs QWEN)
"""

import fitz
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class TableInfo:
    """테이블 정보"""
    table_id: int
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    row_count: int
    col_count: int
    cells: List[List[str]]  # 2D array
    is_simple: bool  # fitz로 처리 가능한지
    
    def to_dict(self):
        return {
            'table_id': self.table_id,
            'bbox': self.bbox,
            'row_count': self.row_count,
            'col_count': self.col_count,
            'cell_count': len(self.cells) * len(self.cells[0]) if self.cells else 0,
            'is_simple': self.is_simple
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
                    
                    table_info = TableInfo(
                        table_id=i,
                        bbox=table.bbox,
                        row_count=table.row_count,
                        col_count=table.col_count,
                        cells=cells,
                        is_simple=self._is_simple_table(cells)
                    )
                    
                    layout.tables.append(table_info)
        except Exception as e:
            print(f"  Warning: Table detection failed on page {page_num + 1}: {e}")
        
        # 이미지
        images = page.get_images()
        if images:
            layout.has_image = True
        
        return layout
    
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
        """테이블 continuation 판단 (위치 기반 휴리스틱)"""
        # 둘 다 테이블이 있어야 함
        if not prev_layout.has_table or not curr_layout.has_table:
            return False
        
        # 이전 페이지 마지막 테이블
        prev_table = prev_layout.tables[-1]
        
        # 현재 페이지 첫 테이블
        curr_table = curr_layout.tables[0]
        
        # ===== 위치 기반 휴리스틱 =====
        
        # 조건 1: 현재 페이지 테이블이 페이지 상단에 있는가?
        if curr_table.bbox[1] > 200:  # 상단 200pt 이내 (100에서 완화)
            return False
        
        # 조건 2: 현재 페이지 테이블이 적은 행을 가지는가?
        # (많은 행이면 새로운 테이블일 가능성이 높음)
        if curr_table.row_count > 15:  # 15행 이상이면 새 테이블
            return False
        
        # 조건 3: X 좌표(왼쪽 정렬)가 비슷한가?
        x_diff = abs(prev_table.bbox[0] - curr_table.bbox[0])
        if x_diff > 20:  # 20pt 오차 허용 (10에서 완화)
            return False
        
        # 조건 4: 테이블 너비가 비슷한가?
        prev_width = prev_table.bbox[2] - prev_table.bbox[0]
        curr_width = curr_table.bbox[2] - curr_table.bbox[0]
        width_diff = abs(prev_width - curr_width)
        
        # 너비 차이가 30pt 이내 또는 20% 이내
        if width_diff > 30 and width_diff / max(prev_width, curr_width) > 0.2:
            return False
        
        # 조건 5: 이전 테이블이 충분히 큰가?
        # 작은 테이블은 continuation 가능성 낮음
        if prev_table.row_count < 3:
            # 단, 현재 페이지가 매우 짧으면 (1-2행) continuation 가능
            if curr_table.row_count > 2:
                return False
        
        # 모든 조건을 통과하면 continuation으로 판단
        return True
    
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


def main():
    """테스트 실행"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python fitz_layout_analyzer.py <pdf_file>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    # 분석 실행
    analyzer = FitzLayoutAnalyzer(pdf_path)
    
    try:
        # 전체 분석
        layouts = analyzer.analyze_all_pages()
        
        # 요약 출력
        analyzer.print_summary()
        
        # JSON 저장
        output_path = Path(pdf_path).stem + "_layout.json"
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
                    print(f"  Header columns: {header_info['column_names']}")
                    print(f"  Column count: {header_info['col_count']}")
        
    finally:
        analyzer.close()


if __name__ == '__main__':
    main()
