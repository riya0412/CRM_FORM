import streamlit as st
import pandas as pd
import mysql.connector
from datetime import datetime
import tempfile
from ftplib import FTP
import requests
import ftplib
import os
import time as tm

# Initialize MySQL connection
def get_db_connection():
    dbcreds=st.secrets["database"]
    host = dbcreds["dbhost"]
    user = dbcreds["dbuser"]
    password = dbcreds["dbpassword"]
    database=dbcreds["dbdatabase"]
    return mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )

# Load data from MySQL
def load_data():
    conn = get_db_connection()
    query = "SELECT * FROM Leads"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Update pipeline in MySQL
def update_pipeline(lead_id, column_name, value):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = f"UPDATE Pipeline SET {column_name} = %s WHERE Lead_Project_ID = %s"
    cursor.execute(query, (value, lead_id))
    conn.commit()
    cursor.close()
    conn.close()

# Log action in MySQL
def log_action(lead_project_id, sheet_name, column_name, action, old_value, new_value):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO Logs (Primary_Key, Timestamp, Sheet_Name, Column_Name, Action, Old_Value, New_Value)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(timestamp)
    cursor.execute(query, (lead_project_id, timestamp, sheet_name, column_name, action, old_value, new_value))
    conn.commit()
    cursor.close()
    conn.close()

# Update lead status in MySQL
def update_lead_status(lead_id, new_status):
    conn = get_db_connection()
    cursor = conn.cursor()
    query1="select Status from Leads where Lead_Project_ID=%s "
    cursor.execute(query1, (lead_id,))
    old_status=cursor.fetchone()
    query2 = "UPDATE Leads SET Status = %s, Last_Contact = %s WHERE Lead_Project_ID = %s"
    cursor.execute(query2, (new_status, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), lead_id))
    conn.commit()
    cursor.close()
    conn.close()
    log_action(lead_id, 'Leads', 'Status', 'Update', old_status[0], new_status)

# Upload to FTP
def upload_to_ftp(uploaded_file, ftp_host, ftp_user, ftp_pass, ftp_directory):
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(uploaded_file.getbuffer())
        temp_file_path = temp_file.name

    ftp_link = ''
    filename = uploaded_file.name
    with FTP(ftp_host) as ftp:
        try:
            ftp.login(ftp_user, ftp_pass)
            ftp.cwd(ftp_directory)
            with open(temp_file_path, 'rb') as file:
                ftp.storbinary(f'STOR {filename}', file)
            ftp_link = f'{ftp_directory}/{filename}'
            print(f"File '{filename}' uploaded successfully. Link: {ftp_link}")
        except Exception as e:
            print(f"Failed to upload file: {e}")
    return ftp_link

# Update document link in MySQL
def update_document_link(client_id, column_name, file_link):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Update document link in leads table
    query = f"UPDATE Leads SET {column_name} = %s WHERE Lead_Project_ID = %s"
    cursor.execute(query, (file_link, client_id))
    # Log document upload
    log_action(client_id, "Leads", column_name, "Update", "", file_link)
    # Update pipeline table
    update_pipeline(client_id, column_name, "TRUE")
    
    # Log document upload
    log_action(client_id, "Pipeline", column_name, "Update", "", "TRUE")
    
    conn.commit()
    cursor.close()
    conn.close()

# Handle file upload
# def upload_documents(column_name, ftp_host, ftp_user, ftp_pass, ftp_directory):
#     uploaded_files = st.file_uploader("Upload Documents", accept_multiple_files=True, key='file_uploader')

#     if st.button("Upload"):
#         if uploaded_files:
#             for uploaded_file in uploaded_files:
#                 file_link = upload_to_ftp(uploaded_file, ftp_host, ftp_user, ftp_pass, ftp_directory)
#                 st.success(f"Document uploaded successfully: {file_link}")
#                 update_document_link(st.session_state.selected_client_id, column_name, file_link)
#             st.session_state.uploaded_files = []
#         else:
#             st.warning("Please select a file to upload.")

        # st.rerun()

