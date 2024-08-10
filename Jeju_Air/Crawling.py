# 필요한 Selenium 및 기타 모듈 import
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time

def click_button_js(driver, element):
    driver.execute_script("arguments[0].click();", element)

# Chrome 옵션 설정
options = Options()
options.add_experimental_option("detach", True)  # 브라우저 창을 열린 상태로 유지

# 웹사이트 URL 설정 및 Chrome 드라이버 초기화
url = "https://www.jejuair.net/ko/ibe/booking/Availability.do"
driver = webdriver.Chrome(options=options)
driver.get(url)  # 지정된 URL로 이동

# 편도 버튼 클릭
try:
    oneway_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'li[data-triptype="OW"] .item-btn'))
    )
    if 'selected' not in oneway_button.get_attribute('class'):
        oneway_button.click()
        print("편도 버튼이 클릭되었습니다.")
    else:
        print("편도가 이미 선택되어 있습니다.")
except TimeoutException:
    print("편도 버튼을 찾을 수 없습니다.")

try:
    departure_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.start.js-target-pick"))
    )
    click_button_js(driver, departure_button)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "depAirportLayer"))
    )
except TimeoutException:
    print("출발지 버튼을 찾는 데 시간이 초과되었습니다.")

departure_arrival_info = {}

# 출발지 지역 탭 리스트 찾기
dep_region_tabs = WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#divDepArea .tab__button"))
)

for dep_region_tab in dep_region_tabs:
    try:
        dep_region_button = dep_region_tab.find_element(By.TAG_NAME, "button")
        dep_region_name = dep_region_button.text
        print(f"\n출발지 지역: {dep_region_name}")
        
        click_button_js(driver, dep_region_button)
        time.sleep(1)
        
        # 출발 공항 버튼들 찾기
        dep_airport_buttons = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".tab__panel.is-active .choise__button"))
        )
        
        for dep_airport in dep_airport_buttons:
            dep_airport_name = dep_airport.find_element(By.CLASS_NAME, "stationName").text
            dep_airport_code = dep_airport.find_element(By.CLASS_NAME, "airport").text
            print(f"  출발 공항: {dep_airport_name} ({dep_airport_code})")
            
            click_button_js(driver, dep_airport)
            time.sleep(1)
            
            # 도착지 버튼 클릭
            arrival_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.target.js-target-pick"))
            )
            click_button_js(driver, arrival_button)
            time.sleep(1)
            
            arrival_airports = {}
            
            # 도착지 지역 탭 리스트 찾기
            arr_region_tabs = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#divArrArea .tab__button"))
            )

            for arr_region_tab in arr_region_tabs:
                try:
                    arr_region_button = arr_region_tab.find_element(By.TAG_NAME, "button")
                    arr_region_name = arr_region_button.text
                    print(f"    도착지 지역: {arr_region_name}")
                    
                    click_button_js(driver, arr_region_button)
                    time.sleep(1)
                    
                    # 현재 활성화된 패널에서 공항 버튼들을 찾음
                    arr_airport_buttons = WebDriverWait(driver, 5).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".tab__panel.is-active .choise__button"))
                    )
                    
                    for arr_airport in arr_airport_buttons:
                        arr_airport_name = arr_airport.find_element(By.CLASS_NAME, "stationName").text
                        arr_airport_code = arr_airport.find_element(By.CLASS_NAME, "airport").text
                        if arr_airport_name=="":
                            continue
                        print(f"      도착 공항: {arr_airport_name} ({arr_airport_code})")
                        
                        arrival_airports[f"{arr_airport_name} ({arr_airport_code})"] = {
                            'name': arr_airport_name,
                            'code': arr_airport_code
                        }
                    
                except Exception as e:
                    print(f"Error processing arrival region tab {arr_region_name}: {str(e)}")
                    continue

            # 도착지 레이어 닫기
            try:
                close_button = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".layer-close"))
                )
                click_button_js(driver, close_button)
            except:
                webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()

            time.sleep(1)

            # 다시 출발지 선택 화면으로 돌아가기
            departure_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.start.js-target-pick"))
            )
            click_button_js(driver, departure_button)
            time.sleep(1)

            # 이전에 선택했던 출발지 지역 탭 다시 클릭
            click_button_js(driver, dep_region_button)
            time.sleep(1)

    except Exception as e:
        print(f"Error processing departure region tab {dep_region_name}: {str(e)}")
        continue

# 수집된 정보 출력
for dep_airport, arr_airports in departure_arrival_info.items():
    print(f"\n출발지: {dep_airport}")
    print("가능한 도착지:")
    for arr_airport in arr_airports.keys():
        print(f"  - {arr_airport}")

# 브라우저 종료
driver.quit()