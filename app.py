import streamlit as st
import pandas as pd
from datetime import datetime, date
from database import (
    load_children,
    load_attendance,
    save_child,
    save_attendance,
    update_child,
    get_supabase_client
)

# ✅ Must be the first Streamlit command
st.set_page_config(
    page_title="Sunday School App",
    page_icon="icon_2_4ze_icon.icon",
    layout="wide"
)

# --- SIMPLE LOGIN SYSTEM ---
def check_login():
    st.markdown("### 🔐 Login to Access App")
    password = st.text_input("Enter password", type="password")
    if password == "Sundayschool2025":
        return True
    elif password:
        st.error("Incorrect password. Try again.")
        return False
    else:
        return False

if not check_login():
    st.stop()

# Load data
try:
    children_df = load_children()
    attendance_df = load_attendance()
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.stop()

# Show connection status in sidebar
st.sidebar.markdown("---")
if get_supabase_client() is not None:
    st.sidebar.success("🟢 Connected to Supabase")
else:
    st.sidebar.error("🔴 Not Connected")

# Cache clear button
if st.sidebar.button("🔄 Refresh Data"):
    load_children.clear()
    load_attendance.clear()
    st.rerun()

# Backup button
if st.sidebar.button("💾 Backup Data"):
    try:
        from backup_data import backup_data
        backup_data()
        st.sidebar.success("✅ Backup completed successfully!")
    except Exception as e:
        st.sidebar.error(f"Error during backup: {str(e)}")

# Sidebar navigation
page = st.sidebar.selectbox("Choose a page", [
    "📋 Registration", "🗓️ Attendance", "📊 Reports", "📚 Performance", 
    "👤 Profile", "✏️ Edit Profiles"
])

if page == "📋 Registration":
    st.title("📋 Register or Update Child Record")
    
    existing_names = children_df["full_name"].tolist() if not children_df.empty else []

    st.markdown("### ✍️ New or Incomplete Registration")

    with st.form("child_form"):
        full_name = st.text_input("Full Name")
        class_group = st.selectbox("Group/Class", [
            "Chosen Generation(grade PP1–PP2)",
            "Chosen Nation(grade 1–3)",
            "Priesthood (grade 4–6)",
            "Preisthood 2(grade 7–12)",
            "Priesthood 2(form 1–4)"
        ])
        
        gender = st.selectbox("Gender", ["", "Male", "Female"])
        dob = st.date_input("Date of Birth", value=date.today(), max_value=date.today())
        school = st.text_input("School Name")
        grade = st.selectbox("Grade / Form", [""] + [
            "PP1", "PP2", "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6",
            "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12",
            "Form 1", "Form 2", "Form 3", "Form 4"
        ])
        residence = st.text_input("Where do they live?")
        parent1 = st.text_input("Parent/Guardian 1 Name")
        contact1 = st.text_input("Contact for Parent 1")
        parent2 = st.text_input("Parent/Guardian 2 Name (optional)")
        contact2 = st.text_input("Contact for Parent 2")
        sponsored = st.checkbox("Sponsored by OCM")

        submitted = st.form_submit_button("💾 Save")

    if submitted and full_name:
        try:
            # Prepare new record
            new_record = {
                "full_name": full_name,
                "gender": gender,
                "date_of_birth": dob.isoformat(),
                "school": school,
                "grade": grade,
                "class_group": class_group,
                "residence": residence,
                "parent1_name": parent1,
                "parent1_contact": contact1,
                "parent2_name": parent2,
                "parent2_contact": contact2,
                "sponsored": sponsored
            }
            
            # Save to Supabase
            if save_child(new_record):
                st.success(f"✅ {'Updated' if full_name in existing_names else 'Added'} record for {full_name}")
                # Clear cache to refresh data
                load_children.clear()
                
        except Exception as e:
            st.error(f"Error saving record: {str(e)}")

