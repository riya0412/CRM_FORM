import streamlit as st
from login import login_page
from technician_page import technician_page
from admin_page import admin_page
from test import dashboard
from settings import settings_page

# Function to handle logout
def logout():
    st.session_state.clear()
    st.rerun()
# Check login status
if 'logged_in' in st.session_state and st.session_state['logged_in']:
    role = st.session_state.get('role')
    st.title('Document Upload System')

    # Navigation
    if role == 'owner':
        page = st.sidebar.selectbox("Choose a page", ["Technician", "Admin", "Dashboard", "Settings"])
    elif role == 'admin':
        page = st.sidebar.selectbox("Choose a page", ["Technician", "Admin", "Dashboard"])
    elif role == 'technician':
        page = st.sidebar.selectbox("Choose a page", ["Technician"])
    
    # Load the appropriate page
    if page == "Technician":
        technician_page()
    elif page == "Admin":
        admin_page()
    elif page == "Dashboard":
        dashboard()
    elif page == "Settings":
        if role == 'owner':
            settings_page()
        else:
            st.error("Access denied")
    # Logout button
    if st.sidebar.button("Logout"):
        logout()
else:
    login_page()
