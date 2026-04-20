import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
import re
import datetime
import os

def scrape_wuzzuf(job_title, num_pages=2):
    jobs_data = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    for page in range(num_pages):
        url = f"https://wuzzuf.net/search/jobs/?q={job_title.replace(' ', '+')}&start={page}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            job_cards = soup.find_all("div", class_="css-pkv5jc")
            
            for card in job_cards:
                title = card.find("h2", class_="css-193uk2c")
                company = card.find("a", class_="css-ipsyv7")
                location = card.find("span", class_="css-16x61xq")
                
                exp_span = card.find(lambda tag: tag.name == "span" and "Yrs of Exp" in tag.text)
                raw_exp = exp_span.text.replace("·", "").strip() if exp_span else "0"
                nums = re.findall(r'\d+', raw_exp)
                exp_clean = f"{nums[0]}-{nums[1]}" if len(nums) == 2 else (f"{nums[0]}+" if len(nums) == 1 else "0")
                
                skills_tags = card.find_all("a", class_=["css-5x9pm1", "css-o171kl"])
                skills_list = [tag.text.replace("·", "").strip() for tag in skills_tags if "Yrs of Exp" not in tag.text]
                
                jobs_data.append({
                    "Job Title": title.text.strip() if title else None,
                    "Company": company.text.strip().replace(" -", "") if company else None,
                    "Location": location.text.strip() if location else None,
                    "Experience": exp_clean,
                    "Skills": ", ".join(skills_list),
                    "Scrape_Date": datetime.datetime.now().strftime("%Y-%m-%d")
                })
        except Exception as e:
            print(f"Error scraping {job_title} on page {page}: {e}")
            
    return pd.DataFrame(jobs_data).dropna(subset=['Job Title', 'Company']).drop_duplicates()

def save_to_db(df, db_name="wuzzuf_data.db"):
    if df.empty:
        return 0
    conn = sqlite3.connect(db_name)
    try:
        existing_df = pd.read_sql_query("SELECT * FROM jobs", conn)
        merged = df.merge(existing_df, on=["Job Title", "Company", "Location"], how="left", indicator=True)
        new_records = merged[merged["_merge"] == "left_only"].drop(columns=["_merge"])
        cols_to_keep = ["Job Title", "Company", "Location", "Experience_x", "Skills_x", "Scrape_Date_x"]
        new_records = new_records[cols_to_keep].rename(columns={
            "Experience_x": "Experience", "Skills_x": "Skills", "Scrape_Date_x": "Scrape_Date"
        })
    except:
        new_records = df

    if not new_records.empty:
        new_records.to_sql("jobs", conn, if_exists="append", index=False)
    
    count = len(new_records)
    conn.close()
    return count

if __name__ == "__main__":
    print("🚀 Running Automated Pipeline...")
    track_file = "jobs_to_track.txt"
    if os.path.exists(track_file):
        with open(track_file, "r") as f:
            targets = [line.strip() for line in f.read().splitlines() if line.strip()]
    else:
        targets = ["Data Engineer"] 

    for target in targets:
        print(f"🔍 Processing: {target}")
        data = scrape_wuzzuf(target, num_pages=2)
        added = save_to_db(data)
        print(f"✅ Added {added} new records for {target}")