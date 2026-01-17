"""
단일 섹션 테스트 - Section 089 (4.2.1.2 SPTemplates)
"""

from lib_llm_client import LLMTableParser
import json
from pathlib import Path

# 파서 초기화
parser = LLMTableParser()

# Section 089 로드
section_file = Path("output/section_data_v2/section_089_4_2_1_2.json")
with open(section_file, 'r', encoding='utf-8') as f:
    section_data = json.load(f)

print(f"섹션: {section_data['section_id']} - {section_data['title']}")
print(f"테이블 수: {len(section_data['content']['tables'])}\n")

# 각 테이블 파싱
for i, table in enumerate(section_data['content']['tables'], 1):
    print(f"[{i}/{len(section_data['content']['tables'])}] {table.get('title', 'Untitled')}")
    print(f"  이미지: {table['image_path']}")
    
    image_path = f"output/section_images/{table['image_path']}"
    
    if not Path(image_path).exists():
        print(f"  ❌ 이미지 없음\n")
        continue
    
    print(f"  🔄 LLM 파싱 중...")
    markdown = parser.parse_table_image(image_path)
    
    if markdown:
        print(f"  ✅ 완료!")
        print(f"\n--- Markdown 결과 ---")
        print(markdown[:500])  # 처음 500자만 출력
        if len(markdown) > 500:
            print(f"... (총 {len(markdown)} 문자)")
        print(f"--- 끝 ---\n")
        
        # JSON 업데이트
        table['markdown'] = markdown
    else:
        print(f"  ❌ 파싱 실패\n")

# 저장
with open(section_file, 'w', encoding='utf-8') as f:
    json.dump(section_data, f, ensure_ascii=False, indent=2)

print(f"\n✅ Section 089 업데이트 완료: {section_file}")
