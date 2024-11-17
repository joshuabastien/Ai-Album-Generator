import requests
import time

def download_mp3(url, output_path, retries=3):
    for attempt in range(retries):
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(output_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            file.write(chunk)
                print(f"Download complete: {output_path}")
                return
            else:
                print(f"Failed to download file. Status code: {response.status_code}")
                break  # Exit if the response status is not 200
        except requests.exceptions.ChunkedEncodingError as e:
            print(f"Attempt {attempt + 1} failed due to chunked encoding error. Retrying...")
            time.sleep(1)
    print(f"Failed to download {url} after {retries} attempts.")