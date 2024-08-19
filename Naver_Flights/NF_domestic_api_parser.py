from NF_api_params import domastic_payload_form, return_header
from NF_functions import *
from NF_db_params import get_db_connection, execute_db_query, query_dict

# 로깅 설정
logger=setup_logger()

def fetch_domestic_flights(departure, arrival, date, today, cnt):
    # logger.info("국내 항공권 입니다.")
    headers = return_header(departure, arrival, date)
    
    # 첫 번째 요청
    payload1 = domastic_payload_form(departure=departure, arrival=arrival, date=date)
    response_data1 = send_request(payload1, headers)
    if not response_data1['data']['domesticFlights']:
        # logger.info(f"{airport_region_map[departure]['name']}에서 {airport_region_map[arrival]['name']}로 가는 항공권이 없습니다. {date}")
        cnt +=1
        return cnt
    
    schedules=response_data1['data']['domesticFlights']['departures']

    if len(schedules) == 0:
        # logger.info(f"{airport_region_map[departure]['name']}에서 {airport_region_map[arrival]['name']}로 가는 항공권이 없습니다. {date}")
        cnt+=1
        return cnt
    else:
        cnt=0 # 항공편이 있으면 예외처리 카운터 초기화

    conn=get_db_connection() # db 연결
    cur = conn.cursor() # DB 커서 객체 (insert, delete, select 등 명령어 수행)
    for air in schedules:
        air_id=air['departureDate']+air['depCity']+air['arrCity']+air['airlineCode']+air['fitName']
        fetched_date=today.strftime('%Y%m%d')
        fetched_date=today.strftime('%Y%m%d')
        

        # flights 테이블에 삽입
        query = query_dict['flights_table']
        execute_db_query(conn, cur, query, (air_id, True, False, None, fetched_date))
        # 항공권 정보 삽입
        air_id=air_id
        airline_name = air['airlineName'],
        depart_country=airport_region_map[air['depCity']]['country']
        depart_airport= airport_region_map[air['depCity']]['name']
        depart_timestamp= timestamp_to_iso8601(return_time_stamp(air['departureDate']))
            
        arrival_airport= airport_region_map[air['arrCity']]['name']
        arrival_country=airport_region_map[air['arrCity']]['country']
        arrival_timestamp= timestamp_to_iso8601(return_time_stamp(air['arrivalDate']))

        journey_time= int(air['journeyTime'][:2])*60 + int(air['journeyTime'][3:])
        connect_time= 0,
        fetched_date=fetched_date

        query = query_dict['flight_info_table']
        execute_db_query(conn, cur, query, (
                air_id, airline_name, 
                depart_country, depart_airport,depart_timestamp,
                arrival_country, arrival_airport, arrival_timestamp,
                journey_time,
                connect_time,
                fetched_date
            ))

        for agt_option in air['fare']:
            discountFare = agt_option['discountFare'] or 0
            adult_fare = agt_option['adultFare'] + agt_option['aTax'] + agt_option['aFuel'] + discountFare
            child_fare = agt_option['childFare'] + agt_option['cTax'] + agt_option['cFuel'] + discountFare
            agt_code= agt_option['agtCode']
            # booking_class= agt_option['bookingClass'],
            # adult_base_fare= agt_option['adultFare'],
            # atax= agt_option['aTax'],
            # afuel= agt_option['aFuel'],
            # child_base_fare= agt_option['childFare'],
            # ctax= agt_option['cTax'],
            # cfuel= agt_option['cFuel'],
            # publish_free= agt_option['publishFee'],
            # discountFare= discountFare,
            adult_fare= adult_fare
            child_fare= child_fare
            infant_fare=0
            purchase_url=None
            query = query_dict['fare_info_table']
            execute_db_query(conn, cur, query, (air_id, "성인/모든 결제수단", agt_code, 
                                                adult_fare, child_fare, infant_fare, purchase_url, fetched_date))
        

    # logger.info(f"{airport_region_map[departure]['name']}에서 {airport_region_map[arrival]['name']}로 가는 항공권 정보가 데이터베이스에 저장되었습니다.\n")
    conn.commit()
    conn.close()
    return cnt