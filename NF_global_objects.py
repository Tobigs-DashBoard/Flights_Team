import os
import time
os.environ['TZ'] = 'Asia/Seoul'
time.tzset()
from datetime import date
from utils.database import DataBase
from utils.batch_queue import Batch_Queue
from utils.file_io import read_json_file
from config.logger import setup_logger

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
        self.query_map=read_json_file('utils/query_map.json')
        # 배치 큐 초기화
        self.batch_queue = Batch_Queue(self.db,self.query_map, self.logger, 20000)

        self.today=date.today()
# 전역 객체 인스턴스
global_objects = GlobalObjects()

def get_db():
    return global_objects.db

def get_today():
    return global_objects.today

def get_batch_queue():
    return global_objects.batch_queue

def get_logger():
    return global_objects.logger

def get_airport_map():
    return global_objects.airport_map

def get_request_airport_map():
    return global_objects.request_airport_map

def get_query_map():
    return global_objects.query_map