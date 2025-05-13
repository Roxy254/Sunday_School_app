import streamlit as st
import pandas as pd
import os
from datetime import datetime, date
import gspread
from google.oauth2.service_account import Credentials


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
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return gspread.authorize(creds)


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

    file_name = "children_records.csv"
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

elif page == "🗓️ Attendance":
    st.title("🗓️ Sunday Attendance Register (Class View)")

    if os.path.exists("children_records.csv"):
        children_df = pd.read_csv("children_records.csv")

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
                "Arrival Time": "Early" if status == "Present" else "N/A",  # default to Early
                "Brought Bible": bible,
                "Brought Pen": pen,
                "Brought Offering": offering
            })

        if st.button("💾 Submit Class Attendance"):
            att_file = "attendance_records.csv"
            if os.path.exists(att_file):
                att_df = pd.read_csv(att_file)
                att_df = pd.concat([att_df, pd.DataFrame(attendance_data)], ignore_index=True)
            else:
                att_df = pd.DataFrame(attendance_data)

            att_df.to_csv(att_file, index=False)
            st.success(f"✅ Attendance for {selected_class} on {session_date.strftime('%Y-%m-%d')} saved successfully!")
    else:
        st.warning("⚠️ No registered children found. Please register children first.")



elif page == "📊 Reports":
    st.title("📊 Attendance Reports")

    att_file = "attendance_records.csv"
    if os.path.exists(att_file):
        att_df = pd.read_csv(att_file)
        att_df["Session Date"] = pd.to_datetime(att_df["Session Date"])
        att_df["Month"] = att_df["Session Date"].dt.to_period("M").astype(str)

        # Date filter
        st.subheader("📆 Filter Attendance by Date Range")
        min_date = att_df["Session Date"].min().date()
        max_date = att_df["Session Date"].max().date()
        start_date = st.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date)
        end_date = st.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date)

        att_df = att_df[
            (att_df["Session Date"] >= pd.to_datetime(start_date)) &
            (att_df["Session Date"] <= pd.to_datetime(end_date))
        ]

        # Monthly summary
        monthly_summary = att_df.groupby(["Month", "Attendance Status"]).size().unstack(fill_value=0)
        st.subheader("📅 Monthly Attendance Trend")
        st.line_chart(monthly_summary)

        # Download filtered data
        st.subheader("📅 Download Data")
        csv_data = att_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name="attendance_report.csv",
            mime="text/csv"
        )

        # Filter by class
        if "Class" in att_df.columns:
            classes = sorted(att_df["Class"].dropna().unique())
            selected_class = st.selectbox("Filter by Class", ["All"] + list(classes))
            if selected_class != "All":
                att_df = att_df[att_df["Class"] == selected_class]

        # Attendance summary
        summary = att_df.groupby(["Child Name", "Attendance Status"]).size().unstack(fill_value=0)
        summary["Total Sessions"] = summary.sum(axis=1)
        summary["% Present"] = round((summary.get("Present", 0) / summary["Total Sessions"]) * 100, 1)
        if "Absent" not in summary.columns:
            summary["Absent"] = 0

        st.subheader("🧾 Attendance Summary (Counts)")
        columns_to_display = ["Present", "Absent", "Total Sessions", "% Present"]
        st.dataframe(summary[columns_to_display].sort_values("% Present", ascending=False))

        st.subheader("📈 Attendance Percentage")
        st.dataframe(summary[columns_to_display].sort_values("% Present", ascending=False))

        # Individual child report
        st.subheader("📌 Individual Child Report")
        all_children = sorted(att_df["Child Name"].unique())
        selected_child = st.selectbox("Choose a child", all_children)

        child_data = att_df[att_df["Child Name"] == selected_child]
        if not child_data.empty:
            total_sessions = len(child_data)
            present_count = len(child_data[child_data["Attendance Status"] == "Present"])
            percent = round((present_count / total_sessions) * 100, 1)

            st.markdown(f"**Total Sessions:** {total_sessions}")
            st.markdown(f"**Times Present:** {present_count}")
            st.markdown(f"**Attendance %:** {percent}%")

            st.dataframe(child_data[["Session Date", "Attendance Status", "Arrival Time", "Brought Bible", "Brought Pen", "Brought Offering"]])

            child_csv = child_data.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=f"Download Report for {selected_child}",
                data=child_csv,
                file_name=f"{selected_child.replace(' ', '_')}_attendance.csv",
                mime="text/csv"
            )
        else:
            st.info("No data available for this child.")

        # WhatsApp Summary
        st.subheader("📤 WhatsApp Summary Message")

        if os.path.exists("children_records.csv"):
            children_df = pd.read_csv("children_records.csv")
            if "Sponsored by OCM" not in children_df.columns:
                children_df["Sponsored by OCM"] = "No"

            all_kids = children_df["Full Name"].tolist()
            total_kids = len(all_kids)

            att_df = att_df.merge(children_df[["Full Name", "Group/Class", "Sponsored by OCM"]],
                                  left_on="Child Name", right_on="Full Name", how="left")

            total_present = len(att_df[att_df["Attendance Status"] == "Present"])
            total_absent = len(att_df[att_df["Attendance Status"] == "Absent"])

            class_summary = att_df.groupby(["Group/Class", "Attendance Status"]).size().unstack(fill_value=0)
            attendance_by_class = []
            absences_by_class = []
            absent_names_by_class = []

            for group in sorted(att_df["Group/Class"].dropna().unique()):
                group_df = att_df[att_df["Group/Class"] == group]
                group_present = len(group_df[group_df["Attendance Status"] == "Present"])
                group_absent = len(group_df[group_df["Attendance Status"] == "Absent"])
                absent_names = group_df[group_df["Attendance Status"] == "Absent"]["Child Name"].tolist()

                attendance_by_class.append(f"📘 {group}: {group_present} present")
                absences_by_class.append(f"❌ {group}: {group_absent} absent")
                if absent_names:
                    absent_list = ", ".join(absent_names)
                    absent_names_by_class.append(f"❌ *{group} Absent:* {absent_list}")

            ocm_df = att_df[att_df["Sponsored by OCM"] == "Yes"]
            ocm_present = ocm_df[ocm_df["Attendance Status"] == "Present"]["Child Name"].tolist()
            ocm_absent = ocm_df[ocm_df["Attendance Status"] == "Absent"]["Child Name"].tolist()

            lines = [
                "📊 *Sunday School Summary*",
                f"👧👦 Total Children: {total_kids}",
                f"✅ Present: {total_present} | ❌ Absent: {total_absent}",
                "",
                "📚 *Attendance by Class*",
                *attendance_by_class,
                "",
                "🚫 *Absences by Class*",
                *absences_by_class,
                "",
                "💼 *Absent Names by Class*",
                *absent_names_by_class,
                "",
                "🌟 *OCM Sponsored Children*",
                f"✅ Present: {', '.join(ocm_present) if ocm_present else 'None'}",
                f"❌ Absent: {', '.join(ocm_absent) if ocm_absent else 'None'}"
            ]

            summary_msg = "\n".join(lines)
            st.text_area("📲 WhatsApp Message Preview", summary_msg, height=400)

            phone_number = st.text_input("Enter WhatsApp number (e.g. 2547XXXXXXXX)")
            encoded_msg = summary_msg.replace("\n", "%0A").replace(" ", "%20")
            wa_link = f"https://wa.me/{phone_number}?text={encoded_msg}"

            if st.button("📤 Open WhatsApp"):
                st.markdown(f"[Click to send via WhatsApp 🚀]({wa_link})", unsafe_allow_html=True)

        # Top Attendance Chart
        if "Present" in summary.columns:
            top_attendance = summary["Present"].sort_values(ascending=False)
            st.subheader("🏅 Top Attendance (Most Presents)")
            st.bar_chart(top_attendance)

        # Quarterly summary
        att_df["Quarter"] = att_df["Session Date"].dt.to_period("Q").astype(str)
        st.subheader("📊 Quarterly Attendance Summary")

        quarterly_summary = att_df.groupby(["Quarter", "Attendance Status"]).size().unstack(fill_value=0)
        quarterly_summary["Total"] = quarterly_summary.sum(axis=1)
        if "Present" in quarterly_summary.columns:
            quarterly_summary["% Present"] = round((quarterly_summary["Present"] / quarterly_summary["Total"]) * 100, 1)

        st.dataframe(quarterly_summary)

        if "Present" in quarterly_summary.columns:
            st.subheader("📈 Quarterly Present Count")
            st.bar_chart(quarterly_summary["Present"])

    else:
        st.warning("No attendance data found.")


