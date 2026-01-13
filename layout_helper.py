"""
fitz 레이아웃 분석 결과 활용 유틸리티

기능:
1. 레이아웃 JSON 로드 및 쿼리
2. 페이지 이미지 추출
3. 테이블 영역 crop
4. Markdown 변환 헬퍼
"""

import json
import fitz
from PIL import Image
import io
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class LayoutHelper:
    """레이아웃 분석 결과 활용 헬퍼"""
    
    def __init__(self, pdf_path: str, layout_json_path: Optional[str] = None):
        self.pdf_path = Path(pdf_path)
        self.doc = fitz.open(str(pdf_path))
        
        # 레이아웃 JSON 로드
        if layout_json_path is None:
            layout_json_path = self.pdf_path.stem + "_layout.json"
        
        with open(layout_json_path, 'r', encoding='utf-8') as f:
            self.layout_data = json.load(f)
        
        print(f"✓ Loaded layout data: {layout_json_path}")
    
    def get_page_strategy(self, page_num: int) -> str:
        """페이지 파싱 전략 조회 (1-based)"""
        page_key = str(page_num - 1)  # JSON은 0-based key
        if page_key in self.layout_data['layouts']:
            return self.layout_data['layouts'][page_key]['strategy']
        return 'unknown'
    
    def is_continuation_page(self, page_num: int) -> bool:
        """Continuation 페이지인지 확인"""
        page_key = str(page_num - 1)
        return page_key in self.layout_data['continuations']
    
    def get_previous_page(self, page_num: int) -> Optional[int]:
        """Continuation의 이전 페이지 번호 (1-based)"""
        page_key = str(page_num - 1)
        if page_key in self.layout_data['continuations']:
            return self.layout_data['continuations'][page_key] + 1
        return None
    
    def get_page_image(self, page_num: int, dpi: int = 200) -> Image.Image:
        """페이지 전체를 이미지로 추출 (1-based)"""
        page = self.doc[page_num - 1]
        pix = page.get_pixmap(dpi=dpi)
        img_data = pix.tobytes("png")
        return Image.open(io.BytesIO(img_data))
    
    def get_table_image(
        self, 
        page_num: int, 
        table_id: int = 0,
        dpi: int = 200,
        margin: int = 10
    ) -> Image.Image:
        """특정 테이블 영역만 이미지로 추출"""
        page = self.doc[page_num - 1]
        
        # 테이블 bbox 가져오기
        page_key = str(page_num - 1)
        if page_key not in self.layout_data['layouts']:
            raise ValueError(f"Page {page_num} not found in layout")
        
        tables = self.layout_data['layouts'][page_key]['tables']
        if table_id >= len(tables):
            raise ValueError(f"Table {table_id} not found on page {page_num}")
        
        bbox = tables[table_id]['bbox']
        
        # Margin 추가
        clip_rect = fitz.Rect(
            bbox[0] - margin,
            bbox[1] - margin,
            bbox[2] + margin,
            bbox[3] + margin
        )
        
        pix = page.get_pixmap(clip=clip_rect, dpi=dpi)
        img_data = pix.tobytes("png")
        return Image.open(io.BytesIO(img_data))
    
    def get_header_columns(self, page_num: int, table_id: int = -1) -> List[str]:
        """테이블 헤더 컬럼명 추출 (마지막 테이블 기본)"""
        page_key = str(page_num - 1)
        if page_key not in self.layout_data['layouts']:
            return []
        
        tables = self.layout_data['layouts'][page_key]['tables']
        if not tables:
            return []
        
        # fitz 추출 데이터는 저장 안 되어 있음 (용량 문제)
        # 실제 추출은 다시 해야 함
        page = self.doc[page_num - 1]
        fitz_tables = page.find_tables()
        
        if not fitz_tables:
            return []
        
        # 마지막 테이블의 헤더
        table = fitz_tables[table_id]
        cells = table.extract()
        
        if cells and len(cells) > 0:
            return cells[0]  # 첫 행 = 헤더
        
        return []
    
    def extract_text_only(self, page_num: int) -> str:
        """텍스트만 추출 (1-based)"""
        page = self.doc[page_num - 1]
        return page.get_text()
    
    def extract_table_as_markdown(self, page_num: int, table_id: int = 0) -> str:
        """테이블을 Markdown으로 변환"""
        page = self.doc[page_num - 1]
        fitz_tables = page.find_tables()
        
        if table_id >= len(fitz_tables):
            return ""
        
        table = fitz_tables[table_id]
        cells = table.extract()
        
        return self._cells_to_markdown(cells)
    
    def _cells_to_markdown(self, cells: List[List[str]]) -> str:
        """2D 셀 배열을 Markdown 테이블로 변환"""
        if not cells or not cells[0]:
            return ""
        
        lines = []
        
        # 헤더
        header = cells[0]
        lines.append("| " + " | ".join(str(c) for c in header) + " |")
        lines.append("|" + "|".join(["---"] * len(header)) + "|")
        
        # 데이터 행
        for row in cells[1:]:
            lines.append("| " + " | ".join(str(c) for c in row) + " |")
        
        return "\n".join(lines)
    
    def get_pages_by_strategy(self, strategy: str) -> List[int]:
        """특정 전략을 사용하는 페이지 목록 (1-based)"""
        pages = []
        for page_key, layout in self.layout_data['layouts'].items():
            if layout['strategy'] == strategy:
                pages.append(int(page_key) + 1)
        return sorted(pages)
    
    def close(self):
        """문서 닫기"""
        if self.doc:
            self.doc.close()


