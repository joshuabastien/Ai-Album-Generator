import requests

def download_mp3(url, output_path):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(output_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        print(f"Download complete: {output_path}")
    else:
        print(f"Failed to download file. Status code: {response.status_code}")

if __name__ == "__main__":
    url = "https://audiopipe.suno.ai/?item_id=506f4d10-979d-496d-9e63-028c793b28c5"
    output_path = "songs/downloaded_song.mp3"
    download_mp3(url, output_path)