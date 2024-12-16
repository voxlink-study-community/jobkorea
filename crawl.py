
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
import time
import json
import os
import functions as fc


# Output Directory 설정
output_dir = "output/test"  # 작업 디렉토리 이름
# Chrome 옵션 설정
options = webdriver.ChromeOptions()
options.add_argument('--no-sandbox')  # WSL 환경에서 필수
#options.add_argument('--disable-dev-shm-usage')  # 공유 메모리 비활성화
#options.add_argument('--headless')  # GUI가 필요 없는 경우W
#options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36") #ip막힐 시 proxy 활용
# ChromeDriver 경로 설정
service = Service('/usr/local/bin/chromedriver')
# WebDriver 실행 service=service,
driver = webdriver.Chrome( options=options)

def crawl_quit():
    driver.quit()

def crawl_href(max_pages):

    # 잡코리아 데이터사이언티스트+머신러닝엔지니어  홈페이지 열기
    driver.get('https://www.jobkorea.co.kr/recruit/joblist?menucode=duty')
    print("Page title:", driver.title)
    time.sleep(1)

    # 첫 번째 단계: groupName이 '개발·데이터'인 요소를 클릭
    group_name_element = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//li[@class='item' and contains(@data-value-json, '\"groupName\":\"개발·데이터\"')]"))
    )
    group_name_element.click()

    # 대기: 콘텐츠가 동적으로 로드되기를 기다림
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//li[@class='item' and contains(@data-value-json, '\"subName\":\"데이터사이언티스트\"')]"))
    )

    # XPath를 사용하여 체크박스를 찾고 클릭
    # XPath로 input 태그 찾기

    # data-name="데이터사이언티스트"
    checkbox_datascientist = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@type='checkbox' and @data-name='데이터사이언티스트']"))
    )
    driver.execute_script("arguments[0].click();", checkbox_datascientist)

    time.sleep(0.5)
    # data-name="머신러닝엔지니어"
    checkbox_mlengineer = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@type='checkbox' and @data-name='머신러닝엔지니어']"))
    )
    driver.execute_script("arguments[0].click();", checkbox_mlengineer)


    time.sleep(0.5)

    # 기존 innerHTML 상태 저장
    previous_state = driver.find_element(By.ID, "dev-gi-list").get_attribute("innerHTML")

    # 'dev-btn-search' 버튼을 클릭
    search_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "dev-btn-search"))
    )
    search_button.click()
    time.sleep(0.5)

    # # innerHTML의 변화를 기다림
    WebDriverWait(driver, 10).until(
        lambda d: d.find_element(By.ID, "dev-gi-list").get_attribute("innerHTML") != previous_state
    )
    # id가 'dev-gi-list'인 div 태그 내부에서 href 값 추출
    href_list = []

    # 페이지 넘김 로직
    pagination_id = "dvGIPaging"

    # 최대 페이지 개수를 설정 (필요에 따라 동적으로 계산)
    max_pages = 17  # 예시로 5페이지만 처리

    for j in range(max_pages):
        print('='*30)
        print(f'현재 페이지: {j+1}')
        if j+1 > 1:
            try:
                if (j + 1) % 10 != 0:
                    # data-page의 값이 j+2인 요소를 클릭
                    next_page_element = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, f"//div[@id='{pagination_id}']//a[@data-page='{j+2}']"))
                    )
                    next_page_element.click()
                    time.sleep(2)  # 페이지가 로드되도록 대기

                else:
                    # 10의 배수일 경우 다음 그룹으로 이동
                    next_group_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, f"//div[@id='{pagination_id}']//a[contains(@class, 'tplBtn btnPgnNext')]"))
                    )
                    next_group_button.click()
                    print(f"다음 그룹으로 이동 (페이지 {j+2})")
                    
            except TimeoutException:
                print(f"페이지 {j+2}를 찾을 수 없습니다(현재 마지막 페이지입니다.)")
                

        # 현재 페이지에서 href 값을 수집
        a_elements = driver.find_elements(By.XPATH, "//div[@id='dev-gi-list']//tr//td[@class='tplTit']//a[@href]")
        for i, a_element in enumerate(a_elements):
            href = a_element.get_attribute("href")
            href_list.append(href)
            print(f"추출된 href ({i+1}/{len(a_elements)}): {href}")

    print(f"총 {len(href_list)}개의 href가 추출되었습니다.")
    

    return href_list

