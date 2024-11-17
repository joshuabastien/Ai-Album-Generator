import os
from dotenv import load_dotenv
from openai import OpenAI
import requests
from PIL import Image


# Load environment variables from .env file
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("API key not found. Please set the 'OPENAI_API_KEY' environment variable.")

# Instantiate the OpenAI client
client = OpenAI(api_key=api_key)

# Function to refine the image prompt using ChatGPT
def refine_prompt(initial_prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an assistant that specializes in refining image prompts for AI image generation. "
                                              "Take the user's prompt and make it more descriptive, clear, and visually vivid. You must not have the generated image include any text in it."
                                              "Consider details like color, setting, mood, style, and any specific elements that would enhance the quality of the generated image. "
                                              "Please avoid any text or themes that could be perceived as sensitive or inappropriate. "
                                              "Make the prompt safe and clear and don't use copyrighted material. Keep your response very short and only include the new prompt in your response."},
                {"role": "user", "content": initial_prompt}
            ]
        )
        refined_prompt = response.choices[0].message.content.strip()
        return refined_prompt
    except Exception as e:
        print(f"An error occurred in refine_prompt: {e}")
        return initial_prompt  # Return the initial prompt if an error occurs

# Function to generate an image using OpenAI API
def generate_image(initial_prompt):
    # First, refine the prompt
    refined_prompt = refine_prompt(initial_prompt)
    
    try:
        # Generate the image using the refined prompt
        response = client.images.generate(
            prompt=refined_prompt,
            n=1,
            size="1024x1024"
        )
        # Convert response to dictionary if needed and access URL
        image_url = response.model_dump()["data"][0]["url"]
        return image_url
    except Exception as e:
        print(f"An error occurred in generate_image: {e}")
        return None

# Function to save the image to the covers folder
def save_image(image_url, file_path):
    response = requests.get(image_url)
    if response.status_code == 200:
        with open(file_path, 'wb') as f:
            f.write(response.content)
    else:
        print("Failed to retrieve image")

# New function to generate a video title
def generate_video_title(description, cover_description):
    try:
        prompt = f"'{description}', {cover_description}."
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
            {"role": "system", "content":   "You will create an album title based on the users provided details about the album. The title should be 1 word "
                                            "relating to the descriptions the user has give you. The title should be experimental, you do not need to have it make complete sense. Some example titles (don't use these exactly) "
                                            " are: Sip, Bungeoppang, Trick, Coffee and Milk, Dice, Sofa. Have the title be something very specific and unique, do not use a generic term. Do not have the title include the word "
                                            " bop in it (such as *word*bop, just make the title the *word*). Do not surround the title in quotations, just provide the word."},

            {"role": "user", "content": prompt}
            ]
        )
        title = response.choices[0].message.content.strip()
        return title
    except Exception as e:
        print(f"An error occurred in generate_video_title: {e}")
        return None  # Or return a default title if desired

def generate_video_description(description, title, timestamps_in_minutes):
    try:
        prompt = f"Title: '{title}'. Description:'{description}'. Timestamps: {timestamps_in_minutes}."
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content":   "You will create a Youtube description for an album based on the details provided by the user."
                                                " You must follow a very strict formula. First, you will put a quote/saying about life or philosphy from a long time ago from"
                                                 " someone mostly unknown, then you take the timestamps that the user has given you, and put one per row, followed by the name of"
                                                 " the song that you will come up with. The names of the songs will be 1 word, and be related to the Title and Description the"
                                                 " User provides. For example, if the Title is Whiskey, then all the song names can be different alcoholic drinks. If the title is"
                                                 " Busan, then each song name can be famous streets or places in Busan. Or if the title is some food then each song can be related food."
                                                 " Each song must have a unique title, do not repeat. Do not add ANY extra information, just the quote, timestamps, and song names."},

                {"role": "user", "content": prompt}
            ]
        )
        video_description = response.choices[0].message.content.strip()
        return video_description
    except Exception as e:
        print(f"An error occurred in generate_video_description: {e}")
        return None  # Or return a default description if needed
    
def edit_description(description):
    try:
        prompt = f"Description: '{description}'."
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content":   "You will slightly edit the music description the user provides. The larger program you are attatched to generates music albums on repeat. Your job is to alter the description "
                 "so that it is a little bit different each time and unique albums are created. You must keep the same theme and style of the description, but you can change words/topics. For example, if a country is "
                 "mentioned, choose a different country. If 'jazz' is mentioned, change it Bossa Nova. Do not respond "
                 "with anything except for the new description." 
                },

                {"role": "user", "content": prompt}
            ]
        )
        video_description = response.choices[0].message.content.strip()
        return video_description
    except Exception as e:
        print(f"An error occurred in generate_video_description: {e}")
        return None  # Or return a default description if needed
    
