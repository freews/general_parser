"""
Section 추출기 V3 (DeepSeek Layout 기반)

전략:
1. DeepSeek Layout JSON을 순회하며 'title' 타입의 아이템을 섹션 헤더로 식별
2. 섹션 헤더와 다음 헤더 사이의 모든 'text', 'code', 'list', 'table', 'figure' 아이템을 수집
3. 좌표 계산 없이 Layout 순서대로 콘텐츠 구성
4. 훨씬 정확한 구조 파악 가능 (3 Opal 문제 해결)
"""

import fitz
import json
import re
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from common_parameter import PDF_PATH, OUTPUT_DIR


@dataclass
class TableInfo:
    table_id: str
    title: Optional[str]
    page: int
    bbox: List[float] # PDF 좌표 (pt)
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


class SectionExtractorV3:
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.doc = fitz.open(str(pdf_path))
        
        # DeepSeek Layout 로드
        ds_layout_path = Path(OUTPUT_DIR) / "deepseek_layout.json"
        if not ds_layout_path.exists():
            raise FileNotFoundError(f"DeepSeek layout not found at {ds_layout_path}")
            
        with open(ds_layout_path, 'r', encoding='utf-8') as f:
            self.deepseek_layout = json.load(f)
            
        print(f"Loaded DeepSeek layout for {len(self.deepseek_layout)} pages")
        
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
        
    def _get_text_content(self, page_num: int, ds_bbox: List[float]) -> str:
        """PDF에서 해당 영역의 텍스트 추출"""
        pdf_bbox = self._convert_bbox(page_num, ds_bbox)
        page = self.doc[page_num - 1]
        # clip으로 텍스트 추출
        return page.get_text("text", clip=pdf_bbox).strip()

    def _is_valid_section_title(self, text: str) -> bool:
        """섹션 제목인지 검증"""
        # 1. 너무 짧으면 스킵
        if len(text) < 3: return False
        
        # 2. 숫자만 있는 경우 스킵 (페이지 번호 등)
        if re.match(r'^\d+$', text): return False
        
        # 3. 특정 키워드
        if text.lower() in ['table of contents', 'contents']: return False
        
        return True
        
    def _parse_section_id(self, text: str) -> str:
        """섹션 번호 추출"""
        match = re.match(r'^([\d\.]+)', text)
        if match:
            return match.group(1).rstrip('.')
        return ""

    def process(self, output_dir: Path):
        """전체 처리 메인 로직"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Flatten Layout Items
        # 전체 문서를 일렬로 나열된 아이템 리스트로 변환
        all_items = [] # {'page': int, 'item': dict}
        
        for page_num in range(1, len(self.doc) + 1):
            page_key = str(page_num)
            if page_key in self.deepseek_layout:
                items = self.deepseek_layout[page_key]['items']
                for item in items:
                    all_items.append({
                        'page': page_num,
                        'data': item
                    })
        
        print(f"Total Layout Items: {len(all_items)}")
        
        # 2. Identify Sections
        sections = []
        current_section = None
        
        # 기본 섹션 (Front Matter)
        current_section = {
            'index': 0,
            'id': '',
            'title': 'Front Matter',
            'level': 1,
            'start_page': 1,
            'items': [] # text, tables, figures
        }
        
        for entry in all_items:
            page = entry['page']
            item = entry['data']
            itype = item['type']
            bbox = item['bbox']
            
            # 텍스트 추출 (필요할 때만)
            # title, text, list, code 등은 텍스트가 필요함
            # table, figure는 이미지만 필요하지만 캡션이 있을 수 있음
            
            # 섹션 헤더 감지
            is_new_section = False
            if itype == 'title':
                text = self._get_text_content(page, bbox)
                if self._is_valid_section_title(text):
                    # 섹션 번호 확인 (예: "1.2 Scope")
                    sec_id = self._parse_section_id(text)
                    
                    # 새 섹션 시작 조건:
                    # 1. 번호가 있거나
                    # 2. 특별한 제목들 (References, Appendix 등)
                    
                    is_special = any(k in text.lower() for k in [
                        'references', 'appendix', 'introduction', 'acknowledgement'
                    ])
                    
                    if sec_id or is_special:
                        # 기존 섹션 저장
                        if current_section:
                            # 종료 페이지 설정
                            current_section['end_page'] = page if not current_section['items'] else current_section['items'][-1]['page']
                            sections.append(current_section)
                        
                        # 레벨 계산
                        level = 1
                        if sec_id:
                            level = sec_id.count('.') + 1
                        
                        current_section = {
                            'index': len(sections),
                            'id': sec_id,
                            'title': text,
                            'level': level,
                            'start_page': page,
                            'items': []
                        }
                        is_new_section = True
            
            # 현재 섹션에 아이템 추가
            if not is_new_section:
                 # 텍스트 콘텐츠 미리 추출
                text_content = ""
                if itype in ['title', 'text', 'list', 'code', 'index']:
                    text_content = self._get_text_content(page, bbox)
                    # text_content 가 너무 짧거나 이상한 문자열(예: "|") 이면 제외?
                    # 일단 다 포함

                current_section['items'].append({
                    'page': page,
                    'type': itype,
                    'bbox': bbox,
                    'text': text_content
                })

        # 마지막 섹션 추가
        if current_section:
            current_section['end_page'] = len(self.doc)
            sections.append(current_section)
            
        print(f"Identified {len(sections)} sections")
        
        # 3. Generate Output Files
        final_sections_list = []
        
        for sec in sections:
            # 섹션 데이터 구성
            full_text = []
            tables = []
            figures = []
            
            for item in sec['items']:
                if item['type'] in ['title', 'text', 'list', 'code', 'index']:
                    if item['text']:
                        full_text.append(item['text'])
                
                elif item['type'] == 'table':
                    t_id = f"table_{item['page']}_{int(item['bbox'][1])}"
                    # 제목 찾기 (직전 텍스트 아이템)
                    # 리스트를 거꾸로 탐색하면 됨. 하지만 여기선 간단히 N/A
                    tables.append(TableInfo(
                        table_id=t_id,
                        title=None, # 나중에 개선 가능
                        page=item['page'],
                        bbox=self._convert_bbox(item['page'], item['bbox']),
                        image_path=f"{t_id}.png"
                    ))
                    # 테이블 위치 표시
                    full_text.append(f"\n[Table: {t_id}]\n")
                    
                elif item['type'] == 'figure':
                    f_id = f"figure_{item['page']}_{int(item['bbox'][1])}"
                    figures.append(FigureInfo(
                        figure_id=f_id,
                        title=None,
                        page=item['page'],
                        bbox=self._convert_bbox(item['page'], item['bbox']),
                        image_path=f"{f_id}.png"
                    ))
                    full_text.append(f"\n[Figure: {f_id}]\n")

            # 저장
            s_data = SectionData(
                section_index=sec['index'],
                section_id=sec['id'],
                title=sec['title'],
                level=sec['level'],
                start_page=sec['start_page'],
                end_page=sec['end_page'],
                text_content="\n".join(full_text),
                tables=tables,
                figures=figures
            )
            
            # 파일명 안전하게
            safe_title = re.sub(r'[^\w\-_.]', '_', sec['title'])[:50]
            filename = f"{sec['index']:03d}_{sec['id']}_{safe_title}.json"
            
            with open(output_dir / filename, 'w', encoding='utf-8') as f:
                json.dump(s_data.to_dict(), f, indent=2, ensure_ascii=False)
                
            final_sections_list.append({
                'index': sec['index'],
                'id': sec['id'],
                'title': sec['title'],
                'level': sec['level'],
                'file': filename
            })

        # 인덱스 파일
        with open(output_dir / "section_index.json", 'w', encoding='utf-8') as f:
            json.dump({
                "total_sections": len(sections),
                "sections": final_sections_list
            }, f, indent=2, ensure_ascii=False)
            
        print("✅ Processing Complete!")

    def close(self):
        self.doc.close()

def main():
    print("="*60)
    print("Section Extractor V3 (DeepSeek Layout)")
    print("="*60)
    
    extractor = SectionExtractorV3(PDF_PATH)
    try:
        extractor.process(Path(OUTPUT_DIR) / "section_data_v2")
    finally:
        extractor.close()

if __name__ == '__main__':
    main()
