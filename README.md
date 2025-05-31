# Sunday School App

A Streamlit application for managing Sunday School attendance and student records using Supabase as the backend database.

## Features
- Student Registration
- Attendance Tracking
- Performance Reports
- Profile Management

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure Supabase:
   - Create a `.streamlit/secrets.toml` file with your Supabase credentials:
     ```toml
     [supabase]
     url = "your-project-url"
     key = "your-anon-key"
     ```

3. Run the app:
   ```bash
   streamlit run app.py
   ```

## Files
- `app.py` - Main Streamlit application
- `database.py` - Supabase database operations
- `migrate_to_supabase.py` - Data migration utility
- `requirements.txt` - Python dependencies

## Database Schema
### Children Table
- id (bigint, primary key)
- full_name (text)
- gender (text)
- date_of_birth (date)
- school (text)
- grade (text)
- class_group (text)
- residence (text)
- parent1_name (text)
- parent1_contact (text)
- parent2_name (text)
- parent2_contact (text)
- sponsored (boolean)
- created_at (timestamp)

### Attendance Table
- id (bigint, primary key)
- child_id (bigint, foreign key)
- session_date (date)
- present (boolean)
- has_bible (boolean)
- gave_offering (boolean)
- created_at (timestamp)
