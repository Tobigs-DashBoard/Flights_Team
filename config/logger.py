import os
import logging
def setup_logger():
    log_path = os.environ.get('LOG_PATH', 'logs/crawling_log.log')
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    # 루트 로거 반환
    return logging.getLogger()