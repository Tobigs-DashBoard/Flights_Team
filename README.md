# 네이버 항공권 DB

본 문서는 네이버 항공권 데이터베이스의 구조와 스키마를 설명합니다.

## 데이터베이스 스키마

```mermaid
erDiagram
    FLIGHTS ||--o{ FLIGHT_INFO : has
    FLIGHTS ||--o{ FARE_INFO : has
    FLIGHTS {
        varchar air_id PK
        boolean is_domestic
        boolean is_layover
        date fetched_date PK
        text layover_list
        timestamp created_at
    }
    FLIGHT_INFO {
        varchar air_id PK, FK
        varchar airline
        varchar depart_country
        varchar depart_airport
        varchar arrival_country
        varchar arrival_airport
        timestamp depart_timestamp
        timestamp arrival_timestamp
        integer journey_time
        integer connect_time
        date fetched_date PK, FK
    }
    FARE_INFO {
        varchar air_id PK
        varchar option_type PK
        varchar agt_code
        integer adult_fare
        integer child_fare
        integer infant_fare
        date fetched_date PK
        text purchase_url
    }
```

## 테이블 구조

### Flights 테이블

| 컬럼명 | 데이터 타입 | 설명 | 예시 |
|--------|------------|------|------|
| air_id | varchar | 항공권 ID (출발날짜, 출발공항, 도착 공항, 항공편 번호) | 20240927GMPPUSKE1827+20240928PUSFUKKE2137 |
| is_domestic | boolean | 국내 항공편 여부 | false |
| is_layover | boolean | 경유 여부 | true |
| fetched_date | date | 수집된 날짜 | 2024-08-20 |
| layover_list | text | 경유 시, 편도 항공편 순서 | ['20240927GMPPUSKE1827', '20240928PUSFUKKE2137'] |
| created_at | timestamp | DB에 insert된 타임스탬프 | 2024-08-20 04:16:16.307186+09 |

### Flight_info 테이블

| 컬럼명 | 데이터 타입 | 설명 | 예시 |
|--------|------------|------|------|
| air_id | varchar | 항공권 ID | 20240927GMPPUSKE1827+20240928PUSFUKKE2137 |
| airline | varchar | 항공사 | 대한항공 |
| depart_country | varchar | 출발 국가 | 대한민국 |
| depart_airport | varchar | 출발 공항 | 김포국제공항 |
| arrival_country | varchar | 도착 국가 | 일본 |
| arrival_airport | varchar | 도착 공항 | 후쿠오카 공항 |
| depart_timestamp | timestamp | 출발 타임스탬프 | 2024-09-27 17:20:00 |
| arrival_timestamp | timestamp | 도착 타임스탬프 | 2024-09-28 19:00:00 |
| journey_time | integer | 비행 시간 | 60 |
| connect_time | integer | 경유시 환승 시간 | 0 |
| fetched_date | date | 수집 날짜 | 2024-08-20 |

### Fare_info 테이블

| 컬럼명 | 데이터 타입 | 설명 | 예시 |
|--------|------------|------|------|
| air_id | varchar | 항공권 ID | 20240927GMPPUSKE1827+20240928PUSFUKKE2137 |
| option_type | varchar | 구매 유형 | 성인/우리카드 |
| agt_code | varchar | 여행사 코드 | INT005 |
| adult_fare | integer | 성인 요금 | 210800 |
| child_fare | integer | 어린이 요금 | 10000 |
| infant_fare | integer | 영유아 요금 | 0 |
| fetched_date | date | 수집 날짜 | 2024-08-20 |
| purchase_url | text | 결제 페이지 url | https://fly.interpark.com/partner/... |


## 참고 사항

- `layover_list`는 경유 항공편의 경우 각 구간의 항공편 ID를 순서대로 저장합니다. (각 구간의 id 정보 또한 flight_info에 저장되어 있어, 필요시 join 문을 통해 추가 분석이 가능합니다.)
- `fare_info`는 Flights의 air_id와 FK 제약이 걸려있지 않습니다. (데이터 insert 병렬처리를 위해 외래키 제약을 해재했습니다. 이후 데이터 무결성이 문제될 경우 추가 조치 필요합니다.)


## 테이블 생성 SQL 쿼리

```sql
-- Flights 테이블 생성
CREATE TABLE Flights (
    air_id VARCHAR(255),
    is_domestic BOOLEAN,
    is_layover BOOLEAN,
    fetched_date DATE,
    layover_list TEXT,
    created_at TIMESTAMP,
    PRIMARY KEY (air_id, fetched_date)
);

-- Flight_info 테이블 생성
CREATE TABLE Flight_info (
    air_id VARCHAR(255),
    airline VARCHAR(255),
    depart_country VARCHAR(255),
    depart_airport VARCHAR(255),
    arrival_country VARCHAR(255),
    arrival_airport VARCHAR(255),
    depart_timestamp TIMESTAMP,
    arrival_timestamp TIMESTAMP,
    journey_time INTEGER,
    connect_time INTEGER,
    fetched_date DATE,
    PRIMARY KEY (air_id, fetched_date),
    FOREIGN KEY (air_id, fetched_date) REFERENCES Flights (air_id, fetched_date)
);

-- Fare_info 테이블 생성
CREATE TABLE Fare_info (
    air_id VARCHAR(255),
    option_type VARCHAR(255),
    agt_code VARCHAR(50),
    adult_fare INTEGER,
    child_fare INTEGER,
    infant_fare INTEGER,
    fetched_date DATE,
    purchase_url TEXT,
    PRIMARY KEY (air_id, option_type, fetched_date),
);
```