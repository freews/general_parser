import json
import fitz
from pathlib import Path
from common_parameter import OUTPUT_DIR, PDF_PATH, TABLE_DPI
from step3_image_generator import TableImageGenerator

def recover_with_fitz():
    report_path = Path(OUTPUT_DIR) / "failed_images_report.json"
    output_dir = Path(OUTPUT_DIR) / "section_images_recovery"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not report_path.exists():
        print("No failure report found.")
        return

    with open(report_path, 'r', encoding='utf-8') as f:
        failures = json.load(f)
        
    # 페이지별 그룹화
    pages_to_process = {}
    for fail in failures:
        p = fail['page']
        if p not in pages_to_process:
            pages_to_process[p] = []
        pages_to_process[p].append(fail)
        
    print(f"Recovering {len(pages_to_process)} pages using PyMuPDF (fitz) detection...")
    
    generator = TableImageGenerator(PDF_PATH)
    total_recovered = 0
    
    for page_num, fail_list in pages_to_process.items():
        print(f"\n[Page {page_num}] scanning for tables...")
        
        try:
            page = generator.doc[page_num - 1]
            # PyMuPDF 내장 테이블 감지
            # vertical_strategy='lines', horizontal_strategy='lines' 등으로 선 기반 감지
            # snap_tolerance, join_tolerance 등을 조절할 수 있으나 기본값 사용
            tables_finder = page.find_tables()
            tables = tables_finder.tables
            
            print(f"  Found {len(tables)} tables via fitz.")
            
            # 매핑 전략:
            # 실패한 테이블 수와 찾은 테이블 수가 같으면 1:1 매핑
            # 다르면... 최대한 순서대로 매핑하거나, 가장 큰 녀석을 매핑?
            # 여기서는 순서대로 매핑 시도
            
            for idx, table in enumerate(tables):
                # table.bbox -> (x0, y0, x1, y1)
                bbox = list(table.bbox)
                
                # 파일명 결정
                if idx < len(fail_list):
                    # 실패 리스트의 정보 사용
                    matches = fail_list[idx].get('potential_matches', [])
                    if matches:
                        table_id = matches[0]['table_id']
                    else:
                        table_id = f"table_{page_num}_fitz_{idx+1}"
                else:
                    # 실패 리스트보다 더 많이 찾은 경우 -> 추가 테이블로 저장 (혹시 모르니)
                    table_id = f"table_{page_num}_fitz_extra_{idx+1}"
                
                output_path = output_dir / f"{table_id}.png"
                
                # 유효성 검사 (너무 작은 테이블은 무시)
                if (bbox[2] - bbox[0]) < 50 or (bbox[3] - bbox[1]) < 30:
                    print(f"  Skipping small artifact: {bbox}")
                    continue

                generator.generate_table_image(
                    page_num=page_num,
                    bbox=bbox,
                    output_path=output_path,
                    margin=5,
                    dpi=TABLE_DPI
                )
                print(f"  -> Saved: {output_path.name}")
                total_recovered += 1
                
        except Exception as e:
            print(f"  Error processing page {page_num}: {e}")
            
    generator.close()
    print(f"\nTotal recovered images: {total_recovered}")

if __name__ == "__main__":
    recover_with_fitz()
