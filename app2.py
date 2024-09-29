import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Google Sheets API setup
def connect_to_google_sheet(sheet_url):
    # Define the scope
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

    # Load the credentials from the environment variable
    creds_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    creds_dict = json.loads(creds_json)

    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    # Open the Google Sheet by URL
    sheet = client.open_by_url(sheet_url)
    return sheet

# Function to extract data from the sheet for a specific month
def get_monthly_data(sheet, month):
    worksheet = sheet.worksheet(month)
    data = worksheet.get_all_values()

    # Convert to a pandas DataFrame for easier manipulation
    df = pd.DataFrame(data)
    return df

# Function to get the names of worksheets in the Google Sheet
def get_worksheet_names(sheet):
    return [worksheet.title for worksheet in sheet.worksheets()]


# Function to filter data for a specific day and date and format it
def filter_and_format_data(df, day, date):
    # Find the row for the specified day and date
    day_date_row = df[(df[0] == day) & (df[1] == date)]
    
    if day_date_row.empty:
        print("Date not found in the sheet.")
        return

    # Extract staff information for all teams
    staff_info = {
        "SCBU Team": {
            "Consultant": day_date_row.iloc[0, df.iloc[2].str.contains("Neo").idxmax()],  
            "SpR": day_date_row.iloc[0, df.iloc[1].str.contains("SCBU").idxmax()],      
            "SHO": day_date_row.iloc[0, df.iloc[1].str.contains("SCBU").idxmax() + 9], 
            "PN": day_date_row.iloc[0, df.iloc[1].str.contains("Post Nat").idxmax()],   
            "LW": day_date_row.iloc[0, df.iloc[1].str.contains("Labour Ward").idxmax()], 
        },
        "PAT Team": {
            "Consultant": day_date_row.iloc[0, df.iloc[2].str.contains("Acute").idxmax()],  
            "SpR": day_date_row.iloc[0, df.iloc[1].str.contains("PAT").idxmax()],          
            "SHO": day_date_row.iloc[0, df.iloc[1].str.contains("PAT").idxmax() + 11],     
            "Consultant (Mon - Fri 17:00-21:30/Sat - Sun: 13:30 - 21:30)": day_date_row.iloc[0, df.iloc[2].str.contains("mon - fri 1700-2130 sat -sun 13:30 -21:30").idxmax()]  
        },
        "Twilight Team": {
            "SHO": day_date_row.iloc[0, df.iloc[1].str.contains("Twilight").idxmax()]
        },
        "Registrar (from 5pm) in ED": {
            "Registrar": day_date_row.iloc[0, df.iloc[1].str.contains("Comm Evening|PAT Eve", regex=True).idxmax()]
        },
        "Starlight Team": {
            "Consultant": day_date_row.iloc[0, df.iloc[2].str.contains("Ward").idxmax()],  
            "SpR": day_date_row.iloc[0, df.iloc[1].str.contains("Ward").idxmax()],          
            "SHO": day_date_row.iloc[0, df.iloc[1].str.contains("Ward").idxmax() + 11],     
        },
        "Sunshine Day Unit": {
            "SHO": day_date_row.iloc[0, df.iloc[1].str.contains("Sunshine").idxmax()]
        },
        "Clinic": {
            "SpR": day_date_row.iloc[0, df.iloc[1].str.contains("Clinic").idxmax()],          
            "SHO": day_date_row.iloc[0, df.iloc[1].str.contains("Clinic").idxmax() + 12],     
        },
        "SPA": {
            "SpR": day_date_row.iloc[0, df.iloc[1].str.contains("SPA/Emergency cover").idxmax()],          
            "SHO": day_date_row.iloc[0, df.iloc[1].str.contains("SPA/Emergency cover").idxmax() + 12],     
        },
        "Long Day (17:00 - 21:30)": {
            "SpR": day_date_row.iloc[0, df.iloc[1].str.contains("Long Day PM|Long day PM|Ward Eve", regex=True).idxmax()],          
            "SHO": day_date_row.iloc[0, df.iloc[1].str.contains("SHO Eve x2).idxmax()],     
        },
        "Overnight Consultant": {
            "Consultant": day_date_row.iloc[0, df.iloc[2].str.contains("Off site On call 1700-0830").idxmax()]
        },
        "Night Team": {
            "SpR (315)": day_date_row.iloc[0, df.iloc[2].str.contains("Starlight Ward/HDU").idxmax()],      
            "SpR (355)": day_date_row.iloc[0, df.iloc[2].str.contains("1st ED/PSSU").idxmax()], 
            "SpR (223)": day_date_row.iloc[0, df.iloc[2].str.contains("2nd ED & Neo Blp").idxmax()],   
            "SHO (345)": day_date_row.iloc[0, df.iloc[2].str.contains("21:00 - 09:30 (S)", regex=False).idxmax()],
            "SHO (677)": day_date_row.iloc[0, df.iloc[2].str.contains("21:00 - 09:30 (E)", regex=False).idxmax()],
        },
    }

    # Format the staff information for each team for display
    formatted_data = ""

    # SCBU Team
    formatted_data += "SCBU Team\n"
    for role, staff in staff_info["SCBU Team"].items():
        formatted_data += f"  {role}: {staff if staff else 'Not assigned'}\n"

    # PAT Team
    formatted_data += "\nPAT Team\n"
    for role, staff in staff_info["PAT Team"].items():
        formatted_data += f"  {role}: {staff if staff else 'Not assigned'}\n"

    # Twilight Team
    formatted_data += "\nTwilight Team (13:30 - 21:30)\n"
    for role, staff in staff_info["Twilight Team"].items():
        formatted_data += f"  {role}: {staff if staff else 'Not assigned'}\n"

    # Registrar (from 5pm) in ED
    formatted_data += "\nRegistrar (17:00 - 21:30) in ED\n"
    for role, staff in staff_info["Registrar (from 5pm) in ED"].items():
        formatted_data += f"  {role}: {staff if staff else 'Not assigned'}\n"

    # Starlight Team
    formatted_data += "\nStarlight Team\n"
    for role, staff in staff_info["Starlight Team"].items():
        formatted_data += f"  {role}: {staff if staff else 'Not assigned'}\n"

    # Sunshine Day Unit
    formatted_data += "\nSunshine Day Unit\n"
    for role, staff in staff_info["Sunshine Day Unit"].items():
        formatted_data += f"  {role}: {staff if staff else 'Not assigned'}\n"

    # Clinic
    formatted_data += "\nClinic\n"
    for role, staff in staff_info["Clinic"].items():
        formatted_data += f"  {role}: {staff if staff else 'Not assigned'}\n"

    # SPA
    formatted_data += "\nSPA\n"
    for role, staff in staff_info["SPA"].items():
        formatted_data += f"  {role}: {staff if staff else 'Not assigned'}\n"

    # Long Day (17:00 - 21:30)
    formatted_data += "\nLong Day (17:00 - 21:30)\n"
    for role, staff in staff_info["Long Day (17:00 - 21:30)"].items():
        formatted_data += f"  {role}: {staff if staff else 'Not assigned'}\n"

    # Overnight Consultant
    formatted_data += "\nOvernight Consultant\n"
    for role, staff in staff_info["Overnight Consultant"].items():
        formatted_data += f"  {role}: {staff if staff else 'Not assigned'}\n"

    # Night Team
    formatted_data += "\nNight Team\n"
    for role, staff in staff_info["Night Team"].items():
        formatted_data += f"  {role}: {staff if staff else 'Not assigned'}\n"

    return formatted_data



# Streamlit app
st.title("Staff Rota Viewer")

# Store the URL in a variable without displaying it
sheet_url = "https://docs.google.com/spreadsheets/d/19VnKEQ7Gle0fjHMPPgc2Eujew2BNRht7zpAWrO__yX4/edit?gid=15103853"

if sheet_url:
    sheet = connect_to_google_sheet(sheet_url)
    worksheet_names = get_worksheet_names(sheet)
    month = st.selectbox("Select Month", worksheet_names)

day = st.selectbox("Select Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
date = st.selectbox("Select Date", [f"{i}{'th' if 11 <= i <= 13 else 'st' if i % 10 == 1 else 'nd' if i % 10 == 2 else 'rd' if i % 10 == 3 else 'th'}" for i in range(1, 32)])



if st.button("Get Rota"):
    sheet = connect_to_google_sheet(sheet_url)
    df = get_monthly_data(sheet, month)
    formatted_data = filter_and_format_data(df, day, date)
    
    st.subheader(f"Staff Rota for {day} {date}")
    # Use st.text() or st.markdown() to display the formatted data

    
    st.markdown(formatted_data.replace('\n', '<br>'), unsafe_allow_html=True)

