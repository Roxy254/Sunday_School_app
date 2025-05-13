import pandas as pd
import os

# File paths
att_file = "attendance_records.csv"
child_file = "children_records.csv"

# Check if attendance file exists
if not os.path.exists(att_file):
    print("⚠️ attendance_records.csv not found. Please make sure it exists in the folder.")
    exit()

# Load attendance data
att_df = pd.read_csv(att_file)

