@echo off
streamlit run "C:\Users\AROMA MBAYU MUNGA\Sunday_school_app\app.py"
import pandas as pd
import os
import streamlit as st
from datetime import datetime, date

# Sidebar navigation
page = st.sidebar.selectbox("Choose a page", ["📋 Registration", "🗓️ Attendance", "📊 Reports", "📚 Performance"])


if page == "📋 Registration":
    st.title("📋 Sunday School - Child Registration")

    with st.form("child_form"):
        full_name = st.text_input("Full Name")
        gender = st.selectbox("Gender", ["Male", "Female"])
        dob = st.date_input("Date of Birth", min_value=date(2000, 1, 1), max_value=date.today())
        group = st.selectbox("Group/Class", [
            "Chosen Generation(grade PP1–PP2)",
            "Chosen Nation(grade 1–3)",
            "Priesthood (grade 4–6)",
            "Preisthood 2(grade 7–12)",
            "Priesthood 2(form 1-4)"
        ])
        school = st.text_input("School Name")
        grade = st.selectbox("Grade / Form", [
            "PP1", "PP2",
            "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6",
            "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12",
            "Form 1", "Form 2", "Form 3", "Form 4"
        ])
        residence = st.text_input("Where do they live?")
        parent1 = st.text_input("Parent/Guardian 1 Name")
        contact1 = st.text_input("Contact for Parent 1")
        parent2 = st.text_input("Parent/Guardian 2 Name (optional)")
        contact2 = st.text_input("Contact for Parent 2")

        submitted = st.form_submit_button("Register Child")

        if submitted:
            age = (date.today() - dob).days // 365
            new_entry = {
                "Full Name": full_name,
                "Gender": gender,
                "Date of Birth": dob.strftime("%Y-%m-%d"),
                "Age": age,
                "Group/Class": group,
                "School": school,
                "Grade": grade,
                "Residence": residence,
                "Parent 1": parent1,
                "Contact 1": contact1,
                "Parent 2": parent2,
                "Contact 2": contact2
            }

            file_name = "children_records.csv"
            if os.path.exists(file_name):
                df = pd.read_csv(file_name)
                df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
            else:
                df = pd.DataFrame([new_entry])
            df.to_csv(file_name, index=False)
            st.success(f"{full_name} (Age {age}) registered and saved successfully!")

elif page == "🗓️ Attendance":
    st.title("🗓️ Sunday Attendance")

    if os.path.exists("children_records.csv"):
        children_df = pd.read_csv("children_records.csv")

        selected_class = st.selectbox("Select Class", sorted(children_df["Group/Class"].dropna().unique()))
        class_children = children_df[children_df["Group/Class"] == selected_class]["Full Name"].tolist()
        selected_child = st.selectbox("Select Child", class_children)

        attendance_status = st.selectbox("Attendance Status", ["Present", "Absent"])
        arrival_time = brought_bible = brought_pen = brought_offering = "N/A"

        if attendance_status == "Present":
            arrival_time = st.radio("Arrival Time", ["Early", "Late"])
            brought_bible = st.radio("Brought Bible?", ["Yes", "No"])
            brought_pen = st.radio("Brought Notebook/Pen?", ["Yes", "No"])
            brought_offering = st.radio("Brought Offering?", ["Yes", "No"])

        if st.button("Submit Attendance"):
            attendance_entry = {
                "Child Name": selected_child,
                "Class": selected_class,
                "Session Date": date.today().strftime("%Y-%m-%d"),
                "Attendance Status": attendance_status,
                "Arrival Time": arrival_time,
                "Brought Bible": brought_bible,
                "Brought Pen": brought_pen,
                "Brought Offering": brought_offering
            }

            att_file = "attendance_records.csv"
            if os.path.exists(att_file):
                att_df = pd.read_csv(att_file)
                att_df = pd.concat([att_df, pd.DataFrame([attendance_entry])], ignore_index=True)
            else:
                att_df = pd.DataFrame([attendance_entry])
            att_df.to_csv(att_file, index=False)
            st.success(f"Attendance for {selected_child} recorded successfully!")
    else:
        st.warning("No registered children found. Please register children first.")

elif page == "📊 Reports":
    st.title("📊 Attendance Reports")

    att_file = "attendance_records.csv"

    if os.path.exists(att_file):
        att_df = pd.read_csv(att_file)

        # Ensure date column is datetime
        att_df["Session Date"] = pd.to_datetime(att_df["Session Date"])
        att_df["Month"] = att_df["Session Date"].dt.to_period("M").astype(str)

        # Monthly summary
        monthly_summary = att_df.groupby(["Month", "Attendance Status"]).size().unstack(fill_value=0)
        st.subheader("📅 Monthly Attendance Trend")
        st.line_chart(monthly_summary)

        st.subheader("📥 Download Data")
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

        # Ensure all needed columns exist, handle missing columns if necessary
        summary["Total Sessions"] = summary.sum(axis=1)

        # Compute % Present but handle cases where there are no "Present" values
        summary["% Present"] = round((summary.get("Present", 0) / summary["Total Sessions"]) * 100, 1)

        # Display the summary data, checking if necessary columns exist
        columns_to_display = ["Present", "Absent", "Total Sessions", "% Present"]
        missing_columns = [col for col in columns_to_display if col not in summary.columns]

        # If "Absent" column is missing, add it manually
        if "Absent" not in summary.columns:
            summary["Absent"] = summary.get("Absent", 0)  # Ensure there's a column for absent count

        # Show the attendance summary in a table sorted by the "% Present" column
        st.subheader("🧾 Attendance Summary (Counts)")
        st.dataframe(summary[columns_to_display].sort_values("% Present", ascending=False))

        st.subheader("📈 Attendance Percentage")
        st.dataframe(summary[columns_to_display].sort_values("% Present", ascending=False))

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

            # Download button
            child_csv = child_data.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=f"Download Report for {selected_child}",
                data=child_csv,
                file_name=f"{selected_child.replace(' ', '_')}_attendance.csv",
                mime="text/csv"
            )
        else:
            st.info("No data available for this child.")
        
        # Ensure columns for summary analysis
        if "Present" in summary.columns:
            top_attendance = summary["Present"].sort_values(ascending=False)
            st.subheader("🏅 Top Attendance (Most Presents)")
            st.bar_chart(top_attendance)

    else:
        st.warning("No attendance data found.")
    # ... [your imports and earlier code remain unchanged]
    att_df["Session Date"] = pd.to_datetime(att_df["Session Date"])
    att_df["Quarter"] = att_df["Session Date"].dt.to_period("Q").astype(str)
    st.subheader("📊 Quarterly Attendance Summary")

    quarterly_summary = att_df.groupby(["Quarter", "Attendance Status"]).size().unstack(fill_value=0)
    quarterly_summary["Total"] = quarterly_summary.sum(axis=1)
    if "Present" in quarterly_summary.columns:
        quarterly_summary["% Present"] = round((quarterly_summary["Present"] / quarterly_summary["Total"]) * 100, 1)
  
    st.dataframe(quarterly_summary)

    # Optional: Visual chart
    if "Present" in quarterly_summary.columns:
        st.subheader("📈 Quarterly Present Count")
        st.bar_chart(quarterly_summary["Present"])

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
