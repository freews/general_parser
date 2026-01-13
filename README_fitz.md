# fitz 레이아웃 분석기

PyMuPDF (fitz)를 사용한 PDF 레이아웃 자동 분석 도구

## 🎯 목적

PDF 문서를 분석하여 각 페이지의 파싱 전략을 자동으로 결정:
- **텍스트만**: fitz 직접 추출
- **단순 테이블**: fitz 시도 → 실패 시 QWEN
- **복잡한 테이블**: QWEN 사용
- **Continuation 테이블**: 이전 페이지 헤더 정보 + QWEN

## 📦 설치

```bash
pip install -r requirements_fitz.txt
```

## 🚀 빠른 시작

### 1단계: 레이아웃 분석

```bash
python fitz_layout_analyzer.py your_document.pdf
```

**출력:**
- `your_document_layout.json`: 분석 결과
- 콘솔에 요약 정보 출력

### 2단계: 결과 활용

```bash
python layout_helper.py your_document.pdf
```

**기능:**
- 전략별 페이지 목록 출력
- Continuation 감지
- 결합 이미지 생성

## 📂 파일 구조

```
fitz_layout_analyzer.py   # 메인 분석 모듈
├─ FitzLayoutAnalyzer     # 레이아웃 분석기
├─ PageLayout             # 페이지 레이아웃 정보
└─ TableInfo              # 테이블 정보

layout_helper.py           # 분석 결과 활용
├─ LayoutHelper           # 헬퍼 클래스
└─ create_combined_image  # Continuation 이미지 생성

examples_fitz.py          # 사용 예시

requirements_fitz.txt     # 필수 패키지
```

## 🔧 주요 기능

### 1. 페이지 레이아웃 분석

```python
from fitz_layout_analyzer import FitzLayoutAnalyzer

analyzer = FitzLayoutAnalyzer("document.pdf")
layouts = analyzer.analyze_all_pages()

# 요약 출력
analyzer.print_summary()

# JSON 저장
analyzer.export_to_json("layout.json")
```

**분석 내용:**
- 텍스트 블록 위치
- 테이블 감지 (bbox, 행/열 수, 셀 데이터)
- 이미지 감지
- Continuation 관계

### 2. Continuation 감지

**자동 감지 조건:**
- 이전 페이지와 컬럼 수 동일
- 현재 페이지가 1-2줄 짜리 (강력한 신호)
- X 좌표, 테이블 너비 유사
- 페이지 상단에 위치

### 3. 파싱 전략 결정

**전략 종류:**
- `fitz-only`: 텍스트만 또는 단순 테이블
- `qwen-simple`: 복잡한 레이아웃
- `qwen-continuation`: 페이지 넘어가는 테이블

### 4. 헬퍼 기능

```python
from layout_helper import LayoutHelper

helper = LayoutHelper("document.pdf", "layout.json")

# 전략별 페이지 목록
fitz_pages = helper.get_pages_by_strategy('fitz-only')

# 페이지 이미지 추출
img = helper.get_page_image(page_num=10)

# 테이블만 crop
table_img = helper.get_table_image(page_num=10, table_id=0)

# 헤더 정보 추출
header = helper.get_header_columns(page_num=9)

# Continuation 결합 이미지
from layout_helper import create_combined_image
combined = create_combined_image(helper, prev_page=9, curr_page=10)
```

## 📊 출력 형식

### layout.json 구조

```json
{
  "pdf_name": "document.pdf",
  "total_pages": 100,
  "layouts": {
    "0": {
      "page_num": 1,
      "width": 612.0,
      "height": 792.0,
      "has_text": true,
      "has_table": true,
      "has_image": false,
      "table_count": 2,
      "tables": [
        {
          "table_id": 0,
          "bbox": [72.0, 100.0, 540.0, 300.0],
          "row_count": 10,
          "col_count": 5,
          "is_simple": true
        }
      ],
      "strategy": "fitz-only"
    }
  },
  "continuations": {
    "63": 62  // Page 64 continues from Page 63
  },
  "statistics": {
    "total_pages": 100,
    "pages_with_tables": 45,
    "continuation_count": 5,
    "strategies": {
      "fitz-only": 60,
      "qwen-simple": 35,
      "qwen-continuation": 5
    }
  }
}
```

## 🎯 실전 워크플로우

