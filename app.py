import streamlit as st
import gspread
import json
import os
from datetime import date, datetime # Ensure datetime is imported for current time
from oauth2client.service_account import ServiceAccountCredentials
import time

# A note on the Google Sheets setup:
# The original code used "PTA_Reimbursements_2025-26" as the spreadsheet name
# and "reimbursements" as the worksheet name.
# You will need to create a new Google Sheet for volunteer hours and
# update the sheet_name and worksheet_name variables below.
# Make sure your service account has access to this new sheet.

# ---------- Google Sheets Setup ----------
import streamlit as st
import os
import json
import gspread
from google.oauth2.service_account import Credentials as ServiceAccountCredentials # Renamed to avoid conflict

@st.cache_resource
def get_gsheet():
    """Initializes and returns a gspread worksheet object."""
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = None

    # --- PRIORITY 1: Check for GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable (for Cloud Run) ---
    if "GOOGLE_APPLICATION_CREDENTIALS_JSON" in os.environ:
        try:
            creds_json_string = os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"]
            creds_dict = json.loads(creds_json_string)
            st.success("Credentials loaded from GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable.")
            # IMPORTANT: Return creds_dict immediately if successful to prevent falling to st.secrets check
            # No, we can't return creds_dict directly here, as we need to authorize gspread below.
            # But the logic flow for setting creds_dict is correct.
        except json.JSONDecodeError:
            st.error("Error decoding GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable. Please check your secret format.")
            st.stop() # Stop if there's a problem with the environment variable
        except Exception as e:
            st.error(f"Unexpected error loading env var credentials: {e}")
            st.stop() # Stop if there's an unexpected error
    # --- PRIORITY 2: Check for GOOGLE_CREDS in st.secrets (for local/Streamlit Cloud, only if env var not found) ---
    elif "GOOGLE_CREDS" in st.secrets: # Using elif ensures this only runs if the first if was False
        try:
            # Assuming GOOGLE_CREDS in secrets.toml is a JSON string
            creds_json_string = st.secrets["GOOGLE_CREDS"]
            creds_dict = json.loads(creds_json_string)
            st.success("Credentials loaded from st.secrets['GOOGLE_CREDS'].")
        except json.JSONDecodeError:
            st.error("Error decoding st.secrets['GOOGLE_CREDS']. Please check your secrets.toml format.")
            st.stop() # Stop if there's a problem with st.secrets
        except Exception as e:
            st.error(f"Unexpected error loading st.secrets credentials: {e}")
            st.stop() # Stop if there's an unexpected error
    # --- If no credentials found in either location ---
    else:
        st.error("No Google credentials found. Please set GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable (for Cloud Run) or st.secrets['GOOGLE_CREDS'] (for local/Streamlit Cloud).")
        st.stop() # Stop the app if no credentials could be loaded

    # --- Authorization and Sheet Opening (Only proceeds if creds_dict was successfully populated) ---
    if creds_dict: # This check is crucial now
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            client = gspread.authorize(creds)
            # You must change the spreadsheet and worksheet names here to match your volunteer hours sheet
            sheet_name = "PTA_Volunteer_Hours_2025-26"
            worksheet_name = "hours"
            return client.open(sheet_name).worksheet(worksheet_name)
        except Exception as e:
            st.error(f"Error authorizing gspread with provided credentials: {e}. Ensure your service account has access to the Google Sheet.")
            st.stop()
    else:
        # This else block should theoretically not be reached if st.stop() is used above correctly
        # but it's good for defensive programming.
        st.error("Internal error: Credentials dictionary is unexpectedly empty. Cannot authorize gspread.")
        st.stop()

# Initialize the Google Sheet connection
sheet = get_gsheet()



# ---------- Streamlit UI ----------
st.title("🤝 PTA Volunteer Hours Submission Form")

st.markdown("""
            Please fill out this form to submit your volunteer hours for the PTA.
            Your submission will be recorded in our Google Sheet.
            """)

st.divider()

with st.form("volunteer_hours_form", clear_on_submit=True):
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    col1, col2 = st.columns(2)
    with col1:
        submission_date = st.date_input("Date", value=date.today())
    with col2:
        hours = st.number_input("Hours Volunteered", min_value=0.0, step=0.5, format="%.2f")

    event = st.text_input("Event")

    submitted = st.form_submit_button("Submit Hours")

if submitted:
    # Check if all required fields are filled
    if not first_name or not last_name or not hours or not event:
        st.error("Please fill out all required fields.")
    else:
        try:
            # Append data to Google Sheet
            # The order of the columns here must match the order in your Google Sheet
            sheet.append_row([
                str(submission_date),
                first_name.strip(),
                last_name.strip(),
                f"{hours:.2f}",
                event.strip(),
            ])
            st.success("✅ Volunteer hours submitted successfully. Thank you!")
            time.sleep(3)  # Optional: Pause to allow user to read success message
            st.rerun()
        except Exception as e:
            st.error(f"Failed to submit volunteer hours to Google Sheet: {e}")
            st.warning("Please check your Google Sheet permissions and ensure the sheet name and worksheet name are correct, and that you have columns for all the data.")
