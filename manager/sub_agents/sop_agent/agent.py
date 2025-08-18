from google.adk.agents import Agent
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import re
from typing import Dict, Any, Union


# Google Sheets Setup
SERVICE_ACCOUNT_FILE = "thosewhocare-data-1c04d8e3f1bd.json" 
# The base URL for the spreadsheet. GIDs will be appended to this.
BASE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1UcpYjPaW9RCftkCNf26L-JznWFILTIFqNcgMuMTA6No/"
MAIN_WORKSHEET_ID = 1248492876

scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
client_gs = gspread.authorize(creds)

# Function to get a specific Google Sheet worksheet instance by name or GID
def get_worksheet_by_identifier(identifier: Union[str, int]):
    """
    Opens the spreadsheet and returns a specific worksheet by name or GID.
    If an integer is provided, it attempts to find by GID.
    Otherwise, it assumes it's a worksheet name.

    Args:
        identifier (Union[str, int]): The name (str) or GID (int) of the worksheet.
    """
    spreadsheet = client_gs.open_by_url(BASE_SHEET_URL)
    
    if isinstance(identifier, int): # Assume it's a GID
        return spreadsheet.get_worksheet_by_id(identifier)
    elif isinstance(identifier, str): # Assume it's a worksheet name
        try:
            return spreadsheet.worksheet(identifier)
        except gspread.exceptions.WorksheetNotFound:
            # Fallback if name isn't found, maybe it's a string representation of GID
            if identifier.isdigit():
                return spreadsheet.get_worksheet_by_id(int(identifier))
            else:
                raise
    else:
        raise ValueError(f"Invalid worksheet identifier type: {type(identifier)}. Must be str or int.")


def search_sop(query: str) -> str:
    """
    Search the MAIN SOP Master sheet (ID: 1248492876) for matching process, description, or owner.
    Extracts actual hyperlink URLs, handling HYPERLINK formulas, #gid= references, and direct URLs.
    Returns a string representation of the found matches.

    Args:
        query (str): The search term to match against the 'Process', 'Description', or 'New Owner' columns.
    """
    # Always start by checking the main worksheet ID
    sheet = get_worksheet_by_identifier(MAIN_WORKSHEET_ID)

    # Get all values from the worksheet, rendering formulas as they are
    all_data_formulas = sheet.get_all_values(value_render_option='FORMULA')
    # Also get values rendered as displayed, for non-formula cells
    all_data_displayed = sheet.get_all_values(value_render_option='FORMATTED_VALUE')

    if not all_data_formulas:
        return "Main SOP worksheet is empty or could not be read."

    headers = all_data_formulas[0]
    link_col_index = -1
    try:
        link_col_index = headers.index("Link to SOP")
    except ValueError:
        print("Warning: 'Link to SOP' column not found in the main sheet headers. Links will not be extracted.")
        link_col_index = -1 # Ensure it remains -1 if not found

    matches = []
    # Iterate over rows starting from the second row (index 1) to skip headers
    for i in range(1, len(all_data_formulas)):
        row_formula_values = all_data_formulas[i]
        row_displayed_values = all_data_displayed[i]
        
        # Ensure row has enough columns for essential data before processing
        if len(row_displayed_values) < len(headers):
            # Pad shorter rows with empty strings to prevent index errors
            row_displayed_values.extend([''] * (len(headers) - len(row_displayed_values)))
            row_formula_values.extend([''] * (len(headers) - len(row_formula_values)))

        # Extract column values safely
        process_val = row_displayed_values[headers.index("Process")] if "Process" in headers else ""
        description_val = row_displayed_values[headers.index("Description")] if "Description" in headers else ""
        owner_val = row_displayed_values[headers.index("New Owner")] if "New Owner" in headers else ""

        # Check for query match on Process, Description, or New Owner
        if (
            query.lower() in str(process_val).lower()
            or query.lower() in str(description_val).lower()
            or query.lower() in str(owner_val).lower()
        ):
            extracted_link = ""
            if link_col_index != -1: # Only try to extract link if column exists
                current_formula_value = row_formula_values[link_col_index]
                current_displayed_value = row_displayed_values[link_col_index]

                # 1. Try to extract URL from HYPERLINK formula
                if current_formula_value.startswith("=HYPERLINK("):
                    match = re.search(r'=HYPERLINK\("([^"]+)"', current_formula_value)
                    if match:
                        temp_link = match.group(1)
                        # Reconstruct full URL if it's a relative #gid
                        if temp_link.startswith("#gid="):
                            extracted_link = f"{BASE_SHEET_URL}edit{temp_link}"
                        elif temp_link.startswith("http://") or temp_link.startswith("https://"):
                            extracted_link = temp_link # It's already a full URL
                        else:
                            extracted_link = current_displayed_value # Fallback if unexpected formula format
                    else:
                        extracted_link = current_displayed_value # Fallback if regex fails on formula
                
                # 2. If no link from formula, check if it's a relative #gid link in displayed value
                elif current_displayed_value.startswith("#gid="):
                    extracted_link = f"{BASE_SHEET_URL}edit{current_displayed_value}"
                
                # 3. If still no extracted_link (neither formula nor #gid), check if it's a direct URL or just text
                if not extracted_link: # Check again after previous attempts
                    if current_displayed_value.startswith("http://") or current_displayed_value.startswith("https://"):
                        extracted_link = current_displayed_value
                    else:
                        extracted_link = current_displayed_value # Final fallback to displayed text

            matches.append({
                "Process": process_val,
                "Owner": owner_val,
                "Link": extracted_link, # This will now be the full, absolute URL
                "Description": description_val
            })
            
    return str(matches if matches else "No matches found.")

