import psycopg2
from NF_functions import logger
# DB 연결 함수
def get_db_connection():
    return psycopg2.connect(
        host="", # 인스턴스 엔드포인트
        database="", # 데이터베이스 이름
        user="postgres", # 사용자 이름
        password="" # 사용자 비밀번호
    )

# DB 쿼리 실행 함수
def execute_db_query(conn,cur, query, params=None):
    try:
        cur.execute(query, params) # 쿼리 실행
        return True
    except Exception as e:
        logger.info(f"INSERT 오류: {e}")
        # print(f"INSERT 오류: {e}")
        if conn:
            conn.rollback() # 오류난 경우 쿼리 이전으로 롤백
        return False
    

def batch_insert():
    return 0

query_dict = {
    "flight_info": """
        INSERT INTO flight_info
        (air_id, airline, depart_airport, depart_timestamp,
        arrival_airport, arrival_timestamp, journey_time, fetched_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (air_id, fetched_date) DO UPDATE
        SET airline = EXCLUDED.airline,
            depart_airport = EXCLUDED.depart_airport,
            depart_timestamp = EXCLUDED.depart_timestamp,
            arrival_airport = EXCLUDED.arrival_airport,
            arrival_timestamp = EXCLUDED.arrival_timestamp,
            journey_time = EXCLUDED.journey_time
    """,
    
    "fare_info": """
        INSERT INTO fare_info 
        (air_id, option_type, agt_code, adult_fare, purchase_url, fetched_date)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (air_id, option_type, agt_code, fetched_date) DO UPDATE
        SET adult_fare = EXCLUDED.adult_fare,
            purchase_url = EXCLUDED.purchase_url
    """,
    
    "layover_info": """
        INSERT INTO layover_info (air_id, segment_id, layover_order, connect_time, fetched_date)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (air_id, segment_id, fetched_date) DO UPDATE
        SET layover_order = EXCLUDED.layover_order,
            connect_time = EXCLUDED.connect_time
    """,
    
    "airport_info":"""
        INSERT INTO airport_info
        (airport_code, name, country, time_zone) 
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (airport_code) DO UPDATE
        SET airport_code = EXCLUDED.airport_code,
            name = EXCLUDED.name,
            country = EXCLUDED.country,
            time_zone = EXCLUDED.time_zone
    """
}