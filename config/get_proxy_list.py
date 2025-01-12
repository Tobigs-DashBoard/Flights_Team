import requests
from bs4 import BeautifulSoup
import re
import json

def get_proxy_list():
    result = []
    # 요청할 URL
    url = "https://spys.one/en/socks-proxy-list/"
    # 헤더 정보
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    }
    # GET 요청 보내기
    response = requests.get(url, headers=headers)
    # 응답 상태 코드 확인
    if response.status_code != 200:
        print(f"Error: Unable to fetch the page, status code: {response.status_code}")
        return

    # BeautifulSoup 객체 생성
    soup = BeautifulSoup(response.content, 'html.parser')

    ports = {}
    script = soup.select_one("body > script")
    
    for row in script.text.split(";"):
        if "^" in row:
            line = row.split("=")
            ports[line[0]] = line[1].split("^")[0]
    
    trs = soup.select("tr[onmouseover]")
    for tr in trs:
        e_ip = tr.select_one("font.spy14")
        ip = ""
        e_port = tr.select_one("script")
        port = ""
        if e_port is not None:
            re_port = re.compile(r'\(([a-zA-Z0-9]+)\^[a-zA-Z0-9]+\)')
            match = re_port.findall(e_port.text)
            for item in match:
                port = port + ports[item]
        else:
            continue

        if e_ip is not None:
            for item in e_ip.findAll('script'):
                item.extract()
            ip = e_ip.text
        else:
            continue

        # Get uptime value (%)
        tds = tr.select("td")
        is_skip = False
        for td in tds:
            e_pct = td.select_one("font > acronym")
            if e_pct is not None:
                pct = re.sub(r'([0-9]+)%.*', r'\1', e_pct.text)
                if not pct.isdigit():
                    is_skip = True
            else:
                continue
        if is_skip:
            continue

        result.append((ip + ":" + port, pct))

    # Sort by uptime value
    result.sort(key=lambda element: int(element[1]), reverse=True)

    proxy_map_list = []
    for proxy in result:
        url = "socks5://" + proxy[0]
        proxy_map = {'http': url, 'https': url}
        proxy_map_list.append(proxy_map)
    print(proxy_map_list)

    total_proxy_map = {}
    for index, proxy_map in enumerate(proxy_map_list):
        total_proxy_map[index] = proxy_map

    total_proxy_map[list(total_proxy_map.keys())[-1]+1] = 'my_ip'

    # JSON 파일로 저장
    with open('total_proxy_map.json', 'w', encoding='utf-8-sig') as f:
        json.dump(total_proxy_map, f, ensure_ascii=False, indent=4)

    return total_proxy_map

if __name__ == "__main__":
    get_proxy_list()