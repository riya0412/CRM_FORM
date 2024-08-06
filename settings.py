# settings_page.py
import streamlit as st
import json
import mysql.connector
from mysql.connector import Error
import bcrypt
from template import  fetch_templates
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit
from drip import drip_settings_page
from reminder import reminder_setting

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
        st.rerun()
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
        st.rerun()
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
            # Clear session state
            st.session_state["new_username"] = ""
            st.session_state["new_user_password"] = ""
            st.session_state["new_user_role"] = "owner"
    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def users():
    # st.title("Settings")
    if "new_username" not in st.session_state:
        st.session_state["new_username"] = ""
    if "new_user_password" not in st.session_state:
        st.session_state["new_user_password"] = ""
    if "new_user_role" not in st.session_state:
        st.session_state["new_user_role"] = "owner"
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
    new_username_input = st.text_input("New Username", value="", key="new_username_input")
    new_password_input = st.text_input("New Password", type="password", value="", key="new_user_password_input")
    new_role_input = st.selectbox("Role", ["owner", "admin", "technician"], index=0, key="new_user_role_input")
    if st.button("Add User", key="add_user"):
        if new_username_input and new_password_input:
            add_user(new_username_input, new_password_input, new_role_input)
            
        # st.rerun()
        else:
            st.error("Username and Password are required to add a new user.")
        # Resetting session state values
        st.session_state["new_username"] = ""
        st.session_state["new_user_password"] = ""
        st.session_state["new_user_role"] = "owner"
        st.rerun()
    

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
    default_hour = 10
    default_minute = 0
    # Schedule the API fetch task
    def schedule_task(hour, minute):
        scheduler.remove_all_jobs()
        scheduler.add_job(fetch_templates, trigger=CronTrigger(hour=hour, minute=minute))

    # Initialize scheduler
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
    schedule_task(default_hour,default_minute)
    # st.header("Settings")
    fetch_hour = st.number_input("Hour", min_value=0, max_value=23, value=10, step=1)
    fetch_minute = st.number_input("Minute", min_value=0, max_value=59, value=0, step=1)
    if st.button("Update Time"):
        schedule_task(fetch_hour, fetch_minute)
        st.success(f"API fetch time updated to {fetch_hour:02d}:{fetch_minute:02d}.")
    # st.header("Current Scheduled Interval")
    # st.write(f"The current interval for the API call is set to {current_interval} hours.")
    
    st.header("Manual Fetch")
    if st.button("Fetch Templates Now"):
        fetch_templates()
        st.success("Templates fetched and database updated.")

def fetch_templates():
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
    # connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM templates")
            templates = cursor.fetchall()
            return templates
        except Error as e:
            st.error(f"Error: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return []

def display_templates():
    templates = fetch_templates()
    if templates:
        st.header("Templates Overview")
        st.dataframe(templates)
        template_ids = [template['id'] for template in templates]
        selected_id = st.selectbox("Select a Template to View Details", options=template_ids, format_func=lambda x: f"Template ID: {x}")

        if selected_id:
            for template in templates:
                if template['id'] == selected_id:
                    st.subheader(f"Details for Template ID: {template['id']}")
                    st.write(f"**Template Name:** {template['templateName']}")
                    st.write(f"**Media Type:** {template['mediaType']}")
                    st.write(f"**Message Text:** {template['msgText']}")
                    st.write(f"**Media File Name:** {template['mediaFileName']}")
                    st.write(f"**Template Status:** {template['templateStatus']}")
                    st.write(f"**Is Active:** {template['isActive']}")
                    st.write(f"**Last Updated:** {template['lastUpdated']}")
    else:
        st.write("No templates found.")

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

    setting=st.sidebar.selectbox("Choose settings", ["User Setting", "API Setting","Schedule Job","Template","Reminder Message","Drip"])
    if setting == "User Setting":
        users()
    elif setting == "API Setting":
        api()
    elif setting == "Schedule Job":
        templates()
    elif setting == "Template":
        display_templates()
    elif setting == "Reminder Message":
        reminder_setting()
    elif setting == "Drip":
        drip_settings_page()

