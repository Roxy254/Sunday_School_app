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
            col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5])
            with col1:
                st.write("**Name**")
            with col2:
                st.write("**Present**")
            with col3:
                st.write("**Early**")
            with col4:
                st.write("**Book**")
            with col5:
                st.write("**Pen**")
            with col6:
                st.write("**Bible**")
            with col7:
                st.write("**Offering**")
            
            attendance_records = []
            
            # Create a container for scrollable content
            with st.container():
                for _, child in children_df.iterrows():
                    col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5])
                    with col1:
                        st.write(child["full_name"])
                    with col2:
                        present = st.checkbox("Present", key=f"present_{child['id']}")
                    with col3:
                        early = st.checkbox("Early", key=f"early_{child['id']}")
                    with col4:
                        book = st.checkbox("Book", key=f"book_{child['id']}")
                    with col5:
                        pen = st.checkbox("Pen", key=f"pen_{child['id']}")
                    with col6:
                        bible = st.checkbox("Bible", key=f"bible_{child['id']}")
                    with col7:
                        offering = st.checkbox("Offering", key=f"offering_{child['id']}")
                    
                    if present:
                        attendance_records.append({
                            "child_id": child["id"],
                            "session_date": session_date.isoformat(),
                            "present": present,
                            "early": early,
                            "has_book": book,
                            "has_pen": pen,
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
    
    if not attendance_df.empty and not children_df.empty:
        report_type = st.selectbox(
            "Select Report Type",
            ["Daily Attendance", "Weekly Summary", "Monthly Summary"]
        )
        
        if report_type == "Daily Attendance":
            selected_date = st.date_input("Select Date", date.today())
            
            # Filter attendance for selected date
            daily_attendance = attendance_df[attendance_df['session_date'] == selected_date.isoformat()]
            
            # Get all children for the day
            all_children = children_df.copy()
            
            # Mark present/absent
            present_ids = daily_attendance['child_id'].unique()
            all_children['status'] = all_children['id'].apply(lambda x: 'Present' if x in present_ids else 'Absent')
            
            # Overall Statistics
            total_children = len(all_children)
            total_present = len(present_ids)
            total_absent = total_children - total_present
            
            # Display overall statistics
            st.markdown("### 📈 Overall Attendance")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Children", total_children)
            with col2:
                st.metric("Present", total_present)
            with col3:
                st.metric("Absent", total_absent)
            
            if not daily_attendance.empty:
                st.markdown("### 📚 Overall Participation")
                total_early = daily_attendance['early'].sum()
                total_books = daily_attendance['has_book'].sum()
                total_pens = daily_attendance['has_pen'].sum()
                total_bibles = daily_attendance['has_bible'].sum()
                total_offerings = daily_attendance['gave_offering'].sum()
                
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("Early Arrival", f"{total_early} ({(total_early/total_present*100):.1f}%)")
                with col2:
                    st.metric("With Books", f"{total_books} ({(total_books/total_present*100):.1f}%)")
                with col3:
                    st.metric("With Pens", f"{total_pens} ({(total_pens/total_present*100):.1f}%)")
                with col4:
                    st.metric("With Bibles", f"{total_bibles} ({(total_bibles/total_present*100):.1f}%)")
                with col5:
                    st.metric("With Offering", f"{total_offerings} ({(total_offerings/total_present*100):.1f}%)")
            
            # Class-wise Statistics
            st.markdown("### 📊 Class-wise Attendance")
            for class_name in all_children['class_group'].unique():
                st.markdown(f"#### {class_name}")
                class_children = all_children[all_children['class_group'] == class_name]
                class_present = len(class_children[class_children['status'] == 'Present'])
                class_absent = len(class_children[class_children['status'] == 'Absent'])
                
                # Basic attendance metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total", len(class_children))
                with col2:
                    st.metric("Present", class_present)
                with col3:
                    st.metric("Absent", class_absent)
                
                # Detailed participation metrics for this class
                if class_present > 0:
                    present_children = class_children[class_children['status'] == 'Present']
                    present_df = daily_attendance[daily_attendance['child_id'].isin(present_children['id'])]
                    
                    class_early = present_df['early'].sum()
                    class_books = present_df['has_book'].sum()
                    class_pens = present_df['has_pen'].sum()
                    class_bibles = present_df['has_bible'].sum()
                    class_offerings = present_df['gave_offering'].sum()
                    
                    st.markdown("**Class Participation:**")
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.metric("Early", f"{class_early} ({(class_early/class_present*100):.1f}%)")
                    with col2:
                        st.metric("Books", f"{class_books} ({(class_books/class_present*100):.1f}%)")
                    with col3:
                        st.metric("Pens", f"{class_pens} ({(class_pens/class_present*100):.1f}%)")
                    with col4:
                        st.metric("Bibles", f"{class_bibles} ({(class_bibles/class_present*100):.1f}%)")
                    with col5:
                        st.metric("Offering", f"{class_offerings} ({(class_offerings/class_present*100):.1f}%)")
                    
                    # Show present children with their details
                    st.markdown("**Present Children Details:**")

                    # Debug information
                    st.write("Debug - present_df columns before merge:", present_df.columns.tolist())
                    st.write("Debug - present_children columns:", present_children[['id', 'full_name']].columns.tolist())

                    # Merge the DataFrames
                    present_df = present_df.merge(
                        present_children[['id', 'full_name']],
                        left_on='child_id',
                        right_on='id',
                        suffixes=('_attendance', '_child')
                    )

                    st.write("Debug - present_df columns after merge:", present_df.columns.tolist())

                    # Create display DataFrame with only the columns that exist
                    display_columns = {
                        'full_name': 'Name',
                        'early': 'Early',
                        'has_book': 'Book',
                        'has_pen': 'Pen',
                        'has_bible': 'Bible',
                        'gave_offering': 'Offering'
                    }

                    # Get available columns (using exact column names from debug output)
                    available_columns = [col for col in display_columns.keys() if col in present_df.columns]

                    # Create display DataFrame
                    if available_columns:
                        display_df = present_df[available_columns].copy()
                        display_df.columns = [display_columns[col] for col in available_columns]
                        st.dataframe(display_df)
                    else:
                        st.warning("No display columns available in the data")
                
                # Show absent children in this class
                if class_absent > 0:
                    absent_children = class_children[class_children['status'] == 'Absent']
                    st.markdown("**Absent Children:**")
                    st.dataframe(absent_children[['full_name']])
                
                st.markdown("---")  # Add a separator between classes
            
            # OCM Children Statistics
            st.markdown("### 👥 OCM Children Attendance")
            ocm_children = all_children[all_children['sponsored'] == True]
            if not ocm_children.empty:
                ocm_present = len(ocm_children[ocm_children['status'] == 'Present'])
                ocm_absent = len(ocm_children[ocm_children['status'] == 'Absent'])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total OCM Children", len(ocm_children))
                with col2:
                    st.metric("Present", ocm_present)
                with col3:
                    st.metric("Absent", ocm_absent)
                
                if ocm_present > 0:
                    # Get participation stats for OCM children
                    present_ocm = ocm_children[ocm_children['status'] == 'Present']
                    ocm_attendance = daily_attendance[daily_attendance['child_id'].isin(present_ocm['id'])]
                    
                    ocm_early = ocm_attendance['early'].sum()
                    ocm_books = ocm_attendance['has_book'].sum()
                    ocm_pens = ocm_attendance['has_pen'].sum()
                    ocm_bibles = ocm_attendance['has_bible'].sum()
                    ocm_offerings = ocm_attendance['gave_offering'].sum()
                    
                    st.markdown("**OCM Children Participation:**")
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.metric("Early", f"{ocm_early} ({(ocm_early/ocm_present*100):.1f}%)")
                    with col2:
                        st.metric("Books", f"{ocm_books} ({(ocm_books/ocm_present*100):.1f}%)")
                    with col3:
                        st.metric("Pens", f"{ocm_pens} ({(ocm_pens/ocm_present*100):.1f}%)")
                    with col4:
                        st.metric("Bibles", f"{ocm_bibles} ({(ocm_bibles/ocm_present*100):.1f}%)")
                    with col5:
                        st.metric("Offering", f"{ocm_offerings} ({(ocm_offerings/ocm_present*100):.1f}%)")
                    
                    # Show present OCM children with their details
                    st.markdown("**Present OCM Children Details:**")
                    present_ocm_df = ocm_attendance.merge(present_ocm[['id', 'full_name', 'class_group']], 
                                                        left_on='child_id', right_on='id')
                    display_df = present_ocm_df[['full_name', 'class_group', 'early', 'has_book', 
                                               'has_pen', 'has_bible', 'gave_offering']]
                    display_df.columns = ['Name', 'Class', 'Early', 'Book', 'Pen', 'Bible', 'Offering']
                    st.dataframe(display_df)
                
                # Show absent OCM children
                if ocm_absent > 0:
                    st.markdown("**Absent OCM Children:**")
                    absent_ocm = ocm_children[ocm_children['status'] == 'Absent']
                    st.dataframe(absent_ocm[['full_name', 'class_group']])
    else:
        st.warning("No attendance data available yet!")

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
        
        try:
            # Ensure child_info has the required id field
            if 'id' not in child_info:
                st.error("Error: Child record is missing ID field")
                st.stop()
                
            # Get attendance records for this child
            child_attendance = attendance_df[attendance_df['child_id'] == child_info['id']]
            
            if not child_attendance.empty:
                # Create a display-friendly version of the attendance data
                display_columns = ['session_date', 'present', 'early', 'has_book', 'has_pen', 'has_bible', 'gave_offering']
                display_attendance = child_attendance[display_columns].copy()
                display_attendance.columns = ['Date', 'Present', 'Early', 'Book', 'Pen', 'Bible', 'Offering']
                
                # Sort by date in descending order
                display_attendance = display_attendance.sort_values('Date', ascending=False)
                st.dataframe(display_attendance)
                
                # Calculate statistics
                total_sessions = len(child_attendance)
                present_count = child_attendance['present'].sum() if 'present' in child_attendance else 0
                early_count = child_attendance['early'].sum() if 'early' in child_attendance else 0
                book_count = child_attendance['has_book'].sum() if 'has_book' in child_attendance else 0
                pen_count = child_attendance['has_pen'].sum() if 'has_pen' in child_attendance else 0
                bible_count = child_attendance['has_bible'].sum() if 'has_bible' in child_attendance else 0
                offering_count = child_attendance['gave_offering'].sum() if 'gave_offering' in child_attendance else 0
                
                # Display metrics in two rows
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Sessions", total_sessions)
                with col2:
                    st.metric("Attendance Rate", f"{(present_count/total_sessions*100):.1f}%" if total_sessions > 0 else "0%")
                with col3:
                    st.metric("Early Rate", f"{(early_count/total_sessions*100):.1f}%" if total_sessions > 0 else "0%")
                with col4:
                    st.metric("Book Rate", f"{(book_count/total_sessions*100):.1f}%" if total_sessions > 0 else "0%")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Pen Rate", f"{(pen_count/total_sessions*100):.1f}%" if total_sessions > 0 else "0%")
                with col2:
                    st.metric("Bible Rate", f"{(bible_count/total_sessions*100):.1f}%" if total_sessions > 0 else "0%")
                with col3:
                    st.metric("Offering Rate", f"{(offering_count/total_sessions*100):.1f}%" if total_sessions > 0 else "0%")
            else:
                st.info("No attendance records found for this child")
        except Exception as e:
            st.error(f"Error displaying attendance records: {str(e)}")
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

