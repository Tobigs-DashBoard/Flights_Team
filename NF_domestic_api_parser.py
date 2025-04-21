from utils.fetch_process_functions import convert_to_timestamp, convert_to_utc
from NF_global_objects import get_today, get_batch_manager
import time
today=get_today()
batch_manager=get_batch_manager()


def parsing_domestic_flights(response):
    start=time.time()
    schedules=response['data']['domesticFlights']['departures']
    fetched_date=today.strftime('%Y%m%d')
    for air in schedules:
        seat_class=air['seatClass'] # 좌석 등급
        seat_cnt=air['seatCnt'] # 잔여 좌석수 # TODO 해외 항공권이랑 비교 필요
        air_id=air['departureDate']+air['depCity']+air['arrCity']+air['airlineCode']+air['fitName']+air['seatClass']

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
        
        batch_manager.flight_info_queue.add_to_queue(
                air_id, airline_name, 
                depart_airport, depart_timestamp,
                arrival_airport, arrival_timestamp,
                journey_time,
                False
            )
        
        for agt_option in air['fare']:
            discountFare = agt_option.get('discountFare', 0)
            if isinstance(discountFare, dict):  # type() 대신 isinstance() 사용 권장
                try:
                    discountFare=0
                    # print(discountFare['discountInfo']['cardType']['name'])
                    # print('네이버 페이 적용 금액:', discountFare.get('adultDiscountFare', '할인 금액 이상'))
                except KeyError as e:
                    print(f"KeyError 발생: {e}")  # 키가 없을 경우 에러 처리
            publish_fee=agt_option['publishFee']
            adult_fare = agt_option['adultFare'] + agt_option['aTax'] + agt_option['aFuel']  + publish_fee
            child_fare = agt_option['childFare'] + agt_option['cTax'] + agt_option['cFuel'] + publish_fee
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
            batch_manager.fare_info_queue.add_to_queue(air_id, option_type, agt_code, adult_fare, fetched_date)
        
    return 0