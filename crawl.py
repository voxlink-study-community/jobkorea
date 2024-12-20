from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
import time
import json
import os
import functions as fc
import random
import base64
import cv2
import numpy as np
from google.cloud import vision
from dotenv import load_dotenv


# .env 파일 로드
load_dotenv()

# GOOGLE_APPLICATION_CREDENTIALS 경로 가져오기
credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

os.environ["GRPC_DNS_RESOLVER"] = "native"
os.environ["GRPC_ENABLE_IPV4"] = "true"

if credentials_path:
    # 환경 변수 설정
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
    print(f"Using credentials from: {credentials_path}")


# Chrome 옵션 설정
options = webdriver.ChromeOptions()
options.add_argument('--no-sandbox')  # WSL 환경에서 필수
#options.add_argument('--disable-dev-shm-usage')  # 공유 메모리 비활성화
#options.add_argument('--headless')  # GUI가 필요 없는 경우W

#jobkorea 보안코드 대비
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36") #ip막힐 시 proxy 활용
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-infobars")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

# ChromeDriver 경로 설정
service = Service('/usr/local/bin/chromedriver')
# WebDriver 실행 service=service,
driver = webdriver.Chrome( options=options)

stealth(driver, #chrome://gpu/에서 GPU정보 확인 가능
        languages=["ko-KR", "ko"],  # "en-US", "en"->필요에 따라 "ko-KR", "ko"로 변경 가능
        vendor="Google Inc.",  # GPU 정보에서 확인한 벤더
        platform="Linux x86_64",  # 현재 운영 체제
        webgl_vendor="Google Inc. (Microsoft Corporation)",  # GPU 정보에서 확인한 값
        renderer="ANGLE (Microsoft Corporation, D3D12 (NVIDIA GeForce GTX 1060 3GB), OpenGL 4.2 (Core Profile) Mesa 23.2.1-1ubuntu3.1~22.04.2)",  # 정확한 렌더러 정보
        fix_hairline=False  # 픽셀 보정 비활성화
)

url=""
i=0

def crawl_quit():
    driver.quit()

def setup_driver_with_proxy(proxy_list):
    global driver
    if driver:
        driver.quit()  # 기존 드라이버 종료

    proxy_ip_port = random.choice(proxy_list)

    options.add_argument(f'--proxy-server={proxy_ip_port}')

    # 드라이버 생성
    driver = webdriver.Chrome(options=options)
    print(f"New driver created with proxy: {proxy_ip_port}")

def get_captcha_text_with_preprocessing(driver):
    try:
        # imgCaptcha 요소 찾기
        img_element = driver.find_element(By.ID, "imgCaptcha")
        img_base64 = img_element.screenshot_as_base64  # 이미지를 Base64로 캡처

        # Base64 이미지를 OpenCV로 디코딩
        img_data = base64.b64decode(img_base64)
        np_arr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # 원본 이미지 저장 (디버깅용)
        if not os.path.exists('img'):
            os.mkdir('img')
        img_created_time = f"{time.localtime().tm_mon}{time.localtime().tm_mday}{time.localtime().tm_hour}{time.localtime().tm_min}{time.localtime().tm_sec}"
        original_image_path = f"img/captcha_original{img_created_time}.png"
        cv2.imwrite(original_image_path, img)

        # 기존 전처리: 흑백 변환
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
        denoised = cv2.medianBlur(binary, 3)

        # 기존 전처리 결과 저장
        old_preprocessed_path = f"img/captcha_old_preprocessed{img_created_time}.png"
        cv2.imwrite(old_preprocessed_path, denoised)

        # 개선된 전처리: 이진화, Morphological Operations, Edge Detection
        def enhanced_preprocessing(img):
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            edges = cv2.Canny(cleaned, 100, 200)
            return edges

        enhanced = enhanced_preprocessing(img)

        # 개선된 전처리 결과 저장
        enhanced_preprocessed_path = f"img/captcha_enhanced_preprocessed{img_created_time}.png"
        cv2.imwrite(enhanced_preprocessed_path, enhanced)

        # Vision API로 전달할 이미지 설정
        def get_text_from_image(image):
            _, img_buffer = cv2.imencode('.png', image)
            img_base64 = base64.b64encode(img_buffer).decode('utf-8')

            client = vision.ImageAnnotatorClient()
            vision_image = vision.Image(content=base64.b64decode(img_base64))

            # Vision API로 텍스트 추출
            response = client.text_detection(image=vision_image)
            if response.error.message:
                raise Exception(f"Google Vision API Error: {response.error.message}")

            # 텍스트 추출 및 정제
            extracted_text = response.text_annotations[0].description if response.text_annotations else "텍스트를 추출하지 못했습니다."
            extracted_text = extracted_text.replace("\n", "").strip()[:6]  # 개행 문자 제거 및 앞 6문자 추출
            return extracted_text

        # 개선된 전처리 이미지에서 텍스트 추출
        enhanced_text = get_text_from_image(enhanced)
        print(f"Vision API 개선 전처리 추출 결과: {enhanced_text}")

        # 기존 전처리 이미지에서 텍스트 추출
        old_text = get_text_from_image(denoised)
        print(f"Vision API 기존 전처리 추출 결과: {old_text}")

        # 개선된 전처리 결과 반환
        return old_text

    except Exception as e:
        print(f"Captcha 처리 실패: {e}")
        return None

