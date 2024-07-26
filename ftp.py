import ftplib
import streamlit as st
import base64
import pandas as pd
from urllib.parse import unquote
import os

def download_file_from_ftp(file_path):
    creds=st.secrets["ftp"]
    ftp_host = creds["host"]
    ftp_user = creds["user"]
    ftp_password = creds["password"]
    local_file_path = file_path.split('/')[-1]  # Save locally with the same filename

    with ftplib.FTP(ftp_host) as ftp:
        ftp.login(ftp_user, ftp_password)
        st.write(f"Logged in to FTP server: {ftp_host}")

        with open(local_file_path, 'wb') as local_file:
            ftp.retrbinary(f'RETR {file_path}', local_file.write)
            st.write(f"Downloaded file to {local_file_path}")

    return local_file_path

def display_pdf(file_path):
    with open(file_path, 'rb') as pdf_file:
        pdf_bytes = pdf_file.read()
        st.download_button(label="Download PDF", data=pdf_bytes, file_name="downloaded_file.pdf", mime="application/pdf")
        
        # Embed PDF in Streamlit using an iframe
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{pdf_base64}" width="700" height="1000" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)

# Main Streamlit app
st.title("FTP File Viewer")

query_params = st.experimental_get_query_params()
if "file_path" in query_params:
    file_path = unquote(query_params["file_path"][0])
    local_file_path = download_file_from_ftp(file_path)

    if local_file_path:
        st.header("PDF Document")
        display_pdf(local_file_path)
        os.remove(local_file_path)
else:
    st.write("No file path provided.")
