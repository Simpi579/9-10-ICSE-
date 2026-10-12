# AI-Powered Assessment Platform - LLM Module

Welcome to the LLM module of the AI-Powered Assessment Platform! 
This project focuses entirely on using the Gemini API to generate and validate educational questions.

## 📁 Project Structure

- **`src/`**: Contains the source code.
  - **`llm_module/client.py`**: A reusable Python class (`GeminiClient`) that manages the connection to Google's Gen AI API.
- **`tests/`**: Contains automated tests.
  - **`test_client.py`**: A mock-based test to verify our client logic without needing an internet connection or real API key.
- **`ask_gemini.py`**: A sample script that uses our client to ask the AI an educational question.
- **`requirements.txt`**: Lists all third-party Python libraries needed.
- **`.env.example`**: A template file for your secret API keys and configurations.
- **`health_check.py`**: A script to verify your Python environment.

## 🚀 Getting Started (Windows)

Follow these steps to set up your environment:

### 1. Set up your Secret Keys
1. Copy the `.env.example` file and rename it to `.env`.
   - In PowerShell: `copy .env.example .env`
2. Open the `.env` file and replace `your_api_key_here` with your actual Google Gemini API key. 
   *(Never share your `.env` file or commit it to GitHub!)*

### 2. Activate the Virtual Environment
A virtual environment keeps our project's dependencies isolated. 
- In your terminal, run:
  ```powershell
  .\venv\Scripts\Activate
  ```

### 3. Install the Required Packages
```powershell
pip install -r requirements.txt
```

### 4. Verify the Setup
```powershell
python health_check.py
```

## 🧠 Step 2: Running the AI Script

Once setup is complete and you have added your API key to `.env`, you can ask Gemini a question:
```powershell
python ask_gemini.py
```

## 🧪 Running the Tests

To run the complete automated test suite (schema validation, structural checks, syllabus alignment, and client tests):
```powershell
python -m unittest discover -s tests -p "test_*.py"
```

Or run individual test modules:
```powershell
python -m unittest tests/test_client.py
python -m unittest tests/test_schemas.py
python -m unittest tests/test_structural_validation.py
python -m unittest tests/test_semantic_validation.py
python -m unittest tests/test_generator_and_pipeline.py
python -m unittest tests/test_evaluation_service.py
```

## 🎯 AI Answer Evaluation System (CBSE Class 9 History)

You can evaluate student written answers against the existing CBSE question bank using either the Web Application or the Interactive CLI.

### 1. Launch the Student & Teacher Web Interface
```powershell
python app.py
```
Open your browser to: **`http://127.0.0.1:8000`**
- Select any existing CBSE Class 9 History question.
- View question text, chapter, and official maximum marks.
- Enter/paste the student's answer and click **Evaluate Answer**.
- View awarded marks, itemized rubric criteria, identified concepts, missing points, and historical error corrections.

### 2. Interactive Terminal Evaluation (CLI)
```powershell
python evaluate_answer.py
```

### 3. Generating & Validating Questions (CLI)
```powershell
python generate_questions.py --mock --type "Short Answer"
```

