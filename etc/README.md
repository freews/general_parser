# General Parser - 완전한 워크플로우

## 🎯 전체 프로세스

```
PDF 문서
    ↓
[1] 레이아웃 분석 (fitz_layout_analyzer.py)
    ↓
레이아웃 JSON (테이블/그림 위치)
    ↓
[2] 섹션별 데이터 추출 (section_extractor_v2.py)
    ↓
섹션 JSON (181개) + 텍스트 (테이블 제외)
    ↓
[3] 테이블/그림 이미지 생성 (generate_table_images.py)
    ↓
PNG 이미지 (105개)
    ↓
[4] LLM 파싱 (llm_table_parser.py)
    ↓
Markdown 테이블 + 그림 설명
    ↓
[5] Markdown 변환 (convert_to_markdown.py)
    ↓
최종 Markdown 문서 (181개)
```

---

## 📋 단계별 실행

### Step 1: PDF 레이아웃 분석

**목적**: 페이지별 테이블/그림 위치 파악

```bash
python3 fitz_layout_analyzer.py
```

**출력**:
- `TCG-Storage-Opal-SSC-v2.30_pub_layout.json`

**내용**:
- 페이지별 테이블 bbox, row/col 수
- Continuation 테이블 감지
- 파싱 전략 (fitz-only, qwen-simple, qwen-continuation)

---

### Step 2: 섹션별 데이터 추출 ⭐

**목적**: TOC 기반으로 섹션 분리, 텍스트 추출 (테이블 제외)

```bash
python3 section_extractor_v2.py
```

**출력**:
- `output/section_data_v2/section_XXX_YYY.json` (181개)
- `output/section_data_v2/section_index.json`

**특징**:
- ✅ 텍스트 패턴 매칭으로 정확한 섹션 분리
- ✅ 테이블 영역 텍스트 제외
- ✅ 같은 페이지의 여러 섹션 정확히 구분

**JSON 구조**:
```json
{
  "section_id": "4.2.1.2",
  "title": "4.2.1.2 SPTemplates (M)",
  "pages": {"start": 35, "end": 35},
  "content": {
    "text": "섹션 텍스트 (테이블 제외)...",
    "tables": [
      {
        "table_id": "Table_35_1",
        "title": "Table 19 - ...",
        "page": 35,
        "bbox": [...],
        "image_path": "table_035_1.png",
        "markdown": null  // Step 4에서 채워짐
      }
    ],
    "figures": [...]
  }
}
```

---

### Step 3: 테이블/그림 이미지 생성

**목적**: bbox 정보로 고해상도 PNG 추출

```bash
python3 generate_table_images.py
```

**출력**:
- `output/section_images/table_XXX_Y.png` (103개)
- `output/section_images/figure_XXX_Y.png` (2개)

**특징**:
- 300 DPI 고해상도
- bbox 기반 정확한 크롭
- LLM 파싱 최적화

---

### Step 4: LLM 테이블/그림 파싱 ⭐

**목적**: 이미지를 Markdown/설명으로 변환

```bash
# 테스트 (3개 섹션)
python3 llm_table_parser.py

# 전체 실행
python3 -c "
from llm_table_parser import process_all_sections
process_all_sections(limit=None)
"
```

**요구사항**:
- Ollama 설치 및 실행 중
- qwen2-vl:7b 모델 설치

```bash
# Ollama 설치 확인
ollama list

# 모델 다운로드 (필요시)
ollama pull qwen2-vl:7b

# Ollama 실행 확인
curl http://localhost:11434/api/tags
```

**처리 과정**:
1. Section JSON 읽기
2. 각 테이블 이미지를 LLM에 전달
3. Markdown 테이블 받기
4. JSON 업데이트 (markdown 필드)
5. 그림도 동일하게 처리 (description 필드)

**업데이트된 JSON**:
```json
{
  "tables": [
    {
      "table_id": "Table_35_1",
      "markdown": "| UID | TemplateID | Name | Version |\n|-----|------------|------|---------|..."
    }
  ]
}
```

---

### Step 5: Markdown 변환

**목적**: 읽기 쉬운 Markdown 문서 생성

```bash
python3 convert_to_markdown.py
```

**출력**:
- `output/section_markdown/section_XXX_YYY.md` (181개)
- `output/section_markdown/INDEX.md`

