import pandas as pd
import requests
import os
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

# CONFIGURATION
TARGET_DIR = "background_images"
TARGET_COUNT = 10000
# Unsplash allows resizing via URL parameters
WIDTH = 1920
HEIGHT = 1080
QUALITY = 80

# Create directory
if not os.path.exists(TARGET_DIR):
    os.makedirs(TARGET_DIR)

def download_image(url_data):
    index, photo_id, raw_url = url_data
    
    # Construct the resize URL
    # Unsplash raw URLs allow adding parameters like &w=1920&h=1080&fit=crop
    download_url = f"{raw_url}?w={WIDTH}&h={HEIGHT}&fit=crop&q={QUALITY}"
    
    try:
        response = requests.get(download_url, timeout=10)
        if response.status_code == 200:
            with open(f"{TARGET_DIR}/{index}_{photo_id}.jpg", 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        return False
    return False

# 1. Load the dataset (Assuming you have the 'photos.tsv000' from Unsplash Lite)
# You can download it here: https://unsplash.com/data
print("Loading dataset...")
# Note: You might need to adjust the filename if you downloaded the full version
try:
    df = pd.read_csv('./Layout/photos.csv000', sep='\t', header=0)
    
    # Select first 10k unique photos
    subset = df[['photo_id', 'photo_image_url']].head(TARGET_COUNT)
    
    print(f"Found {len(subset)} images. Starting download...")
    
    # Prepare data for threading
    tasks = []
    for idx, row in subset.iterrows():
        tasks.append((idx, row['photo_id'], row['photo_image_url']))

    # Download in parallel (faster)
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(tqdm(executor.map(download_image, tasks), total=len(tasks)))
        
    print(f"Download complete. Successfully downloaded {sum(results)} images.")

except FileNotFoundError:
    print("Error: 'photos.tsv000' not found. Please download the Unsplash Lite dataset first.")