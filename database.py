import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

@st.cache_resource
def get_supabase_client():
    """Initialize and return Supabase client"""
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Error connecting to Supabase: {str(e)}")
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
        
        # Get attendance data
        attendance_response = supabase.table('attendance').select("*").execute()
        attendance_df = pd.DataFrame(attendance_response.data) if attendance_response.data else pd.DataFrame()
        
        if attendance_df.empty:
            return attendance_df
            
        # Get children data
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