elif page == "📚 Performance":
    st.title("📚 Performance Tracking (School)")

    perf_file = "performance_records.csv"
    if os.path.exists("children_records.csv"):
        children_df = pd.read_csv("children_records.csv")
        child_names = children_df["Full Name"].dropna().unique().tolist()

        selected_child = st.selectbox("Select Child", child_names)
        year = st.selectbox("Select Year", list(range(2020, date.today().year + 1))[::-1])
        term = st.selectbox("Select Term", ["Term 1", "Term 2", "Term 3"])

        subjects = ["Math", "English", "Kiswahili", "Science", "CRE", "Other"]
        scores = {}
        st.subheader("📊 Enter Subject Scores")
        for subject in subjects:
            scores[subject] = st.number_input(
                f"{subject} Score", min_value=0, max_value=100, step=1, key=f"score_{subject}"
            )

        remarks = st.text_area("Teacher’s Remarks")

        if st.button("💾 Save Performance"):
            new_record = {
                "Child Name": selected_child,
                "Year": year,
                "Term": term,
                **scores,
                "Remarks": remarks,
                "Date Recorded": date.today().strftime("%Y-%m-%d")
            }

            if os.path.exists(perf_file):
                perf_df = pd.read_csv(perf_file)
                perf_df = pd.concat([perf_df, pd.DataFrame([new_record])], ignore_index=True)
            else:
                perf_df = pd.DataFrame([new_record])

            perf_df.to_csv(perf_file, index=False)
            st.success("✅ Performance record saved successfully!")

        # ------------------- View Past Records -------------------
        st.markdown("---")
        st.subheader("📄 View Past Performance")

        child_perf = pd.DataFrame()
        if os.path.exists(perf_file):
            perf_df = pd.read_csv(perf_file)
            child_perf = perf_df[perf_df["Child Name"] == selected_child]

            if not child_perf.empty:
                child_perf = child_perf.sort_values(["Year", "Term"])
                st.dataframe(child_perf)

                st.subheader("📈 Subject Score Trend")
                chart_df = child_perf.copy()
                chart_df["Term_Year"] = chart_df["Year"].astype(str) + " " + chart_df["Term"]
                chart_df.set_index("Term_Year", inplace=True)

                st.line_chart(chart_df[subjects])

                st.download_button(
                    label=f"⬇️ Download {selected_child}'s Performance CSV",
                    data=child_perf.to_csv(index=False).encode("utf-8"),
                    file_name=f"{selected_child.replace(' ', '_')}_performance.csv",
                    mime="text/csv"
                )
            else:
                st.info("No past performance records found.")
        else:
            st.warning("No performance file found yet.")

        # ------------------- Edit Existing Entry -------------------
        st.markdown("---")
        st.subheader("✏️ Edit Existing Performance Entry")

        if not child_perf.empty:
            entry_choices = child_perf[["Year", "Term"]].drop_duplicates()
            entry_choices["Label"] = entry_choices["Term"] + " " + entry_choices["Year"].astype(str)
            edit_label = st.selectbox("Select Entry to Edit", entry_choices["Label"])

            edit_term, edit_year = edit_label.split()
            edit_year = int(edit_year)

            edit_record = child_perf[(child_perf["Year"] == edit_year) & (child_perf["Term"] == edit_term)].iloc[0]

            st.markdown("Update scores:")
            updated_scores = {}
            for subject in subjects:
                updated_scores[subject] = st.number_input(
                    f"{subject} Score", value=int(edit_record[subject]), min_value=0, max_value=100, key=f"edit_{subject}"
                )

            updated_remarks = st.text_area("Updated Remarks", value=edit_record["Remarks"])

            if st.button("✅ Update Performance"):
                idx = perf_df[
                    (perf_df["Child Name"] == selected_child) &
                    (perf_df["Year"] == edit_year) &
                    (perf_df["Term"] == edit_term)
                ].index

                for subject in subjects:
                    perf_df.loc[idx, subject] = updated_scores[subject]
                perf_df.loc[idx, "Remarks"] = updated_remarks

                perf_df.to_csv(perf_file, index=False)
                st.success("Performance updated successfully!")

        # ------------------- Export Attendance + Performance -------------------
        st.markdown("---")
        st.subheader("🖨️ Export Full Report")

        if os.path.exists("attendance_records.csv"):
            att_df = pd.read_csv("attendance_records.csv")
            child_att = att_df[att_df["Child Name"] == selected_child]
        else:
            child_att = pd.DataFrame()

        st.download_button(
            label="⬇️ Download Performance Report",
            data=child_perf.to_csv(index=False).encode("utf-8"),
            file_name=f"{selected_child.replace(' ', '_')}_performance.csv",
            mime="text/csv"
        )

        if not child_att.empty:
            st.download_button(
                label="⬇️ Download Attendance Report",
                data=child_att.to_csv(index=False).encode("utf-8"),
                file_name=f"{selected_child.replace(' ', '_')}_attendance.csv",
                mime="text/csv"
            )
        else:
            st.info("No attendance records available for export.")
    else:
        st.warning("⚠️ Please register children first to enter performance data.")


