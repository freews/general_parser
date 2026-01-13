#!/usr/bin/env python3
"""
VLLM 기반 Continuation 테이블 검증

현재는 위치 기반 휴리스틱을 사용하지만, 정확도가 부족할 경우
이 모듈의 VLLM 기반 검증을 사용할 수 있습니다.

사용 시나리오:
1. 위치 기반 휴리스틱으로 후보 탐지
2. 테이블 타이틀 유무 확인
3. 타이틀 없는 경우만 VLLM으로 검증
4. VLLM의 판단으로 최종 결정

장점:
- 더 정확한 continuation 감지
- 테이블 내용을 실제로 이해하고 판단
- False positive/negative 감소
"""

import fitz
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ContinuationCandidate:
    """Continuation 후보"""
    prev_page: int  # 0-based index
    curr_page: int  # 0-based index
    prev_table_idx: int  # 이전 페이지의 테이블 인덱스 (마지막 테이블)
    curr_table_idx: int  # 현재 페이지의 테이블 인덱스 (첫 테이블)
    confidence: str  # 'high', 'medium', 'low'
    has_title: bool  # 현재 페이지 테이블에 타이틀이 있는지


class TableTitleDetector:
    """테이블 타이틀 감지기"""
    
    # 테이블 타이틀 패턴
    TABLE_PATTERNS = [
        r'\bTable\s+\d+',      # "Table 19"
        r'\bFigure\s+\d+',     # "Figure 5"
        r'\bTab\.\s+\d+',      # "Tab. 3"
        r'\bFig\.\s+\d+',      # "Fig. 2"
    ]
    
    @staticmethod
    def has_table_title(page: fitz.Page, table_bbox: Tuple[float, float, float, float]) -> bool:
        """
        테이블 위에 타이틀이 있는지 확인
        
        Args:
            page: PyMuPDF Page 객체
            table_bbox: 테이블의 bounding box (x0, y0, x1, y1)
        
        Returns:
            True if 타이틀 발견, False otherwise
        """
        # 테이블 위 50pt 영역 검색
        search_area = fitz.Rect(
            table_bbox[0] - 20,  # 약간 왼쪽으로 확장
            max(0, table_bbox[1] - 50),  # 위 50pt (페이지 경계 체크)
            table_bbox[2] + 20,  # 약간 오른쪽으로 확장
            table_bbox[1]        # 테이블 상단까지
        )
        
        # 텍스트 추출
        text = page.get_text("text", clip=search_area)
        
        # 패턴 매칭
        for pattern in TableTitleDetector.TABLE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False