elif page == "🗓️ Attendance":
    st.title("🗓️ Mark Attendance")
    
    if not children_df.empty:
        session_date = st.date_input("Session Date", date.today())
        
        with st.form("attendance_form"):
            st.write("Mark attendance for each child:")
            
            # Create columns for the header
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
            with col1:
                st.write("**Name**")
            with col2:
                st.write("**Present**")
            with col3:
                st.write("**Bible**")
            with col4:
                st.write("**Offering**")
            
            attendance_records = []
            
            # Create a container for scrollable content
            with st.container():
                for _, child in children_df.iterrows():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                    with col1:
                        st.write(child["full_name"])
                    with col2:
                        present = st.checkbox("Present", key=f"present_{child['id']}")
                    with col3:
                        bible = st.checkbox("Bible", key=f"bible_{child['id']}")
                    with col4:
                        offering = st.checkbox("Offering", key=f"offering_{child['id']}")
                    
                    if present:
                        attendance_records.append({
                            "child_id": child["id"],
                            "session_date": session_date.isoformat(),
                            "present": present,
                            "has_bible": bible,
                            "gave_offering": offering
                        })
            
            submitted = st.form_submit_button("Save Attendance")
            
            if submitted:
                try:
                    for record in attendance_records:
                        save_attendance(record)
                        st.success("✅ Attendance saved successfully!")
                    load_attendance.clear()
                except Exception as e:
                    st.error(f"Error saving attendance: {str(e)}")
    else:
        st.warning("No children registered yet!")

elif page == "📊 Reports":
    st.title("📊 Attendance Reports")
    
    if not attendance_df.empty:
        report_type = st.selectbox(
            "Select Report Type",
            ["Daily Attendance", "Weekly Summary", "Monthly Summary"]
        )
        
        if report_type == "Daily Attendance":
            selected_date = st.date_input("Select Date", date.today())
            
            # Filter attendance for selected date
            daily_attendance = attendance_df[attendance_df["session_date"] == selected_date.isoformat()]
            
            if not daily_attendance.empty:
                # Join with children data to show names
                daily_attendance = daily_attendance.merge(
                    children_df[["id", "full_name"]],
                    left_on="child_id",
                    right_on="id",
                    how="left"
                )
                st.dataframe(daily_attendance)
                
                # Show statistics
                total_present = daily_attendance["present"].sum()
                total_bible = daily_attendance["has_bible"].sum()
                total_offering = daily_attendance["gave_offering"].sum()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Present", total_present)
                with col2:
                    st.metric("Brought Bible", total_bible)
                with col3:
                    st.metric("Brought Offering", total_offering)
            else:
                st.info("No attendance records for selected date")
    else:
        st.info("No attendance records found")

elif page == "👤 Profile":
    st.title("👤 Child Profile")
    
    if not children_df.empty:
        selected_child = st.selectbox("Select a Child", sorted(children_df["full_name"].tolist()))
        child_info = children_df[children_df["full_name"] == selected_child].iloc[0]
        
        st.subheader("📋 Personal Info")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.info("📷 No profile photo available")
        
        with col2:
            for column in children_df.columns:
                if column != "full_name":
                    st.write(f"**{column}:** {child_info[column]}")
        
        # Show attendance records
        st.subheader("📅 Attendance Records")
        child_attendance = attendance_df[attendance_df["child_id"] == child_info["id"]]
        
        if not child_attendance.empty:
            st.dataframe(child_attendance)
            
            # Calculate statistics
            total_sessions = len(child_attendance)
            present_count = (child_attendance["present"] == True).sum()
            bible_count = (child_attendance["has_bible"] == True).sum()
            offering_count = (child_attendance["gave_offering"] == True).sum()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Sessions", total_sessions)
            with col2:
                st.metric("Attendance Rate", f"{(present_count/total_sessions*100):.1f}%")
            with col3:
                st.metric("Bible Rate", f"{(bible_count/total_sessions*100):.1f}%")
            with col4:
                st.metric("Offering Rate", f"{(offering_count/total_sessions*100):.1f}%")
        else:
            st.info("No attendance records found for this child")
    else:
        st.warning("No children registered yet!")

