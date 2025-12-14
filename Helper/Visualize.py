import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import streamlit as st

def merge_and_deduplicate_data(file_paths, output_filename=None):
    """
    ฟังก์ชันสำหรับรวมไฟล์ CSV หลายไฟล์เข้าด้วยกันและตัดข้อมูลซ้ำโดยใช้ 'id'
    
    Args:
        file_paths (list): รายชื่อ path ของไฟล์ .csv ที่ต้องการรวม
                           เช่น ['data_part1.csv', 'data_part2.csv']
        output_filename (str, optional): ชื่อไฟล์ปลายทางถ้าต้องการบันทึกเป็น CSV ทันที
    
    Returns:
        pd.DataFrame: DataFrame ที่รวมและตัดตัวซ้ำเรียบร้อยแล้ว
    """
    
    all_dfs = []
    
    print(f"--- Starting Merge Process ---")
    
    # 1. วนลูปอ่านไฟล์แต่ละไฟล์ (Read CSVs)
    for file in file_paths:
        if os.path.exists(file):
            try:
                # อ่านไฟล์ CSV เข้ามาเป็น DataFrame
                df = pd.read_csv(file)
                all_dfs.append(df)
                print(f"[READ] {file}: Found {len(df)} rows")
            except Exception as e:
                print(f"[ERROR] Could not read {file}: {e}")
        else:
            print(f"[SKIP] File not found: {file}")
    
    if not all_dfs:
        print("No data loaded.")
        return pd.DataFrame()

    # 2. รวม DataFrame ทั้งหมดเข้าด้วยกัน (Concatenation)
    merged_df = pd.concat(all_dfs, ignore_index=True)
    total_rows_before = len(merged_df)
    
    # 3. ตัดข้อมูลซ้ำโดยดูจาก 'id' (Deduplication)
    # keep='last' หมายถึงถ้าเจอ id ซ้ำกัน ให้เก็บข้อมูลตัวล่าสุดไว้ (สมมติว่าเป็นข้อมูลที่อัปเดตกว่า)
    # subset=['id'] คือระบุว่าให้ดูความซ้ำกันที่คอลัมน์ id เท่านั้น
    cleaned_df = merged_df.drop_duplicates(subset=['id'], keep='last')
    
    total_rows_after = len(cleaned_df)
    duplicates_removed = total_rows_before - total_rows_after
    
    print(f"--- Merge Summary ---")
    print(f"Total rows raw: {total_rows_before}")
    print(f"Duplicates removed: {duplicates_removed}")
    print(f"Final unique rows: {total_rows_after}")
    
    # 4. รีเซ็ต index ให้เรียงสวยงาม 0, 1, 2, ...
    cleaned_df = cleaned_df.reset_index(drop=True)
        
    return cleaned_df

def log_data_stats(df, column_name):
    """
    ฟังก์ชันสำหรับวิเคราะห์สถิติและพล็อตกราฟ
    
    Args:
        df (pd.DataFrame): DataFrame หลัก
        column_name (str): ชื่อคอลัมน์ที่ต้องการวิเคราะห์ (Default: 'salary_amount')
    """
    
    st.subheader(f"Statistical Analysis for '{column_name}'")
    
    # 1. เตรียมข้อมูล (Data Preparation)
    # แปลงเป็นตัวเลข (เผื่อเป็น string) และลบค่าว่าง (NaN) หรือค่า 0 ออกเพื่อความแม่นยำ
    if column_name not in df.columns:
        st.error(f"[ERROR] Column '{column_name}' not found.")
        return

    # coerce จะเปลี่ยน text ที่แปลงไม่ได้เป็น NaN
    data_numeric = pd.to_numeric(df[column_name], errors='coerce') 
    # กรองเอาเฉพาะที่มีค่าและมากกว่า 0 (บางที่ใส่ 0 หมายถึงไม่ระบุ)
    valid = data_numeric.dropna()
    valid = valid[valid > 0]
    
    if len(valid) == 0:
        st.error("No valid data found (all are NaN or 0).")
        return

    # 2. คำนวณสถิติ (Calculation)
    min = valid.min()
    max = valid.max()
    mean = valid.mean()
    
    # Mode อาจมีหลายค่าถ้าความถี่เท่ากัน
    modes = valid.mode()
    mode_str = ", ".join(map(str, modes.tolist()))
    
    # คำนวณ IQR (Interquartile Range)
    q1 = valid.quantile(0.25)
    q3 = valid.quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    # 3. แสดงผล Log (Logging) - Beautiful Stats Display
    tab1, tab2, tab3 = st.tabs(["Summary", "IQR Details", "Outliers"])
    
    with tab1: 
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Valid", f"{len(valid):,}", help="Number of valid data points")
        with col2:
            st.metric("Mean", f"{mean:,.2f}", help="Average value")
        with col3:
            st.metric("Median", f"{valid.median():,.2f}", help="Middle value (50th percentile)")
        with col4:
            st.metric("Std Dev", f"{valid.std():,.2f}", help="Standard deviation")

    with tab2:
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("IQR", f"{iqr:,.2f}", help="Interquartile Range")
        with col2:
            st.metric("Q1 (25%)", f"{q1:,.2f}", help="First quartile")
        with col3:
            st.metric("Q3 (75%)", f"{q3:,.2f}", help="Third quartile")
        with col4:
            st.metric("Lower Bound", f"{lower_bound:,.2f}", help="Lower bound for outliers")
        with col5:
            st.metric("Upper Bound", f"{upper_bound:,.2f}", help="Upper bound for outliers")

    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Min", f"{min:,.2f}", help="Minimum value")
        with col2:
            st.metric("Max", f"{max:,.2f}", help="Maximum value")

    # 4. สร้างกราฟ (Visualization)    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 5))
    
    # Subplot 1: Histogram + KDE (การกระจายตัว)
    sns.histplot(valid, kde=True, color='skyblue', bins=35, ax=ax1)
    ax1.axvline(mean, color='red', linestyle='--', label=f'Mean: {mean:.0f}', linewidth=2)
    ax1.axvline(valid.median(), color='green', linestyle='-', label=f'Median: {valid.median():.0f}', linewidth=2)
    ax1.set_title(f'Distribution of {column_name}', fontsize=14, fontweight='bold')
    ax1.set_xlabel(f'{column_name} (THB)', fontsize=12)
    ax1.set_ylabel('Frequency', fontsize=12)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)

    # Subplot 2: Boxplot (ดู IQR และ Outliers)
    sns.boxplot(x=valid, color='lightgreen', ax=ax2)
    ax2.set_title(f'Boxplot of {column_name} (IQR & Outliers)', fontsize=14, fontweight='bold')
    ax2.set_xlabel(f'{column_name} (THB)', fontsize=12)
    ax2.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    
    # Display in Streamlit
    st.pyplot(fig)
    plt.close(fig)  # Clean up memory