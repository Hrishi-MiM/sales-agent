import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

def generate_voice(text):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/Xb7hH8MSUJpSbSDYk0k2"
    
    # Use environment variable for the API key for security reasons
    api_key = os.getenv("ELEVENLABS_API_KEY")
    headers = {
        'xi-api-key': api_key,  # Use API key from environmenta
        'Content-Type': 'application/json',
    }
    data = {
        "text": text,
        "voice_settings": {
            "stability": 0.1,
            "similarity_boost": 0.3,
            "style": 0.2,
            "optimize_streaming_latency": "0",
            "output_format": "mp3_22050_32"
        }
    }

    # Make the API request
    response = requests.post(url, headers=headers, json=data)

    # Check for success
    if response.status_code == 200:
        if response.headers['Content-Type'].startswith('audio/'):
            # If the response contains audio, save it to a file
            file_path = 'output_audio.mp3'
            with open(file_path, 'wb') as f:
                f.write(response.content)
            return file_path
        elif response.headers['Content-Type'] == 'application/json':
            try:
                json_response = response.json()
                return json_response.get('url')  # Return the URL if available
            except ValueError:
                raise Exception("Failed to parse JSON response")
        else:
            raise Exception(f"Unexpected content type: {response.headers['Content-Type']}")
    else:
        # Log and raise exception if the status code is not successful
        raise Exception(f"Error: {response.status_code}, {response.text}")

# Example usage
if __name__ == "__main__":
    text_to_speak = "Hello, how can I help you today?"
    try:
        audio_url_or_file = generate_voice(text_to_speak)
    except Exception as e:
        print("An error occurred:", str(e))
