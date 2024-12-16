from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json
# WebDriver 초기화
driver = webdriver.Chrome()

# 웹 페이지로 이동
driver.get("https://www.jobkorea.co.kr/recruit/joblist?menucode=duty")  

# 웹 페이지 창 최대화
#driver.maximize_window()                                
driver.implicitly_wait(5) # seconds
driver.find_element(By.XPATH, '//*[@id="devSearchForm"]/div[2]/div/div[1]/dl[1]/dd[2]/div[2]/dl[1]/dd/div[1]/ul/li[6]/label/span/span').click()


# 데이터사이언스, 머신러닝 엔지니어링 버튼 클릭 
xpaths = ['//*[@id="duty_step2_10031_ly"]/li[9]/label/span/span','//*[@id="duty_step2_10031_ly"]/li[14]/label/span/span']
for xpath in xpaths:
    element = WebDriverWait(driver, 4).until(
    EC.presence_of_element_located((By.XPATH, xpath)) #안보이는 부분을 검색하기위해 presence_of_element_located를 활용  
)
    driver.execute_script("arguments[0].click();", element) # 검색완료를 누르게함(안보이는 부분이라 자바스크립트를 강제로 누를 수 있는 execute_script를 활용)

before_text = driver.find_element(By.XPATH, '//*[@id="dev-gi-list"]').text

# 검색버튼 클릭 
driver.find_element(By.XPATH, '//*[@id="dev-btn-search"]/span').click()

# 검색버튼 이전 텍스트와 이후 텍스트 비교를 통해 검색버튼 활성화 여부 비교
time.sleep(3)

# url 추출(헤드헌팅 기업 url과 파견대행 기업 url 제외, only 검색결과 url 추출(40개))
elements = driver.find_elements(By.XPATH, '//*[@id="dev-gi-list"]//a[@class="link normalLog"]')

href_values = [element.get_attribute("href") for element in elements]

# 짝수번호가 기업공고이고, 홀수번호가 기업정보이므로 짝수번호 추출
urls = href_values[1:10:2]
   
  # URL로 이동
all_table_data = []
for url in urls:
    driver.get(url)

    # url로 들어갔을 때, dimension66 값을 확인함 
    dimension66_value = driver.execute_script("return pageviewObj['dimension66']")
    print(dimension66_value)
    try:
        if dimension66_value =="일반기업":
            co_name = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((
                By.XPATH, '//*[@id="tab03"]/article[1]/div/div[2]/h4'))
            )  
            co_name = co_name.text 
            # co_type = WebDriverWait(driver, 15).until(
            # EC.presence_of_element_located((
            #     By.XPATH, '//*[@id="container"]/section/div[1]/article/div[2]/div[3]/dl/dd[4]'))
            # ) 
            # iframe 전환(전환하지 않으면 접근 불가함)
            WebDriverWait(driver, 10).until(
        EC.frame_to_be_available_and_switch_to_it((By.ID, "gib_frame")))
    

    # iframe 안의 내용을 가져오기
            html_content = driver.page_source

            soup = BeautifulSoup(html_content, 'html.parser')
# 회사이름 
            

# 테이블 찾기
            table = soup.find('table')

# 모든 tr 가져오기
            rows = table.find_all('tr')
            table_data = []
            for row in rows:
                try: 
                    cells = row.find_all(['td', 'th'])  # td와 th 모두 포함
                    cell_texts = [cell.get_text(strip=True) for cell in cells]              # 텍스트 추출
                    table_data.append(cell_texts)
                    print("테이블 데이터:")
                    print(table_data)
                    
                    for row_data in table_data:
                        
                        print(row_data)
                except Exception as e:
                    print("no data")
            company_data = {
                "기업":co_name,
                #"유형":co_type
                "table_data":table_data,
                "URL":url}  
            print("table_data 완료")
            all_table_data.append(company_data)     

        elif dimension66_value == "원픽공고":
            element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="wrap"]/main/section[2]/article[2]/div/ul')))
            co_name = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="wrap"]/main/div[1]/a')))
            co_name = co_name.text
            print(element.text)
            table_data = element.text
            company_data = {
                "기업":co_name,
                "table_data":table_data}  
        else: 
            print("해당공고없음")
    except Exception as e: 
        print("crawling error")
        
with open('5company_data.json', 'w', encoding='utf-8') as f:
    json.dump(all_table_data, f, ensure_ascii=False, indent=4)