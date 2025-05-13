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

# Extract unique names and class
child_data = att_df[["Child Name", "Class"]].drop_duplicates().rename(
    columns={"Child Name": "Full Name", "Class": "Group/Class"}
)

# Add blank columns for full child structure
columns = [
    "Full Name", "Gender", "Date of Birth", "Age", "Group/Class", "School", "Grade",
    "Residence", "Parent 1", "Contact 1", "Parent 2", "Contact 2", "Sponsored by OCM"
]
for col in columns:
    if col not in child_data.columns:
        child_data[col] = ""

# Fill in correct column order
child_data = child_data[columns]

# Save it
child_data.to_csv(child_file, index=False)
print(f"✅ New {child_file} created with {len(child_data)} student(s). You can now edit their full details.")
