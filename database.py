import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

@st.cache_resource
def get_supabase_client():
    """Initialize and return Supabase client"""
    try:
        # Get credentials from secrets
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        
        # Debug output
        st.write("Debug - Supabase URL:", url)
        
        # Validate URL format
        if not url.startswith("https://") or not url.endswith(".supabase.co"):
            st.error(f"Invalid Supabase URL format: {url}")
            return None
            
        # Create client with validated credentials
        client = create_client(url, key)
        
        # Test connection
        try:
            # Try a simple query to test connection
            response = client.table('children').select("count", count='exact').execute()
            st.success("Successfully connected to Supabase!")
            return client
        except Exception as e:
            st.error(f"Failed to connect to Supabase: {str(e)}")
            st.error("Response details:", str(e.__dict__))
            return None
            
    except KeyError as e:
        st.error(f"Missing Supabase configuration: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error connecting to Supabase: {str(e)}")
        st.error("Error details:", str(e.__dict__))
        return None

@st.cache_data(ttl=30)
def load_children():
    """Load children data from Supabase"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return pd.DataFrame()
        
        response = supabase.table('children').select("*").execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading children data: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=30)
def load_attendance():
    """Load attendance data from Supabase"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return pd.DataFrame()
        
        # Get attendance data with all fields
        attendance_response = supabase.table('attendance').select("*").execute()
        attendance_df = pd.DataFrame(attendance_response.data) if attendance_response.data else pd.DataFrame()
        
        if attendance_df.empty:
            return attendance_df
            
        # Get children data with id and full_name
        children_response = supabase.table('children').select("id", "full_name").execute()
        children_df = pd.DataFrame(children_response.data) if children_response.data else pd.DataFrame()
        
        if not children_df.empty:
            # Merge attendance with children names
            attendance_df = attendance_df.merge(
                children_df,
                left_on="child_id",
                right_on="id",
                how="left"
            )
            
            # Ensure all required columns exist with correct names
            required_columns = [
                'child_id', 'session_date', 'present', 'early',
                'has_book', 'has_pen', 'has_bible', 'gave_offering',
                'full_name', 'id'
            ]
            
            # Add any missing columns with default values
            for col in required_columns:
                if col not in attendance_df.columns:
                    attendance_df[col] = False if col in ['present', 'early', 'has_book', 'has_pen', 'has_bible', 'gave_offering'] else None
        
        return attendance_df
    except Exception as e:
        st.error(f"Error loading attendance data: {str(e)}")
        return pd.DataFrame()

def save_child(child_data):
    """Save child data to Supabase"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        response = supabase.table('children').insert(child_data).execute()
        return True if response.data else False
    except Exception as e:
        st.error(f"Error saving child data: {str(e)}")
        return False

def update_child(child_id, child_data):
    """Update child data in Supabase"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        response = supabase.table('children').update(child_data).eq('id', child_id).execute()
        return True if response.data else False
    except Exception as e:
        st.error(f"Error updating child data: {str(e)}")
        return False

def save_attendance(attendance_data):
    """Save attendance data to Supabase"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        # Check if attendance record already exists for this child and date
        existing = supabase.table('attendance').select("*").eq(
            'child_id', attendance_data['child_id']
        ).eq(
            'session_date', attendance_data['session_date']
        ).execute()
        
        if existing.data:
            # Update existing record
            response = supabase.table('attendance').update({
                'present': attendance_data['present'],
                'early': attendance_data.get('early', False),
                'has_book': attendance_data.get('has_book', False),
                'has_pen': attendance_data.get('has_pen', False),
                'has_bible': attendance_data.get('has_bible', False),
                'gave_offering': attendance_data.get('gave_offering', False),
                'updated_at': datetime.now().isoformat()
            }).eq(
                'child_id', attendance_data['child_id']
            ).eq(
                'session_date', attendance_data['session_date']
            ).execute()
        else:
            # Add created_at timestamp for new records
            attendance_data['created_at'] = datetime.now().isoformat()
            # Insert new record with all fields
            response = supabase.table('attendance').insert(attendance_data).execute()
        
        return True if response.data else False
    except Exception as e:
        st.error(f"Error saving attendance data: {str(e)}")
        return False 