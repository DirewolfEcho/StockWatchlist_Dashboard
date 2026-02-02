import google.generativeai as genai
import os

key = "AIzaSyCX11m_RJxcifuksECiB_krrf8IkntGQiQ"
genai.configure(api_key=key)

print("Listing models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error listing models: {e}")
