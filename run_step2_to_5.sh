#!/bin/bash
set -e
echo "=== STEP 2: 섹션 데이터 재추출 (JSON 초기화) ==="
python3 step2_section_extractor.py

echo -e "\n=== STEP 3: 이미지 재생성 (상단 여백 추가) ==="
python3 step3_image_generator.py

echo -e "\n=== STEP 4: LLM 테이블 파싱 (이미지 병합 적용) ==="
python3 step4_llm_parser.py

echo -e "\n=== STEP 5: 마크다운 변환 ==="
python3 step5_markdown_converter.py

