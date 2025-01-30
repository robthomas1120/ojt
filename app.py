import pandas as pd
import re

def clean_program_outcomes(input_file, output_file):
    """
    Clean the Program Outcomes column in the ALL sheet of the Excel file.
    
    Args:
        input_file (str): Path to the input Excel file
        output_file (str): Path where the cleaned Excel file will be saved
    """
    try:
        # Read only the ALL sheet
        df = pd.read_excel(input_file, sheet_name='ALL')
        
        def clean_outcomes(text):
            if pd.isna(text):  # Handle NaN/empty values
                return text
            
            # Convert to string in case it's not
            text = str(text)
            
            # Split on any combination of periods, backslashes, forward slashes, 
            # commas, semicolons, or multiple spaces
            elements = re.split(r'[./\\,;\s]+', text)
            
            # Remove empty strings and strip whitespace
            elements = [elem.strip() for elem in elements if elem.strip()]
            
            # Join with commas
            return ', '.join(elements)
        
        # Apply the cleaning function to the Program Outcomes column (index 2)
        df.iloc[:, 2] = df.iloc[:, 2].apply(clean_outcomes)
        
        # Create ExcelWriter object to preserve all sheets
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Copy the original file
            original_excel = pd.read_excel(input_file, sheet_name=None)
            
            # Write all sheets
            for sheet_name in original_excel.keys():
                if sheet_name == 'ALL':
                    # Write the modified ALL sheet
                    df.to_excel(writer, sheet_name='ALL', index=False)
                else:
                    # Copy other sheets as they are
                    original_excel[sheet_name].to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"Successfully cleaned Program Outcomes column and saved to {output_file}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

# Example usage
if __name__ == "__main__":
    input_file = "OUTCOMES MAPPING_PHA.B.xlsx"
    output_file = "OUTCOMES MAPPING_PHA.B_cleaned.xlsx"
    clean_program_outcomes(input_file, output_file)