# Display client details
def client_details(client_id):
    st.title(f"Client Details")

    # Load the data
    df = load_data()
    client_info = df[df['Lead_Project_ID'] == client_id].iloc[0]
    with st.container():

        st.subheader(f"Client: {client_info['Lead_Name']}")
        col1,col2=st.columns(2)

        with col1:
            st.write(f"📱WhatsApp Number: +{client_info['WhatsApp_Number']}")
            st.write(f"📱Email: {client_info['Email']}")
            st.write(f"🏠Address: {client_info['Address']}")
            st.write(f"🕑Status: {client_info['Status']}")
            st.write(f"🕑Follow-Up Required?: {client_info['Follow_Up_Required']}")
            st.write(f"📆Last Contact: {client_info['Last_Contact']}")
            st.write(f"📆Preliminary Meeting Scheduled Date: {client_info['Preliminary_Meeting_Scheduled_Date']}")
        with col2:
            document_fields = [
                ("Document uploaded by Technician", "Document_uploaded_by_Technician"),
                ("Document Upload by Client", "Document_Upload_by_Client"),
                ("Admin Uploads 5 Documents consolidated", "Admin_Uploads_5_Documents_consolidated"),
                ("PI and Survey Sheet Documents uploaded by Technician", "PI_and_Survey_Sheet_Documents_uploaded_by_Technician")
            ]

            for doc_label, doc_field in document_fields:
                if client_info[doc_field]:
                    if client_info[doc_field].startswith('http'):
                        st.write(f"📝{doc_label}: {client_info[doc_field]} [View]({client_info[doc_field]})")
                    else:
                        st.write(f"📝{doc_label}: <a href='https://ftp-file.streamlit.app/?file_path={client_info[doc_field]}' target='_blank'>View</a>", unsafe_allow_html=True)
    # st.write(f"Gratitude Message: {client_info['Gratitude Message']}")

# Handle different tasks
def handle_upload_quotation(df):
    st.subheader("Pending Document Clients")
    df_selected = df[['Lead_Project_ID', 'Lead_Name', 'WhatsApp_Number', 'Email', 'Address', 'Status', 'Last_Contact']]
    pending_df = df_selected[(df_selected['Status'] == 'Document uploaded by Technician') | (df_selected['Status'] == 'Document Upload by Client')]
    st.dataframe(pending_df)
    creds=st.secrets["ftp"]
    ftp_host = creds["host"]
    ftp_user = creds["user"]
    ftp_pass = creds["password"]
    ftp_directory = '/'
    client_id = st.selectbox("Select Client ID", ["Please select"] + list(pending_df['Lead_Project_ID']))

    if client_id != "Please select":
        st.session_state.selected_client_id = int(client_id)
        client_details(st.session_state.selected_client_id)
        st.subheader("Upload Documents")
        uploaded_files = st.file_uploader("Upload Documents", accept_multiple_files=True, key='file_uploader')
        if st.button("Upload"):
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    file_link =  upload_to_ftp(uploaded_file, ftp_host, ftp_user, ftp_pass, ftp_directory)
                    # Update the status in your database
                    update_document_link(client_id, "Admin_Uploads_5_Documents_consolidated", file_link)
                    update_lead_status(client_id, "Admin Uploads 5 Documents consolidated")
                    st.success(f"Document uploaded successfully: {file_link}")
                st.rerun()
        # upload_documents("Admin_Uploads_5_Documents_consolidated", ftp_host, ftp_user, ftp_pass, ftp_directory)
        # update_lead_status(client_id, "Admin Uploads 5 Documents consolidated")
        # update_lead_status(st.session_state.selected_client_id, "Admin Uploads 5 Documents consolidated")
