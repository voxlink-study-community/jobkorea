from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from google.cloud import vision
from dotenv import load_dotenv
import requests
import os
# .env 파일에서 환경 변수 로드
load_dotenv()
# Google Cloud Vision API 키 환경 변수 설정
google_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not google_credentials_path:
    raise Exception("환경 변수 'GOOGLE_APPLICATION_CREDENTIALS'가 설정되지 않았습니다.")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_credentials_path
# Selenium WebDriver 초기화
driver = webdriver.Chrome()
# 대상 URL 열기
url = "https://www.jobkorea.co.kr/Recruit/GI_Read/46099529?rPageCode=SL&logpath=21&sn=6"
driver.get(url)
try:
    # iframe 대기 및 전환
    iframe = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "gib_frame"))
    )
    driver.switch_to.frame(iframe)
    print("id='gib_frame'인 iframe으로 전환 완료.")
    # 특정 이미지 요소 찾기
    img_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//p[@class='visual ct']/img"))
    )
    # 이미지 URL 추출
    img_src = img_element.get_attribute("src")
    print(f"추출된 이미지 URL: {img_src}")
    # Selenium에서 쿠키 가져오기
    cookies = driver.get_cookies()
    cookie_header = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
    # 헤더 설정
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Cookie": cookie_header,
    }
    # 이미지 다운로드
    response = requests.get(img_src, headers=headers, stream=True)
    response.raise_for_status()  # 요청이 성공하지 않으면 예외 발생
    # 다운로드된 이미지 저장
    with open("downloaded_image.jpg", "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print("이미지가 로컬에 저장되었습니다. 'downloaded_image.jpg' 파일 확인!")
    # Google Vision API를 사용하여 OCR 처리
    with open("downloaded_image.jpg", "rb") as image_file:
        image_content = image_file.read()
    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=image_content)
    response = client.text_detection(image=image)
    # OCR 결과 출력
    if response.error.message:
        print(f"Google Vision API 에러: {response.error.message}")
    else:
        texts = response.text_annotations
        if texts:
            print("OCR 추출 텍스트:")
            print(texts[0].description)  # 첫 번째 결과는 전체 텍스트
        else:
            print("텍스트를 추출할 수 없습니다.")
except Exception as e:
    print(f"오류 발생: {str(e)}")
finally:
    driver.quit()