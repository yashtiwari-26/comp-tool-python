from flask import Flask, jsonify, request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import json
import os

app = Flask(__name__)

# Google Sheets setup
SHEET_ID = "1AFVSvSq6fpj3Wf2yzw7Zd3IbAIEroBK8MBkXlwlkweQ"  # You'll provide this later
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def get_sheets_service():
    """Connect to Google Sheets using service account"""
    # Get credentials from environment variable
    creds_json = os.getenv('GOOGLE_CREDENTIALS')
    if not creds_json:
        return None

    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return build('sheets', 'v4', credentials=creds)


@app.route('/', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'alive',
        'message': 'Compensation Tool Python Backend is running!'
    }), 200


@app.route('/fetch-employee', methods=['POST'])
def fetch_employee():
    """Fetch employee data"""
    try:
        data = request.json
        employee_id = data.get('employeeId')
        country = data.get('country')

        if not employee_id or not country:
            return jsonify({'error': 'Missing employeeId or country'}), 400

        service = get_sheets_service()
        if not service:
            return jsonify({'error': 'Google Sheets connection failed'}), 500

        # Read from Employee Data sheet
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range="'Employee Data'!A:Z"
        ).execute()

        values = result.get('values', [])
        headers = values[0]

        # Find employee
        emp_id_idx = headers.index('Employee ID')
        country_idx = headers.index('Country')

        employee_row = None
        for row in values[1:]:
            if len(row) > max(emp_id_idx, country_idx):
                if str(row[emp_id_idx]) == str(employee_id) and row[country_idx] == country:
                    employee_row = row
                    break

        if not employee_row:
            return jsonify({'error': 'Employee not found'}), 404

        # Extract all fields
        result_data = {}
        for i, header in enumerate(headers):
            if i < len(employee_row):
                result_data[header] = employee_row[i]
            else:
                result_data[header] = ''

        return jsonify(result_data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))