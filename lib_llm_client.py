"""
LLM 테이블 파서 - 테이블 이미지를 Markdown으로 변환

로컬 Ollama의 qwen3-vl 모델을 사용하여 테이블 이미지를 파싱
"""

import json
import base64
from pathlib import Path
from typing import Optional
import requests
from PIL import Image
import io


from common_parameter import LLM_MODEL, LLM_URL

class LLMTableParser:
    """LLM 기반 테이블 파서"""
    
    def __init__(self, model: str = LLM_MODEL, 
                 base_url: str = LLM_URL):
        """
        Args:
            model: Ollama 모델 이름
            base_url: Ollama API URL
        """
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
    
    def encode_image(self, image_path: str) -> str:
        """이미지를 base64로 인코딩"""
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def parse_table_images(self, image_paths: list, table_title: str = None) -> Optional[str]:
        """
        여러 테이블 이미지를 하나의 Markdown으로 파싱 (자동 병합)
        
        Args:
            image_paths: 테이블 이미지 경로 리스트
            table_title: 테이블 제목
        """
        if not image_paths:
            return None

        # [안전장치] 이미지별 크기 확인 및 과도한 병합 방지
        # 8192 토큰 제한을 고려하여, 너무 긴 이미지는 나누어서 처리
        MAX_HEIGHT_LIMIT = 6000 # 약 6000px 넘어가면 안전하게 분할 처리

        try:
            images = [Image.open(p) for p in image_paths]
            total_height = sum(img.height for img in images)
            
            if len(images) > 1 and total_height > MAX_HEIGHT_LIMIT:
                print(f"    ⚠️  총 높이({total_height}px)가 너무 큽니다. 분할 처리합니다.")
                
                # 이미지를 적절히 그룹화 (예: 2개씩)
                # 여기서는 간단히 개별 처리 후 합치는 방식으로 변경
                full_markdown = []
                
                # 청크 단위로 처리 (2개씩 묶거나, 4000px 단위로)
                current_chunk = []
                current_height = 0
                
                for img_path in image_paths:
                    with Image.open(img_path) as img:
                        h = img.height
                    
                    if current_height + h > 4000 and current_chunk:
                         # 청크 처리 실행
                         print(f"      🔹 청크 처리 중 ({len(current_chunk)}장)...")
                         chunk_md = self._parse_images_internal(current_chunk, table_title + " (Part)")
                         if chunk_md: full_markdown.append(chunk_md)
                         current_chunk = []
                         current_height = 0
                    
                    current_chunk.append(img_path)
                    current_height += h
                
                # 남은 청크 처리
                if current_chunk:
                    print(f"      🔹 마지막 청크 처리 중 ({len(current_chunk)}장)...")
                    chunk_md = self._parse_images_internal(current_chunk, table_title + " (Part)")
                    if chunk_md: full_markdown.append(chunk_md)
                
                return "\n".join(full_markdown)

        except Exception as e:
             print(f"    ⚠️  이미지 크기 확인 중 오류: {e}")

        # 일반 처리 (병합 가능한 경우)
        return self._parse_images_internal(image_paths, table_title)

    def _parse_images_internal(self, image_paths: list, table_title: str) -> Optional[str]:
        """실제 API 호출 로직 (기존 parse_table_images 내용 이동)"""
        # 1. 이미지 로드 및 병합 (여러 장일 경우)
        if len(image_paths) > 1:
            try:
                images = [Image.open(p) for p in image_paths]
                
                # 전체 크기 계산
                total_width = max(img.width for img in images)
                total_height = sum(img.height for img in images)
                
                # 새 이미지 생성 (흰색 배경)
                merged_img = Image.new('RGB', (total_width, total_height), (255, 255, 255))
                
                # 이어 붙이기
                y_offset = 0
                for img in images:
                    # 중앙 정렬 또는 왼쪽 정렬 (여기선 왼쪽)
                    merged_img.paste(img, (0, y_offset))
                    y_offset += img.height
                
                print(f"    ℹ️  {len(images)}개 이미지 병합 완료 ({total_width}x{total_height})")
                
                # Base64 인코딩
                buffer = io.BytesIO()
                merged_img.save(buffer, format="PNG")
                img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
                images_base64 = [img_str]
                
            except Exception as e:
                print(f"    ⚠️  이미지 병합 실패 (개별 처리 시도): {e}")
                images_base64 = [self.encode_image(path) for path in image_paths]
        else:
            # 단일 이미지
            images_base64 = [self.encode_image(image_paths[0])]
        
        # 2. 프롬프트 생성 (항상 단일 이미지 처리)
        prompt = f"""Please convert this table image to Markdown format.

Table Title: {table_title if table_title else 'N/A'}

Requirements:
1. Extract ALL text from the table accurately.
2. Preserve the table structure (rows and columns).
3. Use standard Markdown table syntax with | and -.
4. If the table is long or stitched from multiple parts, treat it as a SINGLE continuous table.
5. If there are repeated headers in the middle (due to page breaks), IGNORE/REMOVE them and merge the data rows seamlessly.
6. Keep all numerical values and special characters exactly as shown.
7. CRITICAL: Do NOT split multi-line cell content into separate rows. Keep them in a single row using <br> if necessary. 
8. Use only the internal horizontal lines of the table to distinguish rows. Text wrapping within a cell should NOT create a new row.
9. Do NOT add any explanations, just output the Markdown table.

Output the Markdown table directly."""
        
        # API 요청
        payload = {
            "model": self.model,
            "prompt": prompt,
            "images": images_base64,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_ctx": 8192
            }
        }
        
        try:
            # 타임아웃을 10분으로 증가 (병합된 대형 테이블 이미지 처리용)
            response = requests.post(self.api_url, json=payload, timeout=600)
            response.raise_for_status()
            
            result = response.json()
            markdown = result.get('response', '').strip()
            
            return markdown
            
        except Exception as e:
            print(f"❌ Error parsing images: {e}")
            return None
    
    def parse_figure_image(self, image_path: str) -> Optional[str]:
        """
        그림 이미지를 설명으로 변환
        
        Args:
            image_path: 그림 이미지 경로
            
        Returns:
            그림 설명 또는 None
        """
        # 이미지 인코딩
        image_base64 = self.encode_image(image_path)
        
        # 프롬프트
        prompt = """Please describe this figure/diagram in detail.

Requirements:
1. Describe what the figure shows
2. Explain the main components and their relationships
3. Note any labels, arrows, or annotations
4. Keep the description concise but informative

Provide a clear description of the figure."""
        
        # API 요청
        payload = {
            "model": self.model,
            "prompt": prompt,
            "images": [image_base64],
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_ctx": 4096
            }
        }
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=300)
            response.raise_for_status()
            
            result = response.json()
            description = result.get('response', '').strip()
            
            return description
            
        except Exception as e:
            print(f"❌ Error parsing {image_path}: {e}")
            return None


