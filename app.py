import streamlit as st
import pandas as pd
import numpy as np
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
    st.title("🗓️ Sunday Attendance")
    
    if not children_df.empty:
        session_date = st.date_input("Sunday Date", date.today())
        
        with st.form("attendance_form"):
            st.write("Mark Sunday attendance for each child:")
            
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
    st.title("📊 Sunday Attendance Reports")
    
    if not attendance_df.empty and not children_df.empty:
        report_type = st.selectbox(
            "Select Report Type",
            ["Sunday Attendance", "Weekly Summary", "Monthly Summary"]
        )
        
        if report_type == "Sunday Attendance":
            selected_date = st.date_input("Select Sunday Date", date.today())
            
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

                    # Merge the DataFrames
                    present_df = present_df.merge(
                        present_children[['id', 'full_name']],
                        left_on='child_id',
                        right_on='id',
                        suffixes=('_attendance', '_child')
                    )

                    # Create display DataFrame with only the columns that exist
                    display_columns = {
                        'full_name_child': 'Name',
                        'early': 'Early',
                        'has_book': 'Book',
                        'has_pen': 'Pen',
                        'has_bible': 'Bible',
                        'gave_offering': 'Offering'
                    }

                    # Get available columns
                    available_columns = [col for col in display_columns.keys() if col in present_df.columns]

                    # Create display DataFrame
                    if available_columns:
                        display_df = present_df[available_columns].copy()
                        display_df.columns = [display_columns[col] for col in available_columns]
                        st.dataframe(display_df, use_container_width=True)
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
        elif report_type == "Monthly Summary":
            st.markdown("### 📊 Monthly Attendance Overview")
            
            # Get current month and year
            current_date = datetime.now()
            selected_month = st.selectbox(
                "Select Month",
                range(1, 13),
                index=current_date.month - 1
            )
            selected_year = st.selectbox(
                "Select Year",
                range(current_date.year - 2, current_date.year + 1),
                index=2
            )
            
            # Filter attendance for selected month
            monthly_attendance = attendance_df[
                (pd.to_datetime(attendance_df['session_date']).dt.month == selected_month) &
                (pd.to_datetime(attendance_df['session_date']).dt.year == selected_year)
            ]
            
            if not monthly_attendance.empty:
                # Get unique dates in the month
                session_dates = pd.to_datetime(monthly_attendance['session_date']).unique()
                total_sessions = len(session_dates)
                
                # Overall Statistics
                total_children = len(children_df)
                avg_attendance = len(monthly_attendance) / total_sessions if total_sessions > 0 else 0
                attendance_rate = (avg_attendance / total_children * 100) if total_children > 0 else 0
                
                # Display overall statistics
                st.markdown("#### 📈 Overall Statistics")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Sessions", total_sessions)
                with col2:
                    st.metric("Total Children", total_children)
                with col3:
                    st.metric("Avg. Attendance", f"{avg_attendance:.1f}")
                with col4:
                    st.metric("Attendance Rate", f"{attendance_rate:.1f}%")
                
                # Participation Trends
                st.markdown("#### 📊 Monthly Participation Trends")
                
                # Calculate daily stats
                daily_stats = []
                for session_date in session_dates:
                    day_attendance = monthly_attendance[
                        pd.to_datetime(monthly_attendance['session_date']) == session_date
                    ]
                    stats = {
                        'Date': session_date.strftime('%Y-%m-%d'),
                        'Present': len(day_attendance),
                        'Early': day_attendance['early'].sum(),
                        'Books': day_attendance['has_book'].sum(),
                        'Pens': day_attendance['has_pen'].sum(),
                        'Bibles': day_attendance['has_bible'].sum(),
                        'Offering': day_attendance['gave_offering'].sum()
                    }
                    daily_stats.append(stats)
                
                trends_df = pd.DataFrame(daily_stats)
                st.line_chart(trends_df.set_index('Date')[['Present', 'Early', 'Books', 'Pens', 'Bibles', 'Offering']])
                
                # Class-wise Monthly Statistics
                st.markdown("#### 📚 Class-wise Monthly Statistics")
                
                for class_name in children_df['class_group'].unique():
                    st.markdown(f"**{class_name}**")
                    
                    # Get children in this class
                    class_children = children_df[children_df['class_group'] == class_name]
                    class_attendance = monthly_attendance[
                        monthly_attendance['child_id'].isin(class_children['id'])
                    ]
                    
                    if not class_attendance.empty:
                        # Calculate class statistics
                        total_class_children = len(class_children)
                        avg_class_attendance = len(class_attendance) / total_sessions if total_sessions > 0 else 0
                        class_attendance_rate = (avg_class_attendance / total_class_children * 100) if total_class_children > 0 else 0
                        
                        # Display class metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Children", total_class_children)
                        with col2:
                            st.metric("Avg. Attendance", f"{avg_class_attendance:.1f}")
                        with col3:
                            st.metric("Attendance Rate", f"{class_attendance_rate:.1f}%")
                        
                        # Calculate participation rates
                        early_rate = (class_attendance['early'].sum() / len(class_attendance) * 100) if len(class_attendance) > 0 else 0
                        book_rate = (class_attendance['has_book'].sum() / len(class_attendance) * 100) if len(class_attendance) > 0 else 0
                        pen_rate = (class_attendance['has_pen'].sum() / len(class_attendance) * 100) if len(class_attendance) > 0 else 0
                        bible_rate = (class_attendance['has_bible'].sum() / len(class_attendance) * 100) if len(class_attendance) > 0 else 0
                        offering_rate = (class_attendance['gave_offering'].sum() / len(class_attendance) * 100) if len(class_attendance) > 0 else 0
                        
                        # Display participation metrics
                        col1, col2, col3, col4, col5 = st.columns(5)
                        with col1:
                            st.metric("Early %", f"{early_rate:.1f}%")
                        with col2:
                            st.metric("Books %", f"{book_rate:.1f}%")
                        with col3:
                            st.metric("Pens %", f"{pen_rate:.1f}%")
                        with col4:
                            st.metric("Bibles %", f"{bible_rate:.1f}%")
                        with col5:
                            st.metric("Offering %", f"{offering_rate:.1f}%")
                        
                        # Show attendance details
                        with st.expander("View Detailed Attendance"):
                            # Merge attendance with children data
                            detailed_attendance = class_attendance.merge(
                                class_children[['id', 'full_name']],
                                left_on='child_id',
                                right_on='id',
                                suffixes=('_attendance', '')
                            )
                            
                            # Calculate attendance count and rate per child
                            attendance_stats = []
                            for _, child in class_children.iterrows():
                                child_id = child['id']
                                child_name = child['full_name']
                                
                                # Check if child is new (no attendance in March/April 2025)
                                march_april_attendance = attendance_df[
                                    (attendance_df['child_id'] == child_id) &
                                    (pd.to_datetime(attendance_df['session_date']).dt.year == 2025) &
                                    (pd.to_datetime(attendance_df['session_date']).dt.month.isin([3, 4]))
                                ]
                                
                                is_new_child = march_april_attendance.empty
                                
                                # Get child's attendance records
                                child_attendance = detailed_attendance[detailed_attendance['child_id'] == child_id]
                                
                                if not child_attendance.empty:
                                    if is_new_child:
                                        # For new children, use their first attendance date
                                        first_attendance = pd.to_datetime(child_attendance['session_date']).min()
                                        available_sessions = len(pd.date_range(first_attendance, pd.Timestamp.now(), freq='W-SUN'))
                                    else:
                                        # For existing children, count from March 2025
                                        first_attendance = pd.Timestamp('2025-03-01')
                                        available_sessions = total_sessions
                                    
                                    sessions_attended = len(child_attendance[
                                        pd.to_datetime(child_attendance['session_date']) >= first_attendance
                                    ])
                                    
                                    attendance_rate = (sessions_attended / available_sessions * 100) if available_sessions > 0 else 0
                                    
                                    attendance_stats.append({
                                        'Name': child_name,
                                        'First Attendance': first_attendance.strftime('%Y-%m-%d'),
                                        'Available Sessions': available_sessions,
                                        'Sessions Attended': sessions_attended,
                                        'Attendance Rate': round(attendance_rate, 1)
                                    })
                            
                            if attendance_stats:
                                # Convert to DataFrame and display
                                attendance_df = pd.DataFrame(attendance_stats)
                                st.dataframe(attendance_df, use_container_width=True)
                
                # OCM Children Monthly Statistics
                st.markdown("#### 👥 OCM Children Monthly Statistics")
                ocm_children = children_df[children_df['sponsored'] == True]
                
                if not ocm_children.empty:
                    ocm_attendance = monthly_attendance[
                        monthly_attendance['child_id'].isin(ocm_children['id'])
                    ]
                    
                    if not ocm_attendance.empty:
                        # Calculate OCM statistics
                        total_ocm = len(ocm_children)
                        avg_ocm_attendance = len(ocm_attendance) / total_sessions if total_sessions > 0 else 0
                        ocm_attendance_rate = (avg_ocm_attendance / total_ocm * 100) if total_ocm > 0 else 0
                        
                        # Display OCM metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total OCM Children", total_ocm)
                        with col2:
                            st.metric("Avg. Attendance", f"{avg_ocm_attendance:.1f}")
                        with col3:
                            st.metric("Attendance Rate", f"{ocm_attendance_rate:.1f}%")
                        
                        # Calculate participation rates
                        ocm_early_rate = (ocm_attendance['early'].sum() / len(ocm_attendance) * 100) if len(ocm_attendance) > 0 else 0
                        ocm_book_rate = (ocm_attendance['has_book'].sum() / len(ocm_attendance) * 100) if len(ocm_attendance) > 0 else 0
                        ocm_pen_rate = (ocm_attendance['has_pen'].sum() / len(ocm_attendance) * 100) if len(ocm_attendance) > 0 else 0
                        ocm_bible_rate = (ocm_attendance['has_bible'].sum() / len(ocm_attendance) * 100) if len(ocm_attendance) > 0 else 0
                        ocm_offering_rate = (ocm_attendance['gave_offering'].sum() / len(ocm_attendance) * 100) if len(ocm_attendance) > 0 else 0
                        
                        # Display participation metrics
                        col1, col2, col3, col4, col5 = st.columns(5)
                        with col1:
                            st.metric("Early %", f"{ocm_early_rate:.1f}%")
                        with col2:
                            st.metric("Books %", f"{ocm_book_rate:.1f}%")
                        with col3:
                            st.metric("Pens %", f"{ocm_pen_rate:.1f}%")
                        with col4:
                            st.metric("Bibles %", f"{ocm_bible_rate:.1f}%")
                        with col5:
                            st.metric("Offering %", f"{ocm_offering_rate:.1f}%")
                        
                        # Show OCM attendance details
                        with st.expander("View Detailed OCM Attendance"):
                            # Merge attendance with children data
                            detailed_ocm = ocm_attendance.merge(
                                ocm_children[['id', 'full_name', 'class_group']],
                                left_on='child_id',
                                right_on='id',
                                suffixes=('_attendance', '_child')
                            )
                            
                            # Calculate attendance count per child
                            ocm_counts = detailed_ocm.groupby(['full_name', 'class_group']).size().reset_index()
                            ocm_counts.columns = ['Name', 'Class', 'Sessions Attended']
                            ocm_counts['Attendance Rate'] = (ocm_counts['Sessions Attended'] / total_sessions * 100).round(1)
                            
                            # Display the detailed attendance
                            st.dataframe(ocm_counts, use_container_width=True)
                else:
                    st.info("No OCM sponsored children registered")
            else:
                st.info(f"No attendance records found for {datetime(selected_year, selected_month, 1).strftime('%B %Y')}")
    else:
        st.warning("No attendance data available yet!")