def create_combined_image(
    helper: LayoutHelper,
    prev_page_num: int,
    curr_page_num: int,
    bottom_height: int = 200
) -> Image.Image:
    """
    Continuation 처리용: 이전 페이지 하단 + 현재 페이지 결합
    
    Args:
        helper: LayoutHelper 인스턴스
        prev_page_num: 이전 페이지 번호 (1-based)
        curr_page_num: 현재 페이지 번호 (1-based)
        bottom_height: 이전 페이지에서 가져올 하단 높이 (픽셀)
    
    Returns:
        결합된 PIL Image
    """
    # 이전 페이지 전체
    prev_img = helper.get_page_image(prev_page_num)
    
    # 이전 페이지 하단만 crop
    prev_crop = prev_img.crop((
        0,
        prev_img.height - bottom_height,
        prev_img.width,
        prev_img.height
    ))
    
    # 현재 페이지 전체
    curr_img = helper.get_page_image(curr_page_num)
    
    # 결합
    total_height = prev_crop.height + curr_img.height
    combined = Image.new('RGB', (curr_img.width, total_height), 'white')
    combined.paste(prev_crop, (0, 0))
    combined.paste(curr_img, (0, prev_crop.height))
    
    # 구분선 추가 (선택적)
    from PIL import ImageDraw
    draw = ImageDraw.Draw(combined)
    line_y = prev_crop.height
    draw.line([(0, line_y), (combined.width, line_y)], fill='red', width=3)
    
    return combined


def test_helper():
    """헬퍼 테스트"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python layout_helper.py <pdf_file>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    helper = LayoutHelper(pdf_path)
    
    try:
        print(f"\n{'='*70}")
        print("Testing LayoutHelper")
        print(f"{'='*70}\n")
        
        # 1. 전략별 페이지 목록
        print("Pages by strategy:")
        for strategy in ['fitz-only', 'qwen-simple', 'qwen-continuation']:
            pages = helper.get_pages_by_strategy(strategy)
            if pages:
                print(f"  {strategy:20s}: {pages}")
        
        # 2. Continuation 테스트
        print("\nContinuation pages:")
        continuations = helper.layout_data['continuations']
        for curr_key, prev_key in continuations.items():
            curr_page = int(curr_key) + 1
            prev_page = prev_key + 1
            
            print(f"  Page {curr_page} ← Page {prev_page}")
            
            # 헤더 추출
            header = helper.get_header_columns(prev_page)
            if header:
                print(f"    Header: {header}")
            
            # 결합 이미지 생성 테스트
            combined_img = create_combined_image(helper, prev_page, curr_page)
            output_path = f"combined_page_{prev_page}_{curr_page}.png"
            combined_img.save(output_path)
            print(f"    Saved combined image: {output_path}")
        
        # 3. fitz-only 페이지 테스트
        fitz_pages = helper.get_pages_by_strategy('fitz-only')
        if fitz_pages:
            test_page = fitz_pages[0]
            print(f"\nTesting fitz extraction on page {test_page}:")
            
            # 텍스트 추출
            text = helper.extract_text_only(test_page)
            print(f"  Text length: {len(text)} chars")
            print(f"  First 100 chars: {text[:100]}")
        
    finally:
        helper.close()


if __name__ == '__main__':
    test_helper()