def process_all_sections(section_data_dir: str = "output/section_data_v2",
                        image_dir: str = "output/section_images",
                        limit: Optional[int] = None):
    """
    모든 섹션의 테이블/그림을 LLM으로 파싱
    
    Args:
        section_data_dir: 섹션 데이터 디렉토리
        image_dir: 이미지 디렉토리
        limit: 처리할 섹션 수 제한 (테스트용)
    """
    parser = LLMTableParser()
    
    section_path = Path(section_data_dir)
    image_path = Path(image_dir)
    
    # 섹션 JSON 파일 목록
    section_files = sorted(section_path.glob("section_*.json"))
    section_files = [f for f in section_files if f.name != "section_index.json"]
    
    if limit:
        section_files = section_files[:limit]
    
    print(f"\n총 {len(section_files)}개 섹션 처리 시작...\n")
    
    total_tables = 0
    total_figures = 0
    parsed_tables = 0
    parsed_figures = 0
    
    for i, section_file in enumerate(section_files, 1):
        with open(section_file, 'r', encoding='utf-8') as f:
            section_data = json.load(f)
        
        section_id = section_data['section_id']
        title = section_data['title']
        
        tables = section_data['content']['tables']
        figures = section_data['content']['figures']
        
        if not tables and not figures:
            continue
        
        print(f"[{i}/{len(section_files)}] {section_id} - {title}")
        print(f"  테이블: {len(tables)}개, 그림: {len(figures)}개")
        
        updated = False
        
        # 테이블 파싱
        for table in tables:
            if table.get('markdown'):
                continue  # 이미 파싱됨
            
            image_file = image_path / table['image_path']
            if not image_file.exists():
                print(f"  ⚠️  이미지 없음: {table['image_path']}")
                continue
            
            print(f"  📊 파싱 중: {table.get('title', 'Untitled')}...")
            markdown = parser.parse_table_image(str(image_file))
            
            if markdown:
                table['markdown'] = markdown
                parsed_tables += 1
                updated = True
                print(f"  ✅ 완료")
            else:
                print(f"  ❌ 실패")
        
        # 그림 파싱
        for figure in figures:
            if figure.get('description'):
                continue  # 이미 파싱됨
            
            image_file = image_path / figure['image_path']
            if not image_file.exists():
                print(f"  ⚠️  이미지 없음: {figure['image_path']}")
                continue
            
            print(f"  🖼️  파싱 중: {figure.get('title', 'Untitled')}...")
            description = parser.parse_figure_image(str(image_file))
            
            if description:
                figure['description'] = description
                parsed_figures += 1
                updated = True
                print(f"  ✅ 완료")
            else:
                print(f"  ❌ 실패")
        
        # JSON 업데이트
        if updated:
            with open(section_file, 'w', encoding='utf-8') as f:
                json.dump(section_data, f, ensure_ascii=False, indent=2)
        
        total_tables += len(tables)
        total_figures += len(figures)
        print()
    
    print(f"\n✅ 완료!")
    print(f"총 테이블: {total_tables}개 (파싱: {parsed_tables}개)")
    print(f"총 그림: {total_figures}개 (파싱: {parsed_figures}개)")


def main():
    """테스트 실행"""
    print("=" * 80)
    print("LLM Table Parser - 테이블/그림 파싱")
    print("=" * 80)
    
    # 처음 3개 섹션만 테스트
    process_all_sections(
        section_data_dir="output/section_data_v2",
        image_dir="output/section_images",
        limit=3  # 테스트용
    )


if __name__ == '__main__':
    main()
