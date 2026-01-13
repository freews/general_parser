"""
fitz 레이아웃 분석 - 사용 예시

기본 워크플로우:
1. fitz_layout_analyzer로 PDF 분석
2. layout_helper로 결과 활용
3. 전략에 따라 fitz 또는 QWEN 사용
"""

import sys
from pathlib import Path


def example_basic_analysis():
    """예시 1: 기본 분석"""
    print("\n" + "="*70)
    print("Example 1: Basic Layout Analysis")
    print("="*70)
    
    from fitz_layout_analyzer import FitzLayoutAnalyzer
    
    pdf_path = "./source_doc/TCG-Storage-Opal-SSC-v2.30_pub.pdf"  
    
    # 분석 실행
    analyzer = FitzLayoutAnalyzer(pdf_path)
    layouts = analyzer.analyze_all_pages()
    
    # 결과 출력
    analyzer.print_summary()
    
    # JSON 저장
    analyzer.export_to_json("layout_result.json")
    
    analyzer.close()


def example_use_layout():
    """예시 2: 분석 결과 활용"""
    print("\n" + "="*70)
    print("Example 2: Using Layout Results")
    print("="*70)
    
    from layout_helper import LayoutHelper
    
    pdf_path = "./source_doc/TCG-Storage-Opal-SSC-v2.30_pub.pdf"  
    helper = LayoutHelper(pdf_path, "layout_result.json")
    
    # 전략별 페이지 확인
    fitz_pages = helper.get_pages_by_strategy('fitz-only')
    qwen_pages = helper.get_pages_by_strategy('qwen-simple')
    cont_pages = helper.get_pages_by_strategy('qwen-continuation')
    
    print(f"\nPages to process with fitz: {fitz_pages}")
    print(f"Pages to process with QWEN: {qwen_pages}")
    print(f"Continuation pages: {cont_pages}")
    
    # fitz-only 페이지 처리
    for page_num in fitz_pages[:3]:  # 처음 3개만
        text = helper.extract_text_only(page_num)
        print(f"\nPage {page_num} (fitz):")
        print(f"  Length: {len(text)} chars")
    
    helper.close()


def example_continuation_handling():
    """예시 3: Continuation 페이지 처리"""
    print("\n" + "="*70)
    print("Example 3: Handling Continuation Tables")
    print("="*70)
    
    from layout_helper import LayoutHelper, create_combined_image
    
    pdf_path = "./source_doc/TCG-Storage-Opal-SSC-v2.30_pub.pdf"  
    helper = LayoutHelper(pdf_path, "layout_result.json")
    
    # Continuation 페이지 찾기
    cont_pages = helper.get_pages_by_strategy('qwen-continuation')
    
    for curr_page in cont_pages:
        prev_page = helper.get_previous_page(curr_page)
        
        print(f"\nPage {curr_page} continues from page {prev_page}")
        
        # 이전 페이지 헤더 추출
        header = helper.get_header_columns(prev_page)
        print(f"  Header columns: {header}")
        
        # 결합 이미지 생성 (QWEN에게 전달할 이미지)
        combined_img = create_combined_image(helper, prev_page, curr_page)
        
        # QWEN에게 전달할 프롬프트 생성
        # None 값 필터링
        header_str = ' | '.join(str(h) if h else '' for h in header)
        prompt = f"""Extract the table from this image.

Column headers (from previous page): {header_str}
Number of columns: {len(header)}

This is a continuation table. The top part (above red line) shows 
the context from previous page. Extract ONLY the table content 
below the red line and format as Markdown table."""
        
        print(f"  Prompt created for QWEN")
        print(f"  Combined image size: {combined_img.size}")
        
        # 실제로 QWEN 호출은 여기서 수행 (예시)
        # TODO: 실제 VLLM 모델 사용 시 아래 주석 해제
        # from qwen_vl import QwenVLModel
        # qwen_model = QwenVLModel()
        # result = qwen_model.generate(combined_img, prompt)
        # print(f"  QWEN result: {result}")
    
    print(f"\n✓ Processed {len(cont_pages)} continuation pages")
    print(f"  Note: Actual VLLM processing not implemented in this example")
    
    helper.close()