def update_leads_action(lead_project_id, action, date_time=None):
    conn = get_db_connection()
    cursor = conn.cursor()

    now = datetime.now()

    if action == 'Follow Up':
        follow_up_date = datetime.combine(date_time[0], date_time[1])
        time_diff = (follow_up_date - now).days
        
        if time_diff <= 15:
            drip_message = 3
            drip_message_sequence = 1
        else:
            drip_message = 4
            drip_message_sequence = 1

        # Update Leads table
        update_leads_query = """
        UPDATE Leads
        SET Status = 'Follow Up',
            Last_Contact = %s,
            Follow_up_Date = %s,
            Next_Activity = DATE_ADD(%s, INTERVAL 48 HOUR),
            Drip_sequence = %s,
            Drip_Message_sequence = %s
        WHERE Lead_Project_ID = %s
        """
        cursor.execute(update_leads_query, (now, follow_up_date, now, drip_message, drip_message_sequence, lead_project_id))
        conn.commit()
        # Log the update
        log_query = """
        INSERT INTO Logs (Primary_Key, Timestamp, Sheet_Name, Column_Name, Action, Old_Value, New_Value)
        VALUES (%s, %s, 'Leads', 'Follow_up_Date', 'Update', NULL, %s),
               (%s, %s, 'Leads', 'Status', 'Update', NULL, 'Follow Up'),
               (%s, %s, 'Leads', 'Last_Contact', 'Update', NULL, %s),
               (%s, %s, 'Leads', 'Next_Activity', 'Update', NULL, %s)
        """
        cursor.execute(log_query, (lead_project_id, now, follow_up_date,lead_project_id, now, lead_project_id, now, now, lead_project_id, now, follow_up_date))
        conn.commit()
        # Update Pipeline table
        update_pipeline_query = """
        UPDATE Pipeline
        SET Drip = TRUE
        WHERE Lead_Project_ID = %s
        """
        cursor.execute(update_pipeline_query, (lead_project_id,))
        conn.commit()
    elif action == 'Visit Scheduled':
        visit_date = datetime.combine(date_time[0], date_time[1])

        # Update Leads table
        update_leads_query = """
        UPDATE Leads
        SET Status = 'Visit Scheduled',
            Last_Contact = %s,
            Final_Meeting_Scheduled_Date = %s,
            Next_Activity = DATE_ADD(%s, INTERVAL 48 HOUR)
        WHERE Lead_Project_ID = %s
        """
        cursor.execute(update_leads_query, (now, visit_date, now, lead_project_id))
        conn.commit()
        # Log the update
        log_query = """
        INSERT INTO Logs (Primary_Key, Timestamp, Sheet_Name, Column_Name, Action, Old_Value, New_Value)
        VALUES (%s, %s, 'Leads', 'Final_Meeting_Scheduled_Date', 'Update', NULL, %s),
               (%s, %s, 'Leads', 'Status', 'Update', NULL, 'Visit Scheduled'),
               (%s, %s, 'Leads', 'Last_Contact', 'Update', NULL, %s),
               (%s, %s, 'Leads', 'Next_Activity', 'Update', NULL, %s)
        """
        cursor.execute(log_query, (lead_project_id, now, visit_date,lead_project_id, now, lead_project_id, now, now, lead_project_id, now, visit_date))
        conn.commit()
    elif action == 'No Response':
        # Update Leads table
        update_leads_query = """
        UPDATE Leads
        SET Status = 'No Response',
            Last_Contact = %s,
            Drip_sequence = 2,
            Drip_Message_sequence = 1
        WHERE Lead_Project_ID = %s
        """
        cursor.execute(update_leads_query, (now, lead_project_id))
        conn.commit()
        # Log the update
        log_query = """
        INSERT INTO Logs (Primary_Key, Timestamp, Sheet_Name, Column_Name, Action, Old_Value, New_Value)
        VALUES (%s, %s, 'Leads', 'Drip_sequence', 'Update', NULL, '2'),
               (%s, %s, 'Leads', 'Drip_Message_sequence', 'Update', NULL, '1'),
               (%s, %s, 'Leads', 'Status', 'Update', NULL, 'No Response'),
               (%s, %s, 'Leads', 'Last_Contact', 'Update', NULL, %s)
        """
        cursor.execute(log_query, (lead_project_id, now,lead_project_id, now, lead_project_id, now, lead_project_id, now, now))
        conn.commit()
    conn.commit()
    cursor.close()
    conn.close()