### TCG Opal 문서 예시

```python
from fitz_layout_analyzer import FitzLayoutAnalyzer
from layout_helper import LayoutHelper, create_combined_image

# 1. 분석
analyzer = FitzLayoutAnalyzer("tcg-opal.pdf")
layouts = analyzer.analyze_all_pages()
analyzer.export_to_json("tcg_layout.json")
analyzer.close()

# 2. 결과 활용
helper = LayoutHelper("tcg-opal.pdf", "tcg_layout.json")

# 3. 전략별 처리
for page_num in range(1, 101):
    strategy = helper.get_page_strategy(page_num)
    
    if strategy == 'fitz-only':
        # fitz 직접 추출
        text = helper.extract_text_only(page_num)
        markdown = text
        
    elif strategy == 'qwen-simple':
        # QWEN 단순 호출
        img = helper.get_page_image(page_num)
        markdown = qwen_model.generate(img, "Extract as Markdown")
        
    elif strategy == 'qwen-continuation':
        # 이전 페이지 컨텍스트 포함
        prev_page = helper.get_previous_page(page_num)
        header = helper.get_header_columns(prev_page)
        
        combined_img = create_combined_image(helper, prev_page, page_num)
        
        prompt = f"""Extract table. Columns: {header}
This is continuation (no header in image)."""
        
        markdown = qwen_model.generate(combined_img, prompt)
    
    # 결과 저장
    save_markdown(page_num, markdown)

helper.close()
```

## 🔍 디버깅

### 특정 페이지 상세 분석

```python
analyzer = FitzLayoutAnalyzer("document.pdf")
layouts = analyzer.analyze_all_pages()

# Page 64 상세 정보
page_64 = layouts[63]  # 0-based
print(f"Strategy: {page_64.strategy}")
print(f"Tables: {len(page_64.tables)}")

for table in page_64.tables:
    print(f"  Table {table.table_id}:")
    print(f"    Size: {table.row_count} x {table.col_count}")
    print(f"    Simple: {table.is_simple}")
    print(f"    BBox: {table.bbox}")

# Continuation 확인
if 63 in analyzer.continuations:
    prev_page = analyzer.continuations[63]
    print(f"  Continues from page {prev_page + 1}")
    
    # 이전 페이지 헤더
    header_info = analyzer.get_header_info(prev_page)
    print(f"  Header: {header_info['column_names']}")
```

## ⚠️ 주의사항

1. **테이블 감지 실패**
   - 복잡한 레이아웃은 감지 못할 수 있음
   - 이 경우 `qwen-simple`로 fallback

2. **Continuation 오감지**
   - 다른 테이블이 우연히 조건 만족할 수 있음
   - JSON 결과 확인 후 수동 조정 필요

3. **셀 데이터 저장 안 됨**
   - JSON에는 테이블 구조만 (bbox, 행/열 수)
   - 실제 셀 데이터는 재추출 필요 (용량 문제)

## 💡 팁

1. **처음 실행**: 작은 문서(10-20 페이지)로 테스트
2. **continuation 확인**: JSON의 `continuations` 섹션 확인
3. **전략 조정**: 필요시 JSON 수동 편집 가능
4. **이미지 저장**: Continuation 결합 이미지 저장 가능

## 🤝 통합 예시

### QWEN과 통합

```python
# fitz 분석 결과 로드
helper = LayoutHelper("document.pdf", "layout.json")

# QWEN 모델 초기화
qwen_model = load_qwen_model()

# 페이지별 처리
for page_num in range(1, len(helper.doc) + 1):
    strategy = helper.get_page_strategy(page_num)
    
    if strategy == 'qwen-continuation':
        # Continuation 처리
        prev_page = helper.get_previous_page(page_num)
        header = helper.get_header_columns(prev_page)
        
        # 결합 이미지
        combined = create_combined_image(helper, prev_page, page_num)
        
        # QWEN 호출 with context
        prompt = create_continuation_prompt(header)
        result = qwen_model.generate(combined, prompt)
        
    elif strategy == 'qwen-simple':
        # 일반 QWEN 처리
        img = helper.get_page_image(page_num)
        result = qwen_model.generate(img, "Extract as Markdown")
        
    else:  # fitz-only
        # fitz 직접 추출
        result = helper.extract_text_only(page_num)
```

## 📄 라이선스

MIT License
