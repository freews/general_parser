#!/usr/bin/env python3
"""
VLLM Continuation Verifier 사용 예시

이 파일은 vllm_continuation_verifier.py의 사용법을 보여줍니다.
실제 VLLM 모델이 필요하므로, 모델 초기화 부분은 주석 처리되어 있습니다.
"""

from vllm_continuation_verifier import (
    find_continuation_candidates_with_title_check,
    verify_continuations_with_vllm,
    TableTitleDetector,
    VLLMContinuationVerifier
)


def example1_find_candidates():
    """예시 1: Continuation 후보 찾기 (타이틀 체크 포함)"""
    print("="*70)
    print("Example 1: Find Continuation Candidates with Title Check")
    print("="*70)
    
    pdf_path = "./source_doc/TCG-Storage-Opal-SSC-v2.30_pub.pdf"
    
    # 후보 찾기
    candidates = find_continuation_candidates_with_title_check(
        pdf_path,
        use_heuristic=True  # 위치 기반 휴리스틱 사용
    )
    
    print(f"\nFound {len(candidates)} candidates")
    
    # 타이틀 유무별 분류
    with_title = [c for c in candidates if c.has_title]
    without_title = [c for c in candidates if not c.has_title]
    
    print(f"  - With title: {len(with_title)} (likely NOT continuations)")
    print(f"  - Without title: {len(without_title)} (need VLLM verification)")
    
    # 타이틀 없는 것들 출력
    print(f"\nCandidates without title (first 10):")
    for i, c in enumerate(without_title[:10], 1):
        print(f"  {i}. Page {c.curr_page + 1} continues from {c.prev_page + 1} "
              f"(confidence: {c.confidence})")


def example2_check_single_table_title():
    """예시 2: 특정 페이지의 테이블 타이틀 확인"""
    print("\n" + "="*70)
    print("Example 2: Check Table Title for Specific Pages")
    print("="*70)
    
    import fitz
    
    pdf_path = "./source_doc/TCG-Storage-Opal-SSC-v2.30_pub.pdf"
    doc = fitz.open(pdf_path)
    
    # 테스트할 페이지들
    test_pages = [35, 36, 37, 38]  # 0-based
    
    for page_num in test_pages:
        page = doc[page_num]
        tables = page.find_tables()
        
        if tables and tables.tables:
            first_table = list(tables)[0]
            has_title = TableTitleDetector.has_table_title(page, first_table.bbox)
            
            print(f"\nPage {page_num + 1}:")
            print(f"  First table has title: {has_title}")
            print(f"  Table bbox: {first_table.bbox}")
    
    doc.close()


def example3_vllm_verification():
    """예시 3: VLLM으로 검증 (실제 모델 필요)"""
    print("\n" + "="*70)
    print("Example 3: VLLM Verification (requires actual VLLM model)")
    print("="*70)
    
    # ⚠️ 실제 VLLM 모델 초기화 필요
    # 예시:
    # from qwen_vl import QwenVLModel
    # vllm_model = QwenVLModel(
    #     model_path="Qwen/Qwen-VL-Chat",
    #     device="cuda"
    # )
    
    print("\n⚠️  This example requires a VLLM model to be initialized.")
    print("Uncomment the model initialization code above to run.")
    print("\nExample usage:")
    print("""
    # VLLM 모델 초기화
    vllm_model = QwenVLModel()
    
    # Continuation 검증
    continuations = verify_continuations_with_vllm(
        pdf_path='./source_doc/TCG-Storage-Opal-SSC-v2.30_pub.pdf',
        vllm_model=vllm_model,
        only_no_title=True,  # 타이틀 없는 것만 검증
        save_debug_images=True  # 디버그 이미지 저장
    )
    
    print(f"Verified continuations: {continuations}")
    
    # 결과를 JSON으로 저장
    import json
    with open('vllm_verified_continuations.json', 'w') as f:
        json.dump({
            'total_continuations': len(continuations),
            'continuation_pages': continuations
        }, f, indent=2)
    """)


def example4_compare_methods():
    """예시 4: 위치 기반 vs VLLM 기반 비교"""
    print("\n" + "="*70)
    print("Example 4: Compare Position-based vs VLLM-based")
    print("="*70)
    
    from fitz_layout_analyzer import FitzLayoutAnalyzer
    
    pdf_path = "./source_doc/TCG-Storage-Opal-SSC-v2.30_pub.pdf"
    
    # 방법 1: 위치 기반 (현재 사용 중)
    print("\nMethod 1: Position-based heuristic")
    analyzer = FitzLayoutAnalyzer(pdf_path)
    layouts = analyzer.analyze_all_pages()
    position_based = list(analyzer.continuations.keys())
    print(f"  Detected: {len(position_based)} continuations")
    print(f"  Pages: {sorted([p + 1 for p in position_based])}")
    analyzer.close()
    
    # 방법 2: VLLM 기반 (후보만 찾기)
    print("\nMethod 2: VLLM-based (candidates only, no actual verification)")
    candidates = find_continuation_candidates_with_title_check(pdf_path)
    no_title_candidates = [c for c in candidates if not c.has_title]
    print(f"  Candidates without title: {len(no_title_candidates)}")
    print(f"  Pages: {sorted([c.curr_page + 1 for c in no_title_candidates])}")
    
    # 비교
    print("\nComparison:")
    position_set = set(position_based)
    candidate_set = set(c.curr_page for c in no_title_candidates)
    
    only_position = position_set - candidate_set
    only_candidate = candidate_set - position_set
    both = position_set & candidate_set
    
    print(f"  Both methods agree: {len(both)} pages")
    print(f"  Only position-based: {len(only_position)} pages")
    print(f"  Only VLLM candidates: {len(only_candidate)} pages")
    
    if only_position:
        print(f"\n  Pages detected only by position-based:")
        print(f"    {sorted([p + 1 for p in only_position])}")
    
    if only_candidate:
        print(f"\n  Pages detected only as VLLM candidates:")
        print(f"    {sorted([p + 1 for p in only_candidate])}")


def main():
    """메인 함수"""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║        VLLM Continuation Verifier - Usage Examples               ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝

This script demonstrates how to use the VLLM-based continuation
verification as an alternative to position-based heuristics.

Available examples:
  1. Find continuation candidates with title check
  2. Check table titles for specific pages
  3. VLLM verification (requires actual model)
  4. Compare position-based vs VLLM-based methods
    """)
    
    # 예시 실행
    example1_find_candidates()
    example2_check_single_table_title()
    example3_vllm_verification()
    example4_compare_methods()
    
    print("\n" + "="*70)
    print("💡 Tip: Use VLLM verification when position-based heuristics")
    print("         produce too many false positives or false negatives.")
    print("="*70)


if __name__ == '__main__':
    main()
