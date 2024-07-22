import streamlit as st
from technician_page import technician_page
from admin_page import admin_page

# Set up the main app layout
st.title('Document Upload System')

# Navigation
page = st.sidebar.selectbox("Choose a page", ["Technician", "Admin"])

# Load the appropriate page
if page == "Technician":
    technician_page()
elif page == "Admin":
    admin_page()
