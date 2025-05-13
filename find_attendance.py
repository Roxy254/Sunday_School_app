import streamlit as st
import os
import glob
import pandas as pd

st.title("📊 Find Attendance Records")

search_root = os.path.expanduser("~")
csv_paths = glob.glob(os.path.join(search_root, "**", "attendance_records.csv"), recursive=True)

if csv_paths:
    st.success(f"Found {len(csv_paths)} attendance file(s).")
else:
    st.warning("No attendance_records.csv files found.")

for path in csv_paths:
    st.markdown("---")
    st.markdown(f"📄 File Path: `{path}`")
    try:
        df = pd.read_csv(path)
        st.markdown(f"Records: {len(df)}")
        st.dataframe(df.head(10))
    except Exception as e:
        st.error(f"Could not read this file: {e}")
