import gspread
from google.oauth2.service_account import Credentials

# ✅ Updated scopes
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials
creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)

# Authorize client
client = gspread.authorize(creds)

# Option A: Open by name
spreadsheet = client.open("Sunday School registrations")

# Option B (recommended for reliability): Open by ID
# spreadsheet = client.open_by_key("your-spreadsheet-id")

sheet = spreadsheet.sheet1
sheet.update("A1", [["✅ Hello from updated scopes!"]])


print("✔️ Successfully wrote to Google Sheet.")

