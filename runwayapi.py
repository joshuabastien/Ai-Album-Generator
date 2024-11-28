import os
import requests
from dotenv import load_dotenv
import base64
import logging
import time
from pathlib import Path
from PIL import Image
from io import BytesIO
from typing import Union, List, Literal, TypedDict
from  uploadtonetlify import verify_image_url, trigger_netlify_build, upload_to_github

# Define the ImagePosition schema
class ImagePosition(TypedDict):
    uri: str
    position: Literal["first", "last"]

PromptImage = Union[str, List[ImagePosition]]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from the .env file
load_dotenv()

def generate_video_with_cover(image_path, prompt_text='Static unmoving camera, dynamic motion within the frame', model='gen3a_turbo', download_folder="video", max_retries=60, delay=10):
    """
    Submits a video generation task, polls for its completion, downloads the video, and returns the video path.

    Parameters:
        image_path (str): Path to the local PNG image file.
        prompt_text (str): Text prompt to guide the video generation.
        model (str, optional): The model to use for generation. Defaults to 'gen3a_turbo'.
        download_folder (str, optional): The folder to save the downloaded video. Defaults to "video".
        max_retries (int, optional): Maximum number of polling attempts. Defaults to 60.
        delay (int, optional): Delay in seconds between polling attempts. Defaults to 10.

    Returns:
        str: The file path where the video was saved.

    Raises:
        FileNotFoundError: If the image file does not exist.
        ValueError: If the API key is not found or image format is unsupported.
        RuntimeError: If the task fails or is cancelled.
        TimeoutError: If the task does not complete within the allowed retries.
        requests.exceptions.HTTPError: If any API request fails.
    """
    # Step 1: Submit the Video Generation Task
    task_id = submit_video_generation_task(image_path, prompt_text, model)

    # Step 2: Poll for Task Completion
    task_info = poll_task_status(task_id, max_retries, delay)

    # Step 3: Extract the Output Video URL
    video_url = extract_video_url(task_info)

    # Step 4: Download the Video
    video_path = download_video(video_url, task_id, download_folder)

    # Step 5: Return the Video Path
    return video_path

def submit_video_generation_task(image_path: str, prompt_text: str, model: str) -> dict:
    """
    Submits a video generation task to the RunwayML API.

    Parameters:
        image_path (str): Path to the local PNG image file.
        prompt_text (str): Text prompt to guide the video generation.
        model (str): The model to use for generation.

    Returns:
        dict: The response from the API.
    """
    api_key = os.getenv("RUNWAYML_API_KEY")
    if not api_key:
        raise ValueError("API key not found. Set the RUNWAYML_API_KEY environment variable.")

    if not os.path.isfile(image_path) or not image_path.lower().endswith(".png"):
        raise FileNotFoundError(f"Invalid PNG file at: {image_path}")

    # Upload the image to GitHub repository
    print("Uploading image to GitHub...")
    uploaded_url = upload_to_github(image_path)
    if not uploaded_url:
        raise RuntimeError("Failed to upload the image to GitHub.")
    print(f"Image uploaded to GitHub: {uploaded_url}")

    # Trigger Netlify build
    print("Triggering Netlify build...")
    deploy_id = trigger_netlify_build()
    if not deploy_id:
        raise RuntimeError("Failed to trigger Netlify build.")

    # Wait for Netlify deploy
    delay_seconds = 120  # Adjust this delay as needed based on typical deployment times
    print(f"Waiting for {delay_seconds} seconds to allow Netlify deployment...")
    time.sleep(delay_seconds)

    # Construct the correct public URL dynamically
    base_path = uploaded_url.split("/main/")[-1]  # Extract the relative path (e.g., "public/uploads/landscape_cover.png")
    prompt_image_url = f"https://joshuabastien.com/{base_path.replace('public/', '')}"  # Remove "public/" for Netlify path

    # Verify the uploaded image URL
    print(f"Attempting to verify the image URL: {prompt_image_url}")
    if not verify_image_url(prompt_image_url, retries=30, delay=30):
        raise RuntimeError(f"Uploaded image URL not accessible: {prompt_image_url}")

    # Construct the payload
    payload = {
        "promptImage": [
            {"uri": prompt_image_url, "position": "first"},
            {"uri": prompt_image_url, "position": "last"}],
        "promptText": prompt_text,
        "model": model,
        "duration": 5
    }
    # Send the request
    url = "https://api.dev.runwayml.com/v1/image_to_video"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "X-Runway-Version": "2024-11-06"
    }


    try:
        logger.info("Sending POST request to RunwayML API to generate video...")
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
        logger.info("Video generation task submitted successfully.")
        task_info = response.json()
        task_id = task_info.get("id")
        if not task_id:
            logger.error("Task ID not found in the response.")
            raise ValueError("Task ID not found in the response.")
        return task_id
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err} - Response: {response.text}")
        raise
    except Exception as err:
        logger.error(f"An unexpected error occurred: {err}")
        raise

