from flask import Flask, request, send_file
import pandas as pd
import re
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

@app.route('/clean', methods=['POST'])
def clean_program_outcomes():
    if 'file' not in request.files:
        return 'No file uploaded', 400
        
    file = request.files['file']
    if file.filename == '':
        return 'No file selected', 400
        
    # Secure the filename
    input_filename = secure_filename(file.filename)
    output_filename = f"cleaned_{input_filename}"
    
    # Save uploaded file temporarily
    file.save(input_filename)
    
    try:
        # Read only the ALL sheet
        df = pd.read_excel(input_filename, sheet_name='ALL')
        
        def clean_outcomes(text):
            if pd.isna(text):
                return text
            text = str(text)
            elements = re.split(r'[./\\,;\s]+', text)
            elements = [elem.strip() for elem in elements if elem.strip()]
            return ', '.join(elements)
        
        # Clean the Program Outcomes column (index 2)
        df.iloc[:, 2] = df.iloc[:, 2].apply(clean_outcomes)
        
        # Create ExcelWriter object to preserve all sheets
        with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
            original_excel = pd.read_excel(input_filename, sheet_name=None)
            
            for sheet_name in original_excel.keys():
                if sheet_name == 'ALL':
                    df.to_excel(writer, sheet_name='ALL', index=False)
                else:
                    original_excel[sheet_name].to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Send the file back
        return send_file(output_filename, as_attachment=True)
        
    except Exception as e:
        return str(e), 500
        
    finally:
        # Clean up temporary files
        if os.path.exists(input_filename):
            os.remove(input_filename)
        if os.path.exists(output_filename):
            os.remove(output_filename)

if __name__ == '__main__':
    app.run(port=5000)