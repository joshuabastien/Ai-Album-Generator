import os
from dotenv import load_dotenv
from openai import OpenAI
import requests

# Load environment variables from .env file
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("API key not found. Please set the 'OPENAI_API_KEY' environment variable.")

# Instantiate the OpenAI client
client = OpenAI(api_key=api_key)

# Function to generate an image using OpenAI API
def generate_image(prompt):
    # Generate the image using the new client method
    response = client.images.generate(
        prompt=prompt,
        n=1,
        size="1024x1024"
    )
    # Convert response to dictionary if needed and access URL
    image_url = response.model_dump()["data"][0]["url"]
    return image_url

# Function to save the image to the covers folder
def save_image(image_url, file_path):
    response = requests.get(image_url)
    if response.status_code == 200:
        with open(file_path, 'wb') as f:
            f.write(response.content)
    else:
        print("Failed to retrieve image")

# Main function
def main():
    prompt = "A beautiful sunset over the mountains"
    image_url = generate_image(prompt)
    covers_folder = 'covers'
    os.makedirs(covers_folder, exist_ok=True)
    file_path = os.path.join(covers_folder, 'cover_image.png')
    save_image(image_url, file_path)
    print(f"Image saved to {file_path}")

if __name__ == "__main__":
    main()
