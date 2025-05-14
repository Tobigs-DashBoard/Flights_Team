import psycopg2
from psycopg2.extras import execute_values
import traceback
import time

# 데이터베이스 클래스 (DB 연결, insert, 연결 종료 메소드)
class DataBase:
    def __init__(self, host, database_name, user, password, max_retries=100, retry_delay=5):
        self.host = host
        self.database = database_name
        self.user = user
        self.password = password
        self.conn = None
        self.cur = None
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def connect(self):
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                self.conn = psycopg2.connect(
                    host=self.host,
                    database=self.database,
                    user=self.user,
                    password=self.password
                )
                self.cur = self.conn.cursor()
                return True
            except Exception as e:
                retry_count += 1
                if retry_count >= self.max_retries:
                    print(f"데이터베이스 연결 최대 재시도 횟수 초과: {e}")
                    return False
                print(f"데이터베이스 연결 오류, 재시도 중 ({retry_count}/{self.max_retries}): {e}")
                time.sleep(self.retry_delay)

    def execute_values_query(self, queue_name, query, params_list):
        if not self.conn or not self.cur:
            if not self.connect():
                return False, "데이터베이스에 연결할 수 없습니다."
        # 큐 이름에 따라 page_size 동적 설정 (16GB RAM 환경 최적화)
        if queue_name == "Flight_Info_Queue":
            page_size = 3000
        elif queue_name == "Fare_Info_Queue":
            page_size = 5000
        elif queue_name == "Layover_Info_Queue":
            page_size = 3000
        else:
            page_size = 4000  # 기본값
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                execute_values(self.cur, query, params_list, page_size=page_size)
                self.conn.commit()
                return True, None
            
            except (psycopg2.errors.DeadlockDetected, psycopg2.errors.SerializationFailure) as e:
                # 데드락 또는 직렬화 오류 처리 - 재시도하는 것이 좋음
                retry_count += 1
                error_traceback = traceback.format_exc()
                self.conn.rollback()
                
                if retry_count >= self.max_retries:
                    print(f"{queue_name} 쿼리 실행 중 데드락 발생, 최대 재시도 횟수 초과")
                    return False, error_traceback
                    
                print(f"{queue_name} 쿼리 실행 중 데드락 발생, 재시도 중 ({retry_count}/{self.max_retries})")
                time.sleep(self.retry_delay * retry_count)  # 지수 백오프
            
            except psycopg2.errors.CardinalityViolation as e:
                # 카디널리티 위반은 재시도해도 같은 오류가 발생할 가능성이 높으므로 바로 처리
                error_traceback = traceback.format_exc()
                self.conn.rollback()
                print(f"{queue_name} 쿼리 실행 중 카디널리티 위반 발생")
                # 중복 데이터에 대한 특별 처리가 필요하면 여기에 추가
                return False, error_traceback
            
            except psycopg2.OperationalError as e:
                # 연결 관련 오류
                retry_count += 1
                error_traceback = traceback.format_exc()
                
                # 연결이 끊어졌을 수 있으므로 재연결 시도
                try:
                    self.close()
                    if not self.connect():
                        return False, "데이터베이스에 재연결할 수 없습니다."
                except Exception:
                    pass
                
                if retry_count >= self.max_retries:
                    return False, error_traceback
                    
                print(f"{queue_name} 쿼리 실행 중 연결 오류, 재시도 중 ({retry_count}/{self.max_retries})")
                time.sleep(self.retry_delay * retry_count)
            
            except Exception as e:
                # 기타 예외 처리
                error_traceback = traceback.format_exc()
                try:
                    self.conn.rollback()
                except Exception:
                    # 이미 연결이 끊어진 경우 처리
                    try:
                        self.close()
                        self.connect()
                    except Exception:
                        pass
                
                return False, error_traceback
        
    def close(self):
        try:
            if self.cur:
                self.cur.close()
        except Exception:
            pass
            
        try:
            if self.conn:
                self.conn.close()
        except Exception:
            pass
            
        self.cur = None
        self.conn = None