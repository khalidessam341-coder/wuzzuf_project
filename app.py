import streamlit as st
import pandas as pd
import sqlite3
import io
import time
import os
from scraper import scrape_wuzzuf, save_to_db

st.set_page_config(page_title="Wuzzuf Tracker", layout="wide")

def add_to_track_list(job_title):
    file_path = "jobs_to_track.txt"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            existing_jobs = f.read().splitlines()
    else:
        existing_jobs = []
    
    if job_title and job_title not in existing_jobs:
        with open(file_path, "a") as f:
            f.write(job_title + "\n")

st.sidebar.title("🔍 أداة السحب المباشر")
st.sidebar.write("ابحث عن وظائف جديدة وضيفها لقاعدة البيانات:")

job_search = st.sidebar.text_input("المسمى الوظيفي:", "Data Engineer")
pages = st.sidebar.number_input("عدد الصفحات:", min_value=1, max_value=10, value=2)

if st.sidebar.button("ابدأ السحب الآن 🚀", use_container_width=True):
    if job_search:
        with st.spinner(f"جاري سحب {job_search}..."):
            add_to_track_list(job_search)
            new_data = scrape_wuzzuf(job_search, num_pages=pages)
            added = save_to_db(new_data)
            
            if added > 0:
                st.sidebar.success(f"تم إضافة {added} وظيفة جديدة بنجاح!")
            else:
                st.sidebar.info("مفيش وظايف جديدة حالياً.")
            time.sleep(1)
            st.rerun()

def load_data():
    try:
        conn = sqlite3.connect("wuzzuf_data.db")
        df = pd.read_sql_query("SELECT * FROM jobs", conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

df = load_data()

st.title("📊 لوحة بيانات سوق العمل (Wuzzuf)")

if not df.empty:
    c1, c2, c3 = st.columns(3)
    c1.metric("إجمالي الوظائف", len(df))
    c2.metric("عدد الشركات", df["Company"].nunique())

    skills_series = df.assign(Skills=df['Skills'].str.split(', ')).explode('Skills')
    c3.metric("إجمالي المهارات", skills_series["Skills"].nunique())
    
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("أكثر الشركات توظيفاً")
        st.bar_chart(df["Company"].value_counts().head(10))
        
    with col2:
        st.subheader("أكثر المهارات طلباً")
        st.bar_chart(skills_series["Skills"].value_counts().head(10))

    st.divider()

    st.subheader("سجل الوظائف المكتشفة")
    st.dataframe(df, use_container_width=True, height=300)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    
    st.download_button(
        label="تحميل قاعدة البيانات (Excel) 📥", 
        data=output.getvalue(), 
        file_name="Wuzzuf_Jobs_Data.xlsx"
    )
else:
    st.info("قاعدة البيانات فاضية. ابدأ بأول عملية سحب من القائمة الجانبية.")