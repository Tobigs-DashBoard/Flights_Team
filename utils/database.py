import psycopg2
from psycopg2.extras import execute_values

# 데이터베이스 클래스 (DB 연결, insert, 연결 종료 메소드)
class DataBase:
    def __init__(self, host, database_name, user, password, logger):
        self.host = host
        self.database = database_name
        self.user = user
        self.password = password
        self.conn = None
        self.cur = None
        self.logger = logger

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )
            self.cur = self.conn.cursor()
            self.logger.info("데이터베이스에 연결되었습니다.")
        except Exception as e:
            self.logger.error(f"데이터베이스 연결 오류: {e}")

    def execute_values_query(self, query, params_list):
        if not self.conn or not self.cur:
            self.logger.error("데이터베이스에 연결되어 있지 않습니다.")
            return False

        try:
            execute_values(self.cur, query, params_list)
            self.conn.commit()
            self.logger.info(f"{len(params_list)}개의 레코드가 성공적으로 삽입되었습니다.")
            return True
        except Exception as e:
            self.logger.error(f"배치 쿼리 실행 오류: {e}")
            self.logger.error(f"실패한 쿼리: {query}")
            self.logger.error(f"실패한 파라미터의 첫 번째 항목: {params_list[0]}")
            self.conn.rollback()
            return False
        
    def close(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
        self.logger.info("데이터베이스 연결이 종료되었습니다.")