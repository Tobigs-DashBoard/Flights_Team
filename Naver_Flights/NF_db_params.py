import psycopg2
from NF_functions import logger
# DB 연결 함수
def get_db_connection():
    return psycopg2.connect(
        host="naver-flights.cdyk2yq24sjs.ap-northeast-2.rds.amazonaws.com", # 인스턴스 엔드포인트
        database="naver_db", # 데이터베이스 이름
        user="gunu", # 사용자 이름
        password="rjsdn5994!" # 사용자 비밀번호
    )

# DB 쿼리 실행 함수
def execute_db_query(conn,cur, query, params=None):
    try:
        cur.execute(query, params) # 쿼리 실행
        return True
    except Exception as e:
        logger.info(f"INSERT 오류: {e}")
        if conn:
            conn.rollback() # 오류난 경우 쿼리 이전으로 롤백
        return False
    

query_dict={
    "flights_table":
            """
            INSERT INTO flights (air_id, is_domestic, is_layover, layover_list, fetched_date)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (air_id, fetched_date) DO UPDATE
            SET is_layover = EXCLUDED.is_layover
            """,

    "flight_info_table":
            """
            INSERT INTO flight_info
            (air_id, airline, depart_country, depart_airport, depart_timestamp, arrival_country, 
            arrival_airport, arrival_timestamp, journey_time, connect_time, fetched_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (air_id, fetched_date) DO UPDATE
            SET airline = EXCLUDED.airline,
                depart_country = EXCLUDED.depart_country,
                depart_airport = EXCLUDED.depart_airport,
                arrival_country = EXCLUDED.arrival_country,
                arrival_airport = EXCLUDED.arrival_airport,
                journey_time = EXCLUDED.journey_time,
                connect_time = EXCLUDED.connect_time,
                depart_timestamp = EXCLUDED.depart_timestamp,
                arrival_timestamp = EXCLUDED.arrival_timestamp
            """,
    
    "fare_info_table":
            """
            INSERT INTO fare_info 
            (air_id, option_type, agt_code, adult_fare, child_fare, infant_fare, purchase_url, fetched_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (air_id, option_type, fetched_date) DO UPDATE
            SET agt_code = EXCLUDED.agt_code,
            adult_fare = EXCLUDED.adult_fare,
            child_fare = EXCLUDED.child_fare,
            infant_fare = EXCLUDED.infant_fare,
            purchase_url = EXCLUDED.purchase_url
            """
}