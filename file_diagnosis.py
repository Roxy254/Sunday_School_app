import streamlit as st
import os
import glob
import pandas as pd

st.title("🛠️ Sunday School Data Diagnostic")

# --- 1. Search for all children_records.csv files ---
st.header("📁 Searching for 'children_records.csv' files...")

# Search everywhere under your user folder
search_root = os.path.expanduser("~")  # E.g. C:/Users/AROMA MBAYU MUNGA
csv_paths = glob.glob(os.path.join(search_root, "**", "children_records.csv"), recursive=True)

if csv_paths:
    st.success(f"🔍 Found {len(csv_paths)} file(s).")
else:
    st.warning("⚠️ No children_records.csv files found.")

# --- 2. Display file paths and preview contents ---
for path in csv_paths:
    st.markdown("---")
    st.markdown(f"📄 **File Path:** `{path}`")
    try:
        df = pd.read_csv(path)
        st.markdown(f"👀 **Preview:** ({len(df)} records)")
        st.dataframe(df.head(10))
    except Exception as e:
        st.error(f"Error reading file: {e}")

# --- 3. Allow user to select and copy a correct file into app folder ---
if csv_paths:
    st.markdown("---")
    st.header("📤 Copy Correct File Into App Folder")

    selected = st.selectbox("Choose the correct CSV to copy:", csv_paths)
    if st.button("✅ Copy to app folder"):
        try:
            app_dir = os.path.dirname(__file__)
            dest = os.path.join(app_dir, "children_records.csv")
            with open(selected, "rb") as src_file, open(dest, "wb") as dst_file:
                dst_file.write(src_file.read())
            st.success(f"Copied successfully to: {dest}")
        except Exception as e:
            st.error(f"Copy failed: {e}")
