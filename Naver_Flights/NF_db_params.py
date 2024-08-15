import psycopg2

# DB 연결 함수
def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="naver_db",
        user="postgres",
        password="5994"
    )

# DB 쿼리 실행 함수
def execute_db_query(conn,cur, query, params=None):
    try:
        cur.execute(query, params) # 쿼리 실행
        return True
    except Exception as e:
        print(f"INSERT 오류: {e}")
        if conn:
            conn.rollback() # 오류난 경우 쿼리 이전으로 롤백
        return False
    

query_dict={
    "flights_table":
            """
            INSERT INTO flights (air_id, is_layover, fetched_date)
            VALUES (%s, %s, %s)
            ON CONFLICT (air_id, fetched_date) DO UPDATE
            SET is_layover = EXCLUDED.is_layover
            """,

    "flight_info_table":
            """
            INSERT INTO flight_info
            (air_id, air_id_segment, fetched_date, airline, depart_region, depart_airport, arrival_region, 
            arrival_airport, journey_time, connect_time, depart_timestamp, arrival_timestamp )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (air_id, air_id_segment, fetched_date) DO UPDATE
            SET airline = EXCLUDED.airline,
                depart_region = EXCLUDED.depart_region,
                depart_airport = EXCLUDED.depart_airport,
                arrival_region = EXCLUDED.arrival_region,
                arrival_airport = EXCLUDED.arrival_airport,
                journey_time = EXCLUDED.journey_time,
                connect_time = EXCLUDED.connect_time,
                depart_timestamp = EXCLUDED.depart_timestamp,
                arrival_timestamp = EXCLUDED.arrival_timestamp
            """,
    
    "fare_info_table":
            """
            INSERT INTO fare_info 
            (air_id, option_type, fetched_date, total_fare, base_fare, naver_fare, tax, qcharge, purchase_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (air_id, option_type, fetched_date) DO UPDATE
            SET total_fare = EXCLUDED.total_fare,
            base_fare = EXCLUDED.base_fare,
            naver_fare = EXCLUDED.naver_fare,
            tax = EXCLUDED.tax,
            qcharge = EXCLUDED.qcharge,
            purchase_url = EXCLUDED.purchase_url
            """
}