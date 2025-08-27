import asyncio
from random import randint
from PIL import Image
import requests
from dotenv import load_dotenv  # Use load_dotenv instead of get_key
import os
from time import sleep

def open_image(prompt):
    folder_path = "Data"
    prompt = prompt.replace(" ", "_")

    files = [f"{prompt}{i}.jpg" for i in range(1, 5)]

    for jpg_file in files:
        image_path = os.path.join(folder_path, jpg_file)

        try:
            img = Image.open(image_path)
            print(f"Opening image: {image_path}")
            img.show()
            sleep(1)
        except IOError:
            print(f"Unable to open {image_path}")

# Load environment variables explicitly
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))  # Adjust path to root .env
api_key = os.getenv("HuggingFaceAPIKey")
if not api_key:
    print("HuggingFaceAPIKey not found in .env. Please add it to proceed.")
    exit(1)

API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {api_key}"}

async def query(payload):
    response = await asyncio.to_thread(requests.post, API_URL, headers=headers, json=payload)
    return response.content

async def generate_images(prompt: str):
    tasks = []

    for _ in range(4):
        payload = {
            "inputs": f"{prompt}, quality=4K, sharpness=maximum, Ultra High details, high resolution, seed={randint(0, 1000000)}",
        }
        task = asyncio.create_task(query(payload))
        tasks.append(task)

    image_bytes_list = await asyncio.gather(*tasks)

    for i, image_bytes in enumerate(image_bytes_list):
        with open(f"Data/{prompt.replace(' ', '_')}{i + 1}.jpg", "wb") as f:
            f.write(image_bytes)

def GenerateImages(prompt: str):
    asyncio.run(generate_images(prompt))
    open_image(prompt)

while True:
    try:
        with open("Frontend/Files/ImageGeneration.data", "r") as f:
            Data: str = f.read()

        # Handle cases where Data doesn't split into two values
        data_parts = Data.split(",")
        Prompt = data_parts[0].strip() if data_parts else ""
        Status = data_parts[1].strip() if len(data_parts) > 1 else "False"

        if Status == "True":
            print("Generating Images ...")
            ImageStatus = GenerateImages(prompt=Prompt)

            with open("Frontend/Files/ImageGeneration.data", "w") as f:
                f.write("False,False")
                break

        else:
            sleep(1)

    except Exception as e:
        print(f"Error: {e}")
        sleep(1)