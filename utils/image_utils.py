from io import BytesIO
from functools import lru_cache
import requests
from PIL import Image
from customtkinter import CTkImage

@lru_cache(5)
def load_image_from_url(url, fallback_path, size):
    if url:
        response = requests.get(url)
        if response.status_code == 200:
            img_data = BytesIO(response.content)
            img = Image.open(img_data)
        else:
            img = Image.open(fallback_path)
    else:
        img = Image.open(fallback_path)
    img = img.resize(size)
    return CTkImage(dark_image=img, light_image=img, size=size)