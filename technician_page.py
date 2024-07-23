import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
from datetime import datetime
import tempfile

# Set up Google Sheets API
credentials = Credentials.from_service_account_info(st.secrets["google_service_account"], scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    # creds = Credentials.from_service_account_info(service_account_info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
client = gspread.authorize(credentials)

# Set up Google Drive API
drive_service = build('drive', 'v3', credentials=credentials)

def load_data():
    workbook = client.open_by_key("1pcmMrkUfhvUn3QvyZ2L0IXDOV4C16SAKNdr85xy2gps")
    leads_sheet = workbook.worksheet('Leads from Anantya') # Assuming the first sheet contains the leads
    data = leads_sheet.get_all_records()
    return pd.DataFrame(data)

def log_action(lead_project_id, sheet_name, column_name, action, old_value, new_value):
    workbook = client.open_by_key("1pcmMrkUfhvUn3QvyZ2L0IXDOV4C16SAKNdr85xy2gps")
    logs_sheet = workbook.worksheet('Logs') # Logs sheet
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logs_sheet.append_row([lead_project_id, timestamp, sheet_name, column_name, action, old_value, new_value])

def upload_to_drive(uploaded_file):
    # Save the uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(uploaded_file.getbuffer())
        temp_file_path = temp_file.name

    file_metadata = {'name': uploaded_file.name}
    media = MediaFileUpload(temp_file_path, mimetype=uploaded_file.type)
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    file_id = file.get('id')
    file_link = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
    return file_link

def upload_5document(client_id):
    df = load_data()
    uploaded_files = st.file_uploader("Upload Documents", accept_multiple_files=True)
    if st.button("Upload"):
        if uploaded_files:
            for uploaded_file in uploaded_files:
                file_link = upload_to_drive(uploaded_file)
                st.success(f"Document uploaded successfully: {file_link}")
                # Update the status in your database
                workbook = client.open_by_key("1pcmMrkUfhvUn3QvyZ2L0IXDOV4C16SAKNdr85xy2gps")
                leads_sheet = workbook.worksheet('Leads from Anantya')
                pipeline_sheet = workbook.worksheet('Pipeline')
                row_index = df[df['Lead Project ID'] == client_id].index[0] + 2  # Adjust for 0-indexing and header row
                leads_sheet.update_cell(row_index, df.columns.get_loc('Admin Uploads 5 Documents consolidated') + 1, file_link)
                log_action(client_id,"Leads from Anantya", "Admin Uploads 5 Documents consolidated","Document Upload", "Pending", "Uploaded")
                pipeline_sheet.update_cell(row_index,df.columns.get_loc('Admin Uploads 5 Documents consolidated') + 1,"TRUE")
                log_action(client_id, "Pipeline", "Admin Uploads 5 Documents consolidated","Document Uploaded", "0", "TRUE")

def upload_PI(client_id):
    df = load_data()
    uploaded_files = st.file_uploader("Upload Documents", accept_multiple_files=True)
    if st.button("Upload"):
        if uploaded_files:
            for uploaded_file in uploaded_files:
                file_link = upload_to_drive(uploaded_file)
                st.success(f"Document uploaded successfully: {file_link}")
                # Update the status in your database
                workbook = client.open_by_key("1pcmMrkUfhvUn3QvyZ2L0IXDOV4C16SAKNdr85xy2gps")
                leads_sheet = workbook.worksheet('Leads from Anantya')
                pipeline_sheet = workbook.worksheet('Pipeline')
                row_index = df[df['Lead Project ID'] == client_id].index[0] + 2  # Adjust for 0-indexing and header row
                leads_sheet.update_cell(row_index, df.columns.get_loc("PI and Survey Sheet Documents uploaded by Technician") + 1, file_link)
                log_action(client_id,"Leads from Anantya", "PI and Survey Sheet Documents uploaded by Technician","Document Upload", "Pending", "Uploaded")
                pipeline_sheet.update_cell(row_index,df.columns.get_loc('PI and Survey Sheet Documents uploaded by Technician?') + 1,"TRUE")
                log_action(client_id, "Pipeline", "PI and Survey Sheet Documents uploaded by Technician?","Document Uploaded", "0", "TRUE")

def client_details(client_id):
    st.title(f"Client Details")

    # Load the data
    df = load_data()
    client_info = df[df['Lead Project ID'] == client_id].iloc[0]
    with st.container():

        st.subheader(f"Client: {client_info['Lead Name']}")
        col1,col2=st.columns(2)

        with col1:
            st.write(f"📱WhatsApp Number: +{client_info['WhatsApp Number']}")
            st.write(f"📱Email: {client_info['Email']}")
            st.write(f"🏠Address: {client_info['Address']}")
            st.write(f"🕑Status: {client_info['Status']}")
            st.write(f"🕑Follow-Up Required?: {client_info['Follow-Up Required?']}")
            st.write(f"📆Last Contact: {client_info['Last Contact']}")
            st.write(f"📆Preliminary Meeting Scheduled Date: {client_info['Preliminary Meeting Scheduled Date']}")
        with col2:
            st.write(f"📝Document uploaded by Technician: {client_info['Document uploaded by Technician']}")
            st.write(f"📝Document Upload by Client: {client_info['Document Upload by Client']}")
            st.write(f"📝Admin Uploads 5 Documents consolidated: {client_info['Admin Uploads 5 Documents consolidated']}")
            st.write(f"📆Final Meeting Scheduled Date: {client_info['Final Meeting Scheduled Date']}")
            st.write(f"📝PI and Survey Sheet Documents uploaded by Technician: {client_info['PI and Survey Sheet Documents uploaded by Technician']}")

def technician_page():
    st.header("Technician Page")

    # Load the data
    df = load_data()
    page=st.sidebar.selectbox("Technician Task",["Upload Dimension","Upload PI and Survey sheet"])
    if page=="Upload Dimension":
        # Display all clients
        st.subheader("Pending Document Clients")
        selected_columns=['Lead Project ID', 'Lead Name', 'WhatsApp Number', 'Email', 'Address', 'Status',"Last Contact"]
        df_selected = df[selected_columns]
        st.dataframe(df_selected[df_selected['Status'] == 'Preliminary Meeting Scheduled'])
        client_id = st.selectbox("Select Client ID", ["Please select"] +  list(df[df['Status'] == 'Preliminary Meeting Scheduled']['Lead Project ID']))
        # client_id = st.sidebar.text_input("Enter Client ID", "")
        if client_id!="Please select":
            client_id=int(client_id)
            client_details(client_id)
            # Upload documents
            st.subheader("Upload Documents")
            upload_5document(client_id)
        # Select a client
        # log_action(client_id, "Leads from Anantya", "Admin Uploads 5 Documents consolidated","Document Upload", "Pending", "Uploaded")
    elif page=="Upload PI and Survey sheet":
        # Display all clients
        st.subheader("Pending Document Clients")
        selected_columns=['Lead Project ID', 'Lead Name', 'WhatsApp Number', 'Email', 'Address', 'Status',"Last Contact"]
        df_selected = df[selected_columns]
        st.dataframe(df_selected[df_selected['Status'] == 'Final Meeting Scheduled'])
        client_id = st.selectbox("Select Client ID", ["Please select"] +  list(df[df_selected['Status'] == 'Final Meeting Scheduled']['Lead Project ID']))
        # client_id = st.sidebar.text_input("Enter Client ID", "")
        if client_id!="Please select":
            client_id=int(client_id)
            client_details(client_id)
            # Upload documents
            st.subheader("Upload Documents")
            upload_PI(client_id)