def poll_task_status(task_id, max_retries=60, delay=10):
    """
    Polls the RunwayML API to check the status of a task until it succeeds or fails.

    Parameters:
        task_id (str): The ID of the task to check.
        max_retries (int, optional): Maximum number of polling attempts. Defaults to 60.
        delay (int, optional): Delay in seconds between polling attempts. Defaults to 10.

    Returns:
        dict: The task information once it has succeeded.

    Raises:
        TimeoutError: If the task does not complete within the maximum number of retries.
        RuntimeError: If the task fails or is cancelled.
        ValueError: If the API key is not found.
        requests.exceptions.HTTPError: If the API request fails.
    """
    api_key = os.getenv("RUNWAYML_API_KEY")
    if not api_key:
        logger.error("API key not found. Please set the RUNWAYML_API_KEY environment variable in your .env file.")
        raise ValueError("API key not found. Please set the RUNWAYML_API_KEY environment variable in your .env file.")

    url = f"https://api.dev.runwayml.com/v1/tasks/{task_id}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Runway-Version": "2024-11-06"
    }

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Polling task status (Attempt {attempt}/{max_retries})...")
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            task_info = response.json()
            status = task_info.get("status")
            logger.info(f"Task Status: {status}")

            if status == "SUCCEEDED":
                logger.info("Task succeeded.")
                return task_info
            elif status in ["FAILED", "CANCELLED"]:
                logger.error(f"Task ended with status: {status}")
                raise RuntimeError(f"Task ended with status: {status}")
            else:
                logger.info(f"Task is still in status: {status}. Waiting for {delay} seconds before next check.")
                time.sleep(delay)
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred while checking task status: {http_err} - Response: {response.text}")
            raise
        except Exception as err:
            logger.error(f"An unexpected error occurred while checking task status: {err}")
            raise

    logger.error(f"Task did not complete within {max_retries * delay} seconds.")
    raise TimeoutError(f"Task did not complete within {max_retries * delay} seconds.")

def extract_video_url(task_info):
    """
    Extracts the first output URL from the task information.

    Parameters:
        task_info (dict): The task information dictionary.

    Returns:
        str: The first output URL.

    Raises:
        ValueError: If no output URLs are found.
    """
    output = task_info.get("output")
    if not output or not isinstance(output, list):
        logger.error("No output URLs found in the task information.")
        raise ValueError("No output URLs found in the task information.")
    return output[0]

def download_video(video_url, task_id, download_folder="video"):
    """
    Downloads a video from the given URL and saves it to the specified folder with a unique name.

    Parameters:
        video_url (str): The URL of the video to download.
        task_id (str): The ID of the task, used to generate a unique filename.
        download_folder (str, optional): The folder to save the downloaded video. Defaults to "video".

    Returns:
        str: The file path where the video was saved.

    Raises:
        requests.exceptions.HTTPError: If the download request fails.
        Exception: For any other errors during download or file saving.
    """
    # Ensure the download folder exists
    Path(download_folder).mkdir(parents=True, exist_ok=True)
    logger.info(f"Download folder '{download_folder}' is ready.")

    # Determine the file extension from the URL
    file_extension = os.path.splitext(video_url)[1].split('?')[0]  # Removes query parameters
    if not file_extension:
        file_extension = ".mp4"  # Default extension
    else:
        # Validate that the extension is a common video format
        supported_extensions = [".mp4", ".mov", ".avi", ".mkv"]
        if file_extension.lower() not in supported_extensions:
            logger.warning(f"Uncommon file extension '{file_extension}' detected. Defaulting to '.mp4'.")
            file_extension = ".mp4"

    # Generate a unique filename using the task ID
    filename = f"{task_id}{file_extension}"
    file_path = os.path.join(download_folder, filename)

    try:
        logger.info(f"Starting download of video from {video_url}...")
        with requests.get(video_url, stream=True) as r:
            r.raise_for_status()
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        logger.info(f"Video downloaded successfully and saved to {file_path}.")
        return file_path
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred during video download: {http_err} - Response: {r.text}")
        raise
    except Exception as err:
        logger.error(f"An unexpected error occurred during video download: {err}")
        raise