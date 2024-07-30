# settings_page.py
import streamlit as st
import json
import mysql.connector
from mysql.connector import Error

def get_api_keys():
    try:
        connection = mysql.connector.connect(
                host="srv1021.hstgr.io",
            user="u627331871_Crmfile",
            password="Crmfile@1234",
            database="u627331871_Crmfile"
        )
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM APIs")
            api_keys = cursor.fetchall()
            return api_keys
    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def update_api_key(api_id, new_key, description):
    try:
        connection = mysql.connector.connect(
            host="srv1021.hstgr.io",
            user="u627331871_Crmfile",
            password="Crmfile@1234",
            database="u627331871_Crmfile"
        )
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE APIs
                SET api_key = %s, descrip = %s
                WHERE id = %s
            """, (new_key, description, api_id))
            connection.commit()
            st.success("API Key updated successfully!")
    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def add_api_key(api_key, description):
    try:
        connection = mysql.connector.connect(
            host="srv1021.hstgr.io",
            user="u627331871_Crmfile",
            password="Crmfile@1234",
            database="u627331871_Crmfile"
        )
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO APIs (api_key, descrip)
                VALUES (%s, %s)
            """, (api_key, description))
            connection.commit()
            st.success("API Key added successfully!")
    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def settings_page():
    st.title("Settings")

    # Manage API Keys
    st.header("API Keys")

    api_keys = get_api_keys()
    
    if api_keys:
        st.write("Existing API Keys:")
        for key in api_keys:
            with st.expander(f"API Key ID: {key['id']}"):
                new_key = st.text_input("New API Key", value=key['api_key'])
                description = st.text_input("Description", value=key['descrip'])
                if st.button(f"Update API Key {key['id']}"):
                    update_api_key(key['id'], new_key, description)

    st.subheader("Add New API Key")
    new_key = st.text_input("New API Key")
    description = st.text_input("Description")
    if st.button("Add API Key"):
        add_api_key(new_key, description)
