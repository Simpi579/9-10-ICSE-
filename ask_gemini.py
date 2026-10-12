import os
import sys

# Since src is a subfolder, we need to make sure Python can find our llm_module.
# We add the 'src' directory to Python's path so it knows where to look.
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.append(src_dir)

from llm_module.client import GeminiClient

def main():
    print("[INFO] Initializing Gemini AI...")
    
    try:
        # Create an instance of our GeminiClient
        client = GeminiClient()
    except ValueError as e:
        print(f"\n[ERROR] Setup Error: {e}")
        print("Please make sure you have created a .env file with your GEMINI_API_KEY.")
        sys.exit(1)
    
    # This is our "prompt" - the specific instructions or question we are sending to the AI model.
    prompt = (
        "You are a helpful high school teacher. "
        "Explain the concept of Photosynthesis in 3 simple bullet points "
        "suitable for a 9th-grade biology student."
    )
    
    print("\n[INFO] Sending the following prompt to the model:")
    print(f"\"{prompt}\"")
    print("\n[INFO] Waiting for the response...\n")
    
    try:
        # Call the API using our client
        answer = client.ask_question(prompt)
        
        print("="*40)
        print("GEMINI RESPONSE")
        print("="*40)
        print(answer)
        print("="*40)
        
    except Exception as e:
        print(f"\n[ERROR] Something went wrong during the API call: {e}")

if __name__ == "__main__":
    main()
