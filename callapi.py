import time
import requests
from downloadsong import download_mp3

base_url = 'http://localhost:3000'


def custom_generate_audio(payload):
    url = f"{base_url}/api/custom_generate"
    response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
    return response.json()


def extend_audio(payload):
    url = f"{base_url}/api/extend_audio"
    response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
    return response.json()

def generate_audio_by_prompt(payload):
    url = f"{base_url}/api/generate"
    response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
    return response.json()


def get_audio_information(audio_ids):
    url = f"{base_url}/api/get?ids={audio_ids}"
    response = requests.get(url)
    return response.json()


def get_quota_information():
    url = f"{base_url}/api/get_limit"
    response = requests.get(url)
    return response.json()

def get_clip(clip_id):
    url = f"{base_url}/api/clip?id={clip_id}"
    response = requests.get(url)
    return response.json()

def generate_whole_song(clip_id, payload):
    payloyd = {"clip_id": clip_id}
    url = f"{base_url}/api/concat"
    response = requests.post(url, json=payload)
    return response.json()


if __name__ == '__main__':
    data = generate_audio_by_prompt({
        "prompt": "Korean cafe jazz music, fast",
        "make_instrumental": True,
        "wait_audio": False
    })

if __name__ == '__main__':
    data = generate_audio_by_prompt({
        "prompt": "Korean cafe jazz music, fast",
        "make_instrumental": True,
        "wait_audio": False
    })

    ids = f"{data[0]['id']},{data[1]['id']}"
    print(f"ids: {ids}")

    for _ in range(60):
        data = get_audio_information(ids)
        if data[0]["status"] == 'streaming':
            audio_url_1 = data[0]['audio_url']
            audio_url_2 = data[1]['audio_url']

            print(f"{data[0]['id']} ==> {audio_url_1}")
            print(f"{data[1]['id']} ==> {audio_url_2}")

            # Download the audio files
            output_path_1 = f"songs/{data[0]['id']}_song.mp3"
            output_path_2 = f"songs/{data[1]['id']}_song.mp3"
            download_mp3(audio_url_1, output_path_1)
            download_mp3(audio_url_2, output_path_2)
            break
        time.sleep(5)

    print("DONE")
