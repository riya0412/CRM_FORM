import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
from datetime import datetime
import tempfile
if 'document_to_delete' not in st.session_state:
    st.session_state.document_to_delete = None
if 'delete_confirmed' not in st.session_state:
    st.session_state.delete_confirmed = False
# from streamlit_modal import Modal
# modal = Modal("Warning", )
# Set up Google Sheets API
credentials = Credentials.from_service_account_info(st.secrets["google_service_account"], scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    # creds = Credentials.from_service_account_info(service_account_info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
client = gspread.authorize(credentials)

# Set up Google Drive API
drive_service = build('drive', 'v3', credentials=credentials)

def load_data():
    workbook = client.open_by_key("1pcmMrkUfhvUn3QvyZ2L0IXDOV4C16SAKNdr85xy2gps")
    leads_sheet = workbook.worksheet('Leads from Anantya')   # Assuming the first sheet contains the leads
    data = leads_sheet.get_all_records()
    return pd.DataFrame(data)



def update_pipeline(lead_id, column_name, value):
    workbook = client.open_by_key("1pcmMrkUfhvUn3QvyZ2L0IXDOV4C16SAKNdr85xy2gps")
    pipeline_sheet = workbook.worksheet('Pipeline')
    lead_id=str(lead_id)
    pipeline_row = pipeline_sheet.find(lead_id).row
    column_index = pipeline_sheet.row_values(1).index(column_name) + 1
    old_value = pipeline_sheet.cell(pipeline_row, column_index).value
    pipeline_sheet.update_cell(pipeline_row, column_index, value)

def log_action(lead_project_id, sheet_name, column_name, action, old_value, new_value):
    workbook = client.open_by_key("1pcmMrkUfhvUn3QvyZ2L0IXDOV4C16SAKNdr85xy2gps")
    logs_sheet = workbook.worksheet('Logs')  # Logs sheet
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logs_sheet.append_row([lead_project_id, timestamp, sheet_name, column_name, action, old_value, new_value])

def update_lead_status(lead_id, new_status):
    lead_id=str(lead_id)
    workbook = client.open_by_key("1pcmMrkUfhvUn3QvyZ2L0IXDOV4C16SAKNdr85xy2gps")
    leads_sheet = workbook.worksheet('Leads from Anantya')
    lead_row = leads_sheet.find(lead_id).row
    old_status = leads_sheet.cell(lead_row, 6).value
    leads_sheet.update_cell(lead_row, 6, new_status)
    leads_sheet.update_cell(lead_row, 7, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    # Log the change
    log_action(lead_id, 'Leads from Anantya', 'Status',"Update", old_status, new_status)

def upload_to_drive(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(uploaded_file.getbuffer())
        temp_file_path = temp_file.name

    file_metadata = {'name': uploaded_file.name}
    media = MediaFileUpload(temp_file_path, mimetype=uploaded_file.type)
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    file_id = file.get('id')
    file_link = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
    return file_link

def update_document_link(client_id, column_name, file_link):
    df = load_data()
    workbook = client.open_by_key("1pcmMrkUfhvUn3QvyZ2L0IXDOV4C16SAKNdr85xy2gps")
    leads_sheet = workbook.worksheet('Leads from Anantya')
    pipeline_sheet = workbook.worksheet('Pipeline')
    
    row_index = df[df['Lead Project ID'] == client_id].index[0] + 2  # Adjust for 0-indexing and header row
    leads_sheet.update_cell(row_index, df.columns.get_loc(column_name) + 1, file_link)
    log_action(client_id, "Leads from Anantya", column_name, "Document Upload", "Pending", "Uploaded")
    update_pipeline(client_id,column_name,"TRUE")
    log_action(client_id, "Pipeline", column_name, "Document Uploaded", "0", "TRUE")
    update_lead_status(client_id,column_name)
    # pipeline_sheet.update_cell(row_index, df.columns.get_loc(column_name) + 1, "TRUE")
    

def upload_documents(column_name):
    uploaded_files = st.file_uploader("Upload Documents", accept_multiple_files=True, key='file_uploader')
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []

    if uploaded_files:
        st.session_state.uploaded_files.extend(uploaded_files)

    if st.button("Upload"):
        for uploaded_file in st.session_state.uploaded_files:
            file_link = upload_to_drive(uploaded_file)
            st.success(f"Document uploaded successfully: {file_link}")
            update_document_link(st.session_state.selected_client_id, column_name, file_link)
        st.session_state.uploaded_files = []  # Clear uploaded files after upload


def handle_upload_quotation(df):
    st.subheader("Pending Document Clients")
    df_selected = df[['Lead Project ID', 'Lead Name', 'WhatsApp Number', 'Email', 'Address', 'Status', "Last Contact"]]
    pending_df = df_selected[(df_selected['Status'] == 'Document uploaded by Technician') | (df_selected['Status'] == 'Document Upload by Client')]
    st.dataframe(pending_df)

    client_id = st.selectbox("Select Client ID", ["Please select"] + list(pending_df['Lead Project ID']))

    if client_id != "Please select":
        st.session_state.selected_client_id = int(client_id)
        # if st.button("Submit"):
        client_details(st.session_state.selected_client_id)
        st.subheader("Upload Documents")
        upload_documents("Admin Uploads 5 Documents consolidated")

def handle_schedule_call(df):
    st.subheader("All Clients")
    df_selected = df[['Lead Project ID', 'Lead Name', 'WhatsApp Number', 'Email', 'Address', 'Status', "Last Contact"]]
    st.dataframe(df_selected)

    client_id = st.selectbox("Select Client ID", ["Please select"] + list(df['Lead Project ID']))

    if client_id != "Please select":
        st.session_state.selected_client_id = int(client_id)
        if st.button("Select"):
            client_details(st.session_state.selected_client_id)

def handle_upload_pi_survey_sheet(df):
    st.subheader("Pending Document Clients")
    df_selected = df[['Lead Project ID', 'Lead Name', 'WhatsApp Number', 'Email', 'Address', 'Status', "Last Contact"]]
    pending_df = df_selected[df_selected['Status'] == 'Final Meeting Scheduled']
    st.dataframe(pending_df)

    client_id = st.selectbox("Select Client ID", ["Please select"] + list(pending_df['Lead Project ID']))

    if client_id != "Please select":
        st.session_state.selected_client_id = int(client_id)
        if st.button("Select"):
            client_details(st.session_state.selected_client_id)
            st.subheader("Upload Documents")
            upload_documents("PI and Survey Sheet Documents uploaded by Technician")

def handle_upload_survey_feedback(df):
    st.subheader("Pending Document Clients")
    df_selected = df[['Lead Project ID', 'Lead Name', 'WhatsApp Number', 'Email', 'Address', 'Status', "Last Contact"]]
    pending_df = df_selected[df_selected['Status'] == 'Order Delivered and Installation']
    st.dataframe(pending_df)

    client_id = st.selectbox("Select Client ID", ["Please select"] + list(pending_df['Lead Project ID']))

    if client_id != "Please select":
        st.session_state.selected_client_id = int(client_id)
        if st.button("Select"):
            client_details(st.session_state.selected_client_id)
            st.subheader("Upload Documents")
            upload_documents("Survey Feedback")

def delete_document(doc_name, client_id):
    df = load_data()
    workbook = client.open_by_key("1pcmMrkUfhvUn3QvyZ2L0IXDOV4C16SAKNdr85xy2gps")
    leads_sheet = workbook.worksheet('Leads from Anantya')
    pipeline_sheet = workbook.worksheet('Pipeline')
    row_index = df[df['Lead Project ID'] == client_id].index[0] + 2  # Adjust for 0-indexing and header row

    if doc_name == "Document uploaded by Technician":
        update_pipeline(client_id, "Document uploaded by Technician?", "0")
        log_action(client_id, "Pipeline", "Document uploaded by Technician?", "Document Delete", "TRUE", "0")
        leads_sheet.update_cell(row_index, df.columns.get_loc("Document uploaded by Technician") + 1, "")
        log_action(client_id, "Leads from Anantya", "Document uploaded by Technician", "Document Delete", "", "")
    
    elif doc_name == "Document Upload by Client":
        update_pipeline(client_id, "Document Upload by Client", "0")
        log_action(client_id, "Pipeline", "Document Upload by Client", "Document Delete", "TRUE", "False")
        leads_sheet.update_cell(row_index, df.columns.get_loc("Document Upload by Client") + 1, "")
        log_action(client_id, "Leads from Anantya", "Document Upload by Client", "Document Delete", "", "")
    
    elif doc_name == "Admin Uploads 5 Documents consolidated":
        leads_sheet.update_cell(row_index, df.columns.get_loc("Admin Uploads 5 Documents consolidated") + 1, "")
        log_action(client_id, "Leads from Anantya", "Admin Uploads 5 Documents consolidated", "Document Delete", "", "")
        update_pipeline(client_id, "Admin Uploads 5 Documents consolidated", "0")
        log_action(client_id, "Pipeline", "Admin Uploads 5 Documents consolidated", "Document Delete", "TRUE", "0")
    
    elif doc_name == "PI and Survey Sheet Documents uploaded by Technician":
        leads_sheet.update_cell(row_index, df.columns.get_loc("PI and Survey Sheet Documents uploaded by Technician") + 1, "")
        log_action(client_id, "Leads from Anantya", "PI and Survey Sheet Documents uploaded by Technician", "Document Delete", "", "")
        update_pipeline(client_id, "PI and Survey Sheet Documents uploaded by Technician?", "0")
        log_action(client_id, "Pipeline", "PI and Survey Sheet Documents uploaded by Technician?", "Document Delete", "TRUE", "0")

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

def show_delete_entity_page(df):
    st.title("Delete Entity")
    selected_columns = ['Lead Project ID', 'Lead Name', 'WhatsApp Number', 'Email', 'Address', 'Status', "Last Contact"]
    df_selected = df[selected_columns]
    st.dataframe(df_selected)
    client_id = st.selectbox("Select Client ID", ["Please select"] + list(df['Lead Project ID']))
    
    if client_id != "Please select":
        client_info = df[df['Lead Project ID'] == client_id].iloc[0]
        with st.container():
            st.subheader(f"Client: {client_info['Lead Name']}")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"📱WhatsApp Number: +{client_info['WhatsApp Number']}")
                st.write(f"📱Email: {client_info['Email']}")
                st.write(f"🏠Address: {client_info['Address']}")
                st.write(f"🕑Status: {client_info['Status']}")
            with col2:
                st.write(f"🕑Follow-Up Required?: {client_info['Follow-Up Required?']}")
                st.write(f"📆Last Contact: {client_info['Last Contact']}")
                st.write(f"📆Preliminary Meeting Scheduled Date: {client_info['Preliminary Meeting Scheduled Date']}")
                st.write(f"📆Final Meeting Scheduled Date: {client_info['Final Meeting Scheduled Date']}")

        documents = [
            {"name": "Document uploaded by Technician", "link": {client_info['Document uploaded by Technician']}},
            {"name": "Document Upload by Client", "link": {client_info['Document Upload by Client']}},
            {"name": "Admin Uploads 5 Documents consolidated", "link": {client_info['Admin Uploads 5 Documents consolidated']}},
            {"name": "PI and Survey Sheet Documents uploaded by Technician", "link": {client_info['PI and Survey Sheet Documents uploaded by Technician']}}
        ]

        st.subheader("Documents")
        for doc in documents:
            col1, col2, col3 = st.columns([4, 2, 1])
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
                    st.write(f"Sending {doc['name']}")

        # Handle document deletion confirmation
        if 'delete_confirmation_shown' in st.session_state and st.session_state.delete_confirmation_shown:
            doc_name, _ = st.session_state.document_to_delete
            st.warning("Do you really, really want to delete this document?")
            if st.button("Yes, I'm ready"):
                # doc_name, client_id = st.session_state.document_to_delete
                delete_document(doc_name, client_id)
                st.success(f"Deleted {doc_name}")
                st.session_state.delete_confirmation_shown = False
                st.session_state.document_to_delete = None
                st.experimental_rerun()  # Optional: Rerun to refresh the state
            if st.button("Cancel"):
                st.session_state.delete_confirmation_shown = False
                st.session_state.document_to_delete = None


    if st.button("Back to Admin Page"):
        st.session_state.delete_entity_active = False
        st.rerun()

def show_regular_admin_page(df):
    page = st.sidebar.selectbox("Admin Task", ["Upload Quotation", "Schedule Call", "Upload PI and Survey sheet", "Upload Survey Feedback"])
    
    if page == "Upload Quotation":
        handle_upload_quotation(df)
    elif page == "Schedule Call":
        handle_schedule_call(df)
    elif page == "Upload PI and Survey sheet":
        handle_upload_pi_survey_sheet(df)
    elif page == "Upload Survey Feedback":
        handle_upload_survey_feedback(df)

def admin_page():
    st.header("Admin Page")
    df = load_data()

    # Create a state variable for the Delete Entity button
    if 'delete_entity_active' not in st.session_state:
        st.session_state.delete_entity_active = False

    # Delete Entity button in sidebar
    if st.sidebar.button("Delete Entity"):
        st.session_state.delete_entity_active = True

    # Check if Delete Entity is active
    if st.session_state.delete_entity_active:
        show_delete_entity_page(df)
    else:
        show_regular_admin_page(df)
    
                    
