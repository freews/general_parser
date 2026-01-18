#!/usr/bin/env python3
"""
DeepSeek OCR 후처리 - KEEP AS-IS VERSION
=========================================

전략: 문서에서 보이는 그대로
- HTML 테이블 → 그대로 유지 (변환 안 함)
- rowspan, colspan → 그대로 유지
- 특수 토큰만 제거 (<|ref|>, <|det|>)
"""

import re
from pathlib import Path

def clean_deepseek_tokens(content: str) -> str:
    """
    DeepSeek 특수 토큰만 제거
    
    제거 대상:
    - <|ref|>...<|/ref|>
    - <|det|>[[...]]<|/det|>
    
    유지:
    - HTML 태그 (<table>, <tr>, <td>, <br> 등)
    - 모든 내용
    """
    
    # <|ref|>...<|/ref|> 제거
    content = re.sub(r'<\|ref\|>.*?<\|/ref\|>', '', content, flags=re.DOTALL)
    
    # <|det|>[[...]]<|/det|> 제거
    content = re.sub(r'<\|det\|>\[\[.*?\]\]<\|/det\|>', '', content, flags=re.DOTALL)
    
    return content

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python deepseek_clean_tokens.py <md_folder>")
        print("\nThis will:")
        print("  ✅ Remove: <|ref|>...<|/ref|>")
        print("  ✅ Remove: <|det|>[[...]]<|/det|>")
        print("  ✅ Keep: HTML tables with rowspan/colspan")
        print("  ✅ Keep: All content as-is")
        sys.exit(1)
    
    md_folder = Path(sys.argv[1])
    
    if not md_folder.exists():
        print(f"❌ Folder not found: {md_folder}")
        sys.exit(1)
    
    md_files = sorted(md_folder.glob("*.md"))
    
    if not md_files:
        print(f"❌ No .md files found in {md_folder}")
        sys.exit(1)
    
    print(f"Processing {len(md_files)} files...")
    print("="*70)
    
    for md_file in md_files:
        print(f"📄 {md_file.name}", end=" ")
        
        # 원본 읽기
        content = md_file.read_text(encoding='utf-8')
        
        # 토큰만 제거
        cleaned = clean_deepseek_tokens(content)
        
        # 저장
        md_file.write_text(cleaned, encoding='utf-8')
        
        # 변경 사항 확인
        removed_bytes = len(content) - len(cleaned)
        print(f"→ Removed {removed_bytes} bytes ✅")
    
    print("="*70)
    print(f"✅ All done! HTML tables preserved as-is")

if __name__ == "__main__":
    main()