def edit_cover_description(cover_description):
    try:
        prompt = f"Description: '{cover_description}'. Cover Description:'{cover_description}'."
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content":   "You will edit the music album cover description the user provides. The larger program you are attatched to generates music album covers on repeat. Your job is to alter the description "
                 "so that it is very different each time and unique pictures are created. You must keep the general theme and style, but change a few words/topics so that it is completely unique. "
                 "For example, you must change specific objects to something completely different and scenery and backround. Try to change every word to at least a synonym if not something different. Do not respond "
                 "with anything except for the new cover description."},

                {"role": "user", "content": prompt}
            ]
        )
        video_description = response.choices[0].message.content.strip()
        return video_description
    except Exception as e:
        print(f"An error occurred in generate_video_description: {e}")
        return None  # Or return a default description if needed

def extend_cover_image(cover_path):
    try:
        # Load the original cover image
        cover_image = Image.open(cover_path).convert("RGBA")  # Convert to RGBA
        original_width, original_height = cover_image.size

        # Define a temporary canvas for the initial landscape format with transparent padding
        new_width = original_width * 2  # Double the width to add space on both sides
        new_height = original_height

        # Create a new blank RGBA image with the desired landscape dimensions (transparent background)
        landscape_image = Image.new("RGBA", (new_width, new_height), (255, 255, 255, 0))
        landscape_image.paste(cover_image, ((new_width - original_width) // 2, 0), cover_image)

        # Save this blank-extended image temporarily
        temp_landscape_path = "covers/temp_landscape_cover.png"
        landscape_image.save(temp_landscape_path)

        # Define prompts for left and right outpainting
        left_outpainting_prompt = "A visually cohesive extension of the left side of the cover art, matching style and atmosphere"
        right_outpainting_prompt = "A visually cohesive extension of the right side of the cover art, matching style and atmosphere"

        # Load the temp landscape image
        temp_image = Image.open(temp_landscape_path)

        # Separate the left and right halves, convert to RGBA, and save as temporary files
        left_image = temp_image.crop((0, 0, original_width, new_height)).convert("RGBA")
        right_image = temp_image.crop((original_width, 0, new_width, new_height)).convert("RGBA")
        left_image_path = "covers/temp_left_image.png"
        right_image_path = "covers/temp_right_image.png"
        left_image.save(left_image_path)
        right_image.save(right_image_path)

        # Use the OpenAI API to outpaint the left side
        with open(left_image_path, "rb") as left_file:
            left_response = client.images.edit(
                image=left_file,
                mask=left_file,
                prompt=left_outpainting_prompt,
                n=1,
                size="1024x1024"
            )
        left_url = left_response.model_dump()["data"][0]["url"]
        left_extended = Image.open(requests.get(left_url, stream=True).raw).convert("RGBA")

        # Use the OpenAI API to outpaint the right side
        with open(right_image_path, "rb") as right_file:
            right_response = client.images.edit(
                image=right_file,
                mask=right_file,
                prompt=right_outpainting_prompt,
                n=1,
                size="1024x1024"
            )
        right_url = right_response.model_dump()["data"][0]["url"]
        right_extended = Image.open(requests.get(right_url, stream=True).raw).convert("RGBA")

        # Create the final landscape image and paste all three parts
        final_landscape = Image.new("RGBA", (new_width, new_height), (255, 255, 255, 0))
        final_landscape.paste(left_extended, (0, 0), left_extended)
        final_landscape.paste(cover_image, ((new_width - original_width) // 2, 0), cover_image)
        final_landscape.paste(right_extended, (original_width, 0), right_extended)

        # Define the final save path for the extended landscape cover
        final_cover_path = "covers/landscape_cover.png"
        final_landscape.convert("RGB").save(final_cover_path)  # Convert to RGB for saving without transparency

        # Crop to a 16:9 aspect ratio to fit YouTube's format
        target_ratio = 16 / 9
        final_width, final_height = final_landscape.size
        current_ratio = final_width / final_height

        if current_ratio > target_ratio:
            # Image is too wide; crop horizontally
            new_width = int(final_height * target_ratio)
            left = (final_width - new_width) // 2
            right = left + new_width
            top, bottom = 0, final_height
        else:
            # Image is too tall; crop vertically
            new_height = int(final_width / target_ratio)
            top = (final_height - new_height) // 2
            bottom = top + new_height
            left, right = 0, final_width

        cropped_final = final_landscape.crop((left, top, right, bottom))
        cropped_final.save(final_cover_path)

        # Clean up temporary files
        os.remove(temp_landscape_path)
        os.remove(left_image_path)
        os.remove(right_image_path)

        return final_cover_path

    except Exception as e:
        print(f"An error occurred in extend_cover_image: {e}")
        return cover_path  # Return the original cover path if an error occurs


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
