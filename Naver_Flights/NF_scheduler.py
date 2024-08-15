
from NF_functions import request_airport_map
from NF_international_api_parser import fetch_international_flights
from datetime import date, timedelta

if __name__ == "__main__":
    korea_airport_list=["SEL", "CJU","GMP","PUS","CJJ","KWJ","TAE","RSU","USN","HIN","KPO","WJU","KUV","MWX","ICN"]
    
    # 한국 공항에서 출발 기준
    for departure in korea_airport_list:
        arrival_target_list = ["일본"]#"대한민국", "일본", "동남아" #, "중국", "유럽", "미주", "대양주", "남미", "아시아", "중동", "아프리카"]
        today = date.today() # 오늘 날짜 기준
        for arrival_target in arrival_target_list:
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
                    if cnt>=30: # 연속으로 30일간의 항공편이 없으면 해당 출발지 도착지 조합은 검색 중단
                        print(f"{departure}에서 {arrival}로 가는 노선 검색 중단: 연속 30일 항공편 없음")
                        break
                    elif domestic_flag:
                        target_date = today + timedelta(days=i)
                        formatted_date = target_date.strftime('%Y%m%d')
                        cnt=fetch_international_flights(departure, arrival, formatted_date, today, cnt)
                    
                    else:
                        target_date = today + timedelta(days=i)
                        formatted_date = target_date.strftime('%Y%m%d')
                        cnt=fetch_international_flights(departure, arrival, formatted_date, today, cnt)