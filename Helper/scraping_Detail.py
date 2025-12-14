import requests
import pandas as pd
import time
import random
import streamlit as st

def scraping_Detail(Start_ID=1000, End_ID=2000, Output_Filename="cedt_intern_data.csv", cookie_value=None):
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Cookie": cookie_value
    }

    # ==========================================
    # 1. การตั้งค่า (Configuration)
    # ==========================================
    # URL ของ API เป้าหมาย (ใช้ {} ตรง ID เพื่อรอการแทนค่า)
    API_URL_TEMPLATE = "https://cedtintern.cp.eng.chula.ac.th/api/sessions/5/openings/{}"

    # ตัวแปรสำหรับเก็บข้อมูลทั้งหมด
    all_job_data = []
    temp_log = []
    # ==========================================
    # 2. เริ่มการวนลูป (Scraping Loop)
    # ==========================================
    print(f"Starting scrape from ID {Start_ID} to {End_ID}...")
    progress_bar = st.progress(0)
    idx = 0
    
    for job_id in range(Start_ID, End_ID + 1):
        url = API_URL_TEMPLATE.format(job_id)
        
        try:
            # ยิง Request ไปที่ API
            response = requests.get(url, headers=HEADERS, timeout=10)
            
            # กรณีเจอข้อมูล (Status 200)
            if response.status_code == 200:
                data = response.json()
                
                # ดึงข้อมูลเฉพาะ field ที่ต้องการ (Safe Extraction)
                # ใช้ .get() เพื่อป้องกัน Error กรณีไม่มีข้อมูลใน field นั้น
                job_info = {
                    "id": data.get("openingId"),
                    "company_name": data.get("company", {}).get("companyNameTh"),
                    "position_title": data.get("title"),
                    "quota": data.get("quota"),
                    "salary_amount": data.get("compensationAmount"),
                    "salary_type": data.get("compensationType", {}).get("compensationType"),
                    "work_type": data.get("workingCondition"),
                    "location": data.get("officeName"),
                    # รวม Tags ทั้งหมดเป็นข้อความเดียวคั่นด้วย comma
                    "tags": ", ".join([t['tagName'] for t in data.get("tags", [])]),
                    # เก็บ Description (อาจจะมี HTML tag ติดมา)
                    "description_html": data.get("description"),
                    "api_url": url
                }
                
                all_job_data.append(job_info)
                temp_log.append(f"[OK] ID {job_id}: Found '{job_info['position_title']}'")
            
            # กรณีไม่เจอข้อมูล (404) หรือไม่มีสิทธิ์ (403)
            elif response.status_code == 404:
                temp_log.append(f"[SKIP] ID {job_id}: Not Found")
            else:
                temp_log.append(f"[ERR] ID {job_id}: Status {response.status_code}")

            # แสดงความคืบหน้า
            progress_bar.progress((idx + 1) / (End_ID - Start_ID + 1))
            idx += 1
            if len(temp_log) >= 10:
                log_entry = ''
                for log_i in temp_log:
                    log_entry += log_i + ", "
                st.write(log_entry)
                print(log_entry)
                temp_log = []

        except Exception as e:
            st.error(f"[ERR] ID {job_id}: Exception occurred - {e}")
            print(f"[ERR] ID {job_id}: Exception occurred - {e}")

        # ==========================================
        # 3. หน่วงเวลาแบบสุ่ม (Random Delay)
        # ==========================================
        # สุ่มเวลาระหว่าง 0.2 ถึง 0.5 วินาที เพื่อไม่ให้ Server จับได้
        delay = random.uniform(0.2, 0.5)
        time.sleep(delay)

    for log_i in temp_log:
        log_entry += log_i + " "    
    st.write(log_entry)
    print(log_entry)

    # ==========================================
    # 4. บันทึกผลลัพธ์ (Export to CSV)
    # ==========================================
    print("-" * 30)
    if all_job_data:
        df = pd.DataFrame(all_job_data)
        
        # บันทึกไฟล์ (ใช้ encoding='utf-8-sig' เพื่อให้อ่านภาษาไทยใน Excel รู้เรื่อง)
        df.to_csv(Output_Filename, index=False, encoding='utf-8-sig')
        
        print(f"Scraping Finished! Successfully saved {len(df)} records.")
        print(f"File saved as: {Output_Filename}")
        
        # แสดงตัวอย่างข้อมูล 5 แถวแรก
        print(df.head())
    else:
        st.warning("Scraping Finished, but NO data was found. Please check your Cookie or ID range.")