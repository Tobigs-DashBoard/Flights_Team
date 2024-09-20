from NF_functions import request_airport_map, airport_map, setup_logger
from NF_international_api_parser import fetch_international_flights
from NF_domestic_api_parser import fetch_domestic_flights
from datetime import date, timedelta
import time
import random
import os

os.environ['TZ'] = 'Asia/Seoul'
time.tzset()

# 로깅 설정
logger = setup_logger()

def crawl_flights(departure, arrival, is_domestic):
    today = date.today()
    cnt = 0  # 예외처리용 카운터
    start_time = time.time()
    logger.info(f"출발지:{airport_map[departure]['name']} 도착지:{airport_map[arrival]['name']}")
    # print(f"출발지:{airport_map[departure]['name']} 도착지:{airport_map[arrival]['name']}")

    for i in range(1, 181):
        if cnt >= 10:  # 연속으로 10일간의 항공편이 없으면 해당 출발지 도착지 조합은 검색 중단
            logger.info(f"{departure}에서 {arrival}로 가는 노선 검색 중단: 연속 10일 항공편 없음")
            # print(f"{departure}에서 {arrival}로 가는 노선 검색 중단: 연속 10일 항공편 없음")
            break
        
        target_date = today + timedelta(days=i)
        formatted_date = target_date.strftime('%Y%m%d')
        
        if is_domestic:
            cnt = fetch_domestic_flights(departure, arrival, formatted_date, today, cnt)
            logger.info(f"{departure}에서 {arrival}로 가는 노선 검색")
        else:
            cnt = fetch_international_flights(departure, arrival, formatted_date, today, cnt)
            logger.info(f"{departure}에서 {arrival}로 가는 노선 검색")
        
        random_sec = random.randint(1, 10)
        time.sleep(random_sec)

    end_time = time.time()
    duration = (end_time - start_time) // 60
    logger.info(f"소요시간: {duration} 분\n")
    # print(f"소요시간: {duration} 분\n") 

target_regions = os.environ.get('TARGET_REGION', '대한민국').split(',')

if __name__ == "__main__":
    time.sleep(60)  # 매일 자정 00시에 실행되기 때문에 1분 늦게 시작시킴
    korea_airport_list = ["SEL", "CJU", "GMP", "PUS", "CJJ", "KWJ", "TAE", "RSU", "USN", "HIN", "KPO", "WJU", "KUV", "MWX", "ICN"]
    arrival_target_list = target_regions  # "대한민국", "일본", "동남아", "중국", "유럽", "미주", "대양주", "남미", "아시아", "중동", "아프리카"

    # 모든 공항 조합을 한 번에 처리
    for departure in korea_airport_list:
        for arrival_target in arrival_target_list:
            for airport in request_airport_map[arrival_target]:
                arrival = airport['IATA']
                if arrival == departure:  # 출발지와 도착지가 같은 경우 스킵
                    continue
                
                is_domestic = arrival in korea_airport_list and departure in korea_airport_list
                
                # 정방향 크롤링
                crawl_flights(departure, arrival, is_domestic)
                
                # 역방향 크롤링
                crawl_flights(arrival, departure, is_domestic)
    logger.info('\n\n크롤링 완료!!!!')