def handle_schedule_call(df):
    st.subheader("All Clients")
    df_selected = df[['Lead_Project_ID', 'Lead_Name', 'WhatsApp_Number', 'Email', 'Address', 'Status', 'Last_Contact']]
    pending_df = df_selected[df_selected['Status'] == 'Quotation Sent']
    st.dataframe(pending_df)
    creds=st.secrets["ftp"]
    ftp_host = creds["host"]
    ftp_user = creds["user"]
    ftp_pass = creds["password"]
    ftp_directory = '/'
    client_id = st.selectbox("Select Client ID", ["Please select"] + list(pending_df['Lead_Project_ID']))

    if client_id != "Please select":
        st.session_state.selected_client_id = int(client_id)
        client_details(st.session_state.selected_client_id)
        st.subheader("Call Details")
        action = st.selectbox("Select Action", ["Please select"]+["Follow Up", "Visit Scheduled", "No Response"])
        if action in ["Follow Up", "Visit Scheduled"]:
            date = st.date_input("Select Date")
            time = st.time_input("Select Time")
            date_time = (date, time)
            
        if st.button("Submit"):
            if client_id and action:
                if action in ["Follow Up", "Visit Scheduled"] and date_time:
                    update_leads_action(client_id, action, date_time)
                elif action == "No Response":
                    update_leads_action(client_id, action)
                st.success("Lead updated successfully")
                tm.sleep(5)
                st.rerun()
    else:
        st.error("Please provide all required inputs")

def handle_upload_pi_survey_sheet(df):
    st.subheader("Pending Document Clients")
    df_selected = df[['Lead_Project_ID', 'Lead_Name', 'WhatsApp_Number', 'Email', 'Address', 'Status', 'Last_Contact']]
    pending_df = df_selected[df_selected['Status'] == 'Final Meeting Scheduled']
    st.dataframe(pending_df)
    creds=st.secrets["ftp"]
    ftp_host = creds["host"]
    ftp_user = creds["user"]
    ftp_pass = creds["password"]
    ftp_directory = '/'
    client_id = st.selectbox("Select Client ID", ["Please select"] + list(pending_df['Lead_Project_ID']))

    if client_id != "Please select":
        st.session_state.selected_client_id = int(client_id)
        client_details(st.session_state.selected_client_id)
        st.subheader("Upload Documents")
        uploaded_files = st.file_uploader("Upload Documents", accept_multiple_files=True, key='file_uploader')
        if st.button("Upload"):
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    file_link =  upload_to_ftp(uploaded_file, ftp_host, ftp_user, ftp_pass, ftp_directory)
                    # Update the status in your database
                    update_document_link(client_id, "PI_and_Survey_Sheet_Documents_uploaded_by_Technician", file_link)
                    update_lead_status(client_id, "PI and Survey Sheet Documents uploaded by Technician")
                    st.success(f"Document uploaded successfully: {file_link}")
                st.rerun()
        # upload_documents("PI_and_Survey_Sheet_Documents_uploaded_by_Technician", ftp_host, ftp_user, ftp_pass, ftp_directory)
        # update_lead_status(client_id, "PI and Survey Sheet Documents uploaded by Technician")

def handle_upload_survey_feedback(df):
    st.subheader("Pending Document Clients")
    df_selected = df[['Lead_Project_ID', 'Lead_Name', 'WhatsApp_Number', 'Email', 'Address', 'Status', 'Last_Contact']]
    pending_df = df_selected[df_selected['Status'] == 'Order Delivered and Installation']
    st.dataframe(pending_df)
    creds=st.secrets["ftp"]
    ftp_host = creds["host"]
    ftp_user = creds["user"]
    ftp_pass = creds["password"]
    ftp_directory = '/'
    client_id = st.selectbox("Select Client ID", ["Please select"] + list(pending_df['Lead_Project_ID']))

    if client_id != "Please select":
        st.session_state.selected_client_id = int(client_id)
        client_details(st.session_state.selected_client_id)
        st.subheader("Upload Documents")
        uploaded_files = st.file_uploader("Upload Documents", accept_multiple_files=True, key='file_uploader')
        if st.button("Upload"):
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    file_link =  upload_to_ftp(uploaded_file, ftp_host, ftp_user, ftp_pass, ftp_directory)
                    # Update the status in your database
                    update_document_link(client_id, "Survey_Feedback", file_link)
                    update_lead_status(client_id, "Survey Feedback")
                    st.success(f"Document uploaded successfully: {file_link}")
                st.rerun()
        # upload_documents("Survey_Feedback", ftp_host, ftp_user, ftp_pass, ftp_directory)
        # update_lead_status(client_id, "Survey Feedback")