class VLLMContinuationVerifier:
    """VLLM 기반 Continuation 검증기"""
    
    def __init__(self, vllm_model=None):
        """
        Args:
            vllm_model: VLLM 모델 인스턴스 (예: Qwen-VL)
                       None이면 검증 기능 비활성화
        """
        self.vllm_model = vllm_model
    
    def create_verification_prompt(self, prev_page_num: int, curr_page_num: int) -> str:
        """
        VLLM용 검증 프롬프트 생성
        
        Args:
            prev_page_num: 이전 페이지 번호 (1-based)
            curr_page_num: 현재 페이지 번호 (1-based)
        
        Returns:
            프롬프트 문자열
        """
        return f"""You are analyzing a technical specification document.

CONTEXT:
- Page {prev_page_num} ends with a table
- Page {curr_page_num} starts with a table at the top
- The table on page {curr_page_num} has NO title/caption above it

TASK:
Determine if the table on page {curr_page_num} is a CONTINUATION of the 
table from page {prev_page_num}.

INDICATORS OF CONTINUATION:
✓ Same column structure (same headers or similar data layout)
✓ Data continues logically from previous page
✓ No new table title/caption
✓ Similar table formatting and width

INDICATORS OF NEW TABLE:
✗ Different column headers or structure
✗ Unrelated content (different topic)
✗ Significantly different table formatting
✗ Clear start of new information

IMPORTANT:
- Look at the actual table content, not just the position
- Consider the semantic meaning of the data
- A continuation table may or may not repeat column headers

Answer in JSON format:
{{
    "is_continuation": true/false,
    "confidence": "high/medium/low",
    "reason": "brief explanation of your decision"
}}
"""
    
    def create_combined_image(self, doc: fitz.Document, 
                             prev_page: int, curr_page: int,
                             prev_table_bbox: Tuple, curr_table_bbox: Tuple) -> any:
        """
        두 페이지의 테이블 영역을 결합한 이미지 생성
        
        Args:
            doc: PyMuPDF Document
            prev_page: 이전 페이지 번호 (0-based)
            curr_page: 현재 페이지 번호 (0-based)
            prev_table_bbox: 이전 페이지 테이블 bbox
            curr_table_bbox: 현재 페이지 테이블 bbox
        
        Returns:
            PIL Image 객체 (상단: 이전 페이지 하단, 하단: 현재 페이지 상단)
        """
        from PIL import Image
        
        # 이전 페이지: 테이블 영역 + 아래 여백
        prev_page_obj = doc[prev_page]
        prev_clip = fitz.Rect(
            prev_table_bbox[0] - 10,
            prev_table_bbox[1] - 10,
            prev_table_bbox[2] + 10,
            min(prev_page_obj.rect.height, prev_table_bbox[3] + 50)
        )
        prev_pix = prev_page_obj.get_pixmap(matrix=fitz.Matrix(2, 2), clip=prev_clip)
        prev_img = Image.frombytes("RGB", [prev_pix.width, prev_pix.height], prev_pix.samples)
        
        # 현재 페이지: 위 여백 + 테이블 영역
        curr_page_obj = doc[curr_page]
        curr_clip = fitz.Rect(
            curr_table_bbox[0] - 10,
            max(0, curr_table_bbox[1] - 50),
            curr_table_bbox[2] + 10,
            curr_table_bbox[3] + 10
        )
        curr_pix = curr_page_obj.get_pixmap(matrix=fitz.Matrix(2, 2), clip=curr_clip)
        curr_img = Image.frombytes("RGB", [curr_pix.width, curr_pix.height], curr_pix.samples)
        
        # 두 이미지 수직으로 결합
        total_height = prev_img.height + curr_img.height + 20  # 20px 간격
        max_width = max(prev_img.width, curr_img.width)
        
        combined = Image.new('RGB', (max_width, total_height), color='white')
        combined.paste(prev_img, (0, 0))
        
        # 구분선 그리기 (빨간색)
        from PIL import ImageDraw
        draw = ImageDraw.Draw(combined)
        y_line = prev_img.height + 10
        draw.line([(0, y_line), (max_width, y_line)], fill='red', width=3)
        
        combined.paste(curr_img, (0, prev_img.height + 20))
        
        return combined
    
    def verify_continuation(self, doc: fitz.Document, 
                           candidate: ContinuationCandidate) -> Dict:
        """
        VLLM을 사용하여 continuation 여부 검증
        
        Args:
            doc: PyMuPDF Document
            candidate: 검증할 후보
        
        Returns:
            {
                'is_continuation': bool,
                'confidence': str,
                'reason': str,
                'vllm_response': str (원본 응답)
            }
        """
        if self.vllm_model is None:
            raise ValueError("VLLM model not initialized")
        
        # 테이블 bbox 가져오기
        prev_page_obj = doc[candidate.prev_page]
        curr_page_obj = doc[candidate.curr_page]
        
        prev_tables = prev_page_obj.find_tables()
        curr_tables = curr_page_obj.find_tables()
        
        prev_table = list(prev_tables)[candidate.prev_table_idx]
        curr_table = list(curr_tables)[candidate.curr_table_idx]
        
        # 결합 이미지 생성
        combined_img = self.create_combined_image(
            doc, 
            candidate.prev_page, 
            candidate.curr_page,
            prev_table.bbox,
            curr_table.bbox
        )
        
        # 프롬프트 생성 (1-based page numbers for user)
        prompt = self.create_verification_prompt(
            candidate.prev_page + 1,
            candidate.curr_page + 1
        )
        
        # VLLM 호출
        response = self.vllm_model.generate(combined_img, prompt)
        
        # JSON 파싱
        try:
            result = json.loads(response)
            return {
                'is_continuation': result.get('is_continuation', False),
                'confidence': result.get('confidence', 'low'),
                'reason': result.get('reason', ''),
                'vllm_response': response
            }
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 텍스트에서 추출 시도
            is_cont = 'true' in response.lower() or 'yes' in response.lower()
            return {
                'is_continuation': is_cont,
                'confidence': 'low',
                'reason': 'Failed to parse JSON response',
                'vllm_response': response
            }


