"""
섹션별 테이블 그룹화 및 LLM 파싱

같은 제목의 연속된 테이블들을 그룹화하여 LLM에 한번에 전달
"""

from lib_llm_client import LLMTableParser
import json
from pathlib import Path
from typing import List, Dict
from common_parameter import PDF_PATH,OUTPUT_DIR

from utils_logger import setup_advanced_logger
import logging

logger = setup_advanced_logger(name="step4_llm_parser", dir=OUTPUT_DIR, log_level=logging.INFO)



def group_tables_by_title(tables: List[Dict]) -> List[List[Dict]]:
    """
    같은 제목의 연속된 테이블들을 그룹화
    
    Args:
        tables: 테이블 리스트
        
    Returns:
        그룹화된 테이블 리스트의 리스트
    """
    if not tables:
        return []
    
    groups = []
    current_group = [tables[0]]
    current_title = tables[0].get('title')
    
    for table in tables[1:]:
        table_title = table.get('title')
        
        # 제목이 같거나, 다음 테이블에 제목이 없으면 (continuation) 같은 그룹
        if table_title == current_title or table_title is None:
            current_group.append(table)
        else:
            # 새로운 그룹 시작
            groups.append(current_group)
            current_group = [table]
            current_title = table_title
    
    # 마지막 그룹 추가
    if current_group:
        groups.append(current_group)
    
    return groups


