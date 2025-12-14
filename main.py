import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import requests
import time
import random
import csv
import os

from Helper.scraping_Detail import scraping_Detail

# Page configuration
st.set_page_config(
    page_title="CEDT Intern Finder",
    page_icon="🎓",
    layout="wide"
)

# ==========================================
# Session State Initialization
# ==========================================
if 'df' not in st.session_state:
    st.session_state.df = None
if 'scraping_done' not in st.session_state:
    st.session_state.scraping_done = False
    
# ==========================================
# UI Layout
# ==========================================

st.title("CEDT Intern Position Finder")

if st.checkbox("List files in project folder"):
    files = sorted(os.listdir("."))  # current working directory
    st.write(files)
    
cookie = st.text_input("Enter your COOKIE value:")
    
tab1, tab2, tab3 = st.tabs(["Search Intern Positions", 
                            "Data Visualization & Bookmarking", 
                            "Bookmark Positions"])

with tab1:
    # ==========================================
    # Scraping Section Paginated
    # ==========================================
    st.title("Scraping Intern Positions from Paginated API")

    st.subheader("Configure Scraping Parameters")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        start_page = st.number_input("Start Page", min_value=1, value=1, step=1)
    with col2:
        end_page = st.number_input("End Page", min_value=1, value=16, step=1)
    with col3:
        limit = st.number_input("Items per Page", min_value=1, value=20, step=1)
    with col4:
        output_filename = st.text_input("Output Filename", value="cedt_intern_data_paginated.csv")

    if st.button("Start Scraping paginated"):
        from Helper.scraping_Paginated import scraping_Paginated
        try:
            scraping_Paginated(Start_Page=start_page, End_Page=end_page, Limit=limit, Output_Filename=output_filename, cookie_value=cookie)
            st.success(f"Scraping completed! Data saved to {output_filename}")
            st.session_state.scraping_done = True
        except Exception as e:
            st.error(f"An error occurred during scraping: {e}")

    st.markdown("---")


    # ==========================================
    # Scraping Section Detail
    # ==========================================
    st.title("Scraping Intern Positions from Detail API")

    st.subheader("Configure Scraping Parameters")
    col1, col2, col3 = st.columns(3)
    with col1:
        start_id = st.number_input("Start ID", min_value=1, value=1000, step=1)
    with col2:
        end_id = st.number_input("End ID", min_value=1, value=2000, step=1)
    with col3:
        output_filename = st.text_input("Output Filename", value="cedt_intern_data_detail.csv")
    if st.button("Start Scraping detail"):
        from Helper.scraping_Paginated import scraping_Paginated
        try:
            scraping_Detail(Start_ID=start_id, End_ID=end_id, Output_Filename=output_filename, cookie_value=cookie)
            st.success(f"Scraping completed! Data saved to {output_filename}")
            st.session_state.scraping_done = True
        except Exception as e:
            st.error(f"An error occurred during scraping: {e}")

    st.markdown("---")
    
with tab2:
    # ==========================================
    # Data Visualization Section
    # ==========================================
    st.title("Data Visualization")

    csv_files = [f for f in os.listdir(".") if f.endswith(".csv")]

    if csv_files:
        selected_files = st.multiselect("Select CSV files", csv_files)
        
        if st.button("Merge and Visualize"):
            from Helper.Visualize import merge_and_deduplicate_data

            if selected_files:
                # Merge and deduplicate data
                merged_df = merge_and_deduplicate_data(selected_files)
                st.session_state.df = merged_df
                
                # create column student_draft_ratio
                merged_df['inStudentDraftCount'] = merged_df['inStudentDraftCount'].fillna(0)
                merged_df['quota'] = merged_df['quota'].fillna(1)  # เติม 1 เพื่อหลีกเลี่ยงการหารด้วยศูนย์
                merged_df['student_draft_ratio'] = merged_df['inStudentDraftCount']/merged_df['quota']
                
                # Normalize salary_amount to per day if salary_type indicates monthly or fixed
                mask = merged_df['salary_type'].str.contains('บาท/เดือน', na=False, case=False) | merged_df['salary_type'].str.contains('เหมาจ่าย', na=False, case=False)
                merged_df.loc[mask, 'salary_amount'] = merged_df.loc[mask, 'salary_amount'] / 22
                merged_df.loc[mask, 'salary_amount'] = merged_df.loc[mask, 'salary_amount'].round(0)
                
                st.success(f"Merged {len(selected_files)} files with {len(merged_df)} unique entries.")
                
                # Display DataFrame
                st.dataframe(merged_df)
                
                # Visualization
                from Helper.Visualize import log_data_stats
                log_data_stats(merged_df, 'salary_amount')
                st.markdown("---")
                log_data_stats(merged_df, 'student_draft_ratio')
                st.markdown("---")
            else:
                st.warning("Please select at least one CSV file to merge.")
    else :
        st.warning("No CSV files found in the project directory. Please perform scraping first to generate data files.")

