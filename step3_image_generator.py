import fitz
import json
from pathlib import Path
from typing import Dict, List
from PIL import Image
from common_parameter import PDF_PATH, OUTPUT_DIR, TABLE_DPI
from logger import setup_advanced_logger # error 시 Archive/logger.py 사용할 것 
import logging

logger = setup_advanced_logger(name="step3_image_generator", log_dir=OUTPUT_DIR, log_level=logging.INFO)


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
                            output_path: Path, 
                            margin_top: int = 2, margin_bottom: int = 5, 
                            margin_left: int = 2, margin_right: int = 2, 
                            dpi: int = 120):
        """
        테이블 이미지 생성
        
        Args:
            page_num: 페이지 번호 (1-based)
            bbox: [x0, y0, x1, y1]
            output_path: 출력 파일 경로
            margin_*: 각 방향별 여백 (픽셀)
            dpi: 이미지 해상도 (DPI), 기본값 120
        """
        page = self.doc[page_num - 1]
        
        # The BBox in JSON comes from Step 1 (DeepSeek), which typically uses a 1000x1000 normalized coordinate system.
        # PyMuPDF expects coordinates in PDF points (1/72 inch).
        # We must scale the 1000-based coordinates to the actual page dimensions in points.
        
        page_width = page.rect.width
        page_height = page.rect.height
        
        scale_x = page_width / 1000.0
        scale_y = page_height / 1000.0
        
        pdf_bbox = [
            bbox[0] * scale_x,
            bbox[1] * scale_y,
            bbox[2] * scale_x,
            bbox[3] * scale_y
        ]
        
        rect = fitz.Rect(pdf_bbox)
        
        # 상단(y0) 조절 로직
        rect.x0 = max(0, rect.x0 - margin_left)
        rect.y0 = max(0, rect.y0 - margin_top)
        rect.x1 = min(page.rect.width, rect.x1 + margin_right)
        rect.y1 = min(page.rect.height, rect.y1 + margin_bottom)
        
        # 유효성 검사
        if rect.width <= 0 or rect.height <= 0:
            logger.warning(f"  ⚠️ Invalid dimensions for image: {rect} (Page {page_num}) - Skipping")
            return output_path

        # 고해상도 이미지 생성
        try:
            dpi_scale = dpi / 72
            mat = fitz.Matrix(dpi_scale, dpi_scale)
            pix = page.get_pixmap(matrix=mat, clip=rect)
            
            # PNG로 저장
            output_path.parent.mkdir(parents=True, exist_ok=True)
            pix.save(str(output_path))
        except Exception as e:
            logger.error(f"  ❌ Failed to save image {output_path}: {e}")
            return output_path
        
        # # [후처리] PIL로 상단 강제 Crop (제목 제거)
        # try:
        #     with Image.open(str(output_path)) as img:
        #         width, height = img.size
                
        #         # 120 DPI 기준, 상단 8px 제거 
        #         # (150dpi일 때 12px -> 120dpi일 때 약 9.6px -> 8~10px 적절)
        #         # 헤더 보존을 위해 조금 보수적으로 8px 설정 (crop=0은 사용자가 직접 세팅했었으므로, 로직은 유지하되 값만 변경)
        #         # User 요청: crop=0 이었지만 DPI 바뀌면 다시 제목 나올 수 있음.
        #         # 하지만 User는 "지금은 제목 안보이고..." 라고 만족했으므로, DPI 바뀌면 비율 맞춰야 함.
        #         # 그러나 User가 방금 "해상도를 변경하는 것을 해볼까?" 했으므로 DPI 변경에 집중.
        #         # crop_top은 안전하게 0으로 두겠습니다. (User가 0으로 만족했음)
        #         crop_top = 0
                
        #         # 이미지가 crop_top 보다 충분히 클 때만 자름 (최소 50px 남김)
        #         if height > crop_top + 50:
        #             cropped_img = img.crop((0, crop_top, width, height))
        #             cropped_img.save(str(output_path))
        #             # logger.info(f"  ✂️ Cropped top {crop_top}px")
        # except Exception as e:
        #     logger.info(f"  ⚠️ PIL Crop 실패: {e}")
            
        return output_path
    
    def generate_figure_image(self, page_num: int, bbox: List[float], 
                             output_path: Path, 
                             margin_top: int = 1, margin_bottom: int = 1, 
                             margin_left: int = 1, margin_right: int = 1):
        """
        그림 이미지 생성 (테이블과 동일한 방식)
        
        Args:
            page_num: 페이지 번호 (1-based)
            bbox: [x0, y0, x1, y1]
            output_path: 출력 파일 경로
            margin_*: 각 방향별 여백 (픽셀)
        """
        return self.generate_table_image(page_num, bbox, output_path, 
                                       margin_top=margin_top, margin_bottom=margin_bottom,
                                       margin_left=margin_left, margin_right=margin_right,
                                       dpi=TABLE_DPI)
    
    def process_section(self, section_file: Path, output_dir: Path):
        """
        섹션 JSON 파일 처리
        """
        with open(section_file, 'r', encoding='utf-8') as f:
            section_data = json.load(f)
        
        section_id = section_data.get('section_id', '')
        section_title = section_data.get('title', '')
        
        def make_safe(s):
            return "".join([c if c.isalnum() else "_" for c in s]).strip("_")
            
        safe_id = make_safe(section_id)
        clean_title = section_title
        if section_id and section_title.startswith(section_id):
            clean_title = section_title[len(section_id):].strip()
        safe_title = make_safe(clean_title)
        
        while "__" in safe_id: safe_id = safe_id.replace("__", "_")
        while "__" in safe_title: safe_title = safe_title.replace("__", "_")

        BBOX_OVERRIDES = {
            "table_76_124": {"margin_bottom": 45},
        }
        
        json_modified = False
        tables = section_data['content']['tables']
        
        # --- Strict Grouping Logic based on User Rules ---
        # Rule 1: First has title, Next has no title -> Merge
        # Rule 2: Titles are same -> Merge
        # Rule 3: All have no titles -> Merge
        # Logic: Merge if (Current has No Title OR Current Title == Previous Title)
        
        grouped_tables = []
        if tables:
            current_group = [tables[0]]
            
            # Helper to check if title is "real" or missing/generic
            def get_real_title(t):
                # If title key is missing, or None, or starts with 'Table_' (our auto-gen), treat as None
                # Actually, step2 usually doesn't put 'title' key for generic ones.
                # But previous runs of step3 might have put 'Table_...'.
                # We should trust 'user-provided' titles (if any) or assume none.
                # Problem: How to distinguish 'Table_4.3...' from step3 vs real title?
                # Step 2 tables usually look like: {"id": "table_...", "bbox": ...} - No title.
                # So checking 'if "title" not in t' is safest for fresh run.
                # If re-running, step3 added titles.
                # We will check if it matches our auto-gen pattern.
                tit = t.get('title', '')
                if not tit: return None
                if tit.startswith('Table_' + safe_id): return None # Auto-generated
                return tit

            for i in range(1, len(tables)):
                curr_t = tables[i]
                prev_t = current_group[-1]
                
                curr_title = get_real_title(curr_t)
                prev_title = get_real_title(prev_t)
                
                # Merge condition:
                # 1. Current has NO title (Rule 1 & 3)
                # 2. OR Current title matches Previous title (Rule 2)
                should_merge = (curr_title is None) or (curr_title == prev_title)
                
                if should_merge:
                    current_group.append(curr_t)
                else:
                    grouped_tables.append(current_group)
                    current_group = [curr_t]
            
            grouped_tables.append(current_group)

        # --- Process Groups ---
        final_table_list = []
        
        for grp_idx, group in enumerate(grouped_tables):
            # Base name for this group
            # If multiple groups exist, we suffix _1, _2. If only 1 group, no suffix.
            group_suffix = ""
            if len(grouped_tables) > 1:
                group_suffix = f"_{grp_idx+1}"
            
            base_name = f"Table_{safe_id}_{safe_title}{group_suffix}"
            final_image_name = f"{base_name}.png"
            final_image_path = output_dir / final_image_name
            
            # 1. Generate individual images for stitching (or single image)
            temp_images = []
            for t_idx, table in enumerate(group):
                t_id = table.get('id', 'unknown')
                
                # We need a temp path
                temp_name = f"temp_{base_name}_part{t_idx}.png"
                temp_path = output_dir / temp_name
                
                margins = {
                    "margin_top": 2, "margin_bottom": 2, 
                    "margin_left": 2, "margin_right": 2
                }
                if t_id in BBOX_OVERRIDES:
                    margins.update(BBOX_OVERRIDES[t_id])
                
                self.generate_table_image(
                    page_num=table['page'],
                    bbox=table['bbox'],
                    output_path=temp_path,
                    dpi=TABLE_DPI,
                    **margins
                )
                temp_images.append(temp_path)
            
            # 2. Merge if needed (Group size > 1)
            if len(group) > 1:
                logger.info(f"  🔗 Merging {len(group)} tables for {base_name}")
                
                images = [Image.open(p) for p in temp_images]
                total_height = sum(img.height for img in images)
                max_width = max(img.width for img in images)
                
                merged_img = Image.new('RGB', (max_width, total_height), (255, 255, 255))
                y = 0
                for img in images:
                    merged_img.paste(img, (0, y))
                    y += img.height
                
                merged_img.save(final_image_path)
                
            else:
                # Single table -> Just rename/move the temp file
                if temp_images[0].exists():
                    temp_images[0].replace(final_image_path)
            
            # Cleanup temps
            for p in temp_images:
                if p.exists() and p != final_image_path: p.unlink()
                
            # 3. Update JSON Entry
            # We take the first table of the group as the representative
            primary_table = group[0]
            primary_table['image_path'] = final_image_name
            primary_table['title'] = base_name
            
            # Metadata update
            if len(group) > 1:
                primary_table['merged_count'] = len(group)
                # Clear description if merging happened to force re-parse
                primary_table.pop('table_md', None)
            else:
                # If it was previously merged but now isn't (re-run scenario?), clear count
                primary_table.pop('merged_count', None)
                # Also clear table_md if image changed? 
                # Yes, safe to clear to ensure consistency.
                primary_table.pop('table_md', None)
            
            final_table_list.append(primary_table)
            json_modified = True

        # Update section data with the new list of (merged) tables
        section_data['content']['tables'] = final_table_list
        section_data['statistics']['table_count'] = len(final_table_list)

        # --- Figure Logic (Unchanged) ---
        figures = section_data['content']['figures']
        for i, figure in enumerate(figures):
            new_name_base = f"Figure_{safe_id}_{safe_title}"
            if len(figures) > 1:
                new_name_base += f"_{i+1}"
            
            image_name = f"{new_name_base}.png"
            output_path = output_dir / image_name
            
            if not output_path.exists():
                self.generate_figure_image(
                    page_num=figure['page'],
                    bbox=figure['bbox'],
                    output_path=output_path,
                    margin_top=0, margin_bottom=0, margin_left=0, margin_right=0
                )
                logger.info(f"  ✓ 그림 이미지 생성: {image_name}")

            figure['image_path'] = image_name
            if 'title' not in figure or not figure['title']:
                figure['title'] = new_name_base
            json_modified = True
        
        # Save
        if json_modified:
            with open(section_file, 'w', encoding='utf-8') as f:
                json.dump(section_data, f, indent=2, ensure_ascii=False)
        
        return len(final_table_list), len(figures)
    
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
        
        logger.info(f"\n총 {len(json_files)}개 섹션 처리 시작...")
        logger.info(f"출력 디렉토리: {output_path}\n")
        
        total_tables = 0
        total_figures = 0
        
        for i, json_file in enumerate(json_files, 1):
            # 섹션 정보 읽기
            with open(json_file, 'r', encoding='utf-8') as f:
                section_data = json.load(f)
            
            # 진행 상황 표시 (NameError 수정됨)
            logger.info(f"[{i}/{len(json_files)}] {section_data.get('section_id', 'N/A')} - {section_data.get('title', 'Untitled')}")

            table_count = section_data['statistics']['table_count']
            figure_count = section_data['statistics']['figure_count']
            
            if table_count > 0 or figure_count > 0:
                logger.info(f"[{i}/{len(json_files)}] {section_data['section_id']} - {section_data['title']}")
                logger.info(f"  테이블: {table_count}개, 그림: {figure_count}개")
                
                t_count, f_count = self.process_section(json_file, output_path)
                total_tables += t_count
                total_figures += f_count
        
        logger.info(f"\n✅ 완료!")
        logger.info(f"총 테이블 이미지: {total_tables}개")
        logger.info(f"총 그림 이미지: {total_figures}개")
    
    def close(self):
        """문서 닫기"""
        if self.doc:
            self.doc.close()


def main():
    """테스트 실행"""
    from common_parameter import PDF_PATH, OUTPUT_DIR
    
    logger.info("=" * 80)
    logger.info("Table/Figure Image Generator - 테이블/그림 이미지 생성")
    logger.info("=" * 80)
    
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
