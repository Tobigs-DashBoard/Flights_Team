import os
import time
os.environ['TZ'] = 'Asia/Seoul'
time.tzset()
import requests
from datetime import date
from utils.database import DataBase
from utils.batch_queue import Batch_Queue
from utils.file_io import read_json_file
from config.logger import setup_logger
from config.request_ssl import SSLAdapter
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from queue import Queue  # 스레드 안전한 큐 사용
import threading
thread_lock = threading.Lock()
import json

proxy_file_path=os.environ.get('PROXY_PATH', 'total_proxy_map.json')
with open(proxy_file_path, 'r', encoding='utf-8-sig') as f:
    total_proxy_map=json.load(f)

class GlobalObjects:
    new_instance = None

    def __new__(cls):
        if cls.new_instance is None:
            cls.new_instance = super().__new__(cls)
            cls.new_instance._initialize()
        return cls.new_instance

    def _initialize(self):
        # 로거 설정
        self.logger = setup_logger()
        self.logger.info(proxy_file_path)
        self.total_proxy_map=total_proxy_map
        self.proxy_index_queue=Queue()
        for proxy_index in self.total_proxy_map.keys():
            self.proxy_index_queue.put(proxy_index)
        # 데이터베이스 연결
        DB_HOST = os.getenv("DB_HOST", "localhost")
        DB_NAME = os.getenv("DB_NAME", "naver_db")
        DB_USER = os.getenv("DB_USER", "postgres")
        DB_PASSWORD = os.getenv("DB_PASSWORD", "5994")
        self.db = DataBase(DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, self.logger)
        self.db.connect()

        # 공항 정보 맵
        self.airport_map = read_json_file('maps/airport_map.json')
        self.request_airport_map = read_json_file('maps/request_airport_map.json')
        self.query_map = read_json_file('utils/query_map.json')

        # 배치 큐 초기화
        self.batch_queue = Batch_Queue(self.db, self.query_map, self.logger, 20000)

        # 세션 설정
        self.session = requests.Session()
        self.session.mount('https://', SSLAdapter())
        retry = Retry(total=0)  # 재시도를 비활성화
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('https://', adapter)

        # 날짜 및 진행률 초기화
        self.today = date.today()
        self.logger.info(f'수집 날짜:{self.today}')
        self.progress = 0
        self.total_combi_length = 0

        # 작업 큐 초기화
        self.request_queue = Queue()
        self.response_queue = Queue()

        # 프록시 딕셔너리 반환용
        self.failed_proxie_index = set()
        
# 전역 객체 인스턴스
global_objects = GlobalObjects()

# 데이터베이스 연결 객체
def get_db():
    return global_objects.db

# 크롤링 날짜
def get_today():
    return global_objects.today

# 데이터베이스 배치 insert 큐 객체
def get_batch_queue():
    return global_objects.batch_queue

# 로깅 객체
def get_logger():
    return global_objects.logger

# 공항 코드 맵 객체
def get_airport_map():
    return global_objects.airport_map

# 네이버 항공권 사이트 기준 공항 코드 맵
def get_request_airport_map():
    return global_objects.request_airport_map

# 데이터 베이스 insert 쿼리 맵
def get_query_map():
    return global_objects.query_map

# 프록시 서버 적용 세션
def get_session():
    return global_objects.session

# 전역 변수 객체 그자체
def get_global_object():
    return global_objects

def get_proxy():
    try:
        proxy_index = global_objects.proxy_index_queue.get()
    except Exception as e:
        global_objects.logger.info(f'{e}')
    if proxy_index not in global_objects.failed_proxie_index:
        return proxy_index, global_objects.total_proxy_map[proxy_index]
    else:
        global_objects.logger.error(f'이미 밴당한 ip입니다.{global_objects.total_proxy_map[proxy_index]}')
        get_proxy()

# # 프록시 가져가기
# def get_proxy():
#     proxy = r.blpop('proxy_queue', timeout=0)
#     proxy = proxy[1]
#     proxy_value = proxy.decode('utf-8')

#     if proxy_value == 'my_ip' and 'my_ip' not in global_objects.failed_proxies:
#         global_objects.logger.info('이미 my_ip가 밴당함!!!!!')
#         return 'my_ip'
#     elif eval(proxy_value) not in global_objects.failed_proxies:
#         global_objects.logger.info('이미 해당 아이피는 밴당함!!!!!')
#         return eval(proxy_value)


def return_proxy_index(proxy_index):
    if proxy_index not in global_objects.failed_proxie_index:
        global_objects.proxy_index_queue.put(proxy_index)
# 사용 마친 프록시 다시 추가하기
# def return_proxy_index(proxy):
#     if proxy not in global_objects.failed_proxies:
#         r.rpush('proxy_queue', str(proxy))

def get_proxy_queue_size():
    return global_objects.proxy_index_queue.qsize()

def get_proxy_index_queue():
    return global_objects.proxy_index_queue
# def get_proxy_queue_size():
#     return r.llen('proxy_queue')

def insert_failed_proxy_index(proxy_index):
    with thread_lock:
        if proxy_index not in global_objects.failed_proxie_index:
            global_objects.failed_proxie_index.add(proxy_index)

def get_failed_proxy_index():
    return global_objects.failed_proxie_index
# def get_failed_proxies():
#     return global_objects.failed_proxies

# def add_failed_proxy(proxy):
#     # 프록시 식별자 생성
#     proxy_id = proxy.get('http') if isinstance(proxy, dict) else proxy
#     global_objects.failed_proxies.add(proxy_id)
#     # global_objects.logger.info(f"실패한 프록시 추가됨: {proxy_id}")

# def return_proxy_index(proxy):
#     # 프록시 식별자 생성
#     proxy_id = proxy.get('http') if isinstance(proxy, dict) else proxy
#     if proxy_id not in global_objects.failed_proxies:
#         global_objects.proxy_pool.put(proxy)
#         # global_objects.logger.info(f"프록시 반환됨: {proxy_id}")

def get_total_combi_length():
    return global_objects.total_combi_length

def get_progress():
    return global_objects.progress

def update_progress():
    global_objects.progress += 1

def init_total_combi_length(combi_length):
    global_objects.total_combi_length = combi_length
def init_progress():
    global_objects.progress = 0
# def get_request_queue():
#     return global_objects.request_queue

# # 작업 큐에 항공권 일정 삽입
# def insert_request_queue(task):
#     return global_objects.request_queue.put(task)

# def stop_one_thread():
#     global_objects.request_queue.put(None)

# def get_response_queue():
#     return global_objects.response_queue

# # 작업 큐에 응답 데이터 삽입
# def insert_response_queue(task):
#     return global_objects.response_queue.put(task)

# def stop_one_thread():
#     global_objects.response_queue.put(None)


