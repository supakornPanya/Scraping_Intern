from dotenv import load_dotenv
import requests
import pandas as pd
import time
import random
import os
import streamlit as st

def scraping_Paginated(Start_Page=1, End_Page=16, Limit=20, Output_Filename="cedt_intern_data_paginated.csv", cookie_value=None):
    print(f"Cookie loaded: {cookie_value[:50]}..." if cookie_value else "Cookie is None!")
    if not cookie_value:
        raise ValueError("COOKIE not found in .env file!")

    # ==========================================
    # 1. การตั้งค่า (Configuration)
    # ==========================================
    START_PAGE = Start_Page
    END_PAGE = End_Page
    LIMIT = Limit
    OUTPUT_FILENAME = Output_Filename

    # URL พร้อม Query Parameters (เว้น page ไว้ใส่ค่า)
    API_URL_TEMPLATE = "https://cedtintern.cp.eng.chula.ac.th/api/sessions/5/openings?search=&page={}&limit={}&onlyBookmarked=false&onlyAvailablePositions=false"

    # *** ใส่ Cookie ของคุณที่นี่ ***
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Cookie": cookie_value
    }

    all_job_data = []
    temp_log = []

    # ==========================================
    # 2. เริ่มการวนลูปทีละหน้า (Pagination Loop)
    # ==========================================
    print(f"Starting scraping pages {START_PAGE} to {END_PAGE}...")
    st.write(f"Starting scraping pages {START_PAGE} to {END_PAGE}...")
    idx = 0
    progress_bar = st.progress(0)

    for page in range(START_PAGE, END_PAGE + 1):
        # สร้าง URL โดยใส่เลขหน้าและ limit
        url = API_URL_TEMPLATE.format(page, LIMIT)
        
        try:
            print(f"Fetching Page {page}...", end=" ")
            response = requests.get(url, headers=HEADERS, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                temp_log.append(f"[PAGE {page}] Found {len(items)} items.")
                
                # วนลูปดึงข้อมูลย่อยในแต่ละ Page (Iterate items in page)
                for item in items:
                    # Mapping ข้อมูลให้ชื่อ Column ตรงกับไฟล์ CSV เก่า
                    job_info = {
                        "id": item.get("openingId"),
                        "company_nameTh": item.get("company", {}).get("companyNameTh"),
                        "company_nameEn": item.get("company", {}).get("companyNameEn"),
                        "position_title": item.get("title"),
                        "quota": item.get("quota"),
                        "salary_amount": item.get("compensationAmount"),
                        # จัดการกรณี salary_type อาจเป็น None
                        "salary_type": item.get("compensationType", {}).get("compensationType") if item.get("compensationType") else None,
                        "work_type": item.get("workingCondition"),
                        "location": item.get("officeName"),
                        # รวม Tags
                        "Start Date": item.get("startDate"),
                        "End Date": item.get("endDate"),
                        "inStudentDraftCount": item.get("inStudentDraftCount"),
                        "tags": ", ".join([t['tagName'] for t in item.get("tags", [])]),
                        "description_html": item.get("description"),
                        "api_url": url  # เก็บ URL หน้า list ไว้เป็น reference
                    }
                    
                    all_job_data.append(job_info)
                    
            else:
                temp_log.append(f"[ERR] Page {page}: Status {response.status_code}")

            # แสดงความคืบหน้า
            progress_bar.progress((idx + 1) / (End_ID - Start_ID + 1))
            idx += 1
            if len(temp_log) >= 5:
                log_entry = ''
                for log_i in temp_log:
                    log_entry += log_i + " "    
                st.write(log_entry)
                print(log_entry)
                temp_log = []

        except Exception as e:
            st.error(f"Exception occurred: {e}")
            print(f"[ERR] Exception: {e}")

        # ==========================================
        # 3. หน่วงเวลาแบบสุ่ม (Random Delay)
        # ==========================================
        # แม้จะยิงน้อยครั้ง แต่ควรหน่วงเวลาเล็กน้อยเพื่อความปลอดภัย
        delay = random.uniform(2.0, 3.0)
        time.sleep(delay)

    for log_i in temp_log:
        log_entry += log_i + " "    
    st.write(log_entry)
    print(log_entry)

    # ==========================================
    # 4. บันทึกผลลัพธ์ (Export)
    # ==========================================
    print("-" * 30)
    if all_job_data:
        df = pd.DataFrame(all_job_data)
        
        # บันทึกไฟล์
        df.to_csv(OUTPUT_FILENAME, index=False, encoding='utf-8-sig')
        
        print(f"Scraping Finished! Total jobs collected: {len(df)}")
        print(f"Saved to: {OUTPUT_FILENAME}")
        print(df.head())
    else:
        print("No data found. Please check Cookie.")    