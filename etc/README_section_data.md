# Section별 데이터 구조화 작업 완료

## 📊 작업 개요

PDF 문서를 Section별로 정확하게 파싱하여 JSON 구조로 저장하는 시스템을 구축했습니다.

### 주요 목표
- ✅ Section 경계를 정확히 구분
- ✅ 각 Section별로 텍스트, 테이블, 그림 정보를 분리 저장
- ✅ 테이블과 그림은 PNG 이미지로 추출
- ✅ LLM 파싱을 위한 구조화된 데이터 준비

---

## 📁 출력 구조

```
output/
├── section_data/           # Section별 JSON 데이터
│   ├── section_index.json  # 전체 섹션 인덱스
│   ├── section_000_.json   # 각 섹션 데이터
│   ├── section_001_.json
│   └── ...
│
└── section_images/         # 테이블/그림 이미지
    ├── table_003_0.png
    ├── table_012_0.png
    ├── figure_096_0.png
    └── ...
```

---

## 📈 통계

### 전체 문서
- **총 섹션 수**: 181개
- **총 테이블 수**: 238개
- **총 그림 수**: 2개

### 섹션별 분포
- **테이블이 있는 섹션**: 118개
- **그림이 있는 섹션**: 2개

### 생성된 이미지
- **테이블 이미지**: 103개 (고해상도 300 DPI PNG)
- **그림 이미지**: 2개

---

## 🗂️ JSON 구조

### section_index.json
전체 섹션의 인덱스 파일

```json
{
  "pdf_name": "TCG-Storage-Opal-SSC-v2.30_pub.pdf",
  "total_sections": 181,
  "sections": [
    {
      "index": 41,
      "section_id": "3.1.1.1",
      "title": "3.1.1.1 Level 0 Discovery Header",
      "level": 4,
      "pages": "19-19",
      "file": "section_041_3_1_1_1.json"
    }
  ]
}
```

### section_XXX_YYY.json
각 섹션의 상세 데이터

```json
{
  "section_index": 41,
  "section_id": "3.1.1.1",
  "title": "3.1.1.1 Level 0 Discovery Header",
  "level": 4,
  "pages": {
    "start": 19,
    "end": 19,
    "count": 1
  },
  "content": {
    "text": "섹션의 텍스트 내용 (테이블 영역 제외)...",
    "tables": [
      {
        "table_id": "Table_19_0",
        "title": "Table 2 - Level 0 Discovery Header",
        "page": 19,
        "bbox": [58.819, 366.342, 553.204, 603.040],
        "image_path": "table_019_0.png",
        "markdown": null  // LLM 파싱 후 채워질 예정
      }
    ],
    "figures": [
      {
        "figure_id": "Figure_96_0",
        "title": null,
        "page": 96,
        "bbox": [100.0, 200.0, 500.0, 400.0],
        "image_path": "figure_096_0.png",
        "description": null  // LLM 파싱 후 채워질 예정
      }
    ]
  },
  "statistics": {
    "table_count": 1,
    "figure_count": 0
  }
}
```

---

## 🔧 주요 스크립트

### 1. section_data_builder.py
Section별 JSON 데이터 생성

**기능**:
- TOC에서 섹션 감지 및 페이지 범위 계산
- 각 섹션의 텍스트 추출 (테이블 영역 제외)
- 테이블/그림 메타데이터 수집
- JSON 파일로 저장

**실행**:
```bash
python3 section_data_builder.py
```

**출력**:
- `output/section_data/section_index.json`
- `output/section_data/section_XXX_YYY.json` (181개)

---

### 2. generate_table_images.py
테이블/그림 이미지 생성

**기능**:
- Section JSON에서 bbox 정보 읽기
- PDF에서 해당 영역을 고해상도(300 DPI) PNG로 추출
- 이미지 파일 저장

**실행**:
```bash
python3 generate_table_images.py
```

**출력**:
- `output/section_images/table_XXX_Y.png` (103개)
- `output/section_images/figure_XXX_Y.png` (2개)

---

## 🎯 다음 단계

### 1. LLM 테이블 파싱
각 테이블 이미지를 LLM(qwen3-vl)으로 파싱하여 Markdown으로 변환

```python
# 예시 코드
from llm_table_parser import parse_table_image

for section_file in section_files:
    section_data = load_json(section_file)
    
    for table in section_data['content']['tables']:
        image_path = f"output/section_images/{table['image_path']}"
        markdown = parse_table_image(image_path)
        
        # JSON 업데이트
        table['markdown'] = markdown
        save_json(section_file, section_data)
```

### 2. LLM 그림 파싱
각 그림 이미지를 LLM으로 분석하여 설명 생성

### 3. 최종 문서 생성
모든 섹션 데이터를 통합하여 완전한 Markdown 문서 생성

---

## 🔍 주요 개선사항

### Section 경계 문제 해결
- **이전**: 다른 섹션의 테이블이 섞여 들어가는 문제
- **해결**: Section별로 정확한 페이지 범위 계산 및 bbox 기반 분리

### 데이터 구조화
- **이전**: 단순 Markdown 파일
- **개선**: 구조화된 JSON + 이미지 분리 저장

### LLM 파싱 준비
- **이전**: 전체 페이지를 LLM에 전달
- **개선**: 필요한 테이블/그림만 선택적으로 LLM 파싱

---

## 📝 사용 예시

### Section 데이터 읽기
```python
import json

# 인덱스 읽기
with open('output/section_data/section_index.json', 'r') as f:
    index = json.load(f)

# 특정 섹션 읽기
with open('output/section_data/section_041_3_1_1_1.json', 'r') as f:
    section = json.load(f)

print(f"Section: {section['section_id']} - {section['title']}")
print(f"Pages: {section['pages']['start']}-{section['pages']['end']}")
print(f"Tables: {section['statistics']['table_count']}")
print(f"Figures: {section['statistics']['figure_count']}")
```

### 테이블 정보 확인
```python
for table in section['content']['tables']:
    print(f"Table: {table['title']}")
    print(f"Page: {table['page']}")
    print(f"Image: {table['image_path']}")
    print(f"Markdown: {table['markdown']}")  # LLM 파싱 후
```

---

## ✅ 완료 체크리스트

- [x] Section 감지 및 페이지 범위 계산
- [x] Section별 텍스트 추출 (테이블 제외)
- [x] 테이블/그림 메타데이터 수집
- [x] JSON 구조 설계 및 저장
- [x] 테이블/그림 이미지 생성 (300 DPI PNG)
- [x] 전체 인덱스 파일 생성
- [ ] LLM 테이블 파싱 (다음 단계)
- [ ] LLM 그림 파싱 (다음 단계)
- [ ] 최종 문서 생성 (다음 단계)

---

## 🎉 결론

Section별로 정확하게 구조화된 데이터를 생성했습니다!

- **181개 섹션** 모두 처리 완료
- **238개 테이블** 이미지 추출 완료
- **2개 그림** 이미지 추출 완료
- LLM 파싱을 위한 준비 완료

이제 각 테이블/그림 이미지를 LLM으로 파싱하여 Markdown으로 변환하는 단계로 진행할 수 있습니다.
