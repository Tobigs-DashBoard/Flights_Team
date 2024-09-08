from SS_api_params import *
from SS_functions import *
from SS_db_params import *

flight_query = query_dict['flight_info']
fare_query = query_dict['fare_info']
layover_query = query_dict['layover_info']

def fetch_skyscanner_data(origin, destination, date, today, cnt, adults, cabin_class):
    fetched_date=today.strftime('%Y%m%d')
    headers, payload=return_header_payload(origin, destination, date, adults, cabin_class)
    data=send_request(payload=payload, headers=headers)
    itin_data=data['itineraries']
    agents=itin_data['agents']
    agent_map={}
    for agent in agents:
        agent_map[agent['id']]=agent['name']

    if len(itin_data['results'])==0: # 항공권 정보가 없는 경우 종료
        return cnt + 1
    
    # 운항 정보가 들어있는 부분
    for result in itin_data['results']:
        for leg in result['legs']:
            air_id = leg['id']
            if leg['stopCount']!=0:
                origin_code = leg['origin']['id']
                arrival_code = leg['destination']['id']
                departure_utc = convert_to_utc(leg['departure'], origin_code) # 출발지 공항 기준으로 되어있는 출발 시간을 UTC 기준으로 변환
                arrival_utc = convert_to_utc(leg['arrival'], arrival_code)
                journey_time=leg['durationInMinutes']
                if leg['carriers']["operationType"]=="fully_operated":
                    airline=leg['carriers']['marketing'][0]['name']
                else:
                    airline=leg['carriers']['operating'][0]['name']

                # 비행 정보 저장
                execute_db_query(conn, cur, flight_query, (
                    air_id, airline,
                    origin_code, departure_utc,
                    arrival_code, arrival_utc,
                    journey_time,
                    fetched_date
                ))
                
            # print("\n--- 세부 비행 정보 ---")
            for index, segment in enumerate(leg['segments']):
                segment_id = segment['id'].replace(str(segment['marketingCarrier']['id']), str(segment['operatingCarrier']['id']))
                segment_airline=segment['operatingCarrier']['name']
                segment_origin_code = segment['origin']['flightPlaceId']
                segment_arrival_code = segment['destination']['flightPlaceId']
                segment_departure_utc = convert_to_utc(segment['departure'], segment['origin']['flightPlaceId']) # 출발지 공항 기준으로 되어있는 출발 시간을 UTC 기준으로 변환
                segment_arrival_utc = convert_to_utc(segment['arrival'], segment['destination']['flightPlaceId'])
                segment_journey_time=segment['durationInMinutes']
                # 환승 시간 계산
                if index < len(leg['segments']) - 1:
                    next_segment = leg['segments'][index + 1]
                    connect_time = calculate_connect_time(segment['arrival'], next_segment['departure'])
                else:
                    connect_time = 0
                
                # 비행 정보 저장
                execute_db_query(conn, cur, flight_query, (
                    segment_id, segment_airline,
                    segment_origin_code, segment_departure_utc,
                    segment_arrival_code, segment_arrival_utc,
                    segment_journey_time,
                    fetched_date
                ))
                if leg['stopCount']!=0:
                    # 경유 정보 저장
                    execute_db_query(conn, cur, layover_query, (
                        air_id, segment_id, index, connect_time, fetched_date
                        ))
                else:
                    air_id=segment_id
            # 요금 정보 파싱
            # fare_info['id'] = leg['id']
            for option in result['pricingOptions']:
                for item in option['items']:
                    agt=agent_map[item['agentId']]
                    fare = int(item['price']['amount'])
                    if fare == 0:
                        continue
                    purchase_url="https://www.skyscanner.co.kr"+item['url']
                    execute_db_query(conn, cur, fare_query, (
                        air_id, "이코노미", agt, fare, purchase_url, fetched_date
                    ))
    conn.commit()
    return cnt