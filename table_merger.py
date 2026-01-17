"""
Table merger utility

같은 컬럼 구조를 가진 연속된 Markdown 테이블을 하나로 합침
"""

import re
from typing import List, Optional


def extract_table_header(table_md: str) -> Optional[List[str]]:
    """Markdown 테이블에서 헤더 추출
    
    Args:
        table_md: Markdown 테이블 문자열
    
    Returns:
        헤더 컬럼 리스트 또는 None
    """
    lines = table_md.strip().split('\n')
    if len(lines) < 2:
        return None
    
    # 첫 번째 줄이 헤더
    header_line = lines[0].strip()
    if not header_line.startswith('|'):
        return None
    
    # 헤더 파싱
    headers = [h.strip() for h in header_line.split('|')[1:-1]]
    return headers


def merge_tables(table1_md: str, table2_md: str) -> Optional[str]:
    """두 Markdown 테이블을 하나로 합침 (같은 헤더인 경우)
    
    Args:
        table1_md: 첫 번째 테이블
        table2_md: 두 번째 테이블
    
    Returns:
        합쳐진 테이블 또는 None (합칠 수 없는 경우)
    """
    # 헤더 추출
    headers1 = extract_table_header(table1_md)
    headers2 = extract_table_header(table2_md)
    
    if not headers1 or not headers2:
        return None
    
    # 헤더가 같은지 확인
    if headers1 != headers2:
        return None
    
    # 테이블 합치기
    lines1 = table1_md.strip().split('\n')
    lines2 = table2_md.strip().split('\n')
    
    # 첫 번째 테이블의 모든 줄 + 두 번째 테이블의 데이터 줄 (헤더와 구분선 제외)
    merged_lines = lines1 + lines2[2:]  # 헤더(0)와 구분선(1) 제외
    
    return '\n'.join(merged_lines)


def merge_consecutive_tables_in_text(text: str) -> str:
    """텍스트 내의 연속된 테이블들을 자동으로 합침
    
    Args:
        text: Markdown 텍스트
    
    Returns:
        테이블이 합쳐진 텍스트
    """
    # 테이블 패턴 찾기
    table_pattern = r'\n\*\*Table from [^:]+:\*\*\n\n((?:\|[^\n]+\n)+)'
    
    matches = list(re.finditer(table_pattern, text))
    
    if len(matches) < 2:
        return text  # 테이블이 2개 미만이면 합칠 것 없음
    
    # 역순으로 처리 (인덱스 변경 방지)
    for i in range(len(matches) - 1, 0, -1):
        prev_match = matches[i - 1]
        curr_match = matches[i]
        
        prev_table = prev_match.group(1)
        curr_table = curr_match.group(1)
        
        # 테이블 합치기 시도
        merged = merge_tables(prev_table, curr_table)
        
        if merged:
            # 합쳐진 테이블로 교체
            # 이전 테이블의 제목 유지, 현재 테이블 제거
            new_table_block = f"\n**Table from {prev_match.group(0).split('from ')[1].split(':')[0]}:**\n\n{merged}\n"
            
            # 텍스트 교체
            start = prev_match.start()
            end = curr_match.end()
            text = text[:start] + new_table_block + text[end:]
    
    return text


def test_merge():
    """테이블 머지 테스트"""
    table1 = """| UID | TemplateID | Name | Version |
|---|---|---|---|
| 00 00 00 03<br>00 00 00 01 | 00 00 02 04 00 00 00 01 | "Base" | 00 00 00 02<br>*ST1 |"""

    table2 = """| UID | TemplateID | Name | Version |
|---|---|---|---|
| 00 00 00 03<br>00 00 00 02 | 00 00 02 04 00 00 00 02 | "Admin" | 00 00 00 02<br>*ST1 |"""

    print("Table 1:")
    print(table1)
    print("\nTable 2:")
    print(table2)
    
    merged = merge_tables(table1, table2)
    
    if merged:
        print("\nMerged Table:")
        print(merged)
    else:
        print("\nCannot merge tables")


if __name__ == '__main__':
    test_merge()
