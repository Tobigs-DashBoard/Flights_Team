import json
import time
import logging
from entityId_api_params import return_header_payload, send_request

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 공항 엔티티 ID 맵 로드
with open('airport_entityId_map.json', 'r', encoding='utf-8') as f:
    airport_entity_id_map = json.load(f)

def fetch_skyscanner_data(destination, date):
    # API 요청을 위한 헤더와 페이로드 준비
    headers, payload = return_header_payload(destination=destination, date=date)
    
    # API 요청 전송
    data = send_request(payload=payload, headers=headers)
    
    # 디버깅을 위해 원본 데이터 저장
    with open(f'sky_test_origin.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    try:
        # 목적지 ID 추출
        destination_id = data['locations']['airport']
        logging.info(f"{destination}에 대한 데이터 가져오기 성공: {destination_id['entityId']}")
        return destination_id['entityId']
    except KeyError as e:
        logging.error(f"{destination} 처리 중 KeyError 발생: {e}")
    except Exception as e:
        logging.error(f"{destination} 처리 중 예상치 못한 오류 발생: {e}")
    return '-'


if __name__ == "__main__":
    processed_airports = set()
    
    # 이미 처리된 공항 목록 로드 및 결과 파일 준비
    try:
        with open('airport_entity_results.txt', 'r', encoding='utf-8') as f:
            for line in f:
                airport_code = line.split(',')[0].strip()
                processed_airports.add(airport_code)
    except FileNotFoundError:
        pass

    # 결과를 텍스트 파일에 저장
    with open('airport_entity_results.txt', 'a', encoding='utf-8') as f:
        # 모든 공항 코드에 대해 반복
        for key in airport_entity_id_map.keys():
            # 이미 처리된 공항은 건너뛰기
            if key in processed_airports:
                logging.info(f"이미 처리된 공항 건너뛰기: {key}")
                continue
            
            # Skyscanner 데이터 가져오기
            entity_id = fetch_skyscanner_data(key, "240922")
            
            # 결과를 텍스트 파일에 누적 저장
            f.write(f"{key},{entity_id}\n")
            f.flush()  # 파일에 즉시 쓰기
            
            logging.info(f"공항 {key}의 entity ID {entity_id} 저장 완료")
            
            # api 밴 방지를 위해 10초간 대기
            time.sleep(10)