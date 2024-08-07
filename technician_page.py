import streamlit as st
import pandas as pd
import mysql.connector
from datetime import datetime
import tempfile
from ftplib import FTP

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
def load_data():
    conn = get_db_connection()
    query = "SELECT * FROM Old_Leads"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Log action in MySQL
def log_action(lead_project_id, sheet_name, column_name, action, old_value, new_value):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO Logs (Primary_Key, Timestamp, Sheet_Name, Column_Name, Action, Old_Value, New_Value)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(query, (lead_project_id, timestamp, sheet_name, column_name, action, old_value, new_value))
    conn.commit()
    cursor.close()
    conn.close()               

def update_lead_status(lead_id, new_status):
    conn = get_db_connection()
    cursor = conn.cursor()
    query1="select Status from Old_Leads where Lead_Project_ID=%s "
    cursor.execute(query1, (lead_id,))
    old_status=cursor.fetchone()
    query2 = "UPDATE Old_Leads SET Status = %s, Last_Contact = %s WHERE Lead_Project_ID = %s"
    cursor.execute(query2, (new_status, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), lead_id))
    conn.commit()
    cursor.close()
    conn.close()
    log_action(lead_id, 'Old_Leads', 'Status', 'Update', old_status[0], new_status)
def update_pipeline(lead_id, column_name, value):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = f"UPDATE Pipeline SET {column_name} = %s WHERE Lead_Project_ID = %s"
    cursor.execute(query, (value, lead_id))
    conn.commit()
    cursor.close()
    conn.close()

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
    
    # Update document link in Old_Leads table
    query = f"UPDATE Old_Leads SET {column_name} = %s WHERE Lead_Project_ID = %s"
    cursor.execute(query, (file_link, client_id))
    # Log document upload
    log_action(client_id, "Old_Leads", column_name, "Update", "", file_link)
    # Update pipeline table
    update_pipeline(client_id, column_name, "TRUE")
    
    # Log document upload
    log_action(client_id, "Pipeline", column_name, "Update", "", "TRUE")
    
    conn.commit()
    cursor.close()
    conn.close()

def upload_document(client_id):
    df = load_data()
    creds=st.secrets["ftp"]
    ftp_host = creds["host"]
    ftp_user = creds["user"]
    ftp_pass = creds["password"]
    ftp_directory = '/'
    uploaded_files = st.file_uploader("Upload Documents", accept_multiple_files=True, key='file_uploader')
    if st.button("Upload"):
        if uploaded_files:
            for uploaded_file in uploaded_files:
                file_link =  upload_to_ftp(uploaded_file, ftp_host, ftp_user, ftp_pass, ftp_directory)
                # Update the status in your database
                update_document_link(client_id, "Document_uploaded_by_Technician", file_link)
                update_lead_status(client_id, "Document uploaded by Technician")
                st.success(f"Document uploaded successfully: {file_link}")
            st.rerun()
                
def upload_PI(client_id):
    df = load_data()
    creds=st.secrets["ftp"]
    ftp_host = creds["host"]
    ftp_user = creds["user"]
    ftp_pass = creds["password"]
    ftp_directory = '/'
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
            
            st.write(f"📝Document uploaded by Technician: {client_info['Document_uploaded_by_Technician']}")
            st.write(f"📝Document Upload by Client: {client_info['Document_Upload_by_Client']}")
            st.write(f"📝Admin Uploads 5 Documents consolidated: {client_info['Admin_Uploads_5_Documents_consolidated']}")
            st.write(f"📆Final Meeting Scheduled Date: {client_info['Final_Meeting_Scheduled_Date']}")
            st.write(f"📝PI and Survey Sheet Documents uploaded by Technician: {client_info['PI_and_Survey_Sheet_Documents_uploaded_by_Technician']}")

def technician_page():
    st.header("Technician Page")

    # Load the data
    df = load_data()
    page=st.sidebar.selectbox("Technician Task",["Upload Dimension","Upload PI and Survey sheet"])
    if page=="Upload Dimension":
        # Display all clients
        st.subheader("Pending Document Clients")
        selected_columns=['Lead_Project_ID', 'Lead_Name', 'WhatsApp_Number', 'Email', 'Address', 'Status', 'Last_Contact']
        df_selected = df[selected_columns]
        st.dataframe(df_selected[df_selected['Status'] == 'Preliminary Meeting Scheduled'])
        client_id = st.selectbox("Select Client ID", ["Please select"] +  list(df[df['Status'] == 'Preliminary Meeting Scheduled']['Lead_Project_ID']))
        # client_id = st.sidebar.text_input("Enter Client ID", "")
        if client_id!="Please select":
            client_id=int(client_id)
            client_details(client_id)
            # Upload documents
            st.subheader("Upload Documents")
            upload_document(client_id)
        # Select a client
        # log_action(client_id, "Old_Leads from Anantya", "Admin Uploads 5 Documents consolidated","Document Upload", "Pending", "Uploaded")
    elif page=="Upload PI and Survey sheet":
        # Display all clients
        st.subheader("Pending Document Clients")
        selected_columns=['Lead_Project_ID', 'Lead_Name', 'WhatsApp_Number', 'Email', 'Address', 'Status', 'Last_Contact']
        df_selected = df[selected_columns]
        st.dataframe(df_selected[df_selected['Status'] == 'Final Meeting Scheduled'])
        client_id = st.selectbox("Select Client ID", ["Please select"] +  list(df[df_selected['Status'] == 'Final Meeting Scheduled']['Lead_Project_ID']))
        # client_id = st.sidebar.text_input("Enter Client ID", "")
        if client_id!="Please select":
            client_id=int(client_id)
            client_details(client_id)
            # Upload documents
            st.subheader("Upload Documents")
            upload_PI(client_id)
