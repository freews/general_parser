"""
Y 좌표 기반 섹션 테이블 수집

섹션 시작/끝 Y 좌표 사이의 모든 테이블 수집
"""

import fitz
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TableInfo:
    table_id: str
    title: Optional[str]
    page: int
    bbox: List[float]
    image_path: str
    
    def to_dict(self):
        return {
            "table_id": self.table_id,
            "title": self.title,
            "page": self.page,
            "bbox": self.bbox,
            "image_path": self.image_path,
            "markdown": None
        }


def extract_section_id(title: str) -> str:
    """섹션 제목에서 ID 추출 (예: "4.2.1.2")"""
    match = re.match(r'^([\d.]+)\s+', title)
    if match:
        return match.group(1)
    return ""


def find_section_y_on_page(page, section_id: str) -> Optional[float]:
    """
    페이지에서 섹션 ID의 Y 좌표 찾기
    
    Returns:
        Y 좌표 또는 None
    """
    if not section_id:
        return None
    
    blocks = page.get_text("dict")["blocks"]
    
    for block in blocks:
        if block.get("type") == 0:  # 텍스트 블록
            text = ""
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text += span.get("text", "")
            
            # 섹션 ID가 텍스트에 있으면
            if section_id in text:
                return block["bbox"][1]  # Y 좌표
    
    return None


def get_tables_by_y_range(doc, layout_data, start_page: int, 
                          next_section_page: Optional[int],
                          next_section_y: Optional[float],
                          max_pages: int = 10) -> List[TableInfo]:
    """
    섹션의 모든 테이블 수집 (여러 페이지에 걸친 continuation 포함)
    
    Args:
        doc: PDF 문서
        layout_data: 레이아웃 JSON
        start_page: 시작 페이지 (이 페이지의 모든 테이블 포함)
        next_section_page: 다음 섹션 시작 페이지 (None이면 문서 끝까지)
        next_section_y: 다음 섹션 시작 Y 좌표
        max_pages: 최대 확인 페이지 수 (무한 루프 방지)
    """
    tables = []
    current_page = start_page
    
    # 다음 섹션 시작을 만날 때까지 계속 수집
    while current_page <= len(doc) and (current_page - start_page) < max_pages:
        page_idx = str(current_page - 1)
        
        if page_idx not in layout_data['layouts']:
            current_page += 1
            continue
        
        page_layout = layout_data['layouts'][page_idx]
        
        if not page_layout.get('has_table', False):
            current_page += 1
            continue
        
        # 이 페이지의 테이블 수집
        found_any_table = False
        for table in page_layout.get('tables', []):
            table_bbox = table['bbox']
            table_y = table_bbox[1]  # Y 좌표
            
            # 다음 섹션 시작 페이지에서 Y 좌표 체크
            if current_page == next_section_page and next_section_y is not None:
                if table_y >= next_section_y:
                    # 다음 섹션 시작 - 여기서 중단
                    return tables
            
            # 테이블 추가
            table_id = f"Table_{current_page}_{table['table_id']}"
            tables.append(TableInfo(
                table_id=table_id,
                title=table.get('title'),
                page=current_page,
                bbox=table_bbox,
                image_path=f"table_{current_page:03d}_{table['table_id']}.png"
            ))
            found_any_table = True
        
        # 다음 섹션 페이지에 도달했고 테이블을 찾지 못했으면 중단
        if current_page == next_section_page and not found_any_table:
            break
        
        # 다음 섹션 페이지를 넘어섰으면 중단
        if next_section_page and current_page > next_section_page:
            break
        
        current_page += 1
    
    return tables


def test_section_089():
    """Section 089 테스트"""
    from common_parameter import PDF_PATH
    
    doc = fitz.open(PDF_PATH)
    
    # 레이아웃 JSON 로드
    with open('TCG-Storage-Opal-SSC-v2.30_pub_layout.json', 'r') as f:
        layout_data = json.load(f)
    
    # Section 089: 4.2.1.2 SPTemplates (M)
    section_089_id = "4.2.1.2"
    section_089_start_page = 35
    
    # Section 090: 4.2.1.3 Table (M)
    section_090_id = "4.2.1.3"
    section_090_start_page = 36
    
    # 1. Section 089 시작 Y 좌표
    page_35 = doc[34]
    start_y = find_section_y_on_page(page_35, section_089_id)
    print(f"Section 089 시작: Page {section_089_start_page}, Y = {start_y}")
    
    # 2. Section 090 시작 Y 좌표
    page_36 = doc[35]
    end_y = find_section_y_on_page(page_36, section_090_id)
    print(f"Section 090 시작: Page {section_090_start_page}, Y = {end_y}")
    
    # 3. 테이블 수집 (다음 섹션 시작 전까지)
    tables = get_tables_by_y_range(
        doc, layout_data,
        start_page=section_089_start_page,
        next_section_page=section_090_start_page,
        next_section_y=end_y
    )
    
    print(f"\n수집된 테이블: {len(tables)}개")
    for table in tables:
        print(f"  - Page {table.page}, Y={table.bbox[1]:.1f}: {table.title or '(No title)'}")
    
    doc.close()
    
    return tables


if __name__ == '__main__':
    print("=" * 80)
    print("Y 좌표 기반 테이블 수집 테스트")
    print("=" * 80)
    print()
    
    tables = test_section_089()
    
    print(f"\n✅ 완료! Section 089에 {len(tables)}개 테이블 수집")
