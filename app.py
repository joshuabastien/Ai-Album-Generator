import os
import time
from callapi import generate_audio_by_prompt, get_audio_information
from getcover import generate_image, save_image
from moviepy.editor import AudioFileClip, ImageClip
from downloadsong import download_mp3

# Create necessary directories
os.makedirs("songs", exist_ok=True)
os.makedirs("covers", exist_ok=True)
os.makedirs("video", exist_ok=True)

def generate_song(description):
    # Generate audio based on the description
    data = generate_audio_by_prompt({
        "prompt": description,
        "make_instrumental": True,
        "wait_audio": False
    })

    # Extract song IDs and check their status until streaming is available
    ids = f"{data[0]['id']},{data[1]['id']}"
    print(f"Generated song IDs: {ids}")

    # Wait until the songs are ready
    for _ in range(60):
        data = get_audio_information(ids)
        if data[0]["status"] == 'streaming':
            audio_url_1 = data[0]['audio_url']
            audio_url_2 = data[1]['audio_url']

            output_path_1 = f"songs/{data[0]['id']}_song.mp3"
            output_path_2 = f"songs/{data[1]['id']}_song.mp3"

            download_mp3(audio_url_1, output_path_1)
            download_mp3(audio_url_2, output_path_2)

            print("Songs downloaded.")
            return [output_path_1, output_path_2]
        time.sleep(5)
    raise Exception("Audio generation timed out.")

def create_cover_image(description):
    # Generate a cover image
    image_url = generate_image(description)
    cover_path = "covers/cover_image.png"
    save_image(image_url, cover_path)
    print("Cover image created.")
    return cover_path

def create_video(audio_path, cover_path, output_path):
    # Load the audio and image
    audio_clip = AudioFileClip(audio_path)
    image_clip = ImageClip(cover_path)

    # Set the duration of the image to match the audio
    image_clip = image_clip.set_duration(audio_clip.duration)
    image_clip = image_clip.set_audio(audio_clip)

    # Save to the video folder
    image_clip.write_videofile(output_path, codec="libx264", fps=24)
    print(f"Video saved to {output_path}")

def main():
    description = input("Enter a description for the song: ")
    
    # Generate songs based on the description
    audio_files = generate_song(description)
    cover_path = create_cover_image(description)

    # Create a video for each song
    for i, audio_path in enumerate(audio_files, start=1):
        output_path = f"video/{i}_video.mp4"
        create_video(audio_path, cover_path, output_path)

if __name__ == "__main__":
    main()
