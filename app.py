import streamlit as st
import pandas as pd
import os
from datetime import datetime, date
from pymongo import MongoClient
from bson import ObjectId

# ✅ Must be the first Streamlit command
st.set_page_config(
    page_title="Sunday School App",
    page_icon="icon_2_4ze_icon.icon",
    layout="wide"
)

# Initialize session state for caching
if 'db' not in st.session_state:
    st.session_state.db = None
if 'children_cache' not in st.session_state:
    st.session_state.children_cache = None
if 'last_cache_update' not in st.session_state:
    st.session_state.last_cache_update = None

# MongoDB Atlas connection
@st.cache_resource
def get_database():
    try:
        if "MONGODB_URI" not in st.secrets:
            st.error("MONGODB_URI not found in secrets. Please check your .streamlit/secrets.toml file.")
            return None
            
        mongo_uri = st.secrets["MONGODB_URI"]
        client = MongoClient(mongo_uri)
        # Test the connection
        client.admin.command('ping')
        return client.sunday_school_db
    except Exception as e:
        st.error(f"Failed to connect to database: {str(e)}")
        return None

# Cache children data for 5 minutes
@st.cache_data(ttl=300)
def get_children_data(db):
    if db is not None:
        try:
            return list(db.children.find())
        except Exception as e:
            st.error(f"Error fetching children: {str(e)}")
            return []
    return []

# Cache attendance data for 5 minutes
@st.cache_data(ttl=300)
def get_attendance_data(db, query=None):
    if db is not None:
        try:
            if query:
                return list(db.attendance.find(query))
            return list(db.attendance.find())
        except Exception as e:
            st.error(f"Error fetching attendance: {str(e)}")
            return []
    return []

# Initialize database connection
db = get_database()

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

# Sidebar navigation
page = st.sidebar.selectbox("Choose a page", [
    "📋 Registration", "🗓️ Attendance", "📊 Reports", "📚 Performance", "👤 Profile", "✏️ Edit Profiles"
])

# Get cached children data
children = get_children_data(db)

if page == "📋 Registration":
    st.title("📋 Register or Update Child Record")

    existing_names = [child["Full Name"] for child in children]

    st.markdown("### ✍️ New or Incomplete Registration")

    with st.form("child_form"):
        full_name = st.text_input("Full Name")
        group = st.selectbox("Group/Class", [
            "Chosen Generation(grade PP1–PP2)",
            "Chosen Nation(grade 1–3)",
            "Priesthood (grade 4–6)",
            "Preisthood 2(grade 7–12)",
            "Priesthood 2(form 1–4)"
        ])
        st.markdown("*(The rest can be filled later)*")

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
        if db is not None:
            try:
                # Create child record
                child_data = {
                    "Full Name": full_name,
                    "Group/Class": group,
                    "Gender": gender,
                    "Date of Birth": dob.isoformat(),
                    "School": school,
                    "Grade": grade,
                    "Residence": residence,
                    "Parent 1": parent1,
                    "Contact 1": contact1,
                    "Parent 2": parent2,
                    "Contact 2": contact2,
                    "Sponsored by OCM": sponsored,
                    "Last Updated": datetime.now().isoformat()
                }

                # Update if exists, insert if new
                result = db.children.update_one(
                    {"Full Name": full_name},
                    {"$set": child_data},
                    upsert=True
                )
                
                if result.upserted_id:
                    st.success(f"✅ Added new record for {full_name}")
                else:
                    st.success(f"✅ Updated record for {full_name}")
            except Exception as e:
                st.error(f"Error saving record: {str(e)}")
        else:
            st.error("❌ Database connection failed")

