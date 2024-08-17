# import json
import time
from NF_api_params import international_payload_form, return_header
from NF_functions import *
from local_test.NF_db_params import get_db_connection, execute_db_query, query_dict
from multiprocessing import Process, Queue
# from psycopg2 import sql

def save_flight_info(schedules, airline_map, today, queue):
    '''비행 정보 저장'''
    conn=get_db_connection() # db 연결
    cur = conn.cursor() # DB 커서 객체 (insert, delete, select 등 명령어 수행)

    fetched_date=today.strftime('%Y%m%d')
    for schedule in schedules[0].values():
        details = schedule['detail']
        air_id = schedule['id']
        air_id_list = air_id.split('+')
        
        is_layover = "+" in schedule['id'] and len(details) > 1  # 경유 여부 확인

        # flights 테이블에 삽입할 값 출력
        # print(f"Flights 테이블 삽입 값: air_id={air_id}, is_layover={is_layover}, fetched_date={fetched_date}")

        # flights 테이블에 삽입
        query = query_dict['flights_table']
        execute_db_query(conn, cur, query, (air_id, is_layover, fetched_date))

        for index, detail in enumerate(details):
            depart_airport = airport_region_map[detail['sa']]['name']  # 출발 공항
            depart_region = airport_region_map[detail['sa']]['country']
            arrival_airport = airport_region_map[detail['ea']]['name'] # 도착 공항
            arrival_region = airport_region_map[detail['ea']]['country']
            
            # depart_airport = urllib.parse.unquote(airport_map.get(depart_airport, "Unknown"))  # url 변환 값 역변환
            # arrival_airport = urllib.parse.unquote(airport_map.get(arrival_airport, "Unknown"))  # url 변환 값 역변환
            
            # 출발 시각 타임 스탬프 변환
            depart_timestamp = return_time_stamp(detail['sdt'])
            # 도착 시각 타임 스탬프 변환
            arrival_timestamp = return_time_stamp(detail['edt'])
            
            # flight_info 테이블에 삽입
            query = query_dict['flight_info_table']
            execute_db_query(conn, cur, query, (
                air_id, air_id_list[index], airline_map.get(detail['av']), depart_region, depart_airport,
                arrival_region, arrival_airport, 
                int(detail['jt'][:2])*60 + int(detail['jt'][2:]),
                int(detail['ct'][:2])*60 + int(detail['ct'][2:]),
                timestamp_to_iso8601(depart_timestamp),
                timestamp_to_iso8601(arrival_timestamp), fetched_date
            ))

    print(f"항공편 정보가 데이터베이스에 저장되었습니다.")
    conn.commit()
    conn.close() # db 연결 종료
    queue.put("Flight info saved to database")

def save_fare_info(fares, fare_types, today, queue):
    conn=get_db_connection() # db 연결
    cur = conn.cursor() # DB 커서 객체 (insert, delete, select 등 명령어 수행)
    '''운임 정보 저장'''
    fetched_date=today.strftime('%Y%m%d')
    for key, values in fares.items():
        for option, fare_list in values['fare'].items():
            option=decode_url_text(fare_types[option])
            for fare in fare_list:
                try:
                    agt=fare['AgtCode']
                    adult = fare['Adult']
                    child= fare['Child']
                    infant=fare['Infant']
                    
                    adult_base_fare = int(adult['Fare'])
                    adult_naver_fare = int(adult['NaverFare'])
                    adult_tax = int(adult['Tax'])
                    adult_Qcharge = int(adult['QCharge'])
                    adult_fare = adult_base_fare + adult_naver_fare + adult_tax + adult_Qcharge

                    child_base_fare = int(child['Fare'])
                    child_naver_fare = int(child['NaverFare'])
                    child_tax = int(child['Tax'])
                    child_Qcharge = int(child['QCharge'])
                    child_fare = child_base_fare + child_naver_fare + child_tax + child_Qcharge

                    infant_base_fare = int(infant['Fare'])
                    infant_naver_fare = int(infant['NaverFare'])
                    infant_tax = int(infant['Tax'])
                    infant_Qcharge = int(infant['QCharge'])
                    infant_fare = infant_base_fare + infant_naver_fare + infant_tax + infant_Qcharge
                    
                    purchase_url = fare['ReserveParameter']['#cdata-section']
                    
                    # fare_info 테이블에 삽입
                    query = query_dict['fare_info_table']
                    execute_db_query(conn, cur, query, (
                            key, option, agt, adult_fare, child_fare, infant_fare, purchase_url, fetched_date))
                except Exception as e:
                    print(f"운임 정보 처리 중 오류: {e}")
                    continue
    conn.commit()
    conn.close()
    print(f"운임 정보가 데이터베이스에 저장되었습니다.")
    queue.put("Fare info saved to database")

def fetch_international_flights(departure, arrival, date, today, cnt):
    headers = return_header(departure, arrival, date)
    
    # 첫 번째 요청
    payload1 = international_payload_form(first=True, departure=departure, arrival=arrival, date=date)
    response_data1 = send_request(payload1, headers)
    if not response_data1:
        return []
    
    international_list = response_data1.get("data", {}).get("internationalList", {})
    galileo_key = international_list.get("galileoKey")
    travel_biz_key = international_list.get("travelBizKey")
    
    time.sleep(5)

    # 두 번째 요청
    payload2 = international_payload_form(first=False, departure=departure, arrival=arrival, date=date, galileo_key=galileo_key, travel_biz_key=travel_biz_key)
    response_data2 = send_request(payload2, headers)
    if not response_data2:
        return cnt

    international_list = response_data2.get("data", {}).get("internationalList", {})
    results = international_list.get("results", {})
        
    airline_map = results.get('airlines', {})
    # airport_map = results.get('airports', {})
    schedules = results.get("schedules", [])
    fares = results.get("fares", [])
    fare_types = results.get("fareTypes", [])
    
    if len(schedules) == 0:
        print(f"{departure}에서 {arrival}로 가는 항공권이 없습니다. {date}")
        cnt+=1
        return cnt
    # 항공편이 있으면 체크개수 초기화
    cnt=0
    
    '''항공권 정보, 운임 정보 파싱을 멀티 프로세싱으로 분산 처리'''
    queue = Queue()
    p1 = Process(target=save_flight_info, args=(schedules, airline_map, today, queue))
    p2 = Process(target=save_fare_info, args=(fares, fare_types, today, queue))

    p1.start()
    p2.start()
    
    p1.join()
    p2.join()

    return cnt