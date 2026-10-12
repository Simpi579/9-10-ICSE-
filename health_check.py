import os
import sys

def check_environment():
    print("Running Health Check...\n")
    
    # 1. Check Python Version
    print(f"Python Version: {sys.version.split(' ')[0]}")
    if sys.version_info < (3, 9):
        print("[WARNING] Python 3.9 or higher is recommended for this project.")
    else:
        print("[OK] Python version is good.")

    # 2. Check if running inside a virtual environment
    in_venv = sys.prefix != sys.base_prefix
    if in_venv:
        print("[OK] Running inside a virtual environment.")
    else:
        print("[WARNING] NOT running inside a virtual environment. Please activate it first.")

    # 3. Check for required packages
    try:
        import google.generativeai
        import dotenv
        print("[OK] All required packages (google-generativeai, python-dotenv) are installed.")
    except ImportError as e:
        print(f"[ERROR] Missing package: {e}. Did you run 'pip install -r requirements.txt'?")
        return

    print("\n[SUCCESS] Health Check Passed! The environment is ready for Step 2.")

if __name__ == "__main__":
    check_environment()
