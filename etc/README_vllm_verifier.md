# VLLM-based Continuation Verification

## 개요

위치 기반 휴리스틱의 대안으로, VLLM(Vision Language Model)을 사용하여 더 정확하게 continuation 테이블을 감지하는 모듈입니다.

## 왜 필요한가?

### 현재 방식 (위치 기반 휴리스틱)의 한계

```python
# fitz_layout_analyzer.py의 현재 방식
def _is_continuation(self, prev_layout, curr_layout):
    # 위치, 너비, 행 수 등으로 판단
    if curr_table.bbox[1] > 200: return False
    if curr_table.row_count > 15: return False
    # ...
```

**문제점:**
- ❌ 추측에 기반한 판단
- ❌ False positive/negative 가능성
- ❌ 테이블 내용을 실제로 보지 않음

### VLLM 방식의 장점

```python
# vllm_continuation_verifier.py의 방식
def verify_continuation(self, candidate):
    # 1. 테이블 타이틀 확인
    if has_table_title(curr_page):
        return False  # 타이틀 있으면 새 테이블
    
    # 2. VLLM에게 실제 이미지 보여주고 판단 요청
    result = vllm_model.generate(combined_image, prompt)
    return result['is_continuation']
```

**장점:**
- ✅ 테이블 타이틀 유무를 명확한 신호로 사용
- ✅ VLLM이 실제 내용을 보고 판단
- ✅ 더 정확한 결정
- ✅ 이유를 설명해줌 (디버깅 용이)

## 사용 시나리오

### Scenario 1: 위치 기반 방식이 충분한 경우 (현재)

```python
from fitz_layout_analyzer import FitzLayoutAnalyzer

analyzer = FitzLayoutAnalyzer(pdf_path)
layouts = analyzer.analyze_all_pages()

# 42개 continuation 감지 (41.6% of pages)
print(f"Continuations: {len(analyzer.continuations)}")
```

**이 방식을 계속 사용하세요:**
- 빠르고 효율적
- VLLM 모델 불필요
- 대부분의 경우 충분히 정확

### Scenario 2: 더 높은 정확도가 필요한 경우

```python
from vllm_continuation_verifier import verify_continuations_with_vllm
from qwen_vl import QwenVLModel  # 예시

# VLLM 모델 초기화
vllm_model = QwenVLModel()

# VLLM으로 검증
continuations = verify_continuations_with_vllm(
    pdf_path='./source_doc/TCG-Storage-Opal-SSC-v2.30_pub.pdf',
    vllm_model=vllm_model,
    only_no_title=True,  # 타이틀 없는 것만 검증
    save_debug_images=True
)
```

**이 방식을 사용하세요:**
- False positive가 많을 때
- False negative가 많을 때
- 최대한 정확한 결과가 필요할 때
- VLLM 모델 사용 가능할 때

## 주요 기능

### 1. 테이블 타이틀 감지

```python
from vllm_continuation_verifier import TableTitleDetector
import fitz

doc = fitz.open(pdf_path)
page = doc[35]
tables = page.find_tables()
table = list(tables)[0]

# 테이블 위에 "Table XX" 같은 타이틀이 있는지 확인
has_title = TableTitleDetector.has_table_title(page, table.bbox)
print(f"Has title: {has_title}")
```

**감지 패턴:**
- `Table 19`
- `Figure 5`
- `Tab. 3`
- `Fig. 2`

### 2. Continuation 후보 찾기

```python
from vllm_continuation_verifier import find_continuation_candidates_with_title_check

# 후보 찾기 (타이틀 체크 포함)
candidates = find_continuation_candidates_with_title_check(
    pdf_path,
    use_heuristic=True  # 위치 기반 필터링 사용
)

# 타이틀 없는 것만 필터링
no_title = [c for c in candidates if not c.has_title]
print(f"Need VLLM verification: {len(no_title)} pages")
```

### 3. VLLM으로 검증

```python
from vllm_continuation_verifier import VLLMContinuationVerifier

verifier = VLLMContinuationVerifier(vllm_model)

result = verifier.verify_continuation(doc, candidate)

print(f"Is continuation: {result['is_continuation']}")
print(f"Confidence: {result['confidence']}")
print(f"Reason: {result['reason']}")
```