elif page == "👤 Profile":
    st.title("👤 Child Profile")
    
    if not children_df.empty:
        # Add class filter
        class_options = ["All Classes"] + sorted(children_df["class_group"].unique().tolist())
        selected_class = st.selectbox("Select Class", class_options)
        
        # Filter children by class if a specific class is selected
        filtered_df = children_df if selected_class == "All Classes" else children_df[children_df["class_group"] == selected_class]
        
        # Add search box
        search_name = st.text_input("Search by Name", "")
        
        # Filter by search if provided
        if search_name:
            filtered_df = filtered_df[filtered_df["full_name"].str.lower().str.contains(search_name.lower())]
        
        if not filtered_df.empty:
            selected_child = st.selectbox("Select a Child", sorted(filtered_df["full_name"].tolist()))
            child_info = filtered_df[filtered_df["full_name"] == selected_child].iloc[0]
            
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
                
                # Get all attendance records for this child
                child_attendance = attendance_df[attendance_df['child_id'] == child_info['id']]
                
                if not child_attendance.empty:
                    # Get the child's class group
                    class_group = child_info['class_group']
                    
                    # Define the start date for attendance tracking (March 1, 2025)
                    start_date = pd.Timestamp('2025-03-01')
                    
                    # Check if child has any attendance in March or April 2025
                    march_april_attendance = attendance_df[
                        (attendance_df['child_id'] == child_info['id']) &
                        (pd.to_datetime(attendance_df['session_date']).dt.year == 2025) &
                        (pd.to_datetime(attendance_df['session_date']).dt.month.isin([3, 4]))
                    ]
                    
                    is_new_child = march_april_attendance.empty
                    
                    if is_new_child:
                        # For new children, use their first attendance date
                        first_attendance_date = pd.to_datetime(child_attendance['session_date']).min()
                        st.info(f"📝 New child! First attendance: {first_attendance_date.strftime('%Y-%m-%d')}")
                    else:
                        # For existing children, use March 1, 2025
                        first_attendance_date = start_date
                        st.info("👥 Existing child - Attendance tracked from March 2025")
                    
                    # Get all class sessions since the tracking start date
                    class_sessions = attendance_df[
                        pd.to_datetime(attendance_df['session_date']) >= first_attendance_date
                    ]['session_date'].unique()
                    total_available_sessions = len(class_sessions)
                    
                    # Get child's attendance records since tracking start date
                    tracked_attendance = child_attendance[
                        pd.to_datetime(child_attendance['session_date']) >= first_attendance_date
                    ]
                    
                    # Calculate attendance statistics
                    present_count = len(tracked_attendance)
                    absent_count = total_available_sessions - present_count
                    attendance_rate = (present_count / total_available_sessions * 100) if total_available_sessions > 0 else 0
                    
                    # Calculate participation rates based on attended sessions
                    early_rate = (tracked_attendance['early'].sum() / present_count * 100) if present_count > 0 else 0
                    book_rate = (tracked_attendance['has_book'].sum() / present_count * 100) if present_count > 0 else 0
                    pen_rate = (tracked_attendance['has_pen'].sum() / present_count * 100) if present_count > 0 else 0
                    bible_rate = (tracked_attendance['has_bible'].sum() / present_count * 100) if present_count > 0 else 0
                    offering_rate = (tracked_attendance['gave_offering'].sum() / present_count * 100) if present_count > 0 else 0
                    
                    # Display attendance summary
                    st.markdown("#### 📊 Attendance Summary")
                    st.markdown(f"**Tracking Start Date:** {first_attendance_date.strftime('%Y-%m-%d')}")
                    st.markdown(f"**Total Available Sessions:** {total_available_sessions}")
                    
                    # Display metrics in two rows
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Sessions Present", present_count)
                    with col2:
                        st.metric("Sessions Absent", absent_count)
                    with col3:
                        st.metric("Attendance Rate", f"{attendance_rate:.1f}%")
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.metric("Early Rate", f"{early_rate:.1f}%")
                    with col2:
                        st.metric("Book Rate", f"{book_rate:.1f}%")
                    with col3:
                        st.metric("Pen Rate", f"{pen_rate:.1f}%")
                    with col4:
                        st.metric("Bible Rate", f"{bible_rate:.1f}%")
                    with col5:
                        st.metric("Offering Rate", f"{offering_rate:.1f}%")
                    
                    # Show detailed attendance records
                    st.markdown("#### 📅 Detailed Attendance Records")
                    
                    # Create a DataFrame with all sessions since tracking start
                    all_sessions_df = pd.DataFrame({
                        'session_date': class_sessions
                    })
                    
                    # Merge with actual attendance to get present/absent status
                    detailed_attendance = all_sessions_df.merge(
                        tracked_attendance[['session_date', 'early', 'has_book', 'has_pen', 'has_bible', 'gave_offering']],
                        on='session_date',
                        how='left'
                    )
                    
                    # Fill NaN values (absent days)
                    detailed_attendance = detailed_attendance.fillna(False)
                    
                    # Add status column
                    detailed_attendance['Status'] = np.where(
                        pd.isna(detailed_attendance['early']),
                        'Absent',
                        'Present'
                    )
                    
                    # Format for display
                    display_df = detailed_attendance.copy()
                    display_df['Date'] = pd.to_datetime(display_df['session_date']).dt.strftime('%Y-%m-%d')
                    display_df['Early'] = display_df['early'].map({True: '✅', False: '❌'})
                    display_df['Book'] = display_df['has_book'].map({True: '✅', False: '❌'})
                    display_df['Pen'] = display_df['has_pen'].map({True: '✅', False: '❌'})
                    display_df['Bible'] = display_df['has_bible'].map({True: '✅', False: '❌'})
                    display_df['Offering'] = display_df['gave_offering'].map({True: '✅', False: '❌'})
                    
                    # Sort by date in descending order
                    display_df = display_df.sort_values('session_date', ascending=False)
                    
                    # Display the records
                    st.dataframe(
                        display_df[['Date', 'Status', 'Early', 'Book', 'Pen', 'Bible', 'Offering']],
                        use_container_width=True
                    )
                    
                    # Show trends
                    st.markdown("#### 📈 Attendance Trends")
                    
                    # Calculate monthly attendance rates
                    monthly_stats = detailed_attendance.copy()
                    monthly_stats['month'] = pd.to_datetime(monthly_stats['session_date']).dt.strftime('%Y-%m')
                    monthly_attendance = monthly_stats.groupby('month').agg({
                        'Status': lambda x: (x == 'Present').mean() * 100,
                        'early': 'mean',
                        'has_book': 'mean',
                        'has_pen': 'mean',
                        'has_bible': 'mean',
                        'gave_offering': 'mean'
                    }).reset_index()
                    
                    # Multiply by 100 to get percentages
                    for col in ['early', 'has_book', 'has_pen', 'has_bible', 'gave_offering']:
                        monthly_attendance[col] = monthly_attendance[col] * 100
                    
                    # Rename columns for display
                    monthly_attendance.columns = ['Month', 'Attendance', 'Early', 'Book', 'Pen', 'Bible', 'Offering']
                    
                    # Create line chart
                    st.line_chart(
                        monthly_attendance.set_index('Month')[['Attendance', 'Early', 'Book', 'Pen', 'Bible', 'Offering']]
                    )
                    
                    # Compare with class averages
                    st.markdown("#### 🔄 Comparison with Class Averages")
                    
                    # Get class attendance data since tracking start date
                    class_attendance = attendance_df[
                        (attendance_df['child_id'].isin(
                            children_df[children_df['class_group'] == class_group]['id']
                        )) &
                        (pd.to_datetime(attendance_df['session_date']) >= first_attendance_date)
                    ]
                    
                    if not class_attendance.empty:
                        # Calculate class averages
                        total_class_children = len(children_df[children_df['class_group'] == class_group])
                        class_present_rate = (len(class_attendance) / (total_class_children * total_available_sessions) * 100)
                        class_early_rate = (class_attendance['early'].sum() / len(class_attendance) * 100) if len(class_attendance) > 0 else 0
                        class_book_rate = (class_attendance['has_book'].sum() / len(class_attendance) * 100) if len(class_attendance) > 0 else 0
                        class_pen_rate = (class_attendance['has_pen'].sum() / len(class_attendance) * 100) if len(class_attendance) > 0 else 0
                        class_bible_rate = (class_attendance['has_bible'].sum() / len(class_attendance) * 100) if len(class_attendance) > 0 else 0
                        
                        # Display comparison
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric(
                                "Attendance vs Class",
                                f"{attendance_rate:.1f}%",
                                f"{(attendance_rate - class_present_rate):.1f}%"
                            )
                        with col2:
                            st.metric(
                                "Early vs Class",
                                f"{early_rate:.1f}%",
                                f"{(early_rate - class_early_rate):.1f}%"
                            )
                        with col3:
                            st.metric(
                                "Participation vs Class",
                                f"{((book_rate + pen_rate + bible_rate) / 3):.1f}%",
                                f"{((book_rate + pen_rate + bible_rate) / 3 - (class_book_rate + class_pen_rate + class_bible_rate) / 3):.1f}%"
                            )
                else:
                    st.info("No attendance records found for this child")
            except Exception as e:
                st.error(f"Error displaying attendance records: {str(e)}")
        else:
            st.warning("No children found matching the selected criteria!")
    else:
        st.warning("No children registered yet!")

