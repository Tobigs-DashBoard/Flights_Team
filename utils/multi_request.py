import time
import requests
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def send_request(payload, headers, proxy):
    return send_request_with_proxy(payload, headers, proxy)

def send_request_with_proxy(payload, headers, proxy):
    url = "https://airline-api.naver.com/graphql"
    try:
        response = requests.post(
            url, 
            proxies=proxy, 
            json=payload, 
            headers=headers, 
            verify=False, 
            timeout=(10, 10)
        )
        if type(response)==bool:
            print(f'{proxy}->ip 밴당함')
            return None
        response.raise_for_status()
        
        if not response.text.strip():
            return None
            
        try:
            return response.json()
        except json.JSONDecodeError:
            return None
            
    except requests.exceptions.RequestException as e:
        if isinstance(e, (requests.exceptions.ConnectTimeout, 
                         requests.exceptions.ReadTimeout, 
                         requests.exceptions.ConnectionError)):
            # print(e)
            return None
        return None
    except Exception:
        return None