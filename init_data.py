import pandas as pd

# Clean children records
children_columns = [
    "Full Name", "Gender", "Date of Birth", "Age", "Group/Class",
    "School", "Grade", "Residence",
    "Parent 1", "Contact 1", "Parent 2", "Contact 2",
    "Sponsored by OCM"
]
children_df = pd.DataFrame(columns=children_columns)
children_df.to_csv("children_records.csv", index=False)

# Clean attendance records
attendance_columns = [
    "Child Name", "Class", "Session Date", "Attendance Status",
    "Arrival Time", "Brought Bible", "Brought Pen", "Brought Offering"
]
attendance_df = pd.DataFrame(columns=attendance_columns)
attendance_df.to_csv("attendance_records.csv", index=False)

print("✅ Fresh CSVs created successfully!")
