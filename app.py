import os
import time
from callapi import generate_audio_by_prompt, get_audio_information
from openaiapi import generate_image, save_image, generate_video_title, generate_video_description, extend_cover_image, edit_cover_description, edit_description
from runwayapi import generate_video_with_cover
from downloadsong import download_mp3
from pydub import AudioSegment
from uploadtoyoutube import get_authenticated_service, upload_video
import shutil
from datetime import datetime
import os
import time
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.editor import concatenate_videoclips, ImageClip

# Create necessary directories
os.makedirs("songs", exist_ok=True)
os.makedirs("covers", exist_ok=True)
os.makedirs("video", exist_ok=True)
os.makedirs("audio", exist_ok=True)

def generate_song(description):
    # Generate audio based on the description
    data = generate_audio_by_prompt({
        "prompt": description,
        "make_instrumental": True,
        "wait_audio": False
    })
    
    # Check if the API returned the expected structure
    if not data or len(data) < 2:
        raise ValueError("The API did not return two songs as expected.")

    # Extract song IDs for the two generated songs
    ids = f"{data[0]['id']},{data[1]['id']}"
    print(f"Generated song IDs: {ids}")

    # Initialize paths for the audio files to be downloaded
    audio_files = []
    max_attempts = 300  # Number of retries for checking the streaming status

    # Wait until the songs are ready for streaming
    for attempt in range(max_attempts):
        data = get_audio_information(ids)

        # Check if both songs are ready for streaming
        if all(song.get("status") == 'streaming' for song in data[:2]):
            for song in data[:2]:
                audio_url = song['audio_url']
                output_path = f"songs/{song['id']}_song.mp3"
                download_mp3(audio_url, output_path)
                audio_files.append(output_path)

            print("Songs downloaded.")
            return audio_files  # Return list of downloaded song paths

        # Wait for a few seconds before trying again
        time.sleep(5)
    
    # If songs are not ready within the time limit, raise an exception
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

def combine_songs(audio_files, fade_duration=1000):
    combined_audio = AudioSegment.empty()
    timestamps = []
    current_time = 0

    for audio_file in audio_files:
        song = AudioSegment.from_file(audio_file)

        # Apply fade out only
        faded_song = song.fade_out(fade_duration)

        combined_audio += faded_song
        timestamps.append(current_time)
        current_time += len(faded_song) / 1000  # Convert milliseconds to seconds

    # Save the combined audio
    combined_audio_path = "audio/combined_audio_with_fade_out.mp3"
    combined_audio.export(combined_audio_path, format="mp3")
    
    return combined_audio_path, timestamps

def clear_folder(folder_path):
    """Delete all files in the specified folder."""
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")

def filter_short_songs(audio_files, min_duration=30):
    """Filter out audio files under a specified minimum duration (in seconds)."""
    valid_audio_files = []
    for file in audio_files:
        audio = AudioSegment.from_file(file)
        duration_seconds = len(audio) / 1000  # pydub returns duration in milliseconds
        if duration_seconds >= min_duration:
            valid_audio_files.append(file)
    return valid_audio_files