def delete_document(doc_name, client_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = f"SELECT * FROM Leads WHERE Lead_Project_ID = %s"
    cursor.execute(query, (client_id,))
    client_info = cursor.fetchone()
    
    if doc_name == "Document uploaded by Technician":
        update_pipeline(client_id, "Document_uploaded_by_Technician", "0")
        log_action(client_id, "Pipeline", "Document_uploaded_by_Technician", "Delete", "TRUE", "0")
        query1 = "SELECT Document_uploaded_by_Technician FROM Leads WHERE Lead_Project_ID = %s"
        cursor.execute(query1, (client_id,))
        link=cursor.fetchone()
        query = '''
            UPDATE Leads
            SET Document_uploaded_by_Technician = NULL
            WHERE Lead_Project_ID = %s
            '''
        cursor.execute(query, (client_id,))
        conn.commit()
        log_action(client_id, "Leads", "Document_uploaded_by_Technician", "Delete", link[0], "")
        update_lead_status(client_id, "Preliminary Meeting Scheduled")

    elif doc_name == "Document upload by Client":
        update_pipeline(client_id, "Document_upload_by_Client", "0")
        log_action(client_id, "Pipeline", "Document_upload_by_Client", "Delete", "TRUE", "0")
        query1 = "SELECT Document_upload_by_Client FROM Leads WHERE Lead_Project_ID = %s"
        cursor.execute(query1, (client_id,))
        link=cursor.fetchone()
        query = '''
            UPDATE Leads
            SET Document_upload_by_Client = NULL
            WHERE Lead_Project_ID = %s
            '''
        cursor.execute(query, (client_id,))
        conn.commit()
        log_action(client_id, "Leads", "Document_upload_by_Client", "Delete", link[0], "")
        update_lead_status(client_id, "Get Quote")

    elif doc_name == "Admin Uploads 5 Documents consolidated":
        update_pipeline(client_id, "Admin_Uploads_5_Documents_consolidated", "0")
        log_action(client_id, "Pipeline", "Admin_Uploads_5_Documents_consolidated", "Delete", "TRUE", "0")
        query1 = "SELECT Admin_Uploads_5_Documents_consolidated FROM Leads WHERE Lead_Project_ID = %s"
        cursor.execute(query1, (client_id,))
        link=cursor.fetchone()
        query = '''
            UPDATE Leads
            SET Admin_Uploads_5_Documents_consolidated = NULL
            WHERE Lead_Project_ID = %s
            '''
        cursor.execute(query, (client_id,))
        conn.commit()
        log_action(client_id, "Leads", "Admin_Uploads_5_Documents_consolidated", "Delete", link[0], "")
        cursor.execute("""
        SELECT "Document_uploaded_by_Technician", "Document_Upload_by_Client"
        FROM Leads
        WHERE Lead_Project_ID = %s
        """, (client_id,))
        client_info = cursor.fetchone()
        conn.close()
        if client_info:
            doc_uploaded_tech, doc_uploaded_client = client_info
            # Update the lead status based on the condition
            if doc_uploaded_tech != "":
                update_lead_status(client_id, "Document uploaded by Technician")
            elif doc_uploaded_client != "":
                update_lead_status(client_id, "Document Upload by Client")
    
    elif doc_name == "PI and Survey Sheet Documents uploaded by Technician":
        update_pipeline(client_id, "PI_and_Survey_Sheet_Documents_uploaded_by_Technician", "0")
        log_action(client_id, "Pipeline", "PI_and_Survey_Sheet_Documents_uploaded_by_Technician", "Delete", "TRUE", "0")
        query1 = "SELECT PI_and_Survey_Sheet_Documents_uploaded_by_Technician FROM Leads WHERE Lead_Project_ID = %s"
        cursor.execute(query1, (client_id,))
        link=cursor.fetchone()
        query = '''
            UPDATE Leads
            SET PI_and_Survey_Sheet_Documents_uploaded_by_Technician = NULL
            WHERE Lead_Project_ID = %s
            '''
        cursor.execute(query, (client_id,))
        conn.commit()
        log_action(client_id, "Leads", "PI_and_Survey_Sheet_Documents_uploaded_by_Technician", "Delete", link[0], "")
        update_lead_status(client_id, "Final Meeting Scheduled")
    
    elif doc_name == "Survey Feedback":
        update_pipeline(client_id, "Survey_Feedback", "0")
        log_action(client_id, "Pipeline", "Survey_Feedback", "Delete", "TRUE", "0")
        query1 = "SELECT Survey_Feedback FROM Leads WHERE Lead_Project_ID = %s"
        cursor.execute(query1, (client_id,))
        link=cursor.fetchone()
        query = '''
            UPDATE Leads
            SET Survey_Feedback = NULL
            WHERE Lead_Project_ID = %s
            '''
        cursor.execute(query, (client_id,))
        conn.commit()
        log_action(client_id, "Leads", "Survey_Feedback", "Delete", link[0], "")
        update_lead_status(client_id, "Order Delivered and Installation")
    
    # conn.commit()
    # cursor.close()
    # conn.close()

def download_file_from_ftp(ftp_url, local_path):
    try:
        # Parse FTP URL
        creds=st.secrets["ftp"]
        ftp_host = creds["host"]
        ftp_user = creds["user"]
        ftp_password = creds["password"]
        # Remove leading slashes if present
        if ftp_url.startswith('//'):
            ftp_url = ftp_url.lstrip('/')
        print(ftp_url)
        # Extract file name from path
        file_name = os.path.basename(ftp_url)
        print(file_name)
        # Define local file path
        local_file_path = os.path.join(os.path.dirname(__file__), file_name)  # Save locally with the same filename
        print(local_file_path)
        # Connect to FTP server and download file
        with ftplib.FTP(ftp_host) as ftp:
            ftp.login(ftp_user, ftp_password)
            st.write(f"Logged in to FTP server: {ftp_host}")

            with open(local_file_path, 'wb') as local_file:
                ftp.retrbinary(f'RETR {ftp_url}', local_file.write)
        # ftp.quit()
        print(local_file_path)
        return local_file_path
    except Exception as e:
        st.error(f"Failed to download file from FTP: {e}")
        return None

def send_document(client_info, document_name, document_path):
    api=st.secrets["API"]
    API_URL = api["DOC_URL"]
    API_KEY = api["API_KEY"]
    headers = {
    'accept': '*/*',
    'X-Api-Key': API_KEY
    }
    payload = {}
    # Prepare the files parameter
    files = {
        'docFile': (document_name, open(document_path, 'rb'), 'application/pdf')
    }
    # print(client_info['WhatsApp_Number'])
    # print(contact)
    url = f"{API_URL}?contactNo={client_info['WhatsApp_Number']}"
    # Prepare additional form data if needed
    # data = {
    #     'ContactNo': client_info['WhatsApp_Number'],
    #     'ContactName': client_info['Lead_Name'],
    #     # Add other required form fields here
    # }
    st.write(document_path)
    # def display_pdf(file_path):
    #     with open(file_path, 'rb') as pdf_file:
    #         pdf_bytes = pdf_file.read()
    #         st.download_button(label="Download PDF", data=pdf_bytes, file_name="downloaded_file.pdf", mime="application/pdf")
    # display_pdf(document_path)
    os.path.exists
    # Send POST request with files and additional form data
    response = requests.post(url, headers=headers, data=payload, files=files)
    
    if response.status_code == 200:
        st.success(f"Document '{document_name}' sent successfully!")
        st.write(response.text)
    else:
        st.error(f"Failed to send document. Status code: {response.status_code}, Response: {response.text}")

def show_delete_entity_page(df):
    st.title("Verify Uploaded Documents")
    selected_columns = ['Lead_Project_ID', 'Lead_Name', 'WhatsApp_Number', 'Email', 'Address', 'Status', "Last_Contact"]
    df_selected = df[selected_columns]
    st.dataframe(df_selected)
    client_id = st.selectbox("Select Client ID", ["Please select"] + list(df['Lead_Project_ID']))
    
    if client_id != "Please select":
        client_info = df[df['Lead_Project_ID'] == client_id].iloc[0]
        with st.container():
            st.subheader(f"Client: {client_info['Lead_Name']}")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"📱WhatsApp Number: +{client_info['WhatsApp_Number']}")
                st.write(f"📱Email: {client_info['Email']}")
                st.write(f"🏠Address: {client_info['Address']}")
                st.write(f"🕑Status: {client_info['Status']}")
            with col2:
                st.write(f"🕑Follow-Up Required?: {client_info['Follow_Up_Required']}")
                st.write(f"📆Last Contact: {client_info['Last_Contact']}")
                st.write(f"📆Preliminary Meeting Scheduled Date: {client_info['Preliminary_Meeting_Scheduled_Date']}")
                st.write(f"📆Final Meeting Scheduled Date: {client_info['Final_Meeting_Scheduled_Date']}")

        documents = [
            {"name": "Document uploaded by Technician", "link": client_info.get('Document_uploaded_by_Technician')},
            {"name": "Document Upload by Client", "link": client_info.get('Document_Upload_by_Client')},
            {"name": "Admin Uploads 5 Documents consolidated", "link": client_info.get('Admin_Uploads_5_Documents_consolidated')},
            {"name": "PI and Survey Sheet Documents uploaded by Technician", "link": client_info.get('PI_and_Survey_Sheet_Documents_uploaded_by_Technician')}
        ]

        st.subheader("Documents")
        for doc in documents:
            if doc["link"]!=None:
                # print(doc["link"])
                col1, col2, col3 = st.columns([4, 2, 2])
                with col1:
                    st.write(f"[{doc['name']}]({doc['link']})")
                with col2:
                    delete_placeholder = st.empty()
                    if delete_placeholder.button("Delete", key=f"delete_{doc['name']}"):
                        st.session_state.document_to_delete = (doc['name'], client_id)
                        st.session_state.delete_confirmation_shown = True
                        st.session_state.confirmation_doc_name = doc['name']
                with col3:
                    if st.button("Send", key=f"send_{doc['name']}"):
                        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                            local_path = download_file_from_ftp(doc["link"], tmp_file.name)
                            if local_path:
                                send_document(client_info, doc['name'], local_path)
                                # os.remove(local_path)  # Clean up the local file

        # Handle document deletion confirmation
        if 'delete_confirmation_shown' in st.session_state and st.session_state.delete_confirmation_shown:
            doc_name, client_id = st.session_state.document_to_delete
            st.warning("Do you really, really want to delete this document?")
            col1, col2 = st.columns(2)
    
            with col1:
                if st.button("Yes, I'm ready"):
                    delete_document(doc_name, client_id)
                    st.success(f"Deleted {doc_name}")
                    st.session_state.delete_confirmation_shown = False
                    st.session_state.document_to_delete = None
                    st.rerun()
            
            with col2:
                if st.button("Cancel"):
                    st.session_state.delete_confirmation_shown = False
                    st.session_state.document_to_delete = None
                    st.rerun()


    # if st.button("Back to Admin Page"):
    #     st.session_state.delete_entity_active = False
    #     st.rerun()