# -------------------
# Web Browsing Tool
# -------------------
def get_content_from_url(url: str) -> str:
    """
    Fetches the content from a given URL.
    - If it's a Google Sheet GID link, it uses gspread to get the content of that specific sheet tab.
    - For other HTTP/HTTPS links, it simulates access.

    Args:
        url (str): The URL to fetch content from. It can be a full Google Sheet URL with a GID or any other HTTP/HTTPS link.
    """
    # Check if the URL belongs to the current Google Sheet base URL and contains a GID
    if url.startswith(BASE_SHEET_URL) and "#gid=" in url:
        try:
            # Extract the GID from the URL
            match = re.search(r'#gid=(\d+)', url)
            if match:
                gid = match.group(1)
                # Use get_worksheet_by_identifier to get the specific worksheet by GID
                specific_worksheet = get_worksheet_by_identifier(int(gid))
                all_sheet_data = specific_worksheet.get_all_values()
                # Represent the sheet data as a string for the LLM
                content_str = "\n--- Content from Google Sheet Tab (GID: " + gid + ") ---\n"
                for row in all_sheet_data:
                    # Join row elements with a tab or comma for better LLM parsing
                    content_str += "\t".join(row) + "\n"
                content_str += "--- End of Google Sheet Tab Content ---"
                return content_str
            else:
                return f"Could not extract GID from Google Sheet URL: {url}"
        except gspread.exceptions.WorksheetNotFound:
            return f"Error: Google Sheet tab with GID in URL '{url}' not found."
        except Exception as e:
            return f"Error accessing Google Sheet tab '{url}': {e}"
    elif url.startswith("http://") or url.startswith("https://"):
        # This is where actual web scraping for external sites would go if allowed.
        # For this environment, we simulate.
        return f"Successfully identified and would attempt to access external URL: {url}. (Actual content not displayed in this simulation due to environment limitations, but the agent can infer the link is valid and might have content)."
    else:
        return f"Invalid or unrecognized URL format for content fetching: {url}. Please ensure it's a full HTTP/HTTPS URL or a correctly formatted Google Sheet GID link."

sop_agent = Agent(
    name="SOP_agent",
    model="gemini-2.5-flash-lite",
    description="This agent helps find and understand Standard Operating Procedures (SOPs) for Those Who Care (TWC). It can search for SOPs and retrieve their content from Google Sheets.",
    instruction="""
      You are a specialized agent for finding and interpreting Standard Operating Procedures (SOPs) for 'Those Who Care (TWC)'.

   Your primary function is to:
   1.  Use the `search_sop` tool to locate relevant SOPs based on user queries about processes, owners, or keywords.
   2.  Once a relevant SOP is found, use the `get_content_from_url` tool to read its contents from the provided Google Sheet link.
   3.  After retrieving the content, examine it for multiple revisions. Look for version numbers, dates, or a revision history section. If multiple revisions are present, you must identify and use only the information from the latest revision to answer the user's question.
   4.  Synthesize the information from the latest revision in the SOP to provide clear and concise answers.
   5.  If no relevant SOP is found or the SOP does not contain the answer, clearly state that and indicate that you will escalate to the manager.
   Your answers must be strictly based on the information within the SOP documents. Do not infer or provide information from outside the provided context.
   """,
    tools=[search_sop, get_content_from_url]
)
