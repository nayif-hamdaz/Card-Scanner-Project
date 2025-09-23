import os
import base64
import json
from flask import Flask, request, jsonify, render_template
from openai import OpenAI
from dotenv import load_dotenv
import openpyxl

# --- Configuration ---
load_dotenv()
try:
    client = OpenAI()
except Exception as e:
    raise ValueError(f"Failed to initialize OpenAI client. Is OPENAI_API_KEY set? Error: {e}")

app = Flask(__name__)
EXCEL_FILENAME = "card contacts.xlsx"

# --- Route to serve the HTML frontend ---
@app.route('/')
def index():
    return render_template('index.html')

# --- API Endpoint 1: Process the Image(s) ---
@app.route('/process-card', methods=['POST'])
def process_card():
    data = request.json
    front_image_url = data.get('frontImage')
    back_image_url = data.get('backImage') # This can be None

    if not front_image_url:
        return jsonify({"error": "Front image is required."}), 400

    try:
        # Build the content list for the AI
        messages_content = []
        
        # The main instruction for the AI
        system_prompt = """
        You are an expert business card data extractor. You will be given one or two images of a business card (front and back).
        Your job is to read the text from all provided images and intelligently merge the information into a single, complete contact profile.
        Extract the key information in a structured JSON format.
        The fields to extract are: organization, name, designation, contact, email, website, and address. Leave a field for remarks, but you do not need to fill it.
        If a field is not found, use an empty string "" as its value.
        Your response MUST be ONLY the JSON object, with no extra text, explanations, or markdown formatting.
        """
        messages_content.append({"type": "text", "text": system_prompt})
        
        # Add the front image
        messages_content.append({
            "type": "image_url",
            "image_url": {"url": front_image_url}
        })

        # Add the back image only if it exists
        if back_image_url:
            messages_content.append({
                "type": "image_url",
                "image_url": {"url": back_image_url}
            })

        response = client.chat.completions.create(
            model="gpt-4o", 
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": messages_content}]
        )
        
        json_string = response.choices[0].message.content
        if json_string is None:
            return jsonify({"error": "AI model did not return any data."}), 500

        parsed_data = json.loads(json_string)
        return jsonify({"data": parsed_data})
    except Exception as e:
        return jsonify({"error": f"OpenAI API call failed: {e}"}), 500

# --- API Endpoint 2: Save the Data to Excel ---
@app.route('/save-contact', methods=['POST'])
def save_contact():
    contact_data = request.json
    
    try:
        workbook = openpyxl.load_workbook(EXCEL_FILENAME)
        sheet = workbook.active
    except FileNotFoundError:
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Business Cards"
        # FIX: Added 'Remarks' to the header list
        headers = ['Sl. No.', 'Organization', 'Name', 'Designation', 'Contact Number', 'Email', 'Website', 'Address', 'Remarks']
        sheet.append(headers)

    sl_no = sheet.max_row
    
    new_row = [
        sl_no,
        contact_data.get('organization', ''),
        contact_data.get('name', ''),
        contact_data.get('designation', ''),
        contact_data.get('contact', ''),
        contact_data.get('email', ''),
        contact_data.get('website', ''),
        contact_data.get('address', ''),
        contact_data.get('remarks', '') # FIX: Added remarks data to the new row
    ]
    
    sheet.append(new_row)
    
    # Auto-fit column widths
    for column_cells in sheet.columns:
        max_length = 0
        column_letter = column_cells[0].column_letter
        for cell in column_cells:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2)
        sheet.column_dimensions[column_letter].width = adjusted_width

    # --- ADDED: Improved saving with specific error handling ---
    try:
        workbook.save(EXCEL_FILENAME)
    except PermissionError:
        print(f"ERROR: Could not save to {EXCEL_FILENAME}. It is likely open in another program.")
        return jsonify({"error": f"Could not save to Excel. Please close the '{EXCEL_FILENAME}' file if it is open in another program."}), 500
    except Exception as e:
        print(f"An unexpected error occurred during save: {e}")
        return jsonify({"error": f"An unexpected error occurred while saving the file: {e}"}), 500

    
    print(f"Successfully saved contact #{sl_no} to {EXCEL_FILENAME}")
    return jsonify({"status": "success", "message": f"Contact #{sl_no} saved."})

# --- Run the Server ---
if __name__ == '__main__':
    app.run(debug=True)

