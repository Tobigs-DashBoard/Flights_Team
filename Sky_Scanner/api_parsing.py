import requests
import json
from datetime import datetime

def fetch_skyscanner_data(origin_entity_id, destination_entity_id, date, adults=1, cabin_class="ECONOMY"):
    url = "https://www.skyscanner.co.kr/g/radar/api/v2/web-unified-search/"
    
    headers = {
        "authority": "www.skyscanner.co.kr",
        "accept": "application/json",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/json",
        "origin": "https://www.skyscanner.co.kr",
        "referer": f"https://www.skyscanner.co.kr/transport/flights/{origin_entity_id}/{destination_entity_id}/{date}/?adultsv2={adults}&cabinclass={cabin_class.lower()}&childrenv2=&ref=home&rtn=0&preferdirects=false&outboundaltsenabled=false&inboundaltsenabled=false",
        "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "x-skyscanner-market":"KR",
        "x-skyscanner-channelid":"website",
        "x-skyscanner-locale":"ko-KR",
        "x-skyscanner-currency":"KRW",
        "x-skyscanner-traveller-context": "46e93065-10a4-4ff7-8e3c-2a177e638f53",
        "x-skyscanner-trustedfunnelid":"0ab5d749-81aa-4a0c-b943-c72436a3c072",
        "x-skyscanner-viewid": "0ab5d749-81aa-4a0c-b943-c72436a3c072",
        }
    
    payload = {
        "adults": int(adults),
        "cabinClass": cabin_class,
        "childAges": [],
        "legs": [
            {
                "legOrigin": {
                    "@type": "entity",
                    "entityId": origin_entity_id
                },
                "legDestination": {
                    "@type": "entity",
                    "entityId": destination_entity_id
                },
                "dates": {
                    "@type": "date",
                    "year": str(date[:4]),
                    "month": str(date[5:7]),
                    "day": str(date[8:])
                }
            }
        ]
    }
    
    try:
        # print("Sending payload:", json.dumps(payload, indent=2))  # Debug print
        response = requests.post(url, headers=headers, json=payload)
        print("Response status code:", response.status_code)  # Debug print
        print(response.text)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        print(f"Response content: {response.content}")
        return None

def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Data saved to {filename}")

def main():
    origin_entity_id = "95673659"  # Example Entity ID for ICN
    destination_entity_id = "128668889"  # Example Entity ID for NRT
    date = "2024-08-18"
    adults = 1
    cabin_class = "ECONOMY"
    
    data = fetch_skyscanner_data(origin_entity_id, destination_entity_id, date, adults, cabin_class)
    
    if data:
        filename = f"skyscanner_data.json"
        save_to_json(data, filename)
    else:
        print("No data to save.")

if __name__ == "__main__":
    main()