from flask import Flask, request, send_file
from flask_cors import CORS
import pandas as pd
import re
import os
import logging
from werkzeug.utils import secure_filename

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/clean', methods=['POST', 'OPTIONS'])
def clean_program_outcomes():
    # Handle preflight request
    if request.method == 'OPTIONS':
        return '', 204

    logger.info("Received request to clean program outcomes")
    
    if 'file' not in request.files:
        logger.error("No file in request")
        return 'No file uploaded', 400
        
    file = request.files['file']
    if file.filename == '':
        logger.error("No file selected")
        return 'No file selected', 400
        
    try:
        # Secure the filename
        input_filename = secure_filename(file.filename)
        output_filename = f"cleaned_{input_filename}"
        
        logger.info(f"Processing file: {input_filename}")
        
        # Save uploaded file temporarily
        file.save(input_filename)
        logger.info("File saved temporarily")
        
        # Read only the ALL sheet
        df = pd.read_excel(input_filename, sheet_name='ALL')
        logger.info("Excel file read successfully")
        
        def clean_outcomes(text):
            if pd.isna(text):
                return text
            text = str(text)
            elements = re.split(r'[./\\,;\s]+', text)
            elements = [elem.strip() for elem in elements if elem.strip()]
            return ', '.join(elements)
        
        # Clean the Program Outcomes column (index 2)
        df.iloc[:, 2] = df.iloc[:, 2].apply(clean_outcomes)
        logger.info("Program outcomes cleaned")
        
        # Save to new file
        df.to_excel(output_filename, index=False)
        logger.info("Cleaned file saved")
        
        response = send_file(
            output_filename,
            as_attachment=True,
            download_name=output_filename
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}", exc_info=True)
        return str(e), 500
        
    finally:
        # Clean up temporary files
        try:
            if os.path.exists(input_filename):
                os.remove(input_filename)
            if os.path.exists(output_filename):
                os.remove(output_filename)
            logger.info("Temporary files cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up files: {str(e)}")

if __name__ == '__main__':
    logger.info("Starting Flask server...")
    app.run(host='127.0.0.1', port=5000, debug=True)