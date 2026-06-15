
import os
import sys
import requests
from io import BytesIO
from PIL import Image

def reproduce():
    # Create a dummy image
    img = Image.new('RGB', (224, 224), color = 'red')
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)

    url = 'http://localhost:8000/api/predict/'
    files = {'image': ('test.jpg', img_byte_arr, 'image/jpeg')}
    
    print(f"Sending POST request to {url}...")
    try:
        response = requests.post(url, files=files)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 500:
            print("Successfully reproduced 500 error.")
            # Print the first 20 lines of the content if it's HTML (Django debug page)
            print("Response Content (truncated):")
            print(response.text[:2000]) 
            
            # Save full traceback to a file for analysis
            with open('traceback.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("Full traceback saved to traceback.html")
        else:
            print("Did not reproduce 500 error.")
            print(response.text[:500])
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    reproduce()