elif page == "🗓️ Attendance":
    st.title("🗓️ Mark Attendance")
    
    if db is not None:
        if not children:
            st.warning("No children registered yet!")
        else:
            session_date = st.date_input("Session Date", date.today())
            
            # Get cached attendance data for the selected date
            attendance_records = get_attendance_data(db, {"date": session_date.isoformat()})
            attendance_dict = {str(record["child_id"]): record for record in attendance_records}
            
            with st.form("attendance_form"):
                st.write("Mark attendance for each child:")
                attendance_data = []
                
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
                
                # Create a container for scrollable content
                with st.container():
                    for child in children:
                        child_id = str(child["_id"])
                        previous_record = attendance_dict.get(child_id, {})
                        
                        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                        with col1:
                            st.write(child["Full Name"])
                        with col2:
                            present = st.checkbox("", 
                                               key=f"present_{child_id}",
                                               value=previous_record.get("present", False))
                        with col3:
                            bible = st.checkbox("", 
                                             key=f"bible_{child_id}",
                                             value=previous_record.get("brought_bible", False))
                        with col4:
                            offering = st.checkbox("", 
                                                key=f"offering_{child_id}",
                                                value=previous_record.get("brought_offering", False))
                        
                        attendance_data.append({
                            "child_id": child["_id"],
                            "name": child["Full Name"],
                            "present": present,
                            "bible": bible,
                            "offering": offering
                        })
                
                submitted = st.form_submit_button("Save Attendance")
                
                if submitted:
                    try:
                        # Batch update attendance records
                        operations = []
                        for record in attendance_data:
                            operations.append(
                                {
                                    "update_one": {
                                        "filter": {
                                            "child_id": record["child_id"],
                                            "date": session_date.isoformat()
                                        },
                                        "update": {
                                            "$set": {
                                                "child_name": record["name"],
                                                "date": session_date.isoformat(),
                                                "present": record["present"],
                                                "brought_bible": record["bible"],
                                                "brought_offering": record["offering"],
                                                "timestamp": datetime.now().isoformat()
                                            }
                                        },
                                        "upsert": True
                                    }
                                }
                            )
                        
                        if operations:
                            db.attendance.bulk_write(operations)
                            st.success("✅ Attendance saved successfully!")
                            # Clear the cache for attendance data
                            get_attendance_data.clear()
                    except Exception as e:
                        st.error(f"Error saving attendance: {str(e)}")
    else:
        st.error("❌ Database connection failed")

elif page == "📊 Reports":
    st.title("📊 Attendance Reports")
    
    if db is not None:
        try:
            report_type = st.selectbox(
                "Select Report Type",
                ["Daily Attendance", "Weekly Summary", "Monthly Summary"]
            )
            
            if report_type == "Daily Attendance":
                selected_date = st.date_input("Select Date", date.today())
                
                # Get attendance for selected date
                attendance_records = list(db.attendance.find({"date": selected_date.isoformat()}))
                
                if attendance_records:
                    df = pd.DataFrame(attendance_records)
                    df = df[["child_name", "present", "brought_bible", "brought_offering"]]
                    df.columns = ["Name", "Present", "Brought Bible", "Brought Offering"]
                    st.dataframe(df)
                    
                    # Show statistics
                    total_present = df["Present"].sum()
                    total_bible = df["Brought Bible"].sum()
                    total_offering = df["Brought Offering"].sum()
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Present", total_present)
                    with col2:
                        st.metric("Brought Bible", total_bible)
                    with col3:
                        st.metric("Brought Offering", total_offering)
                else:
                    st.info("No attendance records for selected date")
        except Exception as e:
            st.error(f"Error generating report: {str(e)}")
    else:
        st.error("❌ Database connection failed")

elif page == "📚 Performance":
    st.title("📚 Performance Tracking")

    perf_file = "data/performance_records.csv"
    children_file = "data/children_records.csv"
    os.makedirs("data", exist_ok=True)

    if os.path.exists(children_file):
        children_df = pd.read_csv(children_file)
        child_names = sorted(children_df["Full Name"].dropna().unique().tolist())

        if not child_names:
            st.warning("⚠️ No registered children.")
            st.stop()

        selected_child = st.selectbox("Select a Child", child_names)
        year = st.selectbox("Year", list(range(date.today().year, 2019, -1)))
        term = st.selectbox("Term", ["Term 1", "Term 2", "Term 3"])
        subjects = ["Math", "English", "Kiswahili", "Science", "CRE", "Other"]

        st.markdown("### ✍️ Enter Scores")
        scores = {}
        for subject in subjects:
            scores[subject] = st.number_input(
                f"{subject} Score", min_value=0, max_value=100, step=1, key=f"{subject}_score"
            )
        remarks = st.text_area("Remarks")

        if st.button("💾 Save Record"):
            record = {
                "Child Name": selected_child,
                "Year": year,
                "Term": term,
                **scores,
                "Remarks": remarks,
                "Date Recorded": date.today().strftime("%Y-%m-%d")
            }

            if os.path.exists(perf_file):
                perf_df = pd.read_csv(perf_file)
                perf_df = pd.concat([perf_df, pd.DataFrame([record])], ignore_index=True)
            else:
                perf_df = pd.DataFrame([record])

            perf_df.to_csv(perf_file, index=False)
            st.success("✅ Performance record saved!")

        # View past records
        st.markdown("---")
        st.subheader("📄 Past Records")

        if os.path.exists(perf_file):
            perf_df = pd.read_csv(perf_file)
            child_perf = perf_df[perf_df["Child Name"] == selected_child]

            if not child_perf.empty:
                st.dataframe(child_perf)

                chart_df = child_perf.copy()
                chart_df["Term_Year"] = chart_df["Year"].astype(str) + " " + chart_df["Term"]
                chart_df.set_index("Term_Year", inplace=True)
                st.subheader("📈 Score Trend")
                st.line_chart(chart_df[subjects])

                st.download_button(
                    label="⬇️ Download Performance CSV",
                    data=child_perf.to_csv(index=False).encode("utf-8"),
                    file_name=f"{selected_child.replace(' ', '_')}_performance.csv",
                    mime="text/csv"
                )
            else:
                st.info("No records found.")
        else:
            st.info("No performance file exists yet.")

    else:
        st.warning("⚠️ Children registration file not found.")

