import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime

class ColoredFormatter(logging.Formatter):
    """컬러 출력 포매터"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # 청록색
        'INFO': '\033[32m',     # 녹색
        'WARNING': '\033[33m',  # 노란색
        'ERROR': '\033[31m',    # 빨간색
        'CRITICAL': '\033[35m', # 보라색
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)

def setup_advanced_logger(
    name="app",
    log_level=20, # info
    log_dir="logs",
    max_bytes=10*1024*1024,  # 10MB
    backup_count=5,
    console_color=True
):
    """고급 로거 설정 (로그 회전, 색상 출력)"""
    
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.handlers.clear()
    
    # 로그 디렉토리 생성
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # 파일 포매터 (색상 없음)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 콘솔 포매터 (색상 있음)
    if console_color:
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
    else:
        console_formatter = file_formatter
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 회전 파일 핸들러 (일반 로그)
    log_file = log_path / f"{name}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # 에러 전용 파일 핸들러
    error_log_file = log_path / f"{name}_error.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    logger.addHandler(error_handler)
    
    return logger

# 사용 예제
logger = setup_advanced_logger(
    name="ocr_processor",
    log_dir="logs",
    log_level=logging.INFO,
    console_color=True
)
