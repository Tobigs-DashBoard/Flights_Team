# import json
import time
from config.api_params import  return_header, international_payload_form
from utils.fetch_process_functions import convert_to_timestamp, convert_to_utc, send_request, decode_url_text
from NF_global_objects import get_batch_queue, get_today, get_logger

logger=get_logger()
batch_queue=get_batch_queue()
today=get_today()


def save_flight_info(schedules, airline_map):
    '''비행 정보 저장'''
    fetched_date=today.strftime('%Y%m%d')
    inserted_air_id_list=[]
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
                    fetched_date
                )
            if air_id not in inserted_air_id_list:
                inserted_air_id_list.append(air_id)
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
                
                # flight_info 테이블에 삽입
                insert_data_to_flight_info=(
                    air_id_list[index], airline_map.get(detail['av']), 
                    depart_airport, depart_timestamp,
                    arrival_airport, arrival_timestamp,
                    journey_time,
                    fetched_date
                )
                if air_id_list[index] not in inserted_air_id_list:
                    inserted_air_id_list.append(air_id_list[index])
                    batch_queue.add_to_queue('flight_info', insert_data_to_flight_info)

                # layover_info 테이블에 경유 항공권내의 편도 항공권 id, connect_time 정보 삽입
                insert_data_to_layover_info=(
                    air_id, air_id_list[index], index, connect_time, fetched_date
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
                    fetched_date
                )
            if air_id not in inserted_air_id_list:
                inserted_air_id_list.append(air_id)
                batch_queue.add_to_queue('flight_info', insert_data_to_flight_info)
    return True

def save_fare_info(fares, fare_types):
    '''운임 정보 저장'''
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
                    insert_data_to_fare_info=(key, option, agt, adult_fare, purchase_url, fetched_date)
                    batch_queue.add_to_queue('fare_info', insert_data_to_fare_info)
                except Exception as e:
                    logger.info(f"운임 정보 처리 중 오류: {e}")
                    # print(f"운임 정보 처리 중 오류: {e}")
                    continue
    return True

def fetch_international_flights(departure, arrival, date, cnt):
    # logger.info("외국 항공권입니다.")
    headers = return_header(departure, arrival, date)
    
    # 첫 번째 요청
    payload1 = international_payload_form(first=True, departure=departure, arrival=arrival, date=date)
    response_data1 = send_request(payload1, headers)
    
    # TODO 요청오류났을때 어떻게 처리할지
    if not response_data1:
        cnt+=2
        return cnt
    
    international_list = response_data1.get("data", {}).get("internationalList", {})
    galileo_key = international_list.get("galileoKey")
    travel_biz_key = international_list.get("travelBizKey")
    
    time.sleep(5)

    # 두 번째 요청
    payload2 = international_payload_form(first=False, departure=departure, arrival=arrival, date=date, galileo_key=galileo_key, travel_biz_key=travel_biz_key)
    response_data2 = send_request(payload2, headers)
    if not response_data2:
        cnt+=2
        return cnt

    international_list = response_data2.get("data", {}).get("internationalList", {})
    results = international_list.get("results", {})
        
    airline_map = results.get('airlines', {})
    # airport_map = results.get('airports', {})
    schedules = results.get("schedules", [])
    fares = results.get("fares", [])
    fare_types = results.get("fareTypes", [])
    
    if len(schedules) == 0:
        # logger.info(f"{airport_map[departure]['name']}에서 {airport_map[arrival]['name']}로 가는 항공권이 없습니다. {date}")
        cnt+=1
        return cnt
    # 항공편이 있으면 체크개수 초기화
    else:
        cnt=0
    
    next_flag=save_flight_info(schedules=schedules, airline_map=airline_map)
    next_flag=save_fare_info(fares=fares, fare_types=fare_types)
    
    return cnt