elif page == "👤 Profile":
    st.title("👤 Child Profile")

    if db is not None:
        try:
            # Get all children from MongoDB
            children = list(db.children.find())
            
            if not children:
                st.warning("⚠️ No registered children.")
                st.stop()

            child_names = sorted([child["Full Name"] for child in children])
            selected_child = st.selectbox("Select a Child", child_names)

            # Find the selected child's data
            child_info = next((child for child in children if child["Full Name"] == selected_child), None)
            
            if child_info:
                st.subheader("📋 Personal Info")
                cols = st.columns([1, 2])
                
                with cols[0]:
                    image_path = f"photos/{selected_child.replace(' ', '_')}.jpg"
                    if os.path.exists(image_path):
                        st.image(image_path, caption="Profile Photo", use_column_width=True)
                    else:
                        st.info("📷 No profile photo found.")

                with cols[1]:
                    st.markdown(f"**Name:** {child_info['Full Name']}")
                    st.markdown(f"**Gender:** {child_info.get('Gender', 'N/A')}")
                    st.markdown(f"**Date of Birth:** {child_info.get('Date of Birth', 'N/A')}")
                    st.markdown(f"**Grade/Form:** {child_info.get('Grade', 'N/A')}")
                    st.markdown(f"**School:** {child_info.get('School', 'N/A')}")
                    st.markdown(f"**Group/Class:** {child_info.get('Group/Class', 'N/A')}")
                    st.markdown(f"**Residence:** {child_info.get('Residence', 'N/A')}")
                    
                    if child_info.get('Parent 1'):
                        st.markdown(f"**Parent 1:** {child_info['Parent 1']} ({child_info.get('Contact 1', 'No contact')})")
                    if child_info.get('Parent 2'):
                        st.markdown(f"**Parent 2:** {child_info['Parent 2']} ({child_info.get('Contact 2', 'No contact')})")
                    
                    st.markdown(f"**Sponsored by OCM:** {'Yes' if child_info.get('Sponsored by OCM') else 'No'}")
                    st.markdown(f"**Last Updated:** {child_info.get('Last Updated', 'N/A')}")

                # Attendance Overview
                st.subheader("📅 Attendance Records")
                try:
                    attendance_records = list(db.attendance.find({"child_name": selected_child}))
                    if attendance_records:
                        att_df = pd.DataFrame(attendance_records)
                        att_df = att_df[["date", "present", "brought_bible", "brought_offering"]]
                        att_df.columns = ["Date", "Present", "Brought Bible", "Brought Offering"]
                        att_df["Date"] = pd.to_datetime(att_df["Date"]).dt.date
                        att_df = att_df.sort_values("Date", ascending=False)
                        
                        st.dataframe(att_df)

                        st.subheader("📦 Requirements Summary")
                        total_sessions = len(attendance_records)
                        present_count = sum(1 for record in attendance_records if record["present"])
                        bible_count = sum(1 for record in attendance_records if record["brought_bible"])
                        offering_count = sum(1 for record in attendance_records if record["brought_offering"])

                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Sessions", total_sessions)
                        with col2:
                            attendance_rate = (present_count / total_sessions * 100) if total_sessions > 0 else 0
                            st.metric("Attendance Rate", f"{attendance_rate:.1f}%")
                        with col3:
                            bible_rate = (bible_count / total_sessions * 100) if total_sessions > 0 else 0
                            st.metric("Bible Rate", f"{bible_rate:.1f}%")
                        with col4:
                            offering_rate = (offering_count / total_sessions * 100) if total_sessions > 0 else 0
                            st.metric("Offering Rate", f"{offering_rate:.1f}%")

                        # Export option
                        csv_data = att_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="⬇️ Download Attendance Records",
                            data=csv_data,
                            file_name=f"{selected_child.replace(' ', '_')}_attendance.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("No attendance records found for this child.")
                except Exception as e:
                    st.error(f"Error fetching attendance records: {str(e)}")
            else:
                st.error("Child not found in database.")
        except Exception as e:
            st.error(f"Error accessing database: {str(e)}")
    else:
        st.error("❌ Database connection failed")

