from datetime import date

import streamlit as st

from api_client import api
from dashboard import DIFFICULTIES, analytics_view, task_metrics, task_table

st.title("Student dashboard")
section = st.sidebar.radio("Student", ["Today's task", "Day-wise task", "Overall analytics"])
st.header(section)

if section == "Today's task":
    calendar = api("GET", "/calendar/today")
    if calendar is not None:
        st.caption(date.fromisoformat(calendar["date"]).strftime("%A, %d %B %Y"))
        st.button("Refresh tasks")
        message = st.session_state.pop("completion_message", None)
        if message:
            st.success(message)

        tasks = api("GET", "/tasks/today")
        if tasks is not None:
            task_metrics(tasks)
            if not tasks:
                st.info("No questions have been assigned for today.")

            for task in tasks:
                with st.container(border=True):
                    st.subheader(task["ques_no"])
                    if task["status"] == "Completed":
                        st.success(f"Completed · {task['difficulty'] or 'Difficulty unavailable'}")
                    else:
                        with st.form(f"complete_{task['id']}"):
                            st.caption("Pending")
                            difficulty = st.selectbox("Difficulty", DIFFICULTIES, index=None)
                            submitted = st.form_submit_button("Mark completed", type="primary")

                        if submitted:
                            if difficulty is None:
                                st.warning("Select a difficulty first.")
                            else:
                                result = api(
                                    "POST",
                                    f"/tasks/{task['id']}",
                                    json={"difficulty": difficulty},
                                )
                                if result is not None:
                                    st.session_state["completion_message"] = (
                                        f"Marked {result['ques_no']} complete."
                                    )
                                    st.rerun()

elif section == "Day-wise task":
    calendar = api("GET", "/calendar/today")
    if calendar is not None:
        selected = st.date_input("Assigned date", date.fromisoformat(calendar["date"]))
        tasks = api("GET", f"/tasks/date/{selected.isoformat()}")
        if tasks is not None:
            completed = task_metrics(tasks)
            if tasks:
                st.progress(completed / len(tasks), text=f"{completed} of {len(tasks)} complete")
            task_table(tasks)

else:
    analytics_view()