elif page == "👤 Profile":

    st.title("👤 Child Profile")

    if os.path.exists("children_records.csv"):
    import os
    st.write("📁 Looking for file in:", os.getcwd())
    st.write("📄 File exists?", os.path.exists("children_records.csv"))

    children_df = pd.read_csv("children_records.csv")

        children_df = pd.read_csv("children_records.csv")
        child_names = children_df["Full Name"].dropna().unique().tolist()

        if not child_names:
            st.warning("⚠️ No children registered yet.")
        else:
            selected_child = st.selectbox("Select a Child", child_names)

            match = children_df[children_df["Full Name"] == selected_child]

            if match.empty:
                st.error("Child not found in records.")
            else:
                child_info = match.iloc[0]

                st.subheader("📋 Personal Info")
                cols = st.columns([1, 2])

                with cols[0]:
                    # 📷 Profile photo
                    image_path = f"photos/{selected_child.replace(' ', '_')}.jpg"
                    if os.path.exists(image_path):
                        st.image(image_path, caption="Profile Photo", use_column_width=True)
                    else:
                        st.info("📷 No profile photo found.")

                with cols[1]:
                    st.markdown(f"**Name:** {child_info['Full Name']}")
                    st.markdown(f"**Age:** {child_info['Age']}")
                    st.markdown(f"**Gender:** {child_info['Gender']}")
                    st.markdown(f"**Grade/Form:** {child_info['Grade']}")
                    st.markdown(f"**School:** {child_info['School']}")
                    st.markdown(f"**Group/Class:** {child_info['Group/Class']}")
                    st.markdown(f"**Residence:** {child_info['Residence']}")
                    st.markdown(f"**Parent 1:** {child_info['Parent 1']} ({child_info['Contact 1']})")
                    if pd.notna(child_info['Parent 2']):
                        st.markdown(f"**Parent 2:** {child_info['Parent 2']} ({child_info['Contact 2']})")
                    st.markdown(f"**Sponsored by OCM:** {child_info.get('Sponsored by OCM', 'Not specified')}")

                # 📅 Attendance Overview
                if os.path.exists("attendance_records.csv"):
                    att_df = pd.read_csv("attendance_records.csv")
                    att_df = att_df[att_df["Child Name"] == selected_child]

                    if not att_df.empty:
                        st.subheader("📅 Attendance Overview")
                        st.dataframe(att_df[[
                            "Session Date", "Attendance Status", "Arrival Time",
                            "Brought Bible", "Brought Pen", "Brought Offering"
                        ]])

                        st.subheader("📦 Church Requirements Summary")
                        req_summary = {
                            "Brought Bible": att_df["Brought Bible"].value_counts().to_dict(),
                            "Brought Pen": att_df["Brought Pen"].value_counts().to_dict(),
                            "Brought Offering": att_df["Brought Offering"].value_counts().to_dict()
                        }
                        for item, stats in req_summary.items():
                            yes_count = stats.get("Yes", 0)
                            no_count = stats.get("No", 0)
                            total = yes_count + no_count
                            percent = round((yes_count / total) * 100, 1) if total > 0 else 0
                            st.markdown(f"**{item}:** {yes_count} times ✅ ({percent}%)")

                        st.subheader("📈 Attendance Status Chart")
                        att_chart = att_df["Attendance Status"].value_counts()
                        st.bar_chart(att_chart)

                        st.subheader("📤 Export Options")
                        st.download_button(
                            label="⬇️ Download Attendance CSV",
                            data=att_df.to_csv(index=False).encode("utf-8"),
                            file_name=f"{selected_child.replace(' ', '_')}_attendance.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("No attendance data found.")

                # 📚 Performance
                if os.path.exists("performance_records.csv"):
                    perf_df = pd.read_csv("performance_records.csv")
                    perf_df = perf_df[perf_df["Child Name"] == selected_child]

                    if not perf_df.empty:
                        st.subheader("📚 School Performance")
                        st.dataframe(perf_df[[
                            "Year", "Term", "Math", "English", "Kiswahili",
                            "Science", "CRE", "Other", "Remarks"
                        ]])

                        st.download_button(
                            label="⬇️ Download Performance CSV",
                            data=perf_df.to_csv(index=False).encode("utf-8"),
                            file_name=f"{selected_child.replace(' ', '_')}_performance.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("No performance records found.")
    else:
        st.warning("⚠️ No children data found. Please register children first.")
