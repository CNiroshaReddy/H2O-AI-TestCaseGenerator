# H2O AI Test Case Generator

A web application that uses AI to automatically generate test scenarios and test cases from uploaded documents and webpage URLs.

## Features

- User authentication
- Upload Word documents (.doc/.docx) and PDFs
- Add webpage URLs for analysis
- AI-powered test case generation
- View generated test cases in table format
- Download results as Excel file

## Setup Instructions

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Open browser and navigate to:
```
http://localhost:5000
```

## Login Credentials

- Username: `ncharala`
- Password: `Password1!`

## Usage

1. Login with provided credentials
2. Upload documents or add URLs in the "Upload your docs" tab
3. Click "Generate TS's & TC's" to process with AI
4. View results in "AI_TestOutput" tab
5. Download Excel file with all test cases

## Excel Output Format

The generated Excel file contains:
- TS# (Test Scenario ID)
- Scenario Description
- TC# (Test Case ID)
- Test Case Steps
- Expected Results
- Test Data
- Results
- Defects
- Comments
