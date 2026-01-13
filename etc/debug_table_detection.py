#!/usr/bin/env python3
"""
테이블 감지 False Positive 디버깅 도구

PyMuPDF가 테이블을 감지했지만 실제로는 유효한 데이터가 없는 경우를 찾아냅니다.
"""

import fitz
from pathlib import Path
import json


def analyze_false_positive_tables(pdf_path: str, output_dir: str = "debug_false_positive_tables"):
    """
    False positive 테이블 감지 분석
    
    Args:
        pdf_path: PDF 파일 경로
        output_dir: 결과 저장 디렉토리
    """
    doc = fitz.open(pdf_path)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    false_positive_pages = []
    results = []
    total_pages = len(doc)
    
    print(f"Analyzing PDF: {pdf_path}")
    print(f"Total pages: {total_pages}")
    print("="*70)
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        try:
            tables = page.find_tables()
            if tables:
                # 각 테이블 검사
                valid_tables = []
                invalid_tables = []
                
                for i, table in enumerate(tables):
                    cells = table.extract()
                    
                    # 유효한 데이터가 있는지 확인
                    has_content = False
                    if cells and len(cells) > 0:
                        has_content = any(
                            any(cell and str(cell).strip() for cell in row)
                            for row in cells
                        )
                    
                    table_info = {
                        'table_id': i,
                        'bbox': table.bbox,
                        'row_count': table.row_count,
                        'col_count': table.col_count,
                        'has_content': has_content,
                        'cells_preview': cells[:3] if cells else None
                    }
                    
                    if has_content:
                        valid_tables.append(table_info)
                    else:
                        invalid_tables.append(table_info)
                
                # False positive인 경우
                if invalid_tables and not valid_tables:
                    false_positive_pages.append(page_num + 1)
                    
                    page_result = {
                        'page': page_num + 1,
                        'total_tables_detected': len(tables),
                        'invalid_tables': invalid_tables
                    }
                    results.append(page_result)
                    
                    print(f"\n❌ Page {page_num + 1}: False Positive")
                    print(f"   Detected {len(tables)} table(s), but all are invalid")
                    
                    for table_info in invalid_tables:
                        print(f"   Table {table_info['table_id']}:")
                        print(f"     - bbox: {table_info['bbox']}")
                        print(f"     - rows: {table_info['row_count']}, cols: {table_info['col_count']}")
                        print(f"     - cells: {table_info['cells_preview']}")
                    
                    # 페이지 이미지 저장
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img_path = output_path / f"page_{page_num + 1:03d}.png"
                    pix.save(str(img_path))
                    print(f"   ✓ Saved: {img_path}")
                
        except Exception as e:
            print(f"❗ Page {page_num + 1}: Error - {e}")
    
    doc.close()
    
    # 결과 요약
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total pages analyzed: {total_pages}")
    print(f"False positive pages: {len(false_positive_pages)}")
    print(f"\nFalse positive page numbers:")
    print(f"{false_positive_pages}")
    
    # JSON으로 저장
    json_path = output_path / "false_positive_analysis.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            'pdf_path': str(pdf_path),
            'total_pages': total_pages,
            'false_positive_count': len(false_positive_pages),
            'false_positive_pages': false_positive_pages,
            'details': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Analysis saved to: {json_path}")
    print(f"✓ Page images saved to: {output_path}/")
    
    return results


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python debug_table_detection.py <pdf_file>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    analyze_false_positive_tables(pdf_path)
