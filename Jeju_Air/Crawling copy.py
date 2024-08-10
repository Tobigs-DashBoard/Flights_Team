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
import json
# Chrome 옵션 설정
options = Options()
options.add_experimental_option("detach", True)  # 브라우저 창을 열린 상태로 유지

def click_button_js(driver, element):
    driver.execute_script("arguments[0].click();", element)

def get_base_url():
    driver = webdriver.Chrome(options=options)
    url = "https://www.jejuair.net/ko/ibe/booking/Availability.do"
    driver.get(url)  # 지정된 URL로 이동
    return driver

'''편도로 검색'''
def check_one_way_status(driver):
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
    


'''출발지 버튼 클릭'''
def click_departure_button(driver):
    try:
        departure_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.start.js-target-pick"))
        )
        click_button_js(driver, departure_button)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "depAirportLayer"))
        )
        dep_region_tabs = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#divDepArea .tab__button")))
    except TimeoutException:
        print("출발지 버튼을 찾는 데 시간이 초과되었습니다.")


def get_all_routes(driver):
    all_routes=[]
    # 출발지로 선택 가능한 지역 찾기
    dep_region_tabs = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#divDepArea .tab__button")))
    # 출발지 지역 탭에서 지역 선택
    for dep_region_tab in dep_region_tabs:
        try:
            dep_region_button = dep_region_tab.find_element(By.TAG_NAME, "button")
            dep_region_name = dep_region_button.text
            print(f"\n출발지 지역: {dep_region_name}")
            
            click_button_js(driver, dep_region_button)
            time.sleep(1)
            
            # 선택한 출발지 지역내의 선택가능한 공항들 찾기
            dep_airport_buttons = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".tab__panel.is-active .choise__button"))
            )
            # 출발지로 선택가능한 공항의 버튼 정보 가져오기 (공항 이름, 코드)
            for dep_airport in dep_airport_buttons:
                dep_airport_name = dep_airport.find_element(By.CLASS_NAME, "stationName").text
                dep_airport_code = dep_airport.find_element(By.CLASS_NAME, "airport").text
                if dep_airport_name=="":
                    continue
                print(f"  출발 공항: {dep_airport_name} ({dep_airport_code})")
                
                click_button_js(driver, dep_airport)
                time.sleep(1)
                
                # 도착지 버튼은 누를 필요 없음
                # arrival_button = WebDriverWait(driver, 10).until(
                #     EC.element_to_be_clickable((By.CSS_SELECTOR, "button.target.js-target-pick"))
                # )
                # click_button_js(driver, arrival_button)
                # time.sleep(1)
                
                # 도착지로 선택가능한 지역 찾기
                arr_region_tabs = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#divArrArea .tab__button"))
                )
                # 도착지 지역 탭에서 지역 선택
                for arr_region_tab in arr_region_tabs:
                    try:
                        arr_region_button = arr_region_tab.find_element(By.TAG_NAME, "button")
                        arr_region_name = arr_region_button.text
                        print(f"    도착지 지역: {arr_region_name}")
                        
                        click_button_js(driver, arr_region_button)
                        time.sleep(1)
                        
                        # 선택한 도착지 지역내의 선택가능한 공항들 찾기
                        arr_airport_buttons = WebDriverWait(driver, 5).until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".tab__panel.is-active .choise__button"))
                        )
                        # 도착지로 선택가능한 공항의 버튼 정보 가져오기 (공항 이름, 코드)
                        for arr_airport in arr_airport_buttons:
                            route={} # 경로 딕셔너리
                            arr_airport_name = arr_airport.find_element(By.CLASS_NAME, "stationName").text
                            arr_airport_code = arr_airport.find_element(By.CLASS_NAME, "airport").text
                            if arr_airport_name=="":
                                continue
                            print(f"      도착 공항: {arr_airport_name} ({arr_airport_code})")
                            
                            route['dep_region']=dep_region_name
                            route['dep_airport']=dep_airport_name
                            route['arr_region']=arr_region_name
                            route['arr_airport']=arr_airport_name
                            all_routes.append(route)
                        
                    except Exception as e:
                        print(f"지역 버튼 처리 중 오류 발생: {str(e)}")
                        continue

                # # 도착지 레이어 닫을 필요 없음
                # try:
                #     close_button = WebDriverWait(driver, 5).until(
                #         EC.presence_of_element_located((By.CSS_SELECTOR, ".layer-close"))
                #     )
                #     click_button_js(driver, close_button)
                # except:
                #     webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()

                # 다시 출발지 선택 화면으로 돌아가기
                departure_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.start.js-target-pick"))
                )
                click_button_js(driver, departure_button)
                time.sleep(1)

                # # 이전에 선택했던 출발지 지역 탭 다시 클릭 필요 없음
                # click_button_js(driver, dep_region_button)
                # time.sleep(1)

        except Exception as e:
            print(f"출발지 지역 처리 중 오류: {str(e)}")
            continue
    return all_routes
import json
def main():
    driver = get_base_url()
    check_one_way_status(driver)
    click_departure_button(driver)
    all_routes = get_all_routes(driver)
    driver.quit()
    with open('jeju_air_routes.json', 'w', encoding='utf-8-sig') as f:
        json.dump(all_routes, f, ensure_ascii=False, indent=4)
    
if __name__ == "__main__":
    main()