def main_loop(description, cover_description, num_songs):
    # Define folder paths
    folders_to_clear = ['audio', 'covers', 'songs']
    # Clear each folder
    for folder in folders_to_clear:
        clear_folder(folder)
    # Create the cover image using the separate cover description
    cover_path = create_cover_image(cover_description)

    time.sleep(2) 

    # Extend the cover image
    cover_path = extend_cover_image(cover_path)

    time.sleep(2)

    # Generate the video with the given cover image
    video_path = generate_video_with_cover(cover_path)

    if video_path:
        print(f"Video created and saved at {video_path}")
    else:
        print("Video generation failed.")
        return

    # Generate songs in separate calls, each call returns 2 songs
    audio_files = []
    for _ in range(num_songs):  # Repeat to get songs
        audio_files.extend(generate_song(description))
    
    # Filter out songs under 30 seconds
    audio_files = filter_short_songs(audio_files, min_duration=30)

    # Combine all audio files into a single file and get timestamps
    combined_audio_path, timestamps_in_seconds = combine_songs(audio_files)
    timestamps_in_minutes = []
    for timestamp in timestamps_in_seconds:
        minutes = int(timestamp // 60)
        seconds = int(timestamp % 60)
        timestamps_in_minutes.append(f"{minutes:02}:{seconds:02}")

    # Load audio and video
    audio_clip = AudioFileClip(combined_audio_path)
    audio_duration = audio_clip.duration
    print(f"Audio duration: {audio_duration} seconds")

    video_clip = VideoFileClip(video_path)
    video_duration = video_clip.duration
    print(f"Video duration: {video_duration} seconds")

    # Calculate repetitions
    num_repeats = int(audio_duration // video_duration) + 1
    print(f"Number of repeats needed: {num_repeats}")

    # Repeat video to match audio duration
    repeated_clips = [video_clip] * num_repeats
    final_video_without_audio = concatenate_videoclips(repeated_clips).subclip(0, audio_duration)

    # Save video without audio
    temp_video_path = "video/temp_video.mp4"
    final_video_without_audio.write_videofile(temp_video_path, codec="libx264")
    print(f"Temporary video created and saved at {temp_video_path}")

    # Load the saved video and add audio
    final_video_clip = VideoFileClip(temp_video_path).set_audio(audio_clip)

    # Save the final video with audio
    final_video_path = "video/final_video_with_audio.mp4"
    final_video_clip.write_videofile(final_video_path, codec="libx264", audio_codec="mp3")
    print(f"Final video with audio created and saved at {final_video_path}")

    # Print or return the timestamps for each song
    print("Timestamps for each song in the combined file:", timestamps_in_minutes)

    # Generate the title, description, and tags for the video
    video_title = generate_video_title(description, cover_description)
    video_description = generate_video_description(description, video_title, timestamps_in_minutes)

    # Print the generated information
    print(f"Generated Video Title: {video_title}")
    print(f"Generated Video Description: {video_description}")

    text_filename = video_path.replace('.mp4', '.txt')
    text_output_path = f"{text_filename}"

    # Write the video title and description into the text file
    with open(text_output_path, 'w', encoding='utf-8') as file:
        file.write(f"{video_title}\n\n{video_description}")

    # YouTube upload section
    youtube = get_authenticated_service()
    title = video_title
    description = video_description
    category = '10'  # Music Category
    tags = ['lofi', 'jazz', 'study']

    # Upload video to YouTube
    upload_video(youtube, final_video_path, title, description, category, tags)

def main():
    # Get a description for the album's music
    description = input("Enter a description for the album music: ")
    if not description:  # Check if input is blank
        description = "lofi chill retro arcade"

    # Get a separate prompt for the cover image
    cover_description = input("Enter a description for the album cover image: ")
    if not cover_description:  # Check if input is blank
        cover_description = "tiltshift, miniture diorama, student study room, cozy, warm, low light"

    num_songs = input("Enter the number of iterations (2 songs per iteration, default is 9): ")
    if not num_songs:  # Check if input is blank
        num_songs = 9
    else:
        num_songs = int(num_songs)  # Convert to integer if input is not blank

    num_albums = input("Enter the number of albums you would like to make (default is 1): ")
    if not num_albums:  # Check if input is blank
        num_albums = 1
    else:
        num_albums = int(num_albums)  # Convert to integer if input is not blank

    for _ in range(num_albums):
        try:
            main_loop(description, cover_description, num_songs)
            print("Waiting before next iteration...")
            time.sleep(10)  # Adjust the delay as needed
            description = edit_description(description)
            cover_description = edit_cover_description(cover_description)
        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(60)  # Wait before retrying if there's an error

if __name__ == "__main__":
    main()