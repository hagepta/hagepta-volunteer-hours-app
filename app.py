import streamlit as st
import gspread
import json
import os
from datetime import date, datetime # Ensure datetime is imported for current time
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import storage
import time




# ---------- Google Sheets Setup ----------
@st.cache_resource
def get_gsheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = None

    if "GOOGLE_APPLICATION_CREDENTIALS_JSON" in os.environ:
        try:
            creds_json_string = os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"]
            creds_dict = json.loads(creds_json_string)
            #st.success("Credentials loaded from GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable.")
        except json.JSONDecodeError:
            st.error("Error decoding GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable. Please check your secret format.")
        except Exception as e:
            st.error(f"Unexpected error loading env var credentials: {e}")
    elif "GOOGLE_CREDS" in st.secrets:
        try:
            creds_dict = json.loads(st.secrets["GOOGLE_CREDS"])
            st.success("Credentials loaded from st.secrets['GOOGLE_CREDS'].")
        except json.JSONDecodeError:
            st.error("Error decoding st.secrets['GOOGLE_CREDS']. Please check your secrets.toml format.")
        except Exception as e:
            st.error(f"Unexpected error loading st.secrets credentials: {e}")
    else:
        st.error("No Google credentials found. Please set GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable (for Cloud Run) or st.secrets['GOOGLE_CREDS'] (for local/Streamlit Cloud).")
        st.stop()

    if creds_dict:
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            client = gspread.authorize(creds)
            return client.open("PTA_Volunteer_Hours_2025-26").worksheet("hours")
        except Exception as e:
            st.error(f"Error authorizing gspread with provided credentials: {e}. Ensure your service account has access to the Google Sheet.")
            st.stop()
    else:
        st.error("Credentials dictionary is empty. Cannot authorize gspread.")
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
    duties = st.text_area("Duties Performed", placeholder="Describe the duties you performed during your volunteer hours.")

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
                duties.strip(),
            ])
            st.success("✅ Volunteer hours submitted successfully. Thank you!")
            time.sleep(3)  # Optional: Pause to allow user to read success message
            st.rerun()
        except Exception as e:
            st.error(f"Failed to submit volunteer hours to Google Sheet: {e}")
            st.warning("Please check your Google Sheet permissions and ensure the sheet name and worksheet name are correct, and that you have columns for all the data.")
