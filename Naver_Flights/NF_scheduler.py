
from NF_functions import request_airport_map
from NF_international_api_parser import fetch_international_flights
from NF_domestic_api_parser import fetch_domestic_flights
from datetime import date, timedelta
import time
import random
import logging

# 로깅 설정
logging.basicConfig(filename='crawling_log.log', level=logging.INFO, 
                    format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

if __name__ == "__main__":
    korea_airport_list=["SEL", "CJU","GMP","PUS","CJJ","KWJ","TAE","RSU","USN","HIN","KPO","WJU","KUV","MWX","ICN"]
    
    # 한국 공항에서 출발 기준
    for departure in korea_airport_list:
        arrival_target_list = ["대한민국"]# "동남아", "중국", "유럽", "미주", "대양주", "남미", "아시아", "중동", "아프리카"]
        today = date.today() # 오늘 날짜 기준
        start_time=time.time()
        for arrival_target in arrival_target_list:
            print("도착지:", arrival_target)
            for airport in request_airport_map[arrival_target]:
                arrival = airport['IATA']
                if arrival == departure: # 출발지와 도착지가 같은 경우 스킵
                    continue
                if arrival in korea_airport_list and departure in korea_airport_list:
                    domestic_flag=True
                else:
                    domestic_flag=False
                cnt=0 # 예외처리용 카운터
                for i in range(1, 90):
                    if cnt>=10: # 연속으로 10일간의 항공편이 없으면 해당 출발지 도착지 조합은 검색 중단
                        print(f"{departure}에서 {arrival}로 가는 노선 검색 중단: 연속 30일 항공편 없음")
                        break
                    elif domestic_flag:
                        target_date = today + timedelta(days=i)
                        formatted_date = target_date.strftime('%Y%m%d')
                        cnt=fetch_domestic_flights(departure, arrival, formatted_date, today, cnt)
                    
                    else:
                        target_date = today + timedelta(days=i)
                        formatted_date = target_date.strftime('%Y%m%d')
                        cnt=fetch_international_flights(departure, arrival, formatted_date, today, cnt)
                    random_sec=random.randint(5, 10)
                    # print(f"밴 방지를 위해 {random_sec}초 동안 대기")
                    time.sleep(random_sec)
                    print()
                
            end_time=time.time()
            duration=(end_time-start_time)//60
            log_message = f"출발지: {arrival_target}, 소요시간: {duration} 분"
            logging.info(log_message)
            