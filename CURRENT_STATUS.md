# General Parser - 현재 상태

## 📁 디렉토리 구조

```
general_parser/
├── source_doc/                          # PDF 원본 파일
│   ├── TCG-Storage-Opal-SSC-v2.30_pub.pdf
│   ├── NVM-Express-Base-Specification-Revision-2.3-2025.08.01-Ratified.pdf
│   └── Datacenter NVMe SSD Specification v2.0r21.pdf
│
├── output/
│   ├── section_data_v2/                 # ✅ 최신 섹션 데이터 (181개 JSON)
│   │   ├── section_index.json
│   │   ├── section_000_.json
│   │   └── ...
│   └── section_images/                  # ✅ 테이블/그림 이미지 (103개 PNG)
│       ├── table_003_0.png
│       └── ...
│
├── section_extractor_v2.py              # ✅ 최신 섹션 추출기
├── generate_table_images.py             # ✅ 이미지 생성기
├── fitz_layout_analyzer.py              # PDF 레이아웃 분석기
├── llm_table_parser.py                  # LLM 테이블 파서
├── table_merger.py                      # 테이블 병합 유틸
├── layout_helper.py                     # 레이아웃 헬퍼
│
├── TCG-Storage-Opal-SSC-v2.30_pub_layout.json  # 레이아웃 분석 결과
├── common_parameter.py                  # 공통 파라미터
├── General_Parser_목적.txt              # 프로젝트 목적
├── README_section_data.md               # 작업 문서
│
└── etc/                                 # 기타 유틸리티
    ├── vllm_continuation_verifier.py
    ├── examples_vllm_verifier.py
    ├── debug_table_detection.py
    └── README_vllm_verifier.md
```

## ✅ 완료된 작업

### 1. PDF 레이아웃 분석
- ✅ PyMuPDF(fitz)로 페이지별 테이블/이미지 위치 분석
- ✅ Continuation 테이블 자동 감지
- ✅ 파싱 전략 결정 (fitz-only, qwen-simple, qwen-continuation)
- **출력**: `TCG-Storage-Opal-SSC-v2.30_pub_layout.json`

### 2. Section별 데이터 추출 ⭐ (최신)
- ✅ TOC 기반 섹션 감지
- ✅ 텍스트 패턴 매칭으로 정확한 섹션 분리
- ✅ 같은 페이지의 여러 섹션 정확히 구분
- ✅ 181개 섹션 모두 처리 완료
- **출력**: `output/section_data_v2/` (181개 JSON)

### 3. 테이블/그림 이미지 생성
- ✅ bbox 기반 고해상도(300 DPI) PNG 추출
- ✅ 238개 테이블 이미지 생성
- ✅ 2개 그림 이미지 생성
- **출력**: `output/section_images/` (105개 PNG)

## 📊 통계

```
총 섹션 수: 181개
텍스트가 있는 섹션: 173개
총 텍스트 길이: 147,433 문자
총 테이블 수: 238개
총 그림 수: 2개
생성된 이미지: 105개 (테이블 103개 + 그림 2개)
```

## 🎯 다음 단계

### 1. LLM 테이블 파싱
각 테이블 이미지를 qwen3-vl로 파싱하여 Markdown으로 변환

```python
# 예시
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

## 🔧 주요 스크립트

### section_extractor_v2.py
**최신 섹션 추출기**

```bash
python3 section_extractor_v2.py
```

**기능**:
- Page별 MD 생성
- Section 제목 패턴 매칭
- 다음 섹션까지 텍스트 복사
- 테이블/그림 정보 매핑

### generate_table_images.py
**테이블/그림 이미지 생성기**

```bash
python3 generate_table_images.py
```

**기능**:
- Section JSON에서 bbox 읽기
- PDF에서 고해상도 PNG 추출
- 이미지 파일 저장

## 📝 JSON 구조

### section_XXX_YYY.json
```json
{
  "section_index": 89,
  "section_id": "4.2.1.2",
  "title": "4.2.1.2 SPTemplates (M)",
  "level": 4,
  "pages": {
    "start": 35,
    "end": 35,
    "count": 1
  },
  "content": {
    "text": "섹션의 텍스트 내용...",
    "tables": [
      {
        "table_id": "Table_35_1",
        "title": "Table 19 - Admin SP - SPTemplates Table Preconfiguration",
        "page": 35,
        "bbox": [151.86, 652.75, 460.10, 717.05],
        "image_path": "table_035_1.png",
        "markdown": null  // LLM 파싱 후 채워질 예정
      }
    ],
    "figures": []
  },
  "statistics": {
    "table_count": 2,
    "figure_count": 0
  }
}
```

## 🎉 주요 개선사항

### Section 경계 문제 해결 ✅
**이전**: 같은 페이지의 다른 섹션 내용이 섞임
```
Section 089 (4.2.1.2) 에 포함된 내용:
- 4.1.1.3 SyncSession (M)  ❌
- 4.1.1.4 CloseSession (O)  ❌
- 4.2 Admin SP  ❌
- 4.2.1 Base Template Tables  ❌
- 4.2.1.1 SPInfo (M)  ❌
- 4.2.1.2 SPTemplates (M)  ✅ (자신의 내용)
```

**현재**: 각 섹션이 자신의 내용만 포함
```
Section 089 (4.2.1.2) 에 포함된 내용:
- 4.2.1.2 SPTemplates (M)  ✅ (574 문자)
```

### 텍스트 패턴 기반 추출
- Page별 MD 먼저 생성
- Section 제목으로 시작점 찾기
- 다음 Section 제목까지 텍스트 복사
- 페이지 넘어가도 계속 추적

## 📌 참고사항

- **source_doc/**: 원본 PDF 파일 보관
- **output/section_data_v2/**: 최신 섹션 데이터 (이전 버전 삭제됨)
- **output/section_images/**: 테이블/그림 이미지
- 불필요한 디버그 파일, 테스트 파일 모두 정리 완료
