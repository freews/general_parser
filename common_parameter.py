import os

# 환경 변수에서 설정을 읽어옵니다. (배치 실행 지원)
# 기본값은 테스트용 또는 마지막 설정값으로 유지합니다.
PDF_PATH = os.getenv("PDF_PATH", "source_doc/Datacenter NVMe SSD Specification v2.0r21.pdf")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output_ocp")

TABLE_DPI = 120  # Table Image DPI