def parse_section_tables(section_file: Path, image_dir: Path, parser: LLMTableParser):
    """
    섹션의 모든 테이블을 그룹화하여 파싱
    
    Args:
        section_file: 섹션 JSON 파일
        image_dir: 이미지 디렉토리
        parser: LLMTableParser 인스턴스
    """
    # 섹션 데이터 로드
    try:
        with open(section_file, 'r', encoding='utf-8') as f:
            section_data = json.load(f)
    except Exception as e:
        logger.info(f"❌ 파일 읽기 실패: {section_file.name} - {e}")
        return
    
    section_id = section_data['section_id']
    title = section_data['title']
    tables = section_data['content']['tables']
    
    if not tables:
        return
    
    logger.info(f"\n{'-'*60}")
    logger.info(f"섹션: {section_id} - {title}")
    logger.info(f"테이블 수: {len(tables)}")
    
    # 이미 처리된 마크다운이 있는지 확인 (중복 파싱 방지)
    # 단, 사용자 요청에 따라 덮어쓰거나 할 수도 있음. 여기서는 일단 진행.
    
    # 테이블 그룹화
    table_groups = group_tables_by_title(tables)
    logger.info(f"테이블 그룹: {len(table_groups)}개")
    
    updated_count = 0
    
    # 각 그룹 처리
    for group_idx, group in enumerate(table_groups, 1):
        if group[0].get('table_md') and len(group[0]['table_md']) > 10:
            logger.info(f"  ⏭️  이미 파싱됨 (Skip): {group[0].get('title', 'Untitled')}")
            continue

        group_title = group[0].get('title')
        if not group_title:
             group_title = "Untitled Table"
             
        logger.info(f"\n[그룹 {group_idx}/{len(table_groups)}] {group_title}")
        
        # 이미지 경로 수집
        image_paths = []
        for table in group:
            if 'image_path' in table:
                image_name = table['image_path']
            else:
                image_name = f"{table['id']}.png"
                
            image_path = image_dir / image_name
            if image_path.exists():
                image_paths.append(str(image_path))
            else:
                # Recovery 폴더 확인
                recovery_path = image_dir.parent / "section_images_recovery" / image_name
                if recovery_path.exists():
                    image_paths.append(str(recovery_path))
                else:
                    logger.info(f"    ⚠️  이미지 없음: {image_name}")
        
        if not image_paths:
            logger.info(f"  ❌ 파싱할 이미지 없음")
            continue

        logger.info(f"  이미지 {len(image_paths)}개: {[Path(p).name for p in image_paths]}")
        
        # LLM 파싱
        logger.info(f"  🔄 LLM 파싱 중...")
        try:
            markdown = parser.parse_table_images(image_paths, group_title)
            
            if markdown:
                logger.info(f"  ✅ 완료! ({len(markdown)} 문자)")
                
                # JSON 데이터 업데이트
                for i, table in enumerate(group):
                    # 원본 텍스트는 건드리지 않고, 별도 필드에 마크다운 저장
                    if i == 0: # 그룹의 첫 번째 테이블에만 전체 마크다운 저장
                        table['table_md'] = markdown
                    else: # 나머지 테이블들은 참조 표시
                        table['table_md'] = f"(Continuation of {group_title} - see first part)"
                
                updated_count += 1
            else:
                logger.info(f"  ❌ 파싱 결과 없음 (Empty response)")
                
        except Exception as e:
            logger.info(f"  ❌ 파싱 중 오류 발생: {e}")
            
    # 변경사항이 있으면 JSON 저장
    if updated_count > 0:
        with open(section_file, 'w', encoding='utf-8') as f:
            json.dump(section_data, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 섹션 파일 업데이트 완료")


def main():
    """전체 섹션 순차 처리"""
    from common_parameter import OUTPUT_DIR
    
    # 경로 설정
    section_dir = Path(OUTPUT_DIR) / "section_data_v2"
    image_dir = Path(OUTPUT_DIR) / "section_images"
    
    if not section_dir.exists():
        logger.info(f"❌ 섹션 데이터 디렉토리가 없습니다: {section_dir}")
        return
    
    # 섹션 JSON 파일 목록
    json_files = sorted(section_dir.glob("*.json"))
    json_files = [f for f in json_files if f.name != "section_index.json"]
    
    logger.info(f"Target sections: {len(json_files)}")
    
    # LLM 파서 초기화 (한 번만 생성)
    try:
        parser = LLMTableParser()
        logger.info("✅ LLM 파서 초기화 완료\n")
    except Exception as e:
        logger.info(f"❌ LLM 파서 초기화 실패: {e}")
        return

    # 순차 처리
    processed_sections = 0
    tables_processed = 0
    
    # 테스트용 필터 (전체 실행 시에는 비워두거나 제거)
    target_sections = []  # 빈 리스트면 필터링 안 함
    
    for i, section_file in enumerate(json_files, 1): # Changed from section_files to json_files
        # 섹션 데이터 로드
        try:
            with open(section_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            logger.info(f"❌ 파일 읽기 실패: {section_file.name} - {e}")
            continue

        # Section 5 이상은 처리하지 않음 (사용자 요청)
        # 섹션 ID가 '5'로 시작하거나, 순서상 뒤쪽이면 제외할 수도 있음
        # 여기서는 ID 기반 필터링
        # Section 5 이상은 처리하지 않음 (사용자 요청)
        # 섹션 ID가 '5'로 시작하거나, 순서상 뒤쪽이면 제외할 수도 있음
        # 여기서는 ID 기반 필터링
        # section_id = data.get('section_id', '')
        # if section_id.startswith('5.') or section_id == '5':
        #     logger.info(f"  ⏩ 섹션 ID '{section_id}'는 건너뜁니다.")
        #     continue
            
        # 기존 target_sections 필터링 (파일 이름 기반)
        if target_sections and not any(t in section_file.name for t in target_sections):
            continue
            
        # 테이블이 있는 섹션인지 먼저 확인 (불필요한 로딩 방지)
        # 하지만 parse_section_tables 함수 안에서 로드하므로 여기서는 일단 호출
        # 진행 상황 표시
        # logger.info(f"Processing {i}/{len(section_files)}: {section_file.name} ...")
        
        parse_section_tables(section_file, image_dir, parser)
        processed_sections += 1

    logger.info("\n" + "=" * 80)
    logger.info("🎉 모든 처리 완료!")
    logger.info(f"총 처리된 섹션 파일: {processed_sections}/{len(json_files)}")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
