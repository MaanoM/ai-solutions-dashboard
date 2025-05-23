import streamlit as st  # type: ignore

st.set_page_config(
    page_title="Ai-Solutions Product Sales Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Session state initialization ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = ""

# --- Login form ---
if not st.session_state.logged_in:
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Select Role", ["Admin", "Sales Team", "Marketing Team"])
    st.info("Please double click the Login button to proceed.")
    login_btn = st.button("Login")

    if login_btn and username and password:
        # For demo: accept any username/password
        st.session_state.logged_in = True
        st.session_state.role = role
        st.session_state.username = username
    st.stop()

# --- User info and logout ---
st.sidebar.markdown(f"**Logged in as:** {st.session_state.username} ({st.session_state.role})")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = ""
    st.rerun()

# --- Role-based navigation ---
main_page = st.Page("Overview.py", title="Overview", icon="🎈")
page_2 = st.Page("JobsNRequests.py", title="Jobs & Requests", icon="❄️")
page_3 = st.Page("Sales_Team.py", title="Sales Team Performance", icon="🎉")
page_4 = st.Page("CustomerEngagement.py", title="Customer Engagement", icon="🗨️")
page_5 = st.Page("Location.py", title="Location Analysis", icon="📍")

role = st.session_state.role

if role == "Admin":
    pages = [main_page, page_2, page_3, page_4, page_5]
elif role == "Sales Team":
    pages = [main_page, page_2, page_3, page_5]
elif role == "Marketing Team":
    pages = [main_page, page_4, page_5]
else:
    pages = [main_page]

pg = st.navigation(pages)
pg.run()