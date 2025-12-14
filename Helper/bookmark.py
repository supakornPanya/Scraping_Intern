import csv
import requests
import pandas as pd
import time
import random
import streamlit as st

def bookmark_position(listNamePosition, cookie_value):
    """Bookmark selected positions with progress tracking"""
    
    if not listNamePosition:
        st.warning("No positions to bookmark!")
        return
    
    API_URL_TEMPLATE = "https://cedtintern.cp.eng.chula.ac.th/api/sessions/5/openings/{}/bookmark"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://cedtintern.cp.eng.chula.ac.th",
        "Referer": "https://cedtintern.cp.eng.chula.ac.th/opening?page=1",
        "Cookie": cookie_value
    }

    success_count = 0
    error_count = 0
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    total = len(listNamePosition)

    for idx, pos_id in enumerate(listNamePosition):
        url = API_URL_TEMPLATE.format(pos_id)
        
        try:
            status_text.text(f"Bookmarking {pos_id} ({idx+1}/{total})...")
            
            response = requests.post(
                url, 
                headers=HEADERS, 
                timeout=10,
                json={}
            )
            
            if response.status_code == 200:
                success_count += 1
            elif  response.status_code == 400:
                st.warning(f"Position {pos_id} is already bookmarked.")
            else:
                error_count += 1
                st.warning(f"Position {pos_id}: Status {response.status_code}")

        except Exception as e:
            error_count += 1
            st.error(f"Position {pos_id}: {str(e)}")

        # Update progress
        progress_bar.progress((idx + 1) / total)
        
        # Random delay to avoid being blocked
        delay = random.uniform(0.5, 1.5)
        time.sleep(delay)
    
    # Results
    status_text.empty()
    st.success(f"✅ Completed: {success_count} success, {error_count} errors")
    
    # Save results
    with open('bookmark_log.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for pos_id in listNamePosition:
            writer.writerow([pos_id, 'bookmarked'])