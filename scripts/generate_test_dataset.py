import os
import time
import urllib.request

import numpy as np
from PIL import Image

OUTPUT_DIR = "test_images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. Download realistic dummy images from picsum
categories = [
    ("heritage", 10),
    ("animals", 10),
    ("nature", 10),
    ("urban", 10),
    ("indoor", 10),
    ("food", 5),
]

print("Downloading realistic test images...")
img_idx = 1
for cat, count in categories:
    cat_dir = os.path.join(OUTPUT_DIR, cat)
    os.makedirs(cat_dir, exist_ok=True)
    for i in range(count):
        filename = f"{cat}_{i+1}.jpg"
        filepath = os.path.join(cat_dir, filename)
        if not os.path.exists(filepath):
            try:
                # Add random seed to get different images
                url = f"https://picsum.photos/seed/{cat}{i}/800/600"
                urllib.request.urlretrieve(url, filepath)
                print(f"Downloaded {filepath}")
                time.sleep(0.5)
            except Exception as e:
                print(f"Failed to download {filepath}: {e}")
        img_idx += 1

# 2. Generate failure modes
print("Generating failure mode images...")
fail_dir = os.path.join(OUTPUT_DIR, "failure_modes")
os.makedirs(fail_dir, exist_ok=True)

# Completely black
img_black = Image.new("RGB", (800, 600), color="black")
img_black.save(os.path.join(fail_dir, "black.jpg"))

# Completely white
img_white = Image.new("RGB", (800, 600), color="white")
img_white.save(os.path.join(fail_dir, "white.jpg"))

# Noise
noise = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
img_noise = Image.fromarray(noise, "RGB")
img_noise.save(os.path.join(fail_dir, "noise.jpg"))

# Blurry (Resize down and up)
try:
    img = Image.open(os.path.join(OUTPUT_DIR, "nature", "nature_1.jpg"))
    img_small = img.resize((10, 10), resample=Image.NEAREST)
    img_blurry = img_small.resize((800, 600), resample=Image.BILINEAR)
    img_blurry.save(os.path.join(fail_dir, "blurry.jpg"))
except:
    pass

# Tiny
img_tiny = Image.new("RGB", (10, 10), color="red")
img_tiny.save(os.path.join(fail_dir, "tiny.jpg"))

# Huge
# We won't generate a massive file to save space, but maybe a large one
img_huge = Image.new("RGB", (4000, 4000), color="blue")
img_huge.save(os.path.join(fail_dir, "huge.jpg"))

# Unsupported format (txt disguised as jpg)
with open(os.path.join(fail_dir, "corrupted.jpg"), "w") as f:
    f.write("This is not an image.")

print("Test dataset generated.")
