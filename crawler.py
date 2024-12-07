import json
from bs4 import BeautifulSoup
import csv
import re
from datetime import datetime

# JSON 파일 로드
try:
    with open('page_data.json', 'r', encoding='utf-8') as f:
        json_data = json.load(f)
        html_content = json_data['html']
except FileNotFoundError:
    print("Error: JSON 파일이 존재하지 않습니다.")
    exit()

# BeautifulSoup 객체 생성
soup = BeautifulSoup(html_content, 'html.parser')

# 데이터 추출 함수
def extract_reports(soup):
    """보고서 데이터 추출"""
    reports = soup.select("div.Business-layout a.Environ-item")
    data = []

    for report in reports:
        try:
            title = report.get_text(strip=True)
            link = report["href"]
            # 절대 경로 생성
            full_link = f"https://www.china-tcm.com.cn{link}" if link.startswith("/") else link

            # Annual Report인지 확인
            if "Annual Report" in title:
                report_date = extract_date_from_link(link)
                data.append({
                    "title": title,
                    "link": full_link,
                    "date": report_date
                })
        except Exception as e:
            print(f"Error extracting report: {e}")
    return data

# 링크에서 날짜 추출 함수
def extract_date_from_link(link):
    """링크에서 날짜 추출"""
    match = re.search(r"(\d{8})\d{6}", link)
    if match:
        date_str = match.group(1)
        try:
            # 날짜 형식을 YYYY-MM-DD로 변환
            return datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")
        except ValueError:
            return "N/A"
    return "N/A"

# CSV 파일 저장 함수
def save_to_csv(data, file_name="data.csv"):
    """CSV 파일로 저장"""
    try:
        with open(file_name, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["title", "date", "link"])
            writer.writeheader()
            writer.writerows(data)
        print(f"Data successfully saved to {file_name}")
    except IOError as e:
        print(f"File save error: {e}")

# 실행
data = extract_reports(soup)
if data:
    save_to_csv(data)
else:
    print("No Annual Reports found.")
