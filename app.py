import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime, date
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build



# Load credentials from Streamlit secrets
creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
credentials = service_account.Credentials.from_service_account_info(creds_dict)

# Authorize gspread with the credentials
client = gspread.authorize(credentials)


# Ensure 'data/' directory exists
os.makedirs("data", exist_ok=True)

# Set up a consistent data directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Define CSV file paths
CHILDREN_FILE = os.path.join(DATA_DIR, "children_records.csv")
ATTENDANCE_FILE = os.path.join(DATA_DIR, "attendance_records.csv")
PERFORMANCE_FILE = os.path.join(DATA_DIR, "performance_records.csv")

# ✅ Must be the first Streamlit command
st.set_page_config(
    page_title="Sunday School App",
    page_icon="icon_2_4ze_icon.icon",  # Replace with emoji or valid icon file if needed
    layout="wide"
)

# Google Sheets setup
def get_gsheet_client():
    creds = Credentials.from_service_account_info(
        st.secrets["google_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    return gspread.authorize(creds), creds

def load_or_create_sheet(sheet_name: str):
    client, _ = get_gsheet_client()
    try:
        sheet = client.open(sheet_name).sheet1
    except gspread.exceptions.SpreadsheetNotFound:
        # Create a new sheet if it doesn't exist
        sheet = client.create(sheet_name).sheet1
    return sheet

def share_sheet(sheet_id, email_to_share):
    _, creds = get_gsheet_client()
    drive_service = build('drive', 'v3', credentials=creds)
    permission = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': email_to_share
    }
    drive_service.permissions().create(fileId=sheet_id, body=permission).execute()

# Streamlit UI
st.title("📋 Sunday School Spreadsheet Manager")

sheet_name = st.text_input("Enter Google Sheet name", "Sunday School App Sheet")

if st.button("Load Sheet"):
    sheet = load_or_create_sheet(sheet_name)
    st.session_state["sheet"] = sheet
    st.success("Sheet loaded successfully!")
    st.write("Current Data:")
    data = sheet.get_all_records()
    st.dataframe(pd.DataFrame(data))

if "sheet" in st.session_state and st.button("Share Sheet with Me"):
    email = st.text_input("Enter your email address to share access:")
    if email:
        share_sheet(st.session_state["sheet"].spreadsheet.id, email)
        st.success(f"Sheet shared with {email}!")
    else:
        st.warning("Please enter an email address before sharing.")


# --- SIMPLE LOGIN SYSTEM ---
def check_login():
    st.markdown("### 🔐 Login to Access App")
    password = st.text_input("Enter password", type="password")
    if password == "Sundayschool2025":  # 🔒 Change this to your real password
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




if page == "📋 Registration":
    st.title("📋 Register or Update Child Record")

    # Use data/ directory for consistency
    file_name = "data/children_records.csv"
    os.makedirs("data", exist_ok=True)  # Ensure the folder exists

    if os.path.exists(file_name):
        df = pd.read_csv(file_name)
        existing_names = df["Full Name"].tolist()
    else:
        df = pd.DataFrame()
        existing_names = []

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

    if submitted:
        if not full_name or not group:
            st.error("Full Name and Class are required.")
        else:
            age = (date.today() - dob).days // 365 if dob else ""
            new_data = {
                "Full Name": full_name,
                "Gender": gender,
                "Date of Birth": dob.strftime("%Y-%m-%d") if dob else "",
                "Age": age,
                "Group/Class": group,
                "School": school,
                "Grade": grade,
                "Residence": residence,
                "Parent 1": parent1,
                "Contact 1": contact1,
                "Parent 2": parent2,
                "Contact 2": contact2,
                "Sponsored by OCM": "Yes" if sponsored else "No"
            }

            if full_name in existing_names:
                df.loc[df["Full Name"] == full_name] = new_data
                st.success(f"✅ {full_name}'s info updated.")
            else:
                df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                st.success(f"✅ {full_name} added.")

            df.to_csv(file_name, index=False)

            # ✅ Upload to Google Sheets
            try:
                gc = get_gsheet_client()
                sheet = gc.open("Sunday School registrations").sheet1
                sheet.append_row([
                    full_name, gender, dob.strftime("%Y-%m-%d"), age, group, school, grade,
                    residence, parent1, contact1, parent2, contact2, "Yes" if sponsored else "No"
                ])
                st.success("✅ Saved to Google Sheets successfully!")
            except Exception as e:
                st.error(f"⚠️ Failed to update Google Sheet: {e}")


elif page == "🗓️ Attendance":
    st.title("🗓️ Sunday Attendance Register (Class View)")

    child_file = "data/children_records.csv"
    att_file = "data/attendance_records.csv"
    os.makedirs("data", exist_ok=True)

    if os.path.exists(child_file):
        children_df = pd.read_csv(child_file)

        if not children_df.empty:
            selected_class = st.selectbox("Select Class", sorted(children_df["Group/Class"].dropna().unique()))
            class_children = children_df[children_df["Group/Class"] == selected_class]

            session_date = st.date_input("Select Session Date", value=date.today(), max_value=date.today())

            st.markdown("### ✏️ Mark Attendance and Requirements")

            attendance_data = []

            for idx, row in class_children.iterrows():
                col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])

                with col1:
                    st.markdown(f"**{row['Full Name']}**")

                with col2:
                    status = st.selectbox("Status", ["Present", "Absent"], key=f"status_{idx}")

                with col3:
                    bible = st.selectbox("Bible", ["Yes", "No", "N/A"] if status == "Present" else ["N/A"], key=f"bible_{idx}")

                with col4:
                    pen = st.selectbox("Pen", ["Yes", "No", "N/A"] if status == "Present" else ["N/A"], key=f"pen_{idx}")

                with col5:
                    offering = st.selectbox("Offering", ["Yes", "No", "N/A"] if status == "Present" else ["N/A"], key=f"offering_{idx}")

                attendance_data.append({
                    "Child Name": row["Full Name"],
                    "Class": selected_class,
                    "Session Date": session_date.strftime("%Y-%m-%d"),
                    "Attendance Status": status,
                    "Arrival Time": "Early" if status == "Present" else "N/A",
                    "Brought Bible": bible,
                    "Brought Pen": pen,
                    "Brought Offering": offering
                })

            if st.button("💾 Submit Class Attendance"):
                if os.path.exists(att_file):
                    att_df = pd.read_csv(att_file)
                    att_df = pd.concat([att_df, pd.DataFrame(attendance_data)], ignore_index=True)
                else:
                    att_df = pd.DataFrame(attendance_data)

                att_df.to_csv(att_file, index=False)
                st.success(f"✅ Attendance for {selected_class} on {session_date.strftime('%Y-%m-%d')} saved successfully!")

                # ✅ Upload attendance to Google Sheets
                try:
                    gc = get_gsheet_client()
                    att_sheet = gc.open("Sunday School registrations").worksheet("Attendance")
                    for record in attendance_data:
                        att_sheet.append_row(list(record.values()))
                    st.success("✅ Attendance uploaded to Google Sheets!")
                except Exception as e:
                    st.error(f"⚠️ Failed to update Attendance sheet: {e}")
        else:
            st.warning("⚠️ No registered children found in file.")
    else:
        st.warning("⚠️ Children records file not found. Please register children first.")