elif page == "✏️ Edit Profiles":
    st.title("✏️ Edit or Delete Child Profile")

    if db is not None:
        try:
            # Get all children from MongoDB
            children = list(db.children.find())
            
            if not children:
                st.warning("⚠️ No registered children.")
                st.stop()

            child_names = sorted([child["Full Name"] for child in children])
            selected_child = st.selectbox("Select a Child", child_names)

            # Find the selected child's data
            child_info = next((child for child in children if child["Full Name"] == selected_child), None)

            if child_info:
                # Add delete button at the top
                col1, col2 = st.columns([3, 1])
                with col2:
                    if st.button("🗑️ Delete Profile", type="secondary", help="Permanently delete this child's profile"):
                        try:
                            # Delete child's records
                            db.children.delete_one({"_id": child_info["_id"]})
                            # Delete associated attendance records
                            db.attendance.delete_many({"child_id": child_info["_id"]})
                            st.success(f"✅ Deleted {selected_child}'s profile and all associated records")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting profile: {str(e)}")
                            st.stop()

                with st.form("edit_form"):
                    st.subheader("Edit Information")
                    
                    full_name = st.text_input("Full Name", value=child_info["Full Name"])
                    gender = st.selectbox(
                        "Gender", 
                        ["", "Male", "Female"], 
                        index=["", "Male", "Female"].index(child_info.get("Gender", "")) if child_info.get("Gender") in ["Male", "Female"] else 0
                    )
                    
                    # Convert ISO date string to date object if it exists
                    current_dob = None
                    if child_info.get("Date of Birth"):
                        try:
                            current_dob = datetime.fromisoformat(child_info["Date of Birth"]).date()
                        except:
                            current_dob = date.today()
                    
                    dob = st.date_input(
                        "Date of Birth",
                        value=current_dob or date.today(),
                        max_value=date.today()
                    )
                    
                    school = st.text_input("School Name", value=child_info.get("School", ""))
                    
                    current_grade = child_info.get("Grade", "")
                    grade_options = [""] + [
                        "PP1", "PP2", "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6",
                        "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12",
                        "Form 1", "Form 2", "Form 3", "Form 4"
                    ]
                    grade = st.selectbox(
                        "Grade / Form",
                        grade_options,
                        index=grade_options.index(current_grade) if current_grade in grade_options else 0
                    )
                    
                    group_options = [
                        "Chosen Generation(grade PP1–PP2)",
                        "Chosen Nation(grade 1–3)",
                        "Priesthood (grade 4–6)",
                        "Preisthood 2(grade 7–12)",
                        "Priesthood 2(form 1–4)"
                    ]
                    current_group = child_info.get("Group/Class", group_options[0])
                    group = st.selectbox(
                        "Group/Class",
                        group_options,
                        index=group_options.index(current_group) if current_group in group_options else 0
                    )
                    
                    residence = st.text_input("Residence", value=child_info.get("Residence", ""))
                    parent1 = st.text_input("Parent/Guardian 1", value=child_info.get("Parent 1", ""))
                    contact1 = st.text_input("Contact 1", value=child_info.get("Contact 1", ""))
                    parent2 = st.text_input("Parent/Guardian 2", value=child_info.get("Parent 2", ""))
                    contact2 = st.text_input("Contact 2", value=child_info.get("Contact 2", ""))
                    sponsored = st.checkbox("Sponsored by OCM", value=child_info.get("Sponsored by OCM", False))

                    submitted = st.form_submit_button("💾 Save Changes")

                    if submitted:
                        try:
                            # Prepare updated data
                            updated_data = {
                                "Full Name": full_name,
                                "Gender": gender,
                                "Date of Birth": dob.isoformat(),
                                "School": school,
                                "Grade": grade,
                                "Group/Class": group,
                                "Residence": residence,
                                "Parent 1": parent1,
                                "Contact 1": contact1,
                                "Parent 2": parent2,
                                "Contact 2": contact2,
                                "Sponsored by OCM": sponsored,
                                "Last Updated": datetime.now().isoformat()
                            }

                            # Update the record
                            result = db.children.update_one(
                                {"_id": child_info["_id"]},
                                {"$set": updated_data}
                            )

                            if result.modified_count > 0:
                                st.success("✅ Profile updated successfully!")
                                # If name changed, update attendance records
                                if full_name != child_info["Full Name"]:
                                    db.attendance.update_many(
                                        {"child_id": child_info["_id"]},
                                        {"$set": {"child_name": full_name}}
                                    )
                            else:
                                st.info("No changes detected.")
                            
                            # Show current data
                            st.subheader("Current Information")
                            for key, value in updated_data.items():
                                if key != "Last Updated":
                                    st.write(f"**{key}:** {value}")
                                    
                        except Exception as e:
                            st.error(f"Error updating profile: {str(e)}")
            else:
                st.error("Child not found in database.")
        except Exception as e:
            st.error(f"Error accessing database: {str(e)}")
    else:
        st.error("❌ Database connection failed")