elif page == "✏️ Edit Profiles":
    st.title("✏️ Edit or Delete Child Profile")
    
    if not children_df.empty:
        selected_child = st.selectbox("Select a Child", sorted(children_df["full_name"].tolist()))
        child_info = children_df[children_df["full_name"] == selected_child].iloc[0]
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🗑️ Delete Profile"):
                try:
                    # Get Supabase client
                    supabase = get_supabase_client()
                    if not supabase:
                        st.error("Could not connect to database")
                        st.stop()
                    
                    # Delete attendance records first (due to foreign key constraint)
                    supabase.table('attendance').delete().eq('child_id', child_info['id']).execute()
                    
                    # Delete child record
                    supabase.table('children').delete().eq('id', child_info['id']).execute()
                    
                    st.success(f"✅ Deleted {selected_child}'s profile and attendance records")
                    load_children.clear()
                    load_attendance.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting profile: {str(e)}")
        
        with st.form("edit_form"):
            st.subheader("Edit Information")
            
            full_name = st.text_input("Full Name", value=child_info["full_name"])
            gender = st.selectbox(
                "Gender", 
                ["", "Male", "Female"],
                index=["", "Male", "Female"].index(child_info["gender"]) if child_info["gender"] in ["Male", "Female"] else 0
            )
            
            dob = st.date_input(
                "Date of Birth",
                value=datetime.strptime(child_info["date_of_birth"], "%Y-%m-%d").date() if child_info["date_of_birth"] else date.today(),
                max_value=date.today()
            )
            
            school = st.text_input("School Name", value=child_info["school"])
            grade = st.selectbox(
                "Grade / Form",
                [""] + [
                    "PP1", "PP2", "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6",
                    "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12",
                    "Form 1", "Form 2", "Form 3", "Form 4"
                ],
                index=[""] + [
                    "PP1", "PP2", "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6",
                    "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12",
                    "Form 1", "Form 2", "Form 3", "Form 4"
                ].index(child_info["grade"]) if child_info["grade"] else 0
            )
            
            class_group = st.selectbox(
                "Group/Class",
                [
                    "Chosen Generation(grade PP1–PP2)",
                    "Chosen Nation(grade 1–3)",
                    "Priesthood (grade 4–6)",
                    "Preisthood 2(grade 7–12)",
                    "Priesthood 2(form 1–4)"
                ],
                index=[
                    "Chosen Generation(grade PP1–PP2)",
                    "Chosen Nation(grade 1–3)",
                    "Priesthood (grade 4–6)",
                    "Preisthood 2(grade 7–12)",
                    "Priesthood 2(form 1–4)"
                ].index(child_info["class_group"]) if child_info["class_group"] else 0
            )
            
            residence = st.text_input("Residence", value=child_info["residence"])
            parent1 = st.text_input("Parent/Guardian 1", value=child_info["parent1_name"])
            contact1 = st.text_input("Contact 1", value=child_info["parent1_contact"])
            parent2 = st.text_input("Parent/Guardian 2", value=child_info["parent2_name"])
            contact2 = st.text_input("Contact 2", value=child_info["parent2_contact"])
            sponsored = st.checkbox("Sponsored by OCM", value=child_info["sponsored"] == "Yes")
            
            submitted = st.form_submit_button("💾 Save Changes")
            
            if submitted:
                try:
                    # Prepare updated record
                    updated_record = {
                        "full_name": full_name,
                        "gender": gender,
                        "date_of_birth": dob.isoformat(),
                        "school": school,
                        "grade": grade,
                        "class_group": class_group,
                        "residence": residence,
                        "parent1_name": parent1,
                        "parent1_contact": contact1,
                        "parent2_name": parent2,
                        "parent2_contact": contact2,
                        "sponsored": sponsored
                    }
                    
                    # Update the record
                    row_idx = children_df[children_df["full_name"] == selected_child].index[0] + 2
                    sheet = get_supabase_client().open(st.secrets['spreadsheet_id'])
                    worksheet = sheet.worksheet("Children")
                    worksheet.update(f'A{row_idx}:M{row_idx}', [updated_record])
                    
                    # Update attendance records if name changed
                    if full_name != selected_child:
                        attendance_sheet = get_supabase_client().open(st.secrets['spreadsheet_id'])
                        attendance_data = attendance_sheet.worksheet("Attendance").get_all_records()
                        for idx, record in enumerate(attendance_data):
                            if record["Child Name"] == selected_child:
                                attendance_sheet.worksheet("Attendance").update_cell(idx + 2, 2, full_name)  # +2 for header and 1-based index
                    
                    st.success("✅ Profile updated successfully!")
                    load_children.clear()
                except Exception as e:
                    st.error(f"Error updating profile: {str(e)}")
    else:
        st.warning("No children registered yet!")

