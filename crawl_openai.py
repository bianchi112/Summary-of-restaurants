import openai
import pandas as pd
import os
import html
import sys
import re
from supabase import create_client
from datetime import date
from bs4 import BeautifulSoup

# OpenAI API 설정
openai.api_key = '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'

# Supabase 설정
supabase_url = 'https://odabskgeaohkxzxfdxrn.supabase.co'
supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9kYWJza2dlYW9oa3h6eGZkeHJuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTAyMjEzMzQsImV4cCI6MjAyNTc5NzMzNH0.rvqkMc_xr0wT05Ltdx6tE_j-kpdRvNPpu9yQzWDOvm0'
supabase = create_client(supabase_url, supabase_key)

# 파일 열기 또는 생성 함수
def open_or_create_file(file_path):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            pass  # 파일을 생성하고 아무 내용도 쓰지 않음
    return open(file_path, 'a')  # 추가 쓰기 모드로 열기

# blogURL.txt 파일에서 링크 읽기
def read_links_from_file(file_path):
    links = []
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            links = [line.strip() for line in f.readlines()]
    return links

# blogcrawl.csv 파일에서 데이터 읽기
def read_data_from_csv(file_path):
    df = pd.read_csv(file_path)
    return df['링크'].tolist(), df['제목'].tolist(), df['내용'].tolist()

# 중복되지 않는 첫 번째 링크, 제목, 내용 찾기
def find_first_unique_link(links_file, links_csv, titles_csv, contents_csv):
    unique_link = None
    unique_title = None
    unique_content = None
    for link, title, content in zip(links_csv, titles_csv, contents_csv):
        if link not in links_file:
            unique_link = link
            unique_title = title
            unique_content = content
            break
    return unique_link, unique_title, unique_content

# 파일 경로 설정
file_path_txt = 'blogURL.txt'
file_path_csv = 'blogcrawl.csv'

# blogURL.txt 파일에서 링크 읽기
links_file = read_links_from_file(file_path_txt)

# blogcrawl.csv 파일에서 데이터 읽기
links_csv, titles_csv, contents_csv = read_data_from_csv(file_path_csv)

# 중복되지 않은 첫 번째 링크, 제목, 내용 찾기
unique_link, unique_title, unique_content = find_first_unique_link(links_file, links_csv, titles_csv, contents_csv)

# 결과 출력
if unique_link:
    print("중복되지 않는 첫 번째 링크:", unique_link)
    print("제목:", unique_title)
    print("내용:", unique_content)

else:
    print("중복되지 않는 링크가 없습니다.")
    sys.exit()  # 프로그램 종료

# 요약 함수 정의
def summarize_text(unique_content):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0125",
        messages=[{"role": "system", "content": f"너는 맛집을 설명하는 사람입니다. 아래 내용에 대한 맛집 정보를 요약해주세요: {unique_content}"}],
        max_tokens=500
    )
    return response.choices[0].message['content'].strip()

# 요약된 내용을 저장할 변수
summarized_content = summarize_text(unique_content)

# HTML 태그를 제거하고 텍스트만 추출하는 함수
def remove_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

# unique_title에서 HTML 태그 제거하여 save_title에 저장
save_title = remove_html_tags(unique_title)
# HTML 엔터티 디코딩하여 title에 저장
save_title = html.unescape(remove_html_tags(unique_title))

# 출력
print("제목:", save_title)
print("요약된 내용:", summarized_content)

# Supabase에 데이터 추가
def add_data_to_supabase(title, content, link):
    # 오늘의 날짜 가져오기
    today = str(date.today())

    # 데이터 삽입
    response = supabase.table('blog').insert({'title': title, 'content': content, 'link': link, 'date': today}).execute()

    # 삽입 결과 확인
    if 'error' not in response:
        print("데이터가 성공적으로 추가되었습니다.")
    else:
        print("데이터를 추가하는 중에 문제가 발생했습니다.")

# Supabase에 데이터 추가하기
add_data_to_supabase(save_title, summarized_content, unique_link)

# unique_link를 blogURL.txt 파일에 추가
file = open_or_create_file(file_path_txt)
file.write(unique_link + '\n')
file.close()  # 파일을 사용한 후에는 명시적으로 닫아주기