with tab3:
    # ==========================================
    # Bookmark Positions Section
    # ==========================================
    st.title("Bookmark Intern Positions")
    
    # Initialize session state for filters
    if 'student_draft_ratio' not in st.session_state:
        st.session_state.student_draft_ratio = 2.0
    if 'min_salary' not in st.session_state:
        st.session_state.min_salary = 150
    if 'max_salary' not in st.session_state:
        st.session_state.max_salary = 400
    if 'work_type' not in st.session_state:
        st.session_state.work_type = []
    if 'show_filtered' not in st.session_state:
        st.session_state.show_filtered = False
    
    # Check if merged_df exists
    if st.session_state.df is None:
        st.warning("⚠️ Please merge data in 'Data Visualization & Bookmarking' tab first!")
    else:
        merged_df = st.session_state.df
        
        # Create three columns for filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.session_state.student_draft_ratio = st.slider(
                "Maximum Student/Draft Ratio",
                min_value=0.0,
                max_value=10.0,
                value=st.session_state.student_draft_ratio,
                step=0.5,
                key="ratio_slider"
            )
        
        with col2:
            st.session_state.min_salary = st.number_input(
                "Minimum Salary (฿/day)",
                min_value=0,
                value=st.session_state.min_salary,
                step=10,
                key="min_salary_input"
            )
            st.session_state.max_salary = st.number_input(
                "Maximum Salary (฿/day)",
                min_value=0,
                value=st.session_state.max_salary,
                step=10,
                key="max_salary_input"
            )
        
        with col3:
            work_type_options = sorted(merged_df['work_type'].dropna().unique().tolist())
            
            if st.session_state.work_type:
                valid_defaults = [
                    wt for wt in st.session_state.work_type 
                    if wt in work_type_options
                ]
            else:
                valid_defaults = []
            
            st.session_state.work_type = st.multiselect(
                "Type of Working",
                options=work_type_options,
                default=valid_defaults,
                key="work_type_select"
            )
        
        # Apply filters
        filtered_df = merged_df.copy()
        filtered_df = filtered_df[
            (filtered_df['student_draft_ratio'] <= st.session_state.student_draft_ratio) &
            (filtered_df['salary_amount'] >= st.session_state.min_salary) &
            (filtered_df['salary_amount'] <= st.session_state.max_salary)
        ]
        
        if st.session_state.work_type:
            filtered_df = filtered_df[filtered_df['work_type'].isin(st.session_state.work_type)]
        
        # Button to toggle display
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**Found: {len(filtered_df)} / {len(merged_df)} positions**")
        with col2:
            if st.button("🔍 Show Filtered", key="show_button"):
                st.session_state.show_filtered = not st.session_state.show_filtered
        
        # Display table only if button is clicked
        if st.session_state.show_filtered:
            st.subheader(f"Filtered Positions ({len(filtered_df)} found)")
            
            display_cols = ['id', 'company_nameTh', 'position_title', 'salary_amount', 
                        'work_type', 'student_draft_ratio', 'quota']
            st.dataframe(
                filtered_df[display_cols].style.format({
                    'salary_amount': '{:,.0f}฿',
                    'student_draft_ratio': '{:.2f}'
                }),
                use_container_width=True,
                height=400
            )
        
        bookmarked_id_list = filtered_df['id'].tolist()
        
        st.markdown("---")
        st.subheader(f"📌 Bookmark Positions: {len(bookmarked_id_list)} found")
        
        st.write(f"Click button to bookmark **{len(bookmarked_id_list)}** selected positions")
        if st.button("🔖 Bookmark All", type="primary", key="bookmark_btn"):
            from Helper.bookmark import bookmark_position
            
            if cookie.strip() == "":
                st.error("❌ Please enter a valid COOKIE value!")
            elif len(bookmarked_id_list) == 0:
                st.warning("⚠️ No positions to bookmark!")
            else:
                bookmark_position(bookmarked_id_list, cookie)