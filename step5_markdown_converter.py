"""
Section JSON을 읽기 쉬운 Markdown으로 변환

기능:
1. 섹션 헤더 (제목, 레벨)
2. 본문 텍스트
3. 테이블 (LLM 파싱된 table_md 활용)
4. 그림 정보
"""

import json
from pathlib import Path
from typing import Optional
from common_parameter import OUTPUT_DIR, PDF_PATH

from utils_logger import setup_advanced_logger
import logging

logger = setup_advanced_logger(name="step5_markdown_converter", dir=OUTPUT_DIR, log_level=logging.INFO)



def json_to_markdown(json_path: Path, output_dir: Path) -> Path:
    """JSON을 Markdown으로 변환"""
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Markdown 라인 수집
    md_lines = []
    
    # 1. 섹션 헤더
    title = data['title']
    level = data['level']
    section_id = data['section_id']
    
    # 레벨에 따른 헤더 (# 개수)
    header_prefix = '#' * min(level + 1, 6)
    md_lines.append(f"{header_prefix} {title}\n")
    
    # 메타데이터 (주석처럼 표시하거나 생략 가능, 여기서는 작게 표시)
    md_lines.append(f"> **Section ID**: {section_id} | **Page**: {data['pages']['start']}-{data['pages']['end']}\n")
    
    # 2. 본문 텍스트
    text_content = data['content']['text']
    if text_content and text_content.strip():
        md_lines.append(text_content)
        md_lines.append("")
    
    # 3. 테이블
    tables = data['content']['tables']
    if tables:
        md_lines.append("\n---")
        md_lines.append(f"### 📊 Tables ({len(tables)})\n")
        
        for i, table in enumerate(tables, 1):
            table_title = table.get('title') or "Untitled Table"
            md_lines.append(f"#### Table {i}: {table_title}")
            
            # 테이블 이미지 참조 (링크)
            image_filename = table.get('image_path')
            if not image_filename:
                image_filename = f"{table.get('id', 'unknown')}.png"
            
            md_lines.append(f"![{table_title}](../section_images/{image_filename})")
            
            # LLM 파싱 결과 (table_md)
            table_md = table.get('table_md')
            if table_md:
                md_lines.append("\n" + table_md + "\n")
            else:
                md_lines.append("\n*(No markdown content)*\n")
            
            md_lines.append("")
            
    # 4. 그림
    figures = data['content']['figures']
    if figures:
        md_lines.append("\n---")
        md_lines.append(f"### 🖼️ Figures ({len(figures)})\n")
        
        for i, figure in enumerate(figures, 1):
            fig_title = figure.get('title') or "Untitled Figure"
            
            image_filename = figure.get('image_path')
            if not image_filename:
                image_filename = f"{figure.get('id', 'unknown')}.png"
                
            md_lines.append(f"#### Figure {i}: {fig_title}")
            md_lines.append(f"![{fig_title}](../section_images/{image_filename})\n")
            
            if figure.get('description'):
                md_lines.append(f"{figure['description']}\n")
            
            md_lines.append("")

    # 파일 저장
    md_filename = json_path.stem + ".md"
    md_path = output_dir / md_filename
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))
        
    return md_path


def create_index_md(index_json_path: Path, output_dir: Path):
    """전체 인덱스 페이지 생성"""
    if not index_json_path.exists():
        return

    with open(index_json_path, 'r', encoding='utf-8') as f:
        index_data = json.load(f)
        
    md_lines = []
    md_lines.append(f"# {index_data.get('pdf_name', 'Document')} Index\n")
    
    for section in index_data.get('sections', []):
        level = section['level']
        title = section['title']
        section_id = section.get('id', '')
        file_name = section['file'].replace('.json', '.md')
        
        indent = "  " * (level - 1)
        md_lines.append(f"{indent}- [{title}]({file_name})")
        
    with open(output_dir / "INDEX.md", 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))
    logger.info(f"📑 Index created: {output_dir / 'INDEX.md'}")


def main():
    """전체 변환 실행"""
   
    
    # 경로 설정
    section_dir = Path(OUTPUT_DIR) / "section_data_v2"
    markdown_dir = Path(OUTPUT_DIR) / "section_markdown"
    
    # 출력 디렉토리 생성
    markdown_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("=" * 80)
    logger.info("Markdown Converter - JSON to Markdown")
    logger.info("=" * 80)
    
    if not section_dir.exists():
        logger.info(f"Error: Section data directory not found: {section_dir}")
        return

    # JSON 파일 목록
    # 파일명 변경으로 인해 모든 json 파일을 읽되 index 파일 제외
    json_files = sorted(section_dir.glob("*.json"))
    json_files = [f for f in json_files if f.name != "section_index.json"]
    
    logger.info(f"Target sections: {len(json_files)}")
    
    for i, json_file in enumerate(json_files, 1):
        md_file = json_to_markdown(json_file, markdown_dir)
        # logger.info(f"[{i}/{len(json_files)}] Generated: {md_file.name}")
        
    logger.info(f"\n✅ Converted {len(json_files)} sections to Markdown.")
    logger.info(f"Output directory: {markdown_dir}")

    # 인덱스 파일 생성
    create_index_md(section_dir / "section_index.json", markdown_dir)


if __name__ == '__main__':
    main()
