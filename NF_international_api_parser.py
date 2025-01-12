# import json
import time
from config.api_params import  return_header, international_payload_form
from utils.fetch_process_functions import convert_to_timestamp, convert_to_utc, decode_url_text
from utils.multi_request import send_request_with_proxy, origin_send_request
from NF_global_objects import get_batch_queue, get_today, get_logger, get_progress, get_total_combi_length, update_progress, get_airport_map

logger=get_logger()
batch_queue=get_batch_queue()
today=get_today()
airport_map=get_airport_map()


def save_flight_info(schedules, airline_map):
    '''비행 정보 저장'''
    fetched_date=today.strftime('%Y%m%d')
    for schedule in schedules[0].values():
        details = schedule['detail']
        total_journey_time = int(schedule['journeyTime'][0])*60 + int(schedule['journeyTime'][1])
        air_id = schedule['id']
        air_id_list = air_id.split('+')
        is_layover = "+" in schedule['id'] and len(details) > 1  # 경유 여부 확인

        '''편도 일 경우 -> 편도 항공권만 flights_info 테이블에 저장'''
        '''경유 일 경우 -> 전체 항공권 정보, 각각의 편도 항공권을 flights_info 테이블에 저장'''
        '''이때 경유 정보 (경유 항공권, 경유 시간)을 layover_info 테이블에 저장'''
        if is_layover:
            # 경유 전체 항공권 정보
            first_detail = details[0]
            last_detail = details[-1]
            layover_depart_airport = first_detail['sa'] # airport_map[first_detail['sa']]['name']
            # layover_depart_country = airport_map[first_detail['sa']]['country']
            layover_depart_timestamp = convert_to_utc(convert_to_timestamp(first_detail['sdt'], first_detail['sa']))
            
            layover_arrival_airport = last_detail['ea'] # airport_map[last_detail['ea']]['name']
            # layover_arrival_country = airport_map[last_detail['ea']]['country']
            layover_arrival_timestamp = convert_to_utc(convert_to_timestamp(last_detail['edt'], last_detail['ea']))
            
            airline_list=[]
            for detail in details:
                airline_list.append(airline_map.get(detail['av']))
            if len(set(airline_list))==1: # 경유시 모든 항공사가 같으면 db에 넣고 아니면 안넣음 (join문으로 구간별 항공사를 알아낼 수 있음)
                airline=airline_list[0]
            else:
                airline=None

            insert_data_to_flight_info=(
                    air_id, airline,
                    layover_depart_airport, layover_depart_timestamp,
                    layover_arrival_airport, layover_arrival_timestamp,
                    total_journey_time,
                    is_layover
                )
        
            
            batch_queue.add_to_queue('flight_info', insert_data_to_flight_info)

            # 각각의 항공권 정보
            for index, detail in enumerate(details):
                depart_airport = detail['sa']# airport_map[detail['sa']]['name']  # 출발 공항
                # depart_country = airport_map[detail['sa']]['country']
                depart_timestamp = convert_to_utc(convert_to_timestamp(detail['sdt'], detail['sa']))
                arrival_airport = detail['ea'] # airport_map[detail['ea']]['name']  # 도착 공항
                # arrival_country = airport_map[detail['ea']]['country']
                arrival_timestamp = convert_to_utc(convert_to_timestamp(detail['edt'], detail['ea']))
                journey_time = int(detail['jt'][:2])*60 + int(detail['jt'][2:])
                connect_time=int(detail['ct'][:2])*60 + int(detail['ct'][2:])
                
                if depart_airport not in airport_map.keys() and arrival_airport not in airport_map.keys(): # 기본 공항외의 공항을 경유할 경우 처리하지 않음
                    warn_text=""
                    if depart_airport not in airport_map:
                        warn_text+=f"{depart_airport}는 규격외의 공합입니다."
                    if arrival_airport not in airport_map:
                        warn_text+=f"\n{arrival_airport}는 규격외의 공합입니다."
                    logger.warning(warn_text)
                    continue
                # flight_info 테이블에 삽입
                insert_data_to_flight_info=(
                    air_id_list[index], 
                    airline_map.get(detail['av']), 
                    depart_airport, depart_timestamp,
                    arrival_airport, arrival_timestamp,
                    journey_time,
                    False
                )
                
                batch_queue.add_to_queue('flight_info', insert_data_to_flight_info)
                # layover_info 테이블에 경유 항공권내의 편도 항공권 id, connect_time 정보 삽입
                insert_data_to_layover_info=(
                    air_id, air_id_list[index], index, connect_time
                )
                batch_queue.add_to_queue('layover_info', insert_data_to_layover_info)
            
        else:
            detail=details[0]
            depart_airport = detail['sa'] # airport_map[detail['sa']]['name']  # 출발 공항
            # depart_country = airport_map[detail['sa']]['country'] # 출발 국가
            depart_timestamp = convert_to_utc(convert_to_timestamp(detail['sdt'], detail['sa'])) # UTC 기준 출발 시간
            arrival_airport = detail['ea'] # airport_map[detail['ea']]['name']  # 도착 공항
            # arrival_country = airport_map[detail['ea']]['country'] # 도착 국가
            arrival_timestamp = convert_to_utc(convert_to_timestamp(detail['edt'], detail['ea'])) # UTC 기준 도착 시간
            journey_time = int(detail['jt'][:2])*60 + int(detail['jt'][2:]) # 비행 시간
            
            insert_data_to_flight_info=(
                    air_id, airline_map.get(detail['av']), 
                    depart_airport, depart_timestamp,
                    arrival_airport, arrival_timestamp,
                    journey_time,
                    False
                )
            
            batch_queue.add_to_queue('flight_info', insert_data_to_flight_info)
    return True

def save_fare_info(fares, fare_types, seat_class):
    '''운임 정보 저장'''
    seat_class_map={'Y':'일반석',
                    'P': '이코노미',
                    'C': '비즈니스석',
                    'F': '일등석'}
    fetched_date=today.strftime('%Y%m%d')
    for key, values in fares.items():
        for option, fare_list in values['fare'].items():
            option=decode_url_text(fare_types[option])
            if option !="성인/모든 결제수단": # 카드사 제휴는 제외함
                continue
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
                    if infant_fare > 0:
                        continue
                    insert_data_to_fare_info=(key, seat_class_map[seat_class], agt, adult_fare, fetched_date)
                    batch_queue.add_to_queue('fare_info', insert_data_to_fare_info)
                except Exception as e:
                    logger.info(f"운임 정보 처리 중 오류: {e}")
                    # print(f"운임 정보 처리 중 오류: {e}")
                    continue
    return True

def fetch_international_flights(response, flight_text, seat_class):
    # with open('flight_data.json', 'w', encoding='utf-8') as f:
    #     json.dump(response, f, ensure_ascii=False, indent=4)
    start=time.time()
    international_list = response.get("data", {}).get("internationalList", {})
    results = international_list.get("results", {})
    
    airline_map = results.get('airlines', {})
    # airport_map = results.get('airports', {})
    schedules = results.get("schedules", [])
    fares = results.get("fares", [])
    fare_types = results.get("fareTypes", [])
    
    next_flag=save_flight_info(schedules=schedules, airline_map=airline_map)
    next_flag=save_fare_info(fares=fares, fare_types=fare_types, seat_class=seat_class)
    end=time.time()
    update_progress()
    progress=get_progress()
    total_combi_length=get_total_combi_length()
    progress_ratio = progress / total_combi_length * 100
    logger.info(f"{flight_text}\n처리된 항공권 일정 비율 : {progress}/{total_combi_length}\n소요 시간 : {round(end-start, 2)}초") 
    return 0