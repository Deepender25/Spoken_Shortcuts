import os
import sys
import requests
import zipfile
from tqdm import tqdm

MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
MODEL_DIR = "model"

def download_model():
    if os.path.exists(MODEL_DIR):
        print(f"Model directory '{MODEL_DIR}' already exists. Skipping download.")
        return

    print(f"Downloading model from {MODEL_URL}...")
    response = requests.get(MODEL_URL, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    zip_path = "model.zip"
    
    with open(zip_path, "wb") as file, tqdm(
        desc=zip_path,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)

    print("Extracting model...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(".")
        
    # Rename the extracted folder to 'model'
    extracted_folder = "vosk-model-small-en-us-0.15"
    if os.path.exists(extracted_folder):
        os.rename(extracted_folder, MODEL_DIR)
        
    os.remove(zip_path)
    print("Model setup complete.")

if __name__ == "__main__":
    download_model()