def solve_captcha(driver, captcha_text):
    try:
        # 보안 코드 입력 필드 찾기
        input_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "txtInputText"))
        )
        
        # 보안 코드 입력
        input_field.clear()  # 기존 내용 삭제
        input_field.send_keys(captcha_text)  # 반환된 텍스트 입력
        print(f"보안 코드 입력: {captcha_text}")

        # 확인 버튼 클릭
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "btnInput"))
        )
        submit_button.click()
        print("보안 코드 제출 버튼 클릭 완료.")
        
        

    except Exception as e:
        print(f"보안 코드 처리 중 오류 발생: {e}")

def handle_captcha(driver, url,i, retry_count, max_retries, crawl_function, *args):
    """
    보안 코드 페이지를 처리하고 재시도하는 공통 함수.

    Parameters:
        driver: Selenium WebDriver 객체
        url: 처리 중인 URL
        retry_count: 현재 재시도 횟수
        max_retries: 최대 재시도 허용 횟수
        crawl_function: 재시도할 크롤링 함수
        *args: 크롤링 함수에 전달할 추가 인자

    Returns:
        크롤링 함수의 반환값 또는 None
    """
    if retry_count > max_retries:
        print(f"최대 재시도 횟수를 초과했습니다. URL {url} 처리 불가.")
        return None

    print(f"handle_captcha 호출됨: args={args}")

    try:
        # "계속 진행하기" 버튼 탐지 및 클릭
        continue_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "step1_5"))
        )
        continue_button.click()
        print("계속 진행하기 버튼 클릭 완료.")

        # 버튼 클릭 후 보안 코드 입력 화면이 로드되었는지 확인
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "txtInputText"))  # 보안 코드 화면의 특정 요소
        )
        print("보안 코드 화면 로드 완료. 다시 페이지 로드 중...")

        # 보안 코드 처리
        captcha_text = get_captcha_text_with_preprocessing(driver)
        print(f"Vision API에서 추출한 보안 코드: {captcha_text}")

        if captcha_text:
            solve_captcha(driver, captcha_text)

            # 보안 코드 처리 후 크롤링 함수 재시도
            print("보안 코드 입력 완료. 페이지 다시 로드 중...")
            return crawl_function(i, url, retry_count=retry_count + 1, max_retries=max_retries)
        else:
            print("보안 코드 인식 실패.")
            return None

    except (NoSuchElementException, TimeoutException) as e:
        print(f"보안 코드 처리 중 오류 발생: {e}")
        return None

def crawl_href(max_pages, retry_count=0, max_retries=3):
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
    max_pages = 17  # 17페이지로 설정(현재까지 모든 경우가 17페이지가 끝)

    for j in range(max_pages):
        print('='*30)
        print(f'현재 페이지: {j+1}')
    
        # 현재 페이지에서 href 값을 수집
        a_elements = driver.find_elements(By.XPATH, "//div[@id='dev-gi-list']//tr//td[@class='tplTit']//a[@href]")
        for i, a_element in enumerate(a_elements):
            href = a_element.get_attribute("href")
            href_list.append(href)
            print(f"추출된 href ({i+1}/{len(a_elements)}): {href}")

        if j==0:
            next_page_element = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, f"//div[@id='{pagination_id}']//a[@data-page='{j+2}']"))
                        )
            next_page_element.click()
            time.sleep(2)  # 페이지가 로드되도록 대기
        
        if j > 0:
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

    print(f"총 {len(href_list)}개의 href가 추출되었습니다.")
    

    return href_list