elif page == "✏️ Edit Profiles":
    st.title("✏️ Edit or Delete Child Profile")
    
    if not children_df.empty:
        # Add class filter
        class_options = ["All Classes"] + sorted(children_df["class_group"].unique().tolist())
        selected_class = st.selectbox("Select Class", class_options)
        
        # Filter children by class if a specific class is selected
        filtered_df = children_df if selected_class == "All Classes" else children_df[children_df["class_group"] == selected_class]
        
        # Add search box
        search_name = st.text_input("Search by Name", "")
        
        # Filter by search if provided
        if search_name:
            filtered_df = filtered_df[filtered_df["full_name"].str.lower().str.contains(search_name.lower())]
        
        if not filtered_df.empty:
            selected_child = st.selectbox("Select a Child", sorted(filtered_df["full_name"].tolist()))
            child_info = filtered_df[filtered_df["full_name"] == selected_child].iloc[0]
            
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
                sponsored = st.checkbox("Sponsored by OCM", value=child_info["sponsored"])
                
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
                            "sponsored": sponsored,
                            "updated_at": datetime.now().isoformat()
                        }
                        
                        # Update using Supabase
                        supabase = get_supabase_client()
                        if not supabase:
                            st.error("Could not connect to database")
                            st.stop()
                            
                        # Update child record
                        response = supabase.table('children').update(updated_record).eq('id', child_info['id']).execute()
                        
                        if response.data:
                            st.success("✅ Profile updated successfully!")
                            load_children.clear()
                            st.rerun()
                        else:
                            st.error("Failed to update profile")
                            
                    except Exception as e:
                        st.error(f"Error updating profile: {str(e)}")
        else:
            st.warning("No children found matching the selected criteria!")
    else:
        st.warning("No children registered yet!")

