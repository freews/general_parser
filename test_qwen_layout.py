import os
import sys
from pathlib import Path
from deepseek_api.qwen_ocr import QwenOCR

# Test Setup
IMAGE_DIR = "output_nvmebase/page_images"
TEST_PAGE = "0216_page.png" # Section 5.2.5 seems to be around here
IMAGE_PATH = os.path.join(IMAGE_DIR, TEST_PAGE)

def main():
    print(f"Testing Qwen OCR Layout on {IMAGE_PATH}")
    
    if not os.path.exists(IMAGE_PATH):
        print("Image not found! Please ensure PDF to PNG conversion is done.")
        return

    # Direct API Debugging
    import requests
    import base64
    
    url = "http://localhost:11434/api/generate"
    with open(IMAGE_PATH, 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode('utf-8')
        
    models = ["qwen3-vl:32b-instruct-q4_K_M", "qwen3-vl:8b"]
    
    for model_name in models:
        print(f"\n\n==========================================")
        print(f"Testing Model: {model_name}")
        print(f"==========================================\n")
        
        data = {
            "model": model_name,
            "prompt": "You are a layout analysis expert. Ignore all other text content. Identify ONLY Tables, Figures, and Section Titles. Return the result strictly as a JSON list with 'type', 'title', and 'bbox' [x1, y1, x2, y2] (0-1000 scale). Do not include any explanations.",
            "images": [img_b64],
            "stream": False
        }
        
        print("Debug: Sending direct request to Ollama...")
        resp = requests.post(url, json=data)
        print(f"Status Code: {resp.status_code}")
        try:
            if 'error' in resp.json():
                print("Error from API:", resp.json()['error'])
            else:
                print("\n=== Response Content ===\n")
                print(resp.json()['response'])
                print("\n========================\n")
        except:
            print("Raw text:", resp.text)
            
    return # End after loop, skip class wrapper usage for this test

if __name__ == "__main__":
    main()
