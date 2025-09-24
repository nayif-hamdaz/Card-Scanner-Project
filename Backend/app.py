import os
import json
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import gspread # <-- New library for Google Sheets
from google.oauth2.service_account import Credentials
import openpyxl # <-- Still needed for the download function
from io import BytesIO

# --- Configuration ---
load_dotenv()
try:
    client = OpenAI()
except Exception as e:
    raise ValueError(f"Failed to initialize OpenAI client. Is OPENAI_API_KEY set? Error: {e}")

# --- Google Sheets Configuration ---
# Define the scope of access for our robot user
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]
# The name of the Google Sheet you created
# IMPORTANT: Make sure this name exactly matches the name of your Google Sheet.
SHEET_NAME = "Card Scanner Contacts" 

# Authenticate with the credentials file.
# On Render, we will upload `credentials.json` as a Secret File.
if os.path.exists('credentials.json'):
    creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open(SHEET_NAME)
    worksheet = spreadsheet.sheet1
else:
    print("WARNING: credentials.json not found. Google Sheets integration will not work.")
    worksheet = None

app = Flask(__name__)
CORS(app)

# --- Main Route for Live Check ---
@app.route('/')
def index():
    return "Card Scanner Backend is live and connected."

# --- API Endpoint 1: Process the Image(s) ---
@app.route('/process-card', methods=['POST'])
def process_card():
    data = request.json
    front_image_url = data.get('frontImage')
    back_image_url = data.get('backImage') 
    if not front_image_url:
        return jsonify({"error": "Front image is required."}), 400
    try:
        messages_content = []
        system_prompt = """
        You are an expert business card data extractor. You will be given one or two images of a business card (front and back).
        Your job is to read the text from all provided images and intelligently merge the information into a single, complete contact profile.
        Extract the key information in a structured JSON format.
        The fields to extract are: organization, name, designation, contact, email, website, and address. Leave a field for remarks, but you do not need to fill it.
        If a field is not found, use an empty string "" as its value.
        Your response MUST be ONLY the JSON object, with no extra text, explanations, or markdown formatting.
        """
        messages_content.append({"type": "text", "text": system_prompt})
        messages_content.append({"type": "image_url", "image_url": {"url": front_image_url}})
        if back_image_url:
            messages_content.append({"type": "image_url", "image_url": {"url": back_image_url}})
        response = client.chat.completions.create(model="gpt-4o", response_format={"type": "json_object"}, messages=[{"role": "user", "content": messages_content}])
        json_string = response.choices[0].message.content
        if json_string is None:
            return jsonify({"error": "AI model did not return any data."}), 500
        parsed_data = json.loads(json_string)
        return jsonify({"data": parsed_data})
    except Exception as e:
        return jsonify({"error": f"OpenAI API call failed: {e}"}), 500


# --- API Endpoint 2: Save the Data to Google Sheets ---
@app.route('/save-contact', methods=['POST'])
def save_contact():
    if not worksheet:
        return jsonify({"error": "Backend is not configured to connect to Google Sheets."}), 500
        
    contact_data = request.json
    
    try:
        # Get all current rows to determine the next Sl. No.
        all_rows = worksheet.get_all_values()
        sl_no = len(all_rows) # The next serial number is the current row count (since header is row 1)
        
        new_row = [
            sl_no,
            contact_data.get('organization', ''),
            contact_data.get('name', ''),
            contact_data.get('designation', ''),
            contact_data.get('contact', ''),
            contact_data.get('email', ''),
            contact_data.get('website', ''),
            contact_data.get('address', ''),
            contact_data.get('remarks', '')
        ]
        
        worksheet.append_row(new_row)
        
        print(f"Successfully saved contact #{sl_no} to Google Sheets.")
        return jsonify({"status": "success", "message": f"Contact #{sl_no} saved to Google Sheets."})
    except Exception as e:
        print(f"An error occurred while saving to Google Sheets: {e}")
        return jsonify({"error": f"An error occurred while saving to Google Sheets: {e}"}), 500


# --- API Endpoint 3: Download All Data as an Excel File ---
@app.route('/download-excel', methods=['GET'])
def download_excel():
    if not worksheet:
        return jsonify({"error": "Backend is not configured to connect to Google Sheets."}), 500

    try:
        all_data = worksheet.get_all_values()
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Business Card Contacts"
        
        for row_data in all_data:
            sheet.append(row_data)
            
        for column_cells in sheet.columns:
            max_length = 0
            column_letter = column_cells[0].column_letter
            for cell in column_cells:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except: pass
            adjusted_width = (max_length + 2)
            sheet.column_dimensions[column_letter].width = adjusted_width
            
        excel_stream = BytesIO()
        workbook.save(excel_stream)
        excel_stream.seek(0)
        
        return send_file(
            excel_stream,
            as_attachment=True,
            download_name='contacts.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        print(f"An error occurred during Excel download creation: {e}")
        return jsonify({"error": f"An error occurred creating the Excel file: {e}"}), 500


# --- Run the Server (for local testing) ---
if __name__ == '__main__':
    app.run(debug=True)

