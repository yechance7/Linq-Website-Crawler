import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
import os
import csv


# 기본 설정
BASE_URL = "https://www.china-tcm.com.cn"
DOWNLOAD_DIR = Path("./downloads")
CSV_FILE = DOWNLOAD_DIR / "data.csv"

# 폴더 생성
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 방문한 링크 추적
visited_links = set()
pdf_data = []


# PDF 다운로드 함수 (크롤러용)
def download_pdf_from_crawler(pdf_url, title):
    file_name = os.path.basename(urlparse(pdf_url).path)
    local_file_path = DOWNLOAD_DIR / file_name

    try:
        response = requests.get(pdf_url, stream=True)
        if response.status_code == 200:
            with open(local_file_path, "wb") as file:
                file.write(response.content)

            date = extract_date_from_url(pdf_url)
            pdf_data.append({
                "title": title if title else "No Title",
                "date": date,
                "link": str(local_file_path.resolve())
            })

            print(f"다운로드 완료: [{file_name}]")
    except Exception:
        pass


# 날짜 추출 함수
def extract_date_from_url(url):
    segments = urlparse(url).path.split("/")
    for seg in segments:
        if seg.startswith("2024"):
            return seg[:8]
    return "Unknown"


# 크롤러 함수
def crawl(url):
    if url in visited_links:
        return

    visited_links.add(url)

    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        for link in soup.find_all("a", href=True):
            href = link["href"]
            absolute_url = urljoin(url, href)

            if absolute_url.endswith(".pdf") and "2024" in absolute_url:
                download_pdf_from_crawler(absolute_url, link.get_text(strip=True))

            if href.startswith("/") and not href.startswith(("javascript:", "#")):
                crawl(absolute_url)

    except Exception:
        pass


def save_to_csv(datas: list[dict], save_path: Path):
    save_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, 'w', newline='', encoding='utf-8') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(['Title', 'Date', 'File Path'])

        for data in datas:
            filename = data['link'].split('/')[-1]
            file_path = str(save_path.parent / filename)
            csv_writer.writerow([data['title'], data['date'], file_path])


# 크롤링 및 데이터 수집 시작
start_url = urljoin(BASE_URL, "/en/Investor/Announce")
crawl(start_url)
save_to_csv(pdf_data, CSV_FILE)
