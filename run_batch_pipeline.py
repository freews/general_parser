import os
import subprocess
import sys

# ==============================================================================
# Common Parameters (Merged from common_parameter.py)
# ==============================================================================
# 환경 변수에서 설정을 읽어옵니다. (배치 실행 지원)
# 기본값은 테스트용 또는 마지막 설정값으로 유지합니다.
PDF_PATH = os.getenv("PDF_PATH", "source_doc/Datacenter NVMe SSD Specification v2.0r21.pdf")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "test_ocp")

TABLE_DPI = 120  # Table Image DPI 
# ==============================================================================


# 실행할 설정 목록
# 여기에 원하는 PDF와 출력 디렉토리 조합을 추가하거나 순서를 변경할 수 있습니다.
CONFIGS = [
    {
        "PDF_PATH": "source_doc/TCG-Storage-Opal-SSC-v2.30_pub.pdf",
        "OUTPUT_DIR": "output_tcg"
    },
   
    {
        "PDF_PATH": "source_doc/Datacenter NVMe SSD Specification v2.0r21.pdf",
        "OUTPUT_DIR": "output_ocp"
    },

    {
        "PDF_PATH": "./source_doc/NVM-Express-Base-Specification-Revision_2P3.pdf",
        "OUTPUT_DIR": "output_nvmebase"
    },
    
]

# 실행할 스텝 스크립트 목록
STEPS = [
  #  "step1_layout_analyzer.py",
    "step2_section_extractor.py",
    "step3_image_generator.py",
    "step4_llm_parser.py",
    "step5_markdown_converter.py",
    "step6_db_migration.py"
]

def run_pipeline():
    """정의된 설정에 따라 파이프라인을 순차적으로 실행합니다."""
    
    python_executable = sys.executable

    for config_idx, config in enumerate(CONFIGS, 1):
        pdf_path = config["PDF_PATH"]
        output_dir = config["OUTPUT_DIR"]
        
        print(f"\n{'='*60}")
        print(f"Condition {config_idx}/{len(CONFIGS)}")
        print(f"Target PDF : {pdf_path}")
        print(f"Output Dir : {output_dir}")
        print(f"{'='*60}")

        # 현재 프로세스의 환경 변수를 복사하고, 설정값을 덮어씁니다.
        env = os.environ.copy()
        env["PDF_PATH"] = pdf_path
        env["OUTPUT_DIR"] = output_dir

        for step in STEPS:
            print(f"\n >> Running {step} ...")
            try:
                # 각 스텝을 서브 프로세스로 실행
                # check=True는 프로세스가 0이 아닌 exit code를 반환하면 예외를 발생시킵니다.
                subprocess.run([python_executable, step], env=env, check=True)
                print(f" >> {step} Completed.")
            except subprocess.CalledProcessError as e:
                print(f"\n[ERROR] Failed to run {step} for config: {config}")
                print(f"Error details: {e}")
                
                # 에러 발생 시 사용자에게 계속 진행할지 물어보거나 종료할 수 있습니다.
                # 여기서는 해당 설정에 대한 파이프라인을 중단하고 다음 설정으로 넘어갈지 묻지 않고
                # 전체 프로세스의 안전을 위해 스크립트 실행을 완전히 종료할 수도, 
                # 또는 해당 문서는 실패 처리하고 다음 문서로 넘어갈 수도 있습니다.
                # 요청사항이 "자동실행"이므로 다음 설정으로 넘어가는 것이 낫습니다.
                print(f"[WARN] Skipping remaining steps for this config and moving to next condition.")
                break # 다음 step 실행 중단, 다음 config로 이동

    print("\nAll batch jobs finished.")

if __name__ == "__main__":
    run_pipeline()
