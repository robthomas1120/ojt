from flask import Flask, request, send_file, make_response
from flask_cors import CORS
import pandas as pd
import re
import os
import logging
import tempfile
from werkzeug.utils import secure_filename

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/clean', methods=['POST', 'OPTIONS'])
def clean_program_outcomes():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response

    logger.info("Received request to clean program outcomes")
    
    if 'file' not in request.files:
        logger.error("No file in request")
        return 'No file uploaded', 400
        
    file = request.files['file']
    if file.filename == '':
        logger.error("No file selected")
        return 'No file selected', 400
        
    try:
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Secure the filename
            input_filename = os.path.join(temp_dir, secure_filename(file.filename))
            output_filename = os.path.join(temp_dir, f"cleaned_{secure_filename(file.filename)}")
            
            logger.info(f"Processing file: {input_filename}")
            
            # Save uploaded file temporarily
            file.save(input_filename)
            logger.info("File saved temporarily")
            
            # Read only the ALL sheet
            df = pd.read_excel(input_filename, sheet_name='ALL')
            logger.info("Excel file read successfully")
            
            def clean_outcomes(text):
                if pd.isna(text):  # Handle NaN/empty values
                    return text
                
                # Convert to string in case it's not
                text = str(text)
                
                # Split on any combination of periods, backslashes, forward slashes, 
                # commas, semicolons, or multiple spaces
                elements = re.split(r'[./\\,;\s]+', text)
                
                cleaned_elements = []
                for elem in elements:
                    elem = elem.strip()
                    if not elem:
                        continue
                    
                    # Case 1: Convert BCxx to BC_xx (any number)
                    if re.match(r'^BC\d+$', elem):
                        number = re.search(r'\d+', elem).group()
                        elem = f"BC_{number}"
                    
                    # Case 2: Convert Bxx to BC_xx (any number)
                    elif re.match(r'^B\d+$', elem):
                        number = re.search(r'\d+', elem).group()
                        elem = f"BC_{number}"
                    
                    # Case 3: Convert Cxx to BC_xx (any number)
                    elif re.match(r'^C\d+$', elem):
                        number = re.search(r'\d+', elem).group()
                        elem = f"BC_{number}"
                    
                    cleaned_elements.append(elem)
                
                # Join with commas and make sure there's a space after each comma
                return ', '.join(cleaned_elements)
            
            # Apply the cleaning function to the Program Outcomes column (index 2)
            df.iloc[:, 2] = df.iloc[:, 2].apply(clean_outcomes)
            
            # Create ExcelWriter object to preserve all sheets
            with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
                # Copy the original file
                original_excel = pd.read_excel(input_filename, sheet_name=None)
                
                # Write all sheets
                for sheet_name in original_excel.keys():
                    if sheet_name == 'ALL':
                        # Write the modified ALL sheet
                        df.to_excel(writer, sheet_name='ALL', index=False)
                    else:
                        # Copy other sheets as they are
                        original_excel[sheet_name].to_excel(writer, sheet_name=sheet_name, index=False)
            
            logger.info("File processed successfully")
            
            # Send the file
            response = send_file(
                output_filename,
                as_attachment=True,
                download_name=f"cleaned_{secure_filename(file.filename)}"
            )
            
            # Add CORS headers to the response
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
            
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}", exc_info=True)
        return str(e), 500

if __name__ == '__main__':
    logger.info("Starting Flask server...")
    app.run(host='127.0.0.1', port=5000)