# def show_regular_admin_page(df):
#     page = st.sidebar.selectbox("Admin Task", ["Upload Quotation", "Schedule Call", "Upload PI and Survey sheet", "Upload Survey Feedback"])
    
#     if page == "Upload Quotation":
#         handle_upload_quotation(df)
#     elif page == "Schedule Call":
#         handle_schedule_call(df)
#     elif page == "Upload PI and Survey sheet":
#         handle_upload_pi_survey_sheet(df)
#     elif page == "Upload Survey Feedback":
#         handle_upload_survey_feedback(df)

def admin_page():
    st.header("Admin Page")
    df = load_data()

    page = st.sidebar.selectbox("Admin Task", ["Upload Quotation", "Schedule Call", "Upload PI and Survey sheet", "Upload Survey Feedback","Verify Uploaded Documents"])
    
    if page == "Upload Quotation":
        handle_upload_quotation(df)
    elif page == "Schedule Call":
        handle_schedule_call(df)
    elif page == "Upload PI and Survey sheet":
        handle_upload_pi_survey_sheet(df)
    elif page == "Upload Survey Feedback":
        handle_upload_survey_feedback(df)
    elif page=="Verify Uploaded Documents":
        show_delete_entity_page(df)
    # Create a state variable for the Delete Entity button
    # if 'delete_entity_active' not in st.session_state:
    #     st.session_state.delete_entity_active = False

    # # Delete Entity button in sidebar
    # if st.sidebar.button("Delete Entity"):
    #     st.session_state.delete_entity_active = True

    # Check if Delete Entity is active
    # if st.session_state.delete_entity_active:
    #     show_delete_entity_page(df)
    # else:
    #     show_regular_admin_page(df)

# if __name__ == "__main__":
    # main()
