import json
import time
import urllib.parse
import os
from datetime import datetime, timezone, date, timedelta
from NF_api_params import *
from multiprocessing import Process, Queue
import psycopg2
from psycopg2 import sql

# 파일 읽기 함수
def read_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# 항공 코드와 국가를 1대 1 매칭한 딕셔너리
airport_region_map = read_json_file('Naver_Flights/airport_region_map.json')

# 검색용 공항 코드
request_airport_map = read_json_file('Naver_Flights/request_airport_map.json')

# DB 연결 함수
def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="naver_db",
        user="postgres",
        password="5994"
    )

# 데이터베이스 쿼리 실행 함수
def execute_db_query(query, params=None):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        return True
    except Exception as e:
        print(f"INSERT 오류: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def save_flight_info(schedules, airline_map, airport_map, departure, arrival, date, today, queue):
    '''비행 정보 저장'''
    fetched_date=today.strftime('%Y%m%d')
    for schedule in schedules[0].values():
        details = schedule['detail']
        air_id = schedule['id']
        air_id_list = air_id.split('+')
        
        is_layover = "+" in schedule['id'] and len(details) > 1  # 경유 여부 확인

        # flights 테이블에 삽입할 값 출력
        # print(f"Flights 테이블 삽입 값: air_id={air_id}, is_layover={is_layover}, fetched_date={fetched_date}")

        # flights 테이블에 삽입
        query = """
        INSERT INTO flights (air_id, is_layover, fetched_date)
        VALUES (%s, %s, %s)
        ON CONFLICT (air_id, fetched_date) DO UPDATE
        SET is_layover = EXCLUDED.is_layover
        """
        execute_db_query(query, (air_id, is_layover, fetched_date))

        for index, detail in enumerate(details):
            depart_airport = detail['sa']  # 출발 공항
            depart_region = airport_region_map[detail['sa']]
            arrival_airport = detail['ea']  # 도착 공항
            arrival_region = airport_region_map[detail['ea']]
            
            depart_airport = urllib.parse.unquote(airport_map.get(depart_airport, "Unknown"))  # url 변환 값 역변환
            arrival_airport = urllib.parse.unquote(airport_map.get(arrival_airport, "Unknown"))  # url 변환 값 역변환
            
            # 출발 시각 타임 스탬프 변환
            depart_date, depart_hour, depart_minute, depart_timestamp = return_time_stamp(detail['sdt'])
            # 도착 시각 타임 스탬프 변환
            arrival_date, arrival_hour, arrival_minute, arrival_timestamp = return_time_stamp(detail['edt'])
            
            # flight_info 테이블에 삽입
            query = """
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
            """
            execute_db_query(query, (
                air_id, air_id_list[index], fetched_date, airline_map.get(detail['av']), depart_region, depart_airport,
                arrival_region, arrival_airport, 
                int(detail['jt'][:2])*60 + int(detail['jt'][2:]),
                int(detail['ct'][:2])*60 + int(detail['ct'][2:]),
                timestamp_to_iso8601(depart_timestamp),
                timestamp_to_iso8601(arrival_timestamp),
            ))

    print(f"항공편 정보가 데이터베이스에 저장되었습니다.")
    queue.put("Flight info saved to database")

def save_fare_info(fares, fare_types, departure, arrival, date, today, queue):
    '''운임 정보 저장'''
    fetched_date=today.strftime('%Y%m%d')
    for key, values in fares.items():
        for option, fare_list in values['fare'].items():
            option=decode_url_text(fare_types[option])
            for i in fare_list:
                try:
                    adult = i['Adult']
                    base_fare = int(adult['Fare'])
                    naver_fare = int(adult['NaverFare'])
                    tax = int(adult['Tax'])
                    Qcharge = int(adult['QCharge'])
                    
                    adult_fare = base_fare + naver_fare + tax + Qcharge
                    
                    purchase_url = i['ReserveParameter']['#cdata-section']
                    
                    # fare_info 테이블에 삽입
                    query = """
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
                    execute_db_query(query, (
                        key, option,fetched_date, adult_fare, base_fare, naver_fare, tax, Qcharge, 
                        purchase_url
                    ))
                except Exception as e:
                    print(f"운임 정보 처리 중 오류: {e}")
                    continue

    print(f"운임 정보가 데이터베이스에 저장되었습니다.")
    queue.put("Fare info saved to database")

def fetch_naver_flights_date(departure, arrival, date, today):
    headers = return_header(departure, arrival, date)
    
    # 첫 번째 요청
    payload1 = payload_form(first=True, departure=departure, arrival=arrival, date=date)
    response_data1 = send_request(payload1, headers)
    if not response_data1:
        return []
    
    international_list = response_data1.get("data", {}).get("internationalList", {})
    galileo_key = international_list.get("galileoKey")
    travel_biz_key = international_list.get("travelBizKey")

    print("galileo key: ", galileo_key)
    print("travel key: ", travel_biz_key)
    
    time.sleep(5)

    # 두 번째 요청
    payload2 = payload_form(first=False, departure=departure, arrival=arrival, date=date, galileo_key=galileo_key, travel_biz_key=travel_biz_key)
    response_data2 = send_request(payload2, headers)
    if not response_data2:
        return []

    international_list = response_data2.get("data", {}).get("internationalList", {})
    results = international_list.get("results", {})
    
    airline_map = results.get('airlines', {})
    airport_map = results.get('airports', {})
    schedules = results.get("schedules", [])
    fares = results.get("fares", [])
    fare_types = results.get("fareTypes", [])
    
    if len(schedules) == 0:
        print(f"{departure}에서 {arrival}로 가는 항공권이 없습니다. {date}")
        return 0
    
    queue = Queue()
    p1 = Process(target=save_flight_info, args=(schedules, airline_map, airport_map, departure, arrival, date,today, queue))
    p2 = Process(target=save_fare_info, args=(fares, fare_types, departure, arrival, date,today, queue))

    p1.start()
    p2.start()
    
    p1.join()
    p2.join()

    return 0

if __name__ == "__main__":
    departure = "SEL"
    arrival_list = ["대한민국", "일본", "동남아"] #, "중국", "유럽", "미주", "대양주", "남미", "아시아", "중동", "아프리카"]
    today = date.today()
    for arrival_target in arrival_list:
        for airport in request_airport_map[arrival_target]:
            arrival = airport['IATA']
            if arrival == "SEL":
                continue 
            for i in range(1, 4):
                target_date = today + timedelta(days=i)
                formatted_date = target_date.strftime('%Y%m%d')
                fetch_naver_flights_date(departure, arrival, formatted_date, today)