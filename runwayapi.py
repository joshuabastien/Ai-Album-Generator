import os
import time
import base64
import requests
from runwayml import RunwayML
from runwayml.types import TaskRetrieveResponse, ImageToVideoCreateResponse
import runwayml

def generate_video_with_cover(cover_path, prompt_text='Dynamic motion', duration=5):

    print(runwayml.__version__)

    # Initialize the RunwayML client with your API key
    client = RunwayML(
        api_key=os.environ.get("RUNWAYML_API_SECRET"),
    )

    # Encode the image to base64
    with open(cover_path, "rb") as f:
        base64_image = base64.b64encode(f.read()).decode("utf-8")

    # Create a new image-to-video task using the "gen3a_turbo" model
    image_to_video: ImageToVideoCreateResponse = client.image_to_video.create(
        model='gen3a_turbo',
        prompt_image=f"data:image/png;base64,{base64_image}",
        prompt_text=prompt_text,
        duration=duration,  # Set the duration to 5 seconds
    )
    task_id = image_to_video.id

    # Poll the task until it's complete
    time.sleep(10)  # Wait for ten seconds before polling
    task: TaskRetrieveResponse = client.tasks.retrieve(task_id)
    while task.status not in ['SUCCEEDED', 'FAILED']:
        time.sleep(10)  # Wait for ten seconds before polling
        task = client.tasks.retrieve(task_id)

    print('Task complete:', task)

    # Check if the task succeeded
    if task.status == 'SUCCEEDED' and task.output:
        output_url = task.output[0]  # Get the first output URL

        # Ensure the 'video/' directory exists
        os.makedirs('video', exist_ok=True)

        # Download the video from the output URL
        response = requests.get(output_url)
        if response.status_code == 200:
            # Use a unique filename to avoid overwriting files
            video_filename = f'output_{task_id}.mp4'
            video_path = os.path.join('video', video_filename)
            with open(video_path, 'wb') as f:
                f.write(response.content)
            print(f'Video saved to {video_path}')
        else:
            print(f'Failed to download video, status code: {response.status_code}')
    else:
        print('Task failed or no output was generated.')