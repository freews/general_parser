#!/bin/bash

echo "불필요한 파일/디렉토리 정리 중..."

# 디버그 디렉토리 삭제
rm -rf debug_continuation
rm -rf debug_false_positive_tables
rm -rf test_output
rm -rf test_llm_output
rm -rf test_pages_35_36

# 테스트 파일 삭제
rm -f test_llm_integration.py
rm -f test_pages_35_36.py

# 예제 파일 삭제
rm -f examples_fitz.py
rm -f files.zip

# 스크린샷 삭제
rm -f 'Screenshot from 2026-01-17 17-23-56.png'

# 로그 파일 삭제
rm -f parse_all.log
rm -f section_data_builder.log

# output 디렉토리 정리
rm -rf output/images
rm -rf output/sections
rm -rf output/section_data

# 이전 버전 스크립트 삭제 (v2가 최신)
rm -f section_data_builder.py
rm -f section_parser.py

# 불필요한 README 삭제
rm -f README_fitz.md

echo "정리 완료!"
echo ""
echo "유지된 파일/디렉토리:"
echo "- source_doc/ (PDF 원본)"
echo "- output/section_data_v2/ (최신 섹션 데이터)"
echo "- output/section_images/ (테이블/그림 이미지)"
echo "- section_extractor_v2.py (최신 추출기)"
echo "- 기타 필수 파일들"
