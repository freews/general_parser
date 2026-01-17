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
    
    def generate_page_md(self, page_num: int) -> str:
        """
        페이지 전체를 MD로 변환 (테이블 영역 제외)
        
        Args:
            page_num: 페이지 번호 (1-based)
        """
        if page_num in self.page_md_cache:
            return self.page_md_cache[page_num]
        
        page = self.doc[page_num - 1]
        page_idx = str(page_num - 1)
        
        # 테이블 bbox 정보 가져오기
        table_bboxes = []
        if page_idx in self.layout_data['layouts']:
            page_layout = self.layout_data['layouts'][page_idx]
            for table in page_layout.get('tables', []):
                table_bboxes.append(fitz.Rect(table['bbox']))
        
        # 텍스트 블록별로 추출 (테이블 영역 제외)
        text_parts = []
        blocks = page.get_text("dict")["blocks"]
        
        for block in blocks:
            if block.get("type") == 0:  # 텍스트 블록
                block_rect = fitz.Rect(block["bbox"])
                
                # 테이블과 겹치는지 확인
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
        
        # TOC 읽기
        toc = self.doc.get_toc()
        sections_info = []
        
        for i, (level, title, page) in enumerate(toc):
            sections_info.append({
                'index': i,
                'level': level,
                'title': title,
                'start_page': page
            })
        
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
            section_id_safe = section_data.section_id.replace('.', '_')
            section_filename = f"section_{section_info['index']:03d}_{section_id_safe}.json"
            section_file = output_path / section_filename
            
            with open(section_file, 'w', encoding='utf-8') as f:
                json.dump(section_data.to_dict(), f, ensure_ascii=False, indent=2)
    
        # 인덱스 파일 생성
        index_data = {
            "pdf_name": self.pdf_path.name,
            "total_sections": len(sections_info),
            "sections": [
                {
                    "index": s['index'],
                    "section_id": self.extract_section_id(s['title']),
                    "title": s['title'],
                    "level": s['level'],
                    "pages": f"{s['start_page']}-{s['end_page']}",
                    "file": f"section_{s['index']:03d}_{self.extract_section_id(s['title']).replace('.', '_')}.json"
                }
                for s in sections_info
            ]
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