elif page == "📊 Reports":
    st.title("📊 Attendance Reports")

    att_file = "data/attendance_records.csv"
    os.makedirs("data", exist_ok=True)

    if os.path.exists(att_file):
        att_df = pd.read_csv(att_file)

        if att_df.empty:
            st.warning("⚠️ Attendance file exists but has no records.")
            st.stop()

        # Ensure datetime format
        att_df["Session Date"] = pd.to_datetime(att_df["Session Date"])
        att_df["Month"] = att_df["Session Date"].dt.to_period("M").astype(str)
        att_df["Quarter"] = att_df["Session Date"].dt.to_period("Q").astype(str)

        st.subheader("📅 Monthly Attendance Trend")
        monthly_summary = att_df.groupby(["Month", "Attendance Status"]).size().unstack(fill_value=0)
        st.line_chart(monthly_summary)

        st.subheader("📊 Quarterly Summary")
        quarterly_summary = att_df.groupby(["Quarter", "Attendance Status"]).size().unstack(fill_value=0)
        quarterly_summary["Total"] = quarterly_summary.sum(axis=1)
        if "Present" in quarterly_summary.columns:
            quarterly_summary["% Present"] = round((quarterly_summary["Present"] / quarterly_summary["Total"]) * 100, 1)
        st.dataframe(quarterly_summary)

        st.subheader("📌 Filter by Class")
        classes = sorted(att_df["Class"].dropna().unique())
        selected_class = st.selectbox("Choose Class", ["All"] + classes)
        filtered_df = att_df if selected_class == "All" else att_df[att_df["Class"] == selected_class]

        # Attendance summary by child
        summary = filtered_df.groupby(["Child Name", "Attendance Status"]).size().unstack(fill_value=0)
        summary["Total Sessions"] = summary.sum(axis=1)
        summary["% Present"] = round((summary.get("Present", 0) / summary["Total Sessions"]) * 100, 1)
        if "Absent" not in summary:
            summary["Absent"] = 0
        st.subheader("🧾 Attendance Summary")
        st.dataframe(summary[["Present", "Absent", "Total Sessions", "% Present"]].sort_values("% Present", ascending=False))

        st.subheader("📋 Individual Child Report")
        children = sorted(filtered_df["Child Name"].unique())
        selected_child = st.selectbox("Select a Child", children)

        child_data = filtered_df[filtered_df["Child Name"] == selected_child]
        if not child_data.empty:
            st.markdown(f"**Total Sessions:** {len(child_data)}")
            present_count = len(child_data[child_data["Attendance Status"] == "Present"])
            st.markdown(f"**Present:** {present_count}")
            st.markdown(f"**% Present:** {round((present_count / len(child_data)) * 100, 1)}%")

            st.dataframe(child_data[[
                "Session Date", "Attendance Status", "Arrival Time",
                "Brought Bible", "Brought Pen", "Brought Offering"
            ]])

            st.download_button(
                label=f"⬇️ Download {selected_child}'s Report",
                data=child_data.to_csv(index=False).encode("utf-8"),
                file_name=f"{selected_child.replace(' ', '_')}_attendance.csv",
                mime="text/csv"
            )
        else:
            st.info("No data available for this child.")

        # Top attendance chart
        if "Present" in summary.columns:
            st.subheader("🏅 Top Attendance")
            st.bar_chart(summary["Present"].sort_values(ascending=False))

        # Export full data
        st.subheader("⬇️ Export Complete Dataset")
        st.download_button(
            label="Download Full Attendance CSV",
            data=att_df.to_csv(index=False).encode("utf-8"),
            file_name="full_attendance_report.csv",
            mime="text/csv"
        )

    else:
        st.warning("⚠️ No attendance data found.")

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

    record_file = "data/children_records.csv"
    att_file = "data/attendance_records.csv"
    perf_file = "data/performance_records.csv"

    if os.path.exists(record_file):
        children_df = pd.read_csv(record_file)
        child_names = sorted(children_df["Full Name"].dropna().unique().tolist())
        selected_child = st.selectbox("Select a Child", child_names)

        match = children_df[children_df["Full Name"] == selected_child]
        if match.empty:
            st.error("Child not found in records.")
        else:
            child_info = match.iloc[0]

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
                st.markdown(f"**Age:** {child_info.get('Age', 'N/A')}")
                st.markdown(f"**Gender:** {child_info.get('Gender', 'N/A')}")
                st.markdown(f"**Grade/Form:** {child_info.get('Grade', 'N/A')}")
                st.markdown(f"**School:** {child_info.get('School', 'N/A')}")
                st.markdown(f"**Group/Class:** {child_info.get('Group/Class', 'N/A')}")
                st.markdown(f"**Residence:** {child_info.get('Residence', 'N/A')}")
                st.markdown(f"**Parent 1:** {child_info.get('Parent 1')} ({child_info.get('Contact 1')})")
                if pd.notna(child_info.get("Parent 2", "")):
                    st.markdown(f"**Parent 2:** {child_info.get('Parent 2')} ({child_info.get('Contact 2')})")
                st.markdown(f"**Sponsored by OCM:** {child_info.get('Sponsored by OCM', 'No')}")

            # Attendance Overview
            if os.path.exists(att_file):
                att_df = pd.read_csv(att_file)
                att_df = att_df[att_df["Child Name"] == selected_child]
                if not att_df.empty:
                    st.subheader("📅 Attendance Records")
                    st.dataframe(att_df[["Session Date", "Attendance Status", "Arrival Time", "Brought Bible", "Brought Pen", "Brought Offering"]])

                    st.subheader("📦 Requirements Summary")
                    for item in ["Brought Bible", "Brought Pen", "Brought Offering"]:
                        counts = att_df[item].value_counts().to_dict()
                        yes = counts.get("Yes", 0)
                        no = counts.get("No", 0)
                        total = yes + no
                        percent = round((yes / total) * 100, 1) if total > 0 else 0
                        st.markdown(f"**{item}:** {yes} times ✅ ({percent}%)")

                    st.subheader("📈 Attendance Chart")
                    st.bar_chart(att_df["Attendance Status"].value_counts())

                    st.download_button(
                        label="⬇️ Download Attendance CSV",
                        data=att_df.to_csv(index=False).encode("utf-8"),
                        file_name=f"{selected_child.replace(' ', '_')}_attendance.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No attendance data found.")

            # Performance Overview
            if os.path.exists(perf_file):
                perf_df = pd.read_csv(perf_file)
                child_perf = perf_df[perf_df["Child Name"] == selected_child]
                if not child_perf.empty:
                    st.subheader("📚 School Performance")
                    st.dataframe(child_perf[["Year", "Term", "Math", "English", "Kiswahili", "Science", "CRE", "Other", "Remarks"]])
                    st.download_button(
                        label="⬇️ Download Performance CSV",
                        data=child_perf.to_csv(index=False).encode("utf-8"),
                        file_name=f"{selected_child.replace(' ', '_')}_performance.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No performance records found.")
    else:
        st.warning("⚠️ Children records not found. Please register students.")

