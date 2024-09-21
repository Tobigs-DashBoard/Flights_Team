from config.api_params import domastic_payload_form, return_header
from utils.fetch_process_functions import convert_to_timestamp, convert_to_utc, send_request
from NF_global_objects import get_today, get_batch_queue
import json
today=get_today()
batch_queue=get_batch_queue()

def fetch_domestic_flights(departure, arrival, date, cnt):
    # logger.info("국내 항공권 입니다.")
    headers = return_header(departure, arrival, date)
    # 첫 번째 요청
    payload1 = domastic_payload_form(departure=departure, arrival=arrival, date=date)
    response_data1 = send_request(payload1, headers)

    schedules=response_data1['data']['domesticFlights']['departures']
    if not response_data1:
        cnt+=2
        return cnt
    
    if len(schedules) == 0:
        # logger.info(f"{airport_map[departure]['name']}에서 {airport_map[arrival]['name']}로 가는 항공권이 없습니다. {date}")
        cnt+=1
        return cnt
    else:
        cnt=0 # 항공편이 있으면 예외처리 카운터 초기화

    for air in schedules:
        seat_class=air['seatClass'] # 좌석 등급
        seat_cnt=air['seatCnt'] # 잔여 좌석수 # TODO 해외 항공권이랑 비교 필요
        air_id=air['departureDate']+air['depCity']+air['arrCity']+air['airlineCode']+air['fitName']+seat_class
        fetched_date=today.strftime('%Y%m%d')

        # 항공권 정보 삽입
        air_id=air_id
        airline_name = air['airlineName']
        # depart_country=airport_map[air['depCity']]['country']
        depart_airport= air['depCity'] # airport_map[air['depCity']]['name']
        
        depart_timestamp= convert_to_utc(convert_to_timestamp(air['departureDate'], air['depCity'])) # UTC 기준 출발 시간
        
        arrival_airport= air['arrCity'] # airport_map[air['arrCity']]['name']
        # arrival_country=airport_map[air['arrCity']]['country']
        arrival_timestamp= convert_to_utc(convert_to_timestamp(air['arrivalDate'], air['depCity'])) # UTC 기준 출발 시간
        if seat_class == "Y":
            option_type="일반석"
        elif seat_class == "D":
            option_type="할인석"
        elif seat_class=="L":
            option_type="특가석"
        elif seat_class=="C":
            option_type="비즈니스석"

        journey_time= int(air['journeyTime'][:2])*60 + int(air['journeyTime'][3:])
        
        insert_data_to_flight_info=(
                air_id, airline_name, 
                depart_airport, depart_timestamp,
                arrival_airport, arrival_timestamp,
                journey_time,
                fetched_date
            )
        batch_queue.add_to_queue('flight_info', insert_data_to_flight_info) # 배치큐에 삽입

        for agt_option in air['fare']:
            discountFare = agt_option['discountFare'] or 0
            publish_fee=agt_option['publishFee']
            adult_fare = agt_option['adultFare'] + agt_option['aTax'] + agt_option['aFuel'] + discountFare + publish_fee
            child_fare = agt_option['childFare'] + agt_option['cTax'] + agt_option['cFuel'] + discountFare + publish_fee
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
            child_fare=None
            purchase_url=None
            insert_data_to_fare_info=(air_id, option_type, agt_code, adult_fare, purchase_url, fetched_date)
            batch_queue.add_to_queue('fare_info', insert_data_to_fare_info)

    return cnt