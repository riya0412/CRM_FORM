import streamlit as st
import mysql.connector
from mysql.connector import Error

def create_connection():
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
            return connection
    except Error as e:
        st.error(f"Error: {e}")
        return None

def get_reminder_template_id():
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT reminder_template_id FROM reminder LIMIT 1")
            result = cursor.fetchone()
            return result['reminder_template_id'] if result else None
        except Error as e:
            st.error(f"Error: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return None

def update_reminder_template_id(template_id):
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("UPDATE reminder SET reminder_template_id = %s", (template_id,))
            connection.commit()
            st.success("Reminder template ID updated successfully!")
        except Error as e:
            st.error(f"Error: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

def reminder_setting():
     # Reminder Message
    st.header("Reminder Message")
    current_template_id = get_reminder_template_id()
    new_template_id = st.text_input("Reminder Template ID", value=current_template_id)
    if st.button("Update Reminder Template ID"):
        update_reminder_template_id(new_template_id)