**VLLM 프롬프트 예시:**
```
You are analyzing a technical specification document.

CONTEXT:
- Page 35 ends with a table
- Page 36 starts with a table at the top
- The table on page 36 has NO title/caption above it

TASK:
Determine if the table on page 36 is a CONTINUATION of the 
table from page 35.

INDICATORS OF CONTINUATION:
✓ Same column structure
✓ Data continues logically
✓ No new table title/caption
✓ Similar formatting

Answer in JSON format:
{
    "is_continuation": true/false,
    "confidence": "high/medium/low",
    "reason": "brief explanation"
}
```

## 파일 구조

```
general_parser/
├── fitz_layout_analyzer.py          # 현재 사용 중 (위치 기반)
├── vllm_continuation_verifier.py    # VLLM 기반 검증 (대안)
├── examples_vllm_verifier.py        # 사용 예시
└── README_vllm_verifier.md          # 이 문서
```

## 실행 예시

### 예시 1: 후보 찾기

```bash
cd /home/wscho/projects/llm-test/general_parser
python3 examples_vllm_verifier.py
```

**출력:**
```
Found 42 candidates
  - With title: 0 (likely NOT continuations)
  - Without title: 42 (need VLLM verification)

Candidates without title (first 10):
  1. Page 16 continues from 15 (confidence: high)
  2. Page 20 continues from 19 (confidence: high)
  3. Page 22 continues from 21 (confidence: high)
  ...
```

### 예시 2: 특정 페이지 타이틀 확인

```python
python3 -c "
from vllm_continuation_verifier import TableTitleDetector
import fitz

doc = fitz.open('./source_doc/TCG-Storage-Opal-SSC-v2.30_pub.pdf')

for page_num in [35, 36, 37, 38]:
    page = doc[page_num]
    tables = page.find_tables()
    if tables and tables.tables:
        table = list(tables)[0]
        has_title = TableTitleDetector.has_table_title(page, table.bbox)
        print(f'Page {page_num + 1}: has_title={has_title}')

doc.close()
"
```

**출력:**
```
Page 36: has_title=False  ← continuation
Page 37: has_title=False  ← continuation
Page 38: has_title=True   ← new table
Page 39: has_title=True   ← new table
```

## 성능 비교

| 방식 | 속도 | 정확도 | VLLM 필요 | 비용 |
|------|------|--------|-----------|------|
| **위치 기반** | ⚡ 매우 빠름 | 🟡 중간 | ❌ 불필요 | 💰 무료 |
| **VLLM 기반** | 🐌 느림 | ✅ 높음 | ✅ 필요 | 💰💰 비용 발생 |

## 권장 사항

1. **기본적으로 위치 기반 사용** (`fitz_layout_analyzer.py`)
   - 빠르고 효율적
   - 대부분의 경우 충분히 정확

2. **다음 경우에만 VLLM 사용**:
   - False positive/negative가 많을 때
   - 최대한 정확한 결과가 필요할 때
   - VLLM 모델 사용 가능할 때

3. **하이브리드 접근**:
   ```python
   # 1단계: 위치 기반으로 빠르게 처리
   analyzer = FitzLayoutAnalyzer(pdf_path)
   layouts = analyzer.analyze_all_pages()
   
   # 2단계: 의심스러운 케이스만 VLLM으로 재검증
   suspicious_cases = find_suspicious_continuations(layouts)
   verified = verify_with_vllm(suspicious_cases, vllm_model)
   ```

## 향후 개선 사항

- [ ] VLLM 응답 캐싱 (같은 페이지 재검증 방지)
- [ ] Batch 처리 (여러 페이지 한번에 검증)
- [ ] 신뢰도 임계값 조정 가능
- [ ] 다양한 VLLM 모델 지원 (Qwen, LLaVA, etc.)
- [ ] 검증 결과 시각화 도구

## 문의

문제가 있거나 개선 제안이 있으면 이슈를 등록해주세요.
