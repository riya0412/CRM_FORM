import mysql.connector
from mysql.connector import Error
import streamlit as st

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

def fetch_steps():
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT step_id, step_name FROM Steps")
            steps = cursor.fetchall()
            return steps
        except Error as e:
            st.error(f"Error: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return []

def fetch_templates():
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT id, templateName FROM templates WHERE isActive = TRUE")
            templates = cursor.fetchall()
            return templates
        except Error as e:
            st.error(f"Error: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return []

def fetch_drips():
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM drip")
            drips = cursor.fetchall()
            return drips
        except Error as e:
            st.error(f"Error: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return []

def add_drip_to_db(drip_id, step_id, message_details):
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            for detail in message_details:
                cursor.execute("""
                    INSERT INTO drip (step_id, Drip_sequence, drip_Message_sequence, Time_Delay_Hours, Temp_ID, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (step_id, drip_id, detail['drip_Message_sequence'], detail['Time_Delay_Hours'], detail['Temp_ID'], detail['is_active']))
            connection.commit()
            return True
        except Error as e:
            st.error(f"Error: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return False

def drip_settings_page():
    # st.title("Drip Settings")

    # Display existing drips
    st.header("Existing Drips")
    drips = fetch_drips()
    if drips:
        st.write("Select a drip to view details:")
        drip_ids = [drip['Drip_sequence'] for drip in drips]
        selected_drip_id = st.selectbox("Select Drip ID",["Please select"] + drip_ids)
        if selected_drip_id!="Please select":
            for drip in drips:
                if drip['Drip_sequence'] == selected_drip_id:
                    st.subheader(f"Drip ID: {drip['Drip_sequence']}")
                    st.write(f"Step ID: {drip['step_id']}")
                    st.write(f"Message Sequence: {drip['drip_Message_sequence']}")
                    st.write(f"Time Delay Hours: {drip['Time_Delay_Hours']}")
                    st.write(f"Template ID: {drip['Temp_ID']}")
                    st.write(f"Is Active: {drip['is_active']}")
                    st.write(f"Last Updated: {drip['last_updated']}")

    st.header("Add New Drip")

    # Fetch steps and templates
    steps = fetch_steps()
    templates = fetch_templates()

    if not steps or not templates:
        st.error("Unable to fetch steps or templates. Please try again later.")
        return

    step_options = {step['step_name']: step['step_id'] for step in steps}
    template_options = {template['templateName']: template['id'] for template in templates}

    # Select Step ID
    selected_step_name = st.selectbox("Select Step", ["Please select"] +list(step_options.keys()))
    if selected_step_name!="Please select":
        selected_step_id = step_options[selected_step_name]

    # Input Drip ID and Number of Messages
    drip_id = st.number_input("Drip ID", min_value=1, step=1 , value=1)
    num_messages = st.number_input("Number of Messages in Drip", min_value=1, step=1, value=1)

    # Dynamic form for each message in the drip
    message_details = []
    for i in range(num_messages):
        st.subheader(f"Message {i+1}")
        template_name = st.selectbox(f"Template ID for Message {i+1}", list(template_options.keys()), key=f"template_{i}")
        time_delay_hours = st.number_input(f"Time Delay (Hours) for Message {i+1}", min_value=0, step=1, key=f"time_delay_{i}")
        is_active = st.checkbox(f"Is Active for Message {i+1}", key=f"is_active_{i}", value=True)
        
        message_details.append({
            "drip_Message_sequence": i + 1,
            "Temp_ID": template_options[template_name],
            "Time_Delay_Hours": time_delay_hours,
            "is_active": is_active
        })

    # Add Drip Button
    if st.button("Add Drip"):
        if add_drip_to_db(drip_id, selected_step_id, message_details):
            st.success("Drip added successfully!")
        st.rerun()
        else:
            st.error("Failed to add drip. Please try again.")