def example_table_extraction():
    """예시 4: 테이블 직접 추출"""
    print("\n" + "="*70)
    print("Example 4: Direct Table Extraction with fitz")
    print("="*70)
    
    from layout_helper import LayoutHelper
    
    pdf_path = "./source_doc/TCG-Storage-Opal-SSC-v2.30_pub.pdf"  
    helper = LayoutHelper(pdf_path, "layout_result.json")
    
    # fitz-only 페이지의 테이블 추출
    fitz_pages = helper.get_pages_by_strategy('fitz-only')
    
    for page_num in fitz_pages[:2]:  # 처음 2개만
        # 테이블이 있는지 확인
        page_key = str(page_num - 1)
        layout = helper.layout_data['layouts'][page_key]
        
        if layout['table_count'] > 0:
            print(f"\nPage {page_num}: {layout['table_count']} table(s)")
            
            # 첫 번째 테이블 추출
            markdown = helper.extract_table_as_markdown(page_num, table_id=0)
            print(f"Markdown output:")
            print(markdown[:500])  # 처음 500자만
    
    helper.close()


def example_integrated_workflow():
    """예시 5: 전체 통합 워크플로우"""
    print("\n" + "="*70)
    print("Example 5: Complete Integrated Workflow")
    print("="*70)
    
    from fitz_layout_analyzer import FitzLayoutAnalyzer
    from layout_helper import LayoutHelper, create_combined_image
    
    pdf_path = "./source_doc/TCG-Storage-Opal-SSC-v2.30_pub.pdf"  
    
    # Step 1: 레이아웃 분석
    print("\nStep 1: Analyzing layout...")
    analyzer = FitzLayoutAnalyzer(pdf_path)
    layouts = analyzer.analyze_all_pages()
    analyzer.export_to_json("layout.json")
    analyzer.close()
    
    # Step 2: 결과 로드
    print("\nStep 2: Loading layout results...")
    helper = LayoutHelper(pdf_path, "layout.json")
    
    # Step 3: 전략별 처리
    print("\nStep 3: Processing pages by strategy...")
    
    results = []
    
    # 3-1. fitz-only 페이지
    fitz_pages = helper.get_pages_by_strategy('fitz-only')
    print(f"\nProcessing {len(fitz_pages)} fitz-only pages...")
    
    for page_num in fitz_pages:
        text = helper.extract_text_only(page_num)
        results.append({
            'page': page_num,
            'strategy': 'fitz-only',
            'content': text
        })
    
    # 3-2. qwen-simple 페이지
    qwen_pages = helper.get_pages_by_strategy('qwen-simple')
    print(f"\nProcessing {len(qwen_pages)} qwen-simple pages...")
    
    for page_num in qwen_pages:
        img = helper.get_page_image(page_num)
        # QWEN 호출: result = qwen_model.generate(img, prompt)
        results.append({
            'page': page_num,
            'strategy': 'qwen-simple',
            'content': '[QWEN processing needed]'
        })
    
    # 3-3. continuation 페이지
    cont_pages = helper.get_pages_by_strategy('qwen-continuation')
    print(f"\nProcessing {len(cont_pages)} continuation pages...")
    
    for curr_page in cont_pages:
        prev_page = helper.get_previous_page(curr_page)
        header = helper.get_header_columns(prev_page)
        
        combined_img = create_combined_image(helper, prev_page, curr_page)
        
        # QWEN 호출 with header info
        # result = qwen_model.generate(combined_img, prompt_with_header)
        
        results.append({
            'page': curr_page,
            'strategy': 'qwen-continuation',
            'header': header,
            'content': '[QWEN with context needed]'
        })
    
    # Step 4: 결과 저장
    print(f"\nStep 4: Saving results...")
    print(f"Total pages processed: {len(results)}")
    
    helper.close()


def main():
    """메인 함수"""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║           fitz Layout Analyzer - Usage Examples                  ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝

Available examples:
  1. Basic Layout Analysis
  2. Using Layout Results
  3. Handling Continuation Tables
  4. Direct Table Extraction
  5. Complete Integrated Workflow

Run specific example:
  python examples.py <pdf_file>
    """)
    
    if len(sys.argv) < 2:
        print("Please provide a PDF file path")
        return
    
    # 실제 파일로 교체
    example_basic_analysis()
    example_use_layout()
    example_continuation_handling()
    example_table_extraction()
    example_integrated_workflow()
    
    print("\n💡 Tip: Uncomment the example functions you want to run!")


if __name__ == '__main__':
    main()
