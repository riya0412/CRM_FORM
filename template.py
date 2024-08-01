import mysql.connector
import requests
import streamlit as st
# from apscheduler.schedulers.background import BackgroundScheduler
# from apscheduler.triggers.interval import IntervalTrigger
# import atexit

# Global variables
# scheduler = BackgroundScheduler()
# current_interval = 24 

# Database connection
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

# Fetch templates from API
def fetch_templates():
    api=st.secrets["API"]
    API_URL = api["TEMP_URL"]
    API_KEY = api["API_KEY"]
    headers = {
    'accept': '*/*',
    'X-Api-Key': API_KEY
    }
    response = requests.get(API_URL, headers=headers)
    if response.status_code == 200:
        templates = response.json().get('dataObj', [])
        update_database(templates)
    else:
        print(f"Failed to fetch templates: {response.status_code}")

# Update the database with new or modified templates
def update_database(templates):
    connection = get_db_connection()
    with connection.cursor() as cursor:
        for template in templates:
            cursor.execute("""
                INSERT INTO templates (id, templateName, mediaType, msgText, mediaFileName, templateStatus, isActive)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    templateName=VALUES(templateName),
                    mediaType=VALUES(mediaType),
                    msgText=VALUES(msgText),
                    mediaFileName=VALUES(mediaFileName),
                    templateStatus=VALUES(templateStatus),
                    isActive=VALUES(isActive),
                    lastUpdated=CURRENT_TIMESTAMP;
            """, (
                template['id'],
                template['templateName'],
                template['mediaType'],
                template['msgText'],
                template.get('mediaFileName'),
                template['templateStatus'],
                template['isActive']
            ))
        connection.commit()

# # Call this function to fetch and update templates
# fetch_templates()



# Close the connection when done

