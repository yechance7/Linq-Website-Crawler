import requests
from bs4 import BeautifulSoup
import json

# 웹 페이지 요청
url = 'https://www.china-tcm.com.cn/en/Investor/Report'
response = requests.get(url)

# HTML 소스 확인
html_content = response.text

# BeautifulSoup 파싱
soup = BeautifulSoup(html_content, 'html.parser')

# JSON 파일로 저장
data = {'html': soup.prettify()}
with open('page_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
