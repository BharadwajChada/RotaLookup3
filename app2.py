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

    # Find the first and second occurrences of "Ward" separately
    ward_occurrences = df.iloc[1].str.contains(r"^(Ward|Starlight)\s*$", regex=True)
    ward_indexes = ward_occurrences[ward_occurrences].index  # Get all indexes of "Ward"

    if len(ward_indexes) >= 2:
        ward_registrar_index = ward_indexes[0]  # First occurrence for Registrar
        ward_sho_index = ward_indexes[1]  # Second occurrence for SHO
    else:
        ward_registrar_index = ward_indexes[0] if len(ward_indexes) > 0 else None
        ward_sho_index = None

    # Find the first and second occurrences of "PAT" separately
    pat_occurrences = df.iloc[1].str.contains(r"^(PAT|PAT/PSSU)\s*$", regex=True)
    pat_indexes = pat_occurrences[pat_occurrences].index  # Get all indexes of "PAT"

    if len(pat_indexes) >= 2:
        pat_registrar_index = pat_indexes[0]  # First occurrence for Registrar
        pat_sho_index = pat_indexes[1]  # Second occurrence for SHO
    else:
        pat_registrar_index = pat_indexes[0] if len(pat_indexes) > 0 else None
        pat_sho_index = None

    # Find the first and second occurrences of "SCBU" separately
    scbu_occurrences = df.iloc[1].str.contains(r"^SCBU\s*$", regex=True)
    scbu_indexes = scbu_occurrences[scbu_occurrences].index  # Get all indexes of "SCBU"

    if len(scbu_indexes) >= 2:
        scbu_registrar_index = scbu_indexes[0]  # First occurrence for Registrar
        scbu_sho_index = scbu_indexes[1]  # Second occurrence for SHO
    else:
        scbu_registrar_index = scbu_indexes[0] if len(scbu_indexes) > 0 else None
        scbu_sho_index = None

    # Check for occurrences of "Clinic" in the first and second rows separately
    clinic_occurrences_first_row = df.iloc[0].str.contains(r"^Clinic$", regex=True)
    clinic_occurrences_second_row = df.iloc[1].str.contains(r"^Clinic$", regex=True)

    # Get all indexes of "Clinic" in both rows
    clinic_indexes_first_row = clinic_occurrences_first_row[clinic_occurrences_first_row].index.tolist()
    clinic_indexes_second_row = clinic_occurrences_second_row[clinic_occurrences_second_row].index.tolist()

    # Initialize indexes for Registrar and SHO
    clinic_registrar_index = None
    clinic_sho_index = None

    # Determine the appropriate indexes based on where "Clinic" appears
    if clinic_indexes_first_row:
        # If "Clinic" appears in the first row, assign the first occurrence to Registrar
        clinic_registrar_index = clinic_indexes_first_row[0]
        # Check if there is a "Clinic" occurrence in the second row for SHO
        clinic_sho_index = clinic_indexes_second_row[0] if clinic_indexes_second_row else None
    elif clinic_indexes_second_row:
        # If "Clinic" only appears in the second row, assign the first and second occurrences there
        clinic_registrar_index = clinic_indexes_second_row[0]
        clinic_sho_index = clinic_indexes_second_row[1] if len(clinic_indexes_second_row) > 1 else None


   # Define the search pattern to account for both "SPA/Emergency cover" and "SPA/Emergency"
    pattern = r"^SPA/Emergency( cover)?$"

    # Check for occurrences in both the first and second rows
    spa_occurrences_first_row = df.iloc[0].str.contains(pattern, regex=True)
    spa_occurrences_second_row = df.iloc[1].str.contains(pattern, regex=True)

    # Get all indexes of "SPA/Emergency" in both rows
    spa_indexes_first_row = spa_occurrences_first_row[spa_occurrences_first_row].index.tolist()
    spa_indexes_second_row = spa_occurrences_second_row[spa_occurrences_second_row].index.tolist()

    # Initialize indexes for Registrar and SHO
    spa_registrar_index = None
    spa_sho_index = None

    # Determine the appropriate indexes based on where "SPA/Emergency" appears
    if spa_indexes_first_row:
        # If "SPA/Emergency" appears in the first row, assign the first occurrence to Registrar
        spa_registrar_index = spa_indexes_first_row[0]
        # Check if there is a "SPA/Emergency" occurrence in the second row for SHO
        spa_sho_index = spa_indexes_second_row[0] if spa_indexes_second_row else None
    elif spa_indexes_second_row:
        # If "SPA/Emergency" only appears in the second row, assign the first and second occurrences there
        spa_registrar_index = spa_indexes_second_row[0]
        spa_sho_index = spa_indexes_second_row[1] if len(spa_indexes_second_row) > 1 else None



    # Extract staff information for all teams
    staff_info = {
        "SCBU Team": {
            "Consultant": day_date_row.iloc[0, df.iloc[2].str.contains("Neo").idxmax()],  
            "SpR": day_date_row.iloc[0, scbu_registrar_index] if scbu_registrar_index else "Not assigned", 
            "SHO":   day_date_row.iloc[0, scbu_sho_index] if scbu_sho_index else "Not assigned", 
            "PN": day_date_row.iloc[0, df.iloc[1].str.contains("Post Nat").idxmax()],   
            "LW": day_date_row.iloc[0, df.iloc[1].str.contains("Labour Ward").idxmax()], 
        },
        "PAT Team": {
            "Consultant": day_date_row.iloc[0, df.iloc[2].str.contains("Acute").idxmax()],  
            "SpR": day_date_row.iloc[0, pat_registrar_index] if pat_registrar_index else "Not assigned", 
            "SHO":   day_date_row.iloc[0, pat_sho_index] if pat_sho_index else "Not assigned",     
            "Consultant (Mon - Fri 17:00-21:30/Sat - Sun: 13:30 - 21:30)": day_date_row.iloc[0, df.iloc[2].str.contains("mon - fri 1700-2130 sat -sun 13:30 -21:30").idxmax()]  
        },
        "Twilight Team": {
            "SHO": day_date_row.iloc[0, df.iloc[1].str.contains("Twilight").idxmax()]
        },
        "Registrar (from 5pm) in ED": {
            "Registrar": day_date_row.iloc[0, df.iloc[1].str.contains("Comm Evening|PAT Eve|Comm/ED/PAT eve", regex=True).idxmax()]
        },
        "Starlight Team": {
            "Consultant": day_date_row.iloc[0, df.iloc[2].str.contains("Ward").idxmax()],
            "SpR": day_date_row.iloc[0, ward_registrar_index] if ward_registrar_index else "Not assigned", 
            "SHO":   day_date_row.iloc[0, ward_sho_index] if ward_sho_index else "Not assigned"
        },
        "Sunshine Day Unit": {
            "SHO": day_date_row.iloc[0, df.iloc[1].str.contains("Sunshine").idxmax()]
        },
        "Clinic": {
            "SpR": day_date_row.iloc[0, clinic_registrar_index] if clinic_registrar_index else "Not assigned", 
            "SHO":   day_date_row.iloc[0, clinic_sho_index] if clinic_sho_index else "Not assigned"
        },
        "SPA": {
            "SpR": day_date_row.iloc[0, spa_registrar_index] if spa_registrar_index else "Not assigned", 
            "SHO":   day_date_row.iloc[0, spa_sho_index] if spa_sho_index else "Not assigned"    
        },
        "Long Day (17:00 - 21:30)": {
            # Handle the concatenation of "Ward Eve" and "SCBU Eve" or fallback to "Long Day PM"
            "SpR": concatenate_long_day_or_ward_scbu(day_date_row, df),
            "SHO": day_date_row.iloc[0, df.iloc[1].str.contains("SHO Eve x2").idxmax()],     
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

def concatenate_long_day_or_ward_scbu(day_date_row, df):
    ward_eve_idx = df.iloc[1].str.contains("Ward Eve", regex=True)
    scbu_eve_idx = df.iloc[1].str.contains("SCBU Eve", regex=True)
    long_day_pm_idx = df.iloc[1].str.contains("Long Day PM|Long day PM", regex=True)
    
    # New checks for "Starlight Ward/HDU" and "2nd ED & Neo Bleep"
    starlight_idx = df.iloc[1].str.contains("Starlight Ward/HDU", regex=True)
    neo_bleep_idx = df.iloc[1].str.contains("2nd ED and Neo bleep", regex=True)

    # Check if both "Ward Eve" and "SCBU Eve" exist, concatenate them if they do
    if ward_eve_idx.any() and scbu_eve_idx.any():
        ward_eve = day_date_row.iloc[0, ward_eve_idx.idxmax()]
        scbu_eve = day_date_row.iloc[0, scbu_eve_idx.idxmax()]
        result = f"{ward_eve} and {scbu_eve}"
    # Check if both "Starlight Ward/HDU" and "2nd ED & Neo Bleep" exist, concatenate them for Long Day
    elif starlight_idx.any() and neo_bleep_idx.any():
        starlight = day_date_row.iloc[0, starlight_idx.idxmax()]
        neo_bleep = day_date_row.iloc[0, neo_bleep_idx.idxmax()]
        result = f"{starlight} and {neo_bleep}"
    # Otherwise, return "Long Day PM" or "Long day PM" if present
    elif long_day_pm_idx.any():
        result = day_date_row.iloc[0, long_day_pm_idx.idxmax()]
    else:
        result = 'Not assigned'  # or an appropriate fallback
    return result

# Streamlit app
# Streamlit app
st.title("Staff Rota Viewer")

# Store the URL in a variable without displaying it
sheet_url = "https://docs.google.com/spreadsheets/d/19VnKEQ7Gle0fjHMPPgc2Eujew2BNRht7zpAWrO__yX4/edit?gid=15103853"

if sheet_url:
    sheet = connect_to_google_sheet(sheet_url)
    worksheet_names = get_worksheet_names(sheet)
    
    st.sidebar.title("Select Options")
    month = st.sidebar.selectbox("Select Month", worksheet_names)
    day = st.sidebar.selectbox("Select Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
    date = st.sidebar.selectbox("Select Date", [f"{i}{'th' if 11 <= i <= 13 else 'st' if i % 10 == 1 else 'nd' if i % 10 == 2 else 'rd' if i % 10 == 3 else 'th'}" for i in range(1, 32)])

if st.button("📅 Get Rota"):
    with st.spinner("Loading rota..."):
        sheet = connect_to_google_sheet(sheet_url)
        df = get_monthly_data(sheet, month)
        formatted_data = filter_and_format_data(df, day, date)
    
    st.subheader(f"Staff Rota for {day} {date}")
    
    # Use st.text() or st.markdown() to display the formatted data    
    st.markdown(formatted_data.replace('\n', '<br>'), unsafe_allow_html=True)