elif page == "✏️ Edit Profiles":
    st.title("✏️ Edit Child Profile")

    file_name = "data/children_records.csv"

    if not os.path.exists(file_name):
        st.warning("⚠️ No children data found.")
    else:
        df = pd.read_csv(file_name)
        child_names = df["Full Name"].dropna().unique().tolist()

        if not child_names:
            st.info("No registered children to edit.")
        else:
            selected_child = st.selectbox("Select a Child", sorted(child_names))
            child_data = df[df["Full Name"] == selected_child].iloc[0]

            with st.form("edit_form"):
                full_name = st.text_input("Full Name", value=child_data["Full Name"])
                gender = st.selectbox("Gender", ["", "Male", "Female"], index=["", "Male", "Female"].index(child_data.get("Gender", "")))
                dob = st.date_input("Date of Birth", value=pd.to_datetime(child_data["Date of Birth"]) if pd.notna(child_data["Date of Birth"]) else date.today())
                school = st.text_input("School Name", value=child_data.get("School", ""))
                grade = st.selectbox("Grade / Form", [""] + [
                    "PP1", "PP2", "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6",
                    "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12",
                    "Form 1", "Form 2", "Form 3", "Form 4"
                ], index=max(0, [""] + [
                    "PP1", "PP2", "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6",
                    "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12",
                    "Form 1", "Form 2", "Form 3", "Form 4"
                ].index(child_data.get("Grade", "")) if child_data.get("Grade", "") in [
                    "PP1", "PP2", "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6",
                    "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12",
                    "Form 1", "Form 2", "Form 3", "Form 4"
                ] else 0))
                group = st.selectbox("Group/Class", df["Group/Class"].dropna().unique().tolist(), index=df["Group/Class"].dropna().unique().tolist().index(child_data["Group/Class"]))
                residence = st.text_input("Residence", value=child_data.get("Residence", ""))
                parent1 = st.text_input("Parent/Guardian 1", value=child_data.get("Parent 1", ""))
                contact1 = st.text_input("Contact 1", value=child_data.get("Contact 1", ""))
                parent2 = st.text_input("Parent/Guardian 2", value=child_data.get("Parent 2", ""))
                contact2 = st.text_input("Contact 2", value=child_data.get("Contact 2", ""))
                sponsored = st.checkbox("Sponsored by OCM", value=child_data.get("Sponsored by OCM", "No") == "Yes")

                submitted = st.form_submit_button("💾 Save Changes")

            if submitted:
                df.loc[df["Full Name"] == selected_child, :] = {
                    "Full Name": full_name,
                    "Gender": gender,
                    "Date of Birth": dob.strftime("%Y-%m-%d"),
                    "Age": (date.today() - dob).days // 365,
                    "Group/Class": group,
                    "School": school,
                    "Grade": grade,
                    "Residence": residence,
                    "Parent 1": parent1,
                    "Contact 1": contact1,
                    "Parent 2": parent2,
                    "Contact 2": contact2,
                    "Sponsored by OCM": "Yes" if sponsored else "No"
                }
                df.to_csv(file_name, index=False)
                st.success("✅ Profile updated successfully!")