def find_continuation_candidates_with_title_check(
    pdf_path: str,
    use_heuristic: bool = True
) -> List[ContinuationCandidate]:
    """
    Continuation 후보를 찾고 테이블 타이틀 유무 확인
    
    Args:
        pdf_path: PDF 파일 경로
        use_heuristic: True면 위치 기반 휴리스틱 사용,
                      False면 모든 연속 테이블 페어 검사
    
    Returns:
        ContinuationCandidate 리스트
    """
    doc = fitz.open(pdf_path)
    candidates = []
    
    for page_num in range(1, len(doc)):
        prev_page = doc[page_num - 1]
        curr_page = doc[page_num]
        
        prev_tables = prev_page.find_tables()
        curr_tables = curr_page.find_tables()
        
        # 둘 다 테이블이 있어야 함
        if not (prev_tables and prev_tables.tables and curr_tables and curr_tables.tables):
            continue
        
        prev_table = list(prev_tables)[-1]  # 마지막 테이블
        curr_table = list(curr_tables)[0]   # 첫 테이블
        
        # 휴리스틱 체크 (선택적)
        if use_heuristic:
            # 기본 위치 조건
            if curr_table.bbox[1] > 200:  # 상단 200pt 이내
                continue
            if curr_table.row_count > 15:  # 15행 이하
                continue
            
            # X 정렬
            x_diff = abs(prev_table.bbox[0] - curr_table.bbox[0])
            if x_diff > 20:
                continue
            
            # 너비 유사성
            prev_width = prev_table.bbox[2] - prev_table.bbox[0]
            curr_width = curr_table.bbox[2] - curr_table.bbox[0]
            width_diff = abs(prev_width - curr_width)
            if width_diff > 30 and width_diff / max(prev_width, curr_width) > 0.2:
                continue
        
        # 타이틀 확인
        has_title = TableTitleDetector.has_table_title(curr_page, curr_table.bbox)
        
        # Confidence 계산
        confidence = 'high'
        if curr_table.row_count > 10:
            confidence = 'medium'
        if curr_table.bbox[1] > 150:
            confidence = 'medium'
        if has_title:
            confidence = 'low'  # 타이틀 있으면 continuation 가능성 낮음
        
        candidates.append(ContinuationCandidate(
            prev_page=page_num - 1,
            curr_page=page_num,
            prev_table_idx=len(list(prev_tables)) - 1,
            curr_table_idx=0,
            confidence=confidence,
            has_title=has_title
        ))
    
    doc.close()
    return candidates


def verify_continuations_with_vllm(
    pdf_path: str,
    vllm_model,
    only_no_title: bool = True,
    save_debug_images: bool = False
) -> List[int]:
    """
    VLLM을 사용하여 continuation 검증 (메인 함수)
    
    Args:
        pdf_path: PDF 파일 경로
        vllm_model: VLLM 모델 인스턴스
        only_no_title: True면 타이틀 없는 것만 검증
        save_debug_images: True면 디버그 이미지 저장
    
    Returns:
        Continuation으로 확인된 페이지 번호 리스트 (0-based)
    """
    # Step 1: 후보 찾기
    print("Step 1: Finding continuation candidates...")
    candidates = find_continuation_candidates_with_title_check(pdf_path)
    
    print(f"Found {len(candidates)} potential continuations")
    
    # Step 2: 타이틀 없는 것만 필터링 (선택적)
    if only_no_title:
        no_title_candidates = [c for c in candidates if not c.has_title]
        print(f"  - {len(no_title_candidates)} without titles (need VLLM verification)")
        print(f"  - {len(candidates) - len(no_title_candidates)} with titles (auto-reject)")
        candidates = no_title_candidates
    
    # Step 3: VLLM 검증
    print("\nStep 2: Verifying with VLLM...")
    verifier = VLLMContinuationVerifier(vllm_model)
    doc = fitz.open(pdf_path)
    
    verified_continuations = []
    
    for i, candidate in enumerate(candidates, 1):
        print(f"  [{i}/{len(candidates)}] Verifying page {candidate.curr_page + 1}...", end=' ')
        
        result = verifier.verify_continuation(doc, candidate)
        
        print(f"{result['is_continuation']} (confidence: {result['confidence']})")
        print(f"      Reason: {result['reason']}")
        
        # High/Medium confidence이고 continuation이면 채택
        if result['is_continuation'] and result['confidence'] in ['high', 'medium']:
            verified_continuations.append(candidate.curr_page)
        
        # 디버그 이미지 저장 (선택적)
        if save_debug_images:
            debug_dir = Path('debug_vllm_verification')
            debug_dir.mkdir(exist_ok=True)
            
            img = verifier.create_combined_image(
                doc, candidate.prev_page, candidate.curr_page,
                list(doc[candidate.prev_page].find_tables())[candidate.prev_table_idx].bbox,
                list(doc[candidate.curr_page].find_tables())[candidate.curr_table_idx].bbox
            )
            img.save(debug_dir / f"page_{candidate.curr_page + 1}_verification.png")
    
    doc.close()
    
    print(f"\nVerified {len(verified_continuations)} continuations")
    return verified_continuations


# ============================================================================
# 사용 예시
# ============================================================================

if __name__ == '__main__':
    """
    사용 예시:
    
    # VLLM 모델 초기화 (예: Qwen-VL)
    from qwen_vl import QwenVLModel
    vllm_model = QwenVLModel()
    
    # Continuation 검증
    continuations = verify_continuations_with_vllm(
        pdf_path='./source_doc/TCG-Storage-Opal-SSC-v2.30_pub.pdf',
        vllm_model=vllm_model,
        only_no_title=True,
        save_debug_images=True
    )
    
    print(f"Detected continuations: {continuations}")
    """
    
    print("This module provides VLLM-based continuation verification.")
    print("Import and use verify_continuations_with_vllm() function.")
    print("\nSee docstrings for usage examples.")
