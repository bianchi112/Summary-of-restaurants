import urllib.parse
import time
import pandas as pd
import os
import re

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from tqdm import tqdm
from selenium.common.exceptions import NoSuchElementException

# 웹드라이버 설정
options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
options.add_argument("--log-level=3")  # 로그 레벨 설정 (불필요한 데이터 터미널 출력 제한)

# Headless 모드 설정 (chrome 백그라운드 실행)
options.add_argument("--headless")

# 직접 다운로드한 ChromeDriver 경로 지정 (현재 chrome 버전 확인 필요)
chromedriver_path = r'C:\chromedriver-win64\chromedriver.exe'
service = Service(chromedriver_path)
service.start()

# WebDriver 초기화
driver = webdriver.Chrome(options=options)

# Naver API 정보입력
client_id = "6aGecgk3kOKAT5RqdqK1"  # 발급받은 id 입력
client_secret = "PGDpvURadE"  # 발급받은 secret 입력

quote = input("검색어를 입력해주세요.: ")  # 검색어 입력받기
encText = urllib.parse.quote(quote)
display_num = input("검색 출력결과 갯수를 적어주세요.(최대100, 숫자만 입력): ")  # 출력할 갯수 입력받기

url = f"https://openapi.naver.com/v1/search/blog?query={encText}&display={display_num}"  # json 결과
request = urllib.request.Request(url)
request.add_header("X-Naver-Client-Id", client_id)
request.add_header("X-Naver-Client-Secret", client_secret)
response = urllib.request.urlopen(request)

if response.getcode() == 200:
    response_body = response.read()
    body = response_body.decode('utf-8')
    print(body)
else:
    print("Error Code:", response.getcode())

# body를 나누기
list1 = [i for i in body.split('\n\t\t{\n\t\t\t') if 'naver' in i]

# 블로그 제목, 링크 뽑기
titles = []
links = []
for i in list1:
    titles.append(re.findall('"title":"(.*?)",\n\t\t\t"link"', i)[0])
    links.append(re.findall('"link":"(.*?)",\n\t\t\t"description"', i)[0])

# 링크를 다듬기 (필요없는 부분 제거 및 수정)
blog_links = [i.replace('\\', '').replace('?Redirect=Log&logNo=', '/') for i in links]

print('<<제목 모음>>')
print(titles)
print('총 제목 수:', len(titles), '개')  # 제목 갯수 확인
print('\n<<링크 모음>>')
print(blog_links)
print('총 링크 수:', len(blog_links), '개')  # 링크 갯수 확인

# 파일 읽기
file_name = 'blogcrawl.csv'
if os.path.exists(file_name):
    existing_df = pd.read_csv(file_name)
    existing_links = existing_df['링크'].tolist()
else:
    existing_df = pd.DataFrame(columns=['제목', '링크', '내용'])
    existing_links = []

# 새로운 주소와 중복된 주소 카운트 초기화
new_links = [link for link in blog_links if link not in existing_links]
duplicate_count = len(blog_links) - len(new_links)

# 새로 추가된 주소가 없다면 메시지 출력 후 종료
if not new_links:
    print("새로 추가된 주소가 없습니다.")
    driver.quit()
    exit()

print(f"중복된 주소 갯수: {duplicate_count}개")
print(f"새로 추가된 주소 갯수: {len(new_links)}개")

# 중복되지 않은 주소만 이용하여 본문 크롤링 수행
new_contents = []
for i, link in enumerate(tqdm(new_links, desc="크롤링 진행 중")):
    driver.get(link)
    time.sleep(1)
    driver.switch_to.frame("mainFrame")
    try:
        content = driver.find_element(By.CSS_SELECTOR, 'div.se-main-container').text
    except NoSuchElementException:
        content = driver.find_element(By.CSS_SELECTOR, 'div#content-area').text
    new_contents.append(content)
    print(f"{i + 1}/{len(new_links)} 크롤링 진행 중")

# DataFrame 생성 및 저장
new_df = pd.DataFrame({'제목': titles[-len(new_contents):], '링크': new_links, '내용': new_contents})
df = pd.concat([existing_df, new_df], ignore_index=True)
df.to_csv(file_name, encoding='utf-8-sig', index=False)

driver.quit()  # 창 닫기
print("<<크롤링이 완료되었습니다.>>")