**Markdown 구조**:
```markdown
##### 4.2.1.2 SPTemplates (M)

**Section ID**: 4.2.1.2  
**Pages**: 35-35  

---

## 📝 Content

섹션 텍스트 내용...

---

## 📊 Tables (2)

### Table 1: Table 19 - Admin SP - SPTemplates Table Preconfiguration

| UID | TemplateID | Name | Version |
|-----|------------|------|---------|
| ... | ...        | ...  | ...     |

---

## 🖼️ Figures (0)
```

---

## 📊 최종 통계

```
총 섹션: 181개
총 테이블: 238개
총 그림: 2개
생성된 이미지: 105개
```

---

## 🔧 주요 개선사항

### 1. Section 경계 문제 해결 ✅

**이전**: 같은 페이지의 다른 섹션 내용이 섞임

**현재**: 텍스트 패턴 매칭으로 정확한 분리
- Page별 MD 생성
- Section 제목으로 시작점 찾기
- 다음 Section 제목까지 복사

### 2. 테이블 텍스트 제외 ✅

**이전**: 테이블 내부 텍스트가 섹션 텍스트에 포함

**현재**: bbox 기반 필터링
- 레이아웃 JSON에서 테이블 bbox 읽기
- 텍스트 블록이 테이블과 겹치는지 확인
- 겹치지 않는 텍스트만 추출

### 3. LLM 파싱 파이프라인 ✅

**구조화된 데이터**:
- JSON에 이미지 경로 저장
- LLM 파싱 후 markdown 필드 업데이트
- 재실행 시 이미 파싱된 것은 스킵

---

## 📝 사용 예시

### 전체 파이프라인 실행

```bash
# 1. 레이아웃 분석
python3 fitz_layout_analyzer.py

# 2. 섹션 추출
python3 section_extractor_v2.py

# 3. 이미지 생성
python3 generate_table_images.py

# 4. LLM 파싱 (Ollama 실행 중이어야 함)
python3 -c "
from llm_table_parser import process_all_sections
process_all_sections(limit=None)
"

# 5. Markdown 변환
python3 convert_to_markdown.py
```

### 특정 섹션만 처리

```python
from llm_table_parser import LLMTableParser
import json

parser = LLMTableParser()

# 섹션 089 처리
with open('output/section_data_v2/section_089_4_2_1_2.json', 'r') as f:
    section = json.load(f)

for table in section['content']['tables']:
    image_path = f"output/section_images/{table['image_path']}"
    markdown = parser.parse_table_image(image_path)
    table['markdown'] = markdown

# 저장
with open('output/section_data_v2/section_089_4_2_1_2.json', 'w') as f:
    json.dump(section, f, ensure_ascii=False, indent=2)
```

---

## 🎯 다음 단계

### 1. 최종 문서 통합

모든 섹션 Markdown을 하나의 문서로 통합

```python
# 예시
sections = sorted(Path('output/section_markdown').glob('section_*.md'))
with open('FINAL_DOCUMENT.md', 'w') as out:
    for section_file in sections:
        if section_file.name != 'INDEX.md':
            out.write(section_file.read_text())
            out.write('\n\n---\n\n')
```

### 2. HTML 생성

Markdown을 HTML로 변환하여 웹에서 보기

### 3. 검색 기능

섹션별 인덱싱 및 전문 검색

---

## 📌 중요 파일

### 핵심 스크립트
- `section_extractor_v2.py` - 섹션 추출 (최신)
- `generate_table_images.py` - 이미지 생성
- `llm_table_parser.py` - LLM 파싱
- `convert_to_markdown.py` - Markdown 변환

### 데이터 파일
- `TCG-Storage-Opal-SSC-v2.30_pub_layout.json` - 레이아웃 분석
- `output/section_data_v2/` - 섹션 JSON (181개)
- `output/section_images/` - 테이블/그림 이미지 (105개)
- `output/section_markdown/` - 최종 Markdown (181개)

### 원본
- `source_doc/TCG-Storage-Opal-SSC-v2.30_pub.pdf` - PDF 원본

---

## 🎉 완료!

이제 PDF 문서가 완전히 구조화된 Markdown으로 변환되었습니다!

- ✅ 181개 섹션 정확히 분리
- ✅ 테이블 텍스트 제외
- ✅ LLM으로 테이블 파싱 준비 완료
- ✅ 읽기 쉬운 Markdown 형식
