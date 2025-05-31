import streamlit as st
from database import get_supabase_client
import pandas as pd
from datetime import datetime
import os

def backup_data():
    """Backup data from Supabase to local CSV files"""
    print("Starting backup...")
    
    # Create backups directory if it doesn't exist
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Generate timestamp for backup files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        if not supabase:
            print("Error: Could not connect to Supabase")
            return
        
        # Backup children data
        print("Backing up children data...")
        children_response = supabase.table('children').select("*").execute()
        if children_response.data:
            children_df = pd.DataFrame(children_response.data)
            children_file = os.path.join(backup_dir, f"children_backup_{timestamp}.csv")
            children_df.to_csv(children_file, index=False)
            print(f"✓ Children data backed up to {children_file}")
        else:
            print("No children data to backup")
        
        # Backup attendance data
        print("\nBacking up attendance data...")
        attendance_response = supabase.table('attendance').select("*").execute()
        if attendance_response.data:
            attendance_df = pd.DataFrame(attendance_response.data)
            attendance_file = os.path.join(backup_dir, f"attendance_backup_{timestamp}.csv")
            attendance_df.to_csv(attendance_file, index=False)
            print(f"✓ Attendance data backed up to {attendance_file}")
        else:
            print("No attendance data to backup")
        
        print("\nBackup completed successfully!")
        
    except Exception as e:
        print(f"Error during backup: {str(e)}")

if __name__ == "__main__":
    backup_data() 