#보안페이지 대비
    # except TimeoutException:
    #     print("보안 페이지인 경우 보안코드 입력 페이지로 이동하는 버튼을 누릅니다.")
    #     return handle_captcha(
    #     driver=driver,
    #     url=url,
    #     i=i,
    #     retry_count=retry_count,
    #     max_retries=max_retries,
    #     crawl_function=crawl_pages  # 해당 크롤링 함수 전달
    # )            


def crawl_pages(i, url, retry_count=0, max_retries=3):
    url=url
    i=i
    if retry_count > max_retries:
        print(f"최대 재시도 횟수를 초과했습니다. URL {url} 처리 불가.")
        return None
    # for문
    # iframe에 접근
    try:
        driver.get(url)
        print(f"페이지 제목: {driver.title}")
        # 데이터 초기화
        article_text = "N/A"
        extracted_table_data = []

        # id가 'gib_frame'인 iframe을 찾아 전환
        try:
            iframe = WebDriverWait(driver, 30).until(
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
                                print("Table 쪽 StaleElementReferenceException")
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
        time.sleep(random.uniform(0.5, 1.5))  

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
            # dl 요소 가져오기
            dl_element = info_div.find_element(By.TAG_NAME, 'dl')  # 단일 dl 요소 가져오기

            # dt와 dd 요소 가져오기
            dt_elements = dl_element.find_elements(By.TAG_NAME, 'dt')  # dl 내부의 모든 dt 요소
            dd_elements = dl_element.find_elements(By.TAG_NAME, 'dd')  # dl 내부의 모든 dd 요소

            # dt와 dd 쌍으로 데이터 추가
            for dt, dd in zip(dt_elements, dd_elements):
                dt_text = dt.text.strip()
                dd_text = dd.text.strip()
                info_dict[dt_text] = dd_text  # dict에 데이터 추가
        except TimeoutException:
            try:
                recruit_data_div = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'recruit-data'))
            )
                dl_element = recruit_data_div.find_element(By.TAG_NAME, 'dl')
                # dt와 dd 요소 가져오기
                dt_elements = dl_element.find_elements(By.TAG_NAME, 'dt')  # dl 내부의 모든 dt 요소
                dd_elements = dl_element.find_elements(By.TAG_NAME, 'dd')  # dl 내부의 모든 dd 요소

                 # dt와 dd 쌍으로 데이터 추가
                for dt, dd in zip(dt_elements, dd_elements):
                    dt_text = dt.text.strip()
                    dd_text = dd.text.strip()
                    info_dict[dt_text] = dd_text  # dict에 데이터 추가
            except:
                print("company_info 데이터를 추출할 수 없습니다.")

        skill_list = []  # 함수 시작 시 초기화
        try:
            # 스킬 정보를 추출하기 위한 기준 위치 찾기
            job_summary = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "artReadJobSum"))
            )
            # dl 태그 찾기
            dl_element = job_summary.find_element(By.CLASS_NAME, "tbList")
            
            # dt와 dd 요소 가져오기
            dt_elements = dl_element.find_elements(By.TAG_NAME, "dt")
            dd_elements = dl_element.find_elements(By.TAG_NAME, "dd")

            for dt, dd in zip(dt_elements, dd_elements):
                dt_text = dt.text.strip()
                dd_text = dd.text.strip()

                # '스킬' 항목 처리
                if dt_text == "스킬":
                    skill_list = [skill.strip() for skill in dd_text.split(",")]
                    break  # 스킬 항목을 찾았으므로 루프 종료

        except (TimeoutException, UnboundLocalError) :
            print("스킬 정보를 포함한 artReadJobSum을 찾을 수 없습니다.")
            skill_list = []
        company_info.append(info_dict)
        
        # 수집된 데이터를 딕셔너리로 저장
        page_data = {
            "title": driver.title,
            "company_info": company_info,
            "url": url,
            "stack": skill_list,
            "article_text": article_text,
            "tables": extracted_table_data,
            
        }

        return page_data

    except Exception as e:
        print(f"가장 바깥쪽에서 포착된 에러: {type(e).__name__}, {e}")
        print("보안 페이지인 경우 보안코드 입력 페이지로 이동하는 버튼을 누릅니다.")
        return handle_captcha(
        driver=driver,
        url=url,
        i=i,
        retry_count=retry_count,
        max_retries=max_retries,
        crawl_function=crawl_pages # 해당 크롤링 함수 전달
    )

    time.sleep(7)

    driver.quit()
