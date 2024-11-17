# Music Album Generator and YouTube Uploader

This project automates the creation of music albums based on user-provided descriptions. It uses ai and generates songs, creates cover images, combines them into a video, and uploads the final product to YouTube with an ai generated title and description.

# Visit my [YouTube channel](https://www.youtube.com/@while_True_break/videos) to see albums generated by this tool

## Features
- **Music Generation**
Uses [Suno API](https://github.com/gcui-art/suno-api) to host a server that is called through this program to generate songs using Suno Ai and download them.
- **Cover Image Creation** Uses the OpenAI API to create a 1024x1024 cover image which is then cut up and put back into the OpenAI API a couple more times to generate a 16:9 image.
- **Video Compilation**: Combines audio tracks and cover image into a cohesive video file and stores timestamps of each song.
- **YouTube Upload**: Uses the OpenAI API to generate a unique title and description (including a quote, song names, and timestamps) and uses the Youtube Data Api v3 to upload it.
- **Automated Loop**: Can produce multiple albums in a loop, and also uses generative ai so slightly change user inputs each time to ensure unique albums.

 ### The script will prompt you for:
- Album Music Description: Text prompt for generating songs.
- Album Cover Description: Text prompt for creating the cover image.
- Number of Iterations: How many songs to generate per album / 2.
- Number of Albums: How many albums to create in total.
  
If you leave any input blank, default values will be used.
  
## Installation and Usage

1. **Clone Suno API server linked above and get it running**
2. **Clone this Repository**
3. **Install Dependencies**
4. **Set Up Environment Variables**
   Create .env file and add openai api key.
5. **Configure Google API Credentials**
   - Enable the YouTube Data API v3 in your Google Developers Console.
   - Download client_secret.json and place it in the project root directory.
6. **Run 'Python app.py'

Sample outputs:
https://www.youtube.com/@while_True_break/videos



