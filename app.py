import streamlit as st

from api_client import api, browser_link

st.set_page_config(page_title="TaskFlow", layout="wide")


def sign_in():
    st.title("TaskFlow")
    login_tab, signup_tab = st.tabs(["Sign in", "Create student account"])

    with login_tab:
        browser_link("Sign in to TaskFlow", "/browser-login")

    with signup_tab:
        with st.form("signup"):
            username = st.text_input("Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Create account")

        if submitted:
            result = api(
                "POST",
                "/signup",
                authenticated=False,
                json={"username": username, "email": email.strip(), "password": password},
            )
            if result is not None:
                st.success("Account created. Open the Sign in tab to continue.")


account = api("GET", "/me") if st.context.cookies.get("taskflow_session") else None

if account is None:
    page = st.Page(sign_in, title="Sign in", default=True)
else:
    st.sidebar.text(f"Logged in as {account['username']} ({account['role']})")
    browser_link("Sign out", "/browser-logout", sidebar=True)
    if account["role"] == "Admin":
        page = st.Page("pages/admin.py", title="Admin dashboard", default=True)
    else:
        page = st.Page("pages/user.py", title="Student dashboard", default=True)

st.navigation([page], position="hidden").run()