import time
import requests
import random
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from NF_global_objects import (
    get_logger,
    get_session,
    return_proxy_index,
    insert_failed_proxy_index,
)
from config.request_ssl import SSLAdapter
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
logger = get_logger()
session = get_session()

# 원래 요청을 보내는 함수 (프록시 없이)
def origin_send_request(payload, headers, proxy_index):
    url = "https://airline-api.naver.com/graphql"
    try:
        response = requests.post(url, json=payload, headers=headers)
        # logger.info(f"네트워크 통신 소요시간 : {round(end-start, 2)}")
        random_sec=random.randint(1,10)
        start = time.time()
        # time.sleep(random_sec)
        end = time.time()
        response.raise_for_status()
        # release_proxy_index(proxy_index)
        return response.json()
    except Exception as e:
        error_message = f"API 요청 오류: {str(e)}"
        if "[Errno 61] Connection refused" in str(e):
            logger.error("로컬 IP가 차단되었습니다!")
            insert_failed_proxy_index(proxy_index)
            # 로컬 IP는 'my_ip'로 가정하고 실패한 프록시로 추가
        else:
            logger.error(error_message)
        return False

# 각 프록시로 요청을 보내는 함수
def send_request_with_proxy(payload, headers, proxy, proxy_index):
    start = time.time()
    url = "https://airline-api.naver.com/graphql"
    try:
        session = requests.Session()
        session.mount('https://', SSLAdapter())
        retry = Retry(total=0)  # 재시도를 비활성화
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('https://', adapter)
        response = session.post(url, proxies=proxy, json=payload, headers=headers, verify=False, timeout=30)
        end = time.time()
        # logger.info(f"네트워크 통신 소요시간 : {round(end-start, 2)}")
        random_sec=random.randint(1,10)
        # time.sleep(random_sec)
        response.raise_for_status()  # 상태 코드가 200이 아닐 경우 예외 발생
        # release_proxy_index(proxy_index)
        return response.json()  # 성공적으로 응답 받았을 경우 결과 반환
    except requests.exceptions.RequestException as e:
        error_message = f"API 요청 오류: {str(e)}"
        # if "[Errno 61] Connection refused" in str(e) or 'TLS/SSL' in str(e) or '[Errno 54] Connection reset by peer' in str(e):
        #     # logger.error(f"{error_message}")
        #     # insert_failed_proxy_index(proxy_index)
        #     # 실패한 프록시를 추가하고 반환하지 않음
        # else:
        #     # logger.error(error_message)
        return None  # 실패 시 None 반환