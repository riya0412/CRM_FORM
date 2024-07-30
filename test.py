import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import mysql.connector
from mysql.connector import Error
import re

def load_logs():
    try:
        # Replace with your database connection details
        connection = mysql.connector.connect(
            host="srv1021.hstgr.io",
            user="u627331871_Crmfile",
            password="Crmfile@1234",
            database="u627331871_Crmfile"
        )

        if connection.is_connected():
            query = "SELECT * FROM Logs"
            df = pd.read_sql(query, connection)
            return df

    except Error as e:
        st.error(f"Error: {e}")
    finally:
        if connection.is_connected():
            connection.close()

# Initialize MySQL connection
def get_db_connection():
    return mysql.connector.connect(
        host="srv1021.hstgr.io",
        user="u627331871_Crmfile",
        password="Crmfile@1234",
        database="u627331871_Crmfile"
    )

# Load data from MySQL
def load_data():
    conn = get_db_connection()
    query = "SELECT * FROM Leads"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

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

def preprocess_column_name(name):
    # Remove any extra characters like '?' and trim whitespace
    return re.sub(r'[^\w\s]', '', name).strip().lower()

def find_matching_value(stage, leads_data):
    # Preprocess the stage name
    cleaned_stage = preprocess_column_name(stage)
    
    for _, row in leads_data.iterrows():
        # Preprocess the column name from leads data
        cleaned_column_name = preprocess_column_name(row['Column_Name'])
        # Check if the cleaned stage name is a substring of the cleaned column name
        if cleaned_stage in cleaned_column_name:
            return row['New_Value']
    return "No value found"

# Function to plot client flow
def plot_client_flow(df, client_id):
    # Filter data for the given client
    pipeline_data = df[(df['Primary_Key'] == client_id) & (df['Sheet_Name'] == 'Pipeline') & (df['Column_Name'] != 'Status')]
    leads_data = df[(df['Primary_Key'] == client_id) & (df['Sheet_Name'] == 'Leads from Anantya') & (df['Column_Name'] != 'Status')]

    stages = []
    values = []
    timestamps = []
    action=[]

    for _, row in pipeline_data.iterrows():
        stage = row['Column_Name']
        stages.append(stage)
        timestamps.append(row['Timestamp'])
        action.append(row["Action"])

        # Find the corresponding value from leads_data
        value = find_matching_value(stage, leads_data)
        values.append(value)

    if not stages:
        st.warning(f"No stages found for Client ID: {client_id}")
        return

    fig = go.Figure()
    y_positions = list(range(len(stages), 0, -1))

    for i in range(len(stages)):
        fig.add_trace(go.Scatter(
            x=[0],
            y=[y_positions[i]],
            text=f"{stages[i]}<br>Value: {values[i]}<br>{timestamps[i]}<br>{action[i]}",
            mode='markers+text',
            textposition="middle right",
            marker=dict(size=15, color='blue')  # Reduced marker size
        ))

        if i > 0:
            fig.add_shape(
                type="line",
                x0=0, y0=y_positions[i-1],
                x1=0, y1=y_positions[i],
                line=dict(color="RoyalBlue", width=2)
            )

    dynamic_height = max(len(stages) * 80, 400)  # Adjust the multiplier as needed

    fig.update_layout(
        title=f"Client Flow for Client ID: {client_id}",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        showlegend=False,
        height=dynamic_height,
        width=300,  # Set a fixed width for the graph
        margin=dict(l=5, r=5, t=30, b=5)
    )
    return fig

    

def dashboard():
    st.title("Client Flow Dashboard")

    logs_df = load_logs()
    df = load_data()
    if df is not None:
        st.subheader("All Clients")
        df_selected = df[['Lead_Project_ID', 'Lead_Name', 'WhatsApp_Number', 'Email', 'Address', 'Status', 'Last_Contact']]
        st.dataframe(df_selected)
        client_id = st.selectbox("Select Client ID", ["Please select"] + list(df['Lead_Project_ID']))

        if client_id:
            client_details(client_id)
            # Left column: Client flow diagram
            st.header("Client Flow")
            # Create a centered container for the graph
            center_container = st.container()
            with center_container:
                st.markdown(
                    """
                    <style>
                    .centered {
                        display: flex;
                        justify-content: center;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
                )
                with st.container():
                    st.markdown('<div class="centered">', unsafe_allow_html=True)
                    fig = plot_client_flow(logs_df, client_id)
                    st.plotly_chart(fig, use_container_width=False)
                    st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.error("Failed to load data from the database.")
# dashboard()