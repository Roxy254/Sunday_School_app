import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from supabase import create_client
import streamlit as st
from datetime import datetime
import os

def get_google_sheets_data():
    """Get data from Google Sheets"""
    # Google Sheets setup
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    # Get credentials
    creds_path = os.path.join('.streamlit', 'credentials.json')
    client = gspread.service_account(filename=creds_path)
    
    # Get spreadsheet
    spreadsheet_id = st.secrets['spreadsheet_id']
    spreadsheet = client.open_by_key(spreadsheet_id)
    
    # Get children data
    children_sheet = spreadsheet.worksheet("Children")
    children_data = children_sheet.get_all_records()
    children_df = pd.DataFrame(children_data)
    
    # Get attendance data
    attendance_sheet = spreadsheet.worksheet("Attendance")
    attendance_data = attendance_sheet.get_all_records()
    attendance_df = pd.DataFrame(attendance_data)
    
    return children_df, attendance_df

def migrate_data():
    """Migrate data from Google Sheets to Supabase"""
    print("Starting migration...")
    
    # Get Supabase client
    try:
        supabase_url = st.secrets["supabase"]["url"]
        supabase_key = st.secrets["supabase"]["key"]
        supabase = create_client(supabase_url, supabase_key)
    except Exception as e:
        print(f"Error connecting to Supabase: {str(e)}")
        return
    
    # Get data from Google Sheets
    children_df, attendance_df = get_google_sheets_data()
    
    # Migrate children data
    print(f"Migrating {len(children_df)} children records...")
    children_map = {}  # To store old name -> new UUID mapping
    
    for _, child in children_df.iterrows():
        child_data = {
            "full_name": child["Full Name"],
            "gender": child["Gender"],
            "date_of_birth": child["Date of Birth"],
            "school": child["School"],
            "grade": child["Grade"],
            "class_group": child["Group/Class"],
            "residence": child["Residence"],
            "parent1_name": child["Parent 1"],
            "parent1_contact": child["Contact 1"],
            "parent2_name": child["Parent 2"],
            "parent2_contact": child["Contact 2"],
            "sponsored": child["Sponsored by OCM"] == "Yes",
            "created_at": datetime.now().isoformat()
        }
        
        # Insert child record and get the UUID
        response = supabase.table('children').insert(child_data).execute()
        if response.data:
            children_map[child["Full Name"]] = response.data[0]["id"]
            print(f"✓ Migrated {child['Full Name']}")
        else:
            print(f"✗ Failed to migrate {child['Full Name']}")
    
    # Migrate attendance data
    print(f"\nMigrating {len(attendance_df)} attendance records...")
    
    for _, record in attendance_df.iterrows():
        child_name = record["Child Name"]
        if child_name in children_map:
            attendance_data = {
                "child_id": children_map[child_name],
                "session_date": record["Date"],
                "present": record["Present"] == "Yes",
                "has_bible": record["Brought Bible"] == "Yes",
                "gave_offering": record["Brought Offering"] == "Yes",
                "created_at": datetime.now().isoformat()
            }
            
            response = supabase.table('attendance').insert(attendance_data).execute()
            if response.data:
                print(f"✓ Migrated attendance for {child_name} on {record['Date']}")
            else:
                print(f"✗ Failed to migrate attendance for {child_name} on {record['Date']}")
    
    print("\nMigration completed!")

if __name__ == "__main__":
    migrate_data() 