def crawl_pages(i, url):
    
    # 데이터 수집
    all_text_data = []
    all_table_data = []
    all_data = []
    batch_size = 40  # 한 번에 저장할 데이터 개수
    batch_index = 0  # 저장 배치 인덱스

    # for문
    # iframe에 접근
    driver.get(url)
    print(f"페이지 제목: {driver.title}")
    # 데이터 초기화
    article_text = "N/A"
    extracted_table_data = []

    # id가 'gib_frame'인 iframe을 찾아 전환
    try:
        iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "gib_frame"))
        )
        driver.switch_to.frame(iframe)
        print("id='gib_frame'인 iframe으로 전환 완료.")
            
        # 테이블 데이터 추출
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//table"))
            )
            tables = driver.find_elements(By.TAG_NAME, "table")
            for table_index, table in enumerate(tables):
                rows = table.find_elements(By.XPATH, ".//tr")
                table_data = []
                for row in rows:
                    row_data = []
                    cells = row.find_elements(By.XPATH, ".//td | .//th")
                    for cell in cells:
                        try:
                            cell_text = cell.get_attribute("innerText").strip()
                            row_data.append(cell_text if cell_text else "N/A")
                        except StaleElementReferenceException:
                            row_data.append("N/A")
                    table_data.append(row_data)
                extracted_table_data.append({
                    "table_index": table_index,
                    "table_data": table_data
                })

        #gib_frame으로 처리하지만 table 형 데이터가 아닌 것 ->이미지
        except TimeoutException:
            print("페이지에 테이블이 없습니다.")
            # 이미지 데이터 처리 vision API

    except TimeoutException: #gib_frame으로 다루지 않음, article 안에 정보가 있는 경우
        print("id='gib_frame'인 iframe이 존재하지 않습니다. 메인 페이지에서 데이터 추출 시도.")
            
        # article 데이터 추출
        try:
            article_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//article[contains(@class, 'view-content') and contains(@class, 'view-detail') and contains(@class, 'dev-wrap-detailContents')]"))
            )
            article_text = article_element.text.strip()
            print("article 태그 내용 추출 성공")
        except TimeoutException:
            print("해당 클래스명을 가진 article 태그를 찾을 수 없습니다.")


    # iframe에서 메인 페이지로 돌아오기
    driver.switch_to.default_content()
    time.sleep(1)

    # class='tbCol tbCoInfo'의 dl 태그 데이터 추출
    company_info = []
    try:
        cname_element = driver.find_element(By.ID, "hdnBrazeEventProperties")
        cname_value = cname_element.get_attribute("value")
        if cname_value.split('|')[0]=="":
            cname = cname_value.split('|')[1]
        else:
            cname = cname_value.split('|')[0]
    except (IndexError, AttributeError):
        cname = "N/A"
        print('기업명 추출불가')

    info_dict = {"기업명": cname}

    try:
        info_div = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'tbCol.tbCoInfo'))
        )
        dl_elements = info_div.find_elements(By.TAG_NAME, 'dl')
        for dl in dl_elements:
            dt = dl.find_element(By.TAG_NAME, 'dt').text.strip()
            dd = dl.find_element(By.TAG_NAME, 'dd').text.strip()
            info_dict[f"{dt}"] = dd  # dict에 데이터 추가
    except TimeoutException:
        try:
            recruit_data_div = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'recruit-data'))
        )
            dl_elements = recruit_data_div.find_elements(By.TAG_NAME, 'dl')
            for dl in dl_elements:
                dt = dl.find_element(By.TAG_NAME, 'dt').text.strip()
                dd = dl.find_element(By.TAG_NAME, 'dd').text.strip()
                info_dict[f"{dt}"] = dd  # dict에 데이터 추가
        except:
            print("company_info 데이터를 추출할 수 없습니다.")
    company_info.append(info_dict)
    
    # 수집된 데이터를 딕셔너리로 저장
    page_data = {
        "title": driver.title,
        "url": url,
        "article_text": article_text,
        "tables": extracted_table_data,
        "company_info": company_info
    }

    return page_data
    


        

       
        

        

    time.sleep(7)

    driver.quit()
