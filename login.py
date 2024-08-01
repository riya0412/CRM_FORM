# login_page.py
import streamlit as st
import mysql.connector
from mysql.connector import Error
import bcrypt

def authenticate_user(username, password):
    try:
        dbcreds=st.secrets["database"]
        host = dbcreds["dbhost"]
        user = dbcreds["dbuser"]
        password = dbcreds["dbpassword"]
        database=dbcreds["dbdatabase"]
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if user and bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
                return user['role']
            else:
                return None
    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def login_page():
    st.title("Login")

    username = st.text_input("Username")
    password = st.text_input("Password")

    if st.button("Login"):
        role = authenticate_user(username, password)
        if role:
            st.session_state['logged_in'] = True
            st.session_state['role'] = role
            st.success(f"Logged in as {role}")
            st.rerun()
        else:
            st.error("Invalid username or password")
