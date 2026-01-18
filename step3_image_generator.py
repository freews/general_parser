import fitz
import json
from pathlib import Path
from typing import Dict, List
from PIL import Image
from common_parameter import PDF_PATH, OUTPUT_DIR


class TableImageGenerator:
    """테이블/그림 이미지 생성기"""
    
    def __init__(self, pdf_path: str, section_data_dir: str = "output/section_data"):
        """
        Args:
            pdf_path: PDF 파일 경로
            section_data_dir: 섹션 데이터 JSON 디렉토리
        """
        self.pdf_path = Path(pdf_path)
        self.doc = fitz.open(str(pdf_path))
        self.section_data_dir = Path(section_data_dir)
        
    def generate_table_image(self, page_num: int, bbox: List[float], 
                            output_path: Path, margin: int = 5):
        """
        테이블 이미지 생성
        
        Args:
            page_num: 페이지 번호 (1-based)
            bbox: [x0, y0, x1, y1]
            output_path: 출력 파일 경로
            margin: bbox 주변 여백 (픽셀). 상단 여백은 적용하지 않음.
        """
        page = self.doc[page_num - 1]
        
        # bbox에 여백 추가
        rect = fitz.Rect(bbox)
        # 상단(y0)은 여백 없음 (제목 간섭 최소화)
        # 좌우(x) 및 하단(y1)에만 5px 여백 추가
        rect.x0 = max(0, rect.x0 - margin)
        rect.y0 = max(0, rect.y0 - margin)
        rect.x1 = min(page.rect.width, rect.x1 + margin)
        rect.y1 = min(page.rect.height, rect.y1 + margin)
        
        # 고해상도 이미지 생성 (150 DPI) - 사용자 요청
        # 150 DPI = 72 DPI * 2.083
        dpi_scale = 150 / 72
        mat = fitz.Matrix(dpi_scale, dpi_scale)
        pix = page.get_pixmap(matrix=mat, clip=rect)
        
        # PNG로 저장
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pix.save(str(output_path))
        
        # [후처리] PIL로 상단 강제 Crop (제목 제거)
        try:
            with Image.open(str(output_path)) as img:
                width, height = img.size
                
                # 150 DPI 기준, 상단 12px 제거
                # 15px는 헤더가 너무 바짝 잘림, 10px는 캡션이 남음 -> 12px로 미세 조정
                crop_top = 0
                
                # 이미지가 crop_top 보다 충분히 클 때만 자름 (최소 50px 남김)
                if height > crop_top + 50:
                    cropped_img = img.crop((0, crop_top, width, height))
                    cropped_img.save(str(output_path))
                    # print(f"  ✂️ Cropped top {crop_top}px")
        except Exception as e:
            print(f"  ⚠️ PIL Crop 실패: {e}")
            
        return output_path
    
    def generate_figure_image(self, page_num: int, bbox: List[float], 
                             output_path: Path, margin: int = 5):
        """
        그림 이미지 생성 (테이블과 동일한 방식)
        
        Args:
            page_num: 페이지 번호 (1-based)
            bbox: [x0, y0, x1, y1]
            output_path: 출력 파일 경로
            margin: bbox 주변 여백 (픽셀)
        """
        return self.generate_table_image(page_num, bbox, output_path, margin)
    
    def process_section(self, section_file: Path, output_dir: Path):
        """
        섹션 JSON 파일 처리
        
        Args:
            section_file: 섹션 JSON 파일 경로
            output_dir: 이미지 출력 디렉토리
        """
        with open(section_file, 'r', encoding='utf-8') as f:
            section_data = json.load(f)
        
        section_id = section_data['section_id']
        section_index = section_data['section_index']
        
        # 테이블 이미지 생성
        tables = section_data['content']['tables']
        for table in tables:
            image_name = table['image_path']
            output_path = output_dir / image_name
            
            if not output_path.exists():
                self.generate_table_image(
                    page_num=table['page'],
                    bbox=table['bbox'],
                    output_path=output_path
                )
                print(f"  ✓ 테이블 이미지 생성: {image_name}")
            else:
                print(f"  ⏭️  이미지 존재함(건너뜀): {image_name}")
        
        # 그림 이미지 생성
        figures = section_data['content']['figures']
        for figure in figures:
            image_name = figure['image_path']
            output_path = output_dir / image_name
            
            if not output_path.exists():
                self.generate_figure_image(
                    page_num=figure['page'],
                    bbox=figure['bbox'],
                    output_path=output_path
                )
                print(f"  ✓ 그림 이미지 생성: {image_name}")
            else:
                print(f"  ⏭️  이미지 존재함(건너뜀): {image_name}")
        
        return len(tables), len(figures)
    
    def process_all_sections(self, output_dir: str = "output/section_images"):
        """
        모든 섹션 처리
        
        Args:
            output_dir: 이미지 출력 디렉토리
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # JSON 파일 목록
        json_files = sorted(self.section_data_dir.glob("*.json"))
        json_files = [f for f in json_files if f.name != "section_index.json"]
        
        print(f"\n총 {len(json_files)}개 섹션 처리 시작...")
        print(f"출력 디렉토리: {output_path}\n")
        
        total_tables = 0
        total_figures = 0
        
        for i, json_file in enumerate(json_files, 1):
            # 섹션 정보 읽기
            with open(json_file, 'r', encoding='utf-8') as f:
                section_data = json.load(f)
            
            # 진행 상황 표시 (NameError 수정됨)
            print(f"[{i}/{len(json_files)}] {section_data.get('section_id', 'N/A')} - {section_data.get('title', 'Untitled')}")

            table_count = section_data['statistics']['table_count']
            figure_count = section_data['statistics']['figure_count']
            
            if table_count > 0 or figure_count > 0:
                print(f"[{i}/{len(json_files)}] {section_data['section_id']} - {section_data['title']}")
                print(f"  테이블: {table_count}개, 그림: {figure_count}개")
                
                t_count, f_count = self.process_section(json_file, output_path)
                total_tables += t_count
                total_figures += f_count
        
        print(f"\n✅ 완료!")
        print(f"총 테이블 이미지: {total_tables}개")
        print(f"총 그림 이미지: {total_figures}개")
    
    def close(self):
        """문서 닫기"""
        if self.doc:
            self.doc.close()


def main():
    """테스트 실행"""
    from common_parameter import PDF_PATH, OUTPUT_DIR
    
    print("=" * 80)
    print("Table/Figure Image Generator - 테이블/그림 이미지 생성")
    print("=" * 80)
    
    # 디렉토리 확인
    section_data_dir = Path(OUTPUT_DIR) / "section_data_v2"
    image_dir = Path(OUTPUT_DIR) / "section_images"
    image_dir.mkdir(parents=True, exist_ok=True)
    
    generator = TableImageGenerator(
        pdf_path=PDF_PATH,
        section_data_dir=section_data_dir
    )
    
    try:
        generator.process_all_sections(
            output_dir=image_dir
        )
    finally:
        generator.close()


if __name__ == '__main__':
    main()
