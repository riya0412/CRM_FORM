# settings_page.py
import streamlit as st
import json
import mysql.connector
from mysql.connector import Error
import bcrypt
from template import  fetch_templates
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit

def get_users():
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
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
            return users
    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def update_user(user_id, username, password, role):
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
            cursor = connection.cursor()
            if password:  # If password is provided, hash it
                password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                cursor.execute("""
                    UPDATE users
                    SET username = %s, password_hash = %s, role = %s
                    WHERE id = %s
                """, (username, password_hash, role, user_id))
            else:  # If password is not provided, update only username and role
                cursor.execute("""
                    UPDATE users
                    SET username = %s, role = %s
                    WHERE id = %s
                """, (username, role, user_id))
            connection.commit()
            st.success("User updated successfully!")
    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def delete_user(user_id):
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
            cursor = connection.cursor()
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            connection.commit()
            st.success("User deleted successfully!")
    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def add_user(username, password, role):
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
            cursor = connection.cursor()
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            cursor.execute("""
                INSERT INTO users (username, password_hash, role)
                VALUES (%s, %s, %s)
            """, (username, password_hash, role))
            connection.commit()
            st.success("User added successfully!")
    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def users():
    # st.title("Settings")

    # Manage Users
    st.header("User Management")
    st.write("Manage user accounts and their roles.")

    users = get_users()
    if users:
        for user in users:
            with st.expander(f"User ID: {user['id']} - {user['username']}"):
                new_username = st.text_input("Username", value=user['username'], key=f"username_{user['id']}")
                new_password = st.text_input("New Password (leave blank to keep current)", type="password", key=f"password_{user['id']}")
                new_role = st.selectbox("Role", ["owner", "admin", "technician"], index=["owner", "admin", "technician"].index(user['role']), key=f"role_{user['id']}")
                if st.button(f"Update User {user['id']}", key=f"update_user_{user['id']}"):
                    update_user(user['id'], new_username, new_password, new_role)
                if st.button(f"Delete User {user['id']}", key=f"delete_user_{user['id']}"):
                    delete_user(user['id'])

    st.subheader("Add New User")
    new_username = st.text_input("New Username", key="new_username")
    new_password = st.text_input("New Password", type="password", key="new_user_password")
    new_role = st.selectbox("Role", ["owner", "admin", "technician"], key="new_user_role")
    if st.button("Add User", key="add_user"):
        if new_username and new_password:
            add_user(new_username, new_password, new_role)
        else:
            st.error("Username and Password are required to add a new user.")

def get_api_keys():
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

def templates():
    st.title("Template Management")
    scheduler = BackgroundScheduler()
    current_interval = 24 
    # Schedule the API fetch task
    def schedule_task(interval):
        global current_interval
        current_interval = interval
        scheduler.remove_all_jobs()
        scheduler.add_job(fetch_templates, trigger=IntervalTrigger(hours=current_interval))

    # Initialize scheduler
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
    schedule_task(current_interval)
    # st.header("Settings")
    interval = st.number_input("Set Timer Interval (hours)", min_value=1, max_value=168, value=current_interval)
    
    if st.button("Update Interval"):
        schedule_task(interval)
        st.success(f"Timer interval updated to {interval} hours.")

    st.header("Current Scheduled Interval")
    st.write(f"The current interval for the API call is set to {current_interval} hours.")
    
    st.header("Manual Fetch")
    if st.button("Fetch Templates Now"):
        fetch_templates()
        st.success("Templates fetched and database updated.")

def api():
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

def settings_page():
    st.title("Settings")

    setting=st.sidebar.selectbox("Choose settings", ["User Setting", "API Setting","Template Timer"])
    if setting == "User Setting":
        users()
    elif setting == "API Setting":
        api()
    elif setting == "Template Timer":
        templates()
