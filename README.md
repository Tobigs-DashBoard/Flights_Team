# 네이버 항공권 DB 스키마

## DB 스키마
```mermaid
erDiagram
    FLIGHTS ||--o{ FARE_INFO : has
    FLIGHTS ||--o{ FLIGHT_INFO : has
    FLIGHTS {
        string air_id PK
        boolean is_layover
        boolean is_domestic
        string layover_list
        date fetched_date PK
    }
    FARE_INFO {
        string air_id PK
        string option_type PK
        string agt_code
        float adult_fare
        float child_fare
        float infant_fare
        string purchase_url
        date fetched_date PK
    }
    FLIGHT_INFO {
        string air_id PK
        string airline
        string depart_country
        string depart_airport
        string arrival_country
        string arrival_airport
        datetime arrival_timestamp
        datetime depart_timestamp
        time journey_time
        time connect_time
        date fetched_date PK
    }
```