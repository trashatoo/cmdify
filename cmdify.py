import spotipy
from spotipy.oauth2 import SpotifyOAuth
from PIL import Image
from colorama import Fore, Back, Style, init
import os
import platform
import requests
from io import BytesIO
import time
import pyfiglet

# Initialize colorama
init(autoreset=True)

# Your Spotify app credentials
CLIENT_ID = 'your_client_id'
CLIENT_SECRET = 'your_client_secret'
REDIRECT_URI = 'http://localhost:8888/callback'

# Define the scope for reading playback state
SCOPE = "user-read-playback-state"

# Set up the Spotify OAuth object
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE
))

# Clear the terminal screen
def clear_screen():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

# Convert pixel to ANSI escape color code
def pixel_to_ansi(r, g, b):
    return f"\033[48;2;{r};{g};{b}m "

# Resize and convert the image to ASCII
def display_image_as_ascii(img, new_width=30):
    # Get the terminal size
    term_size = os.get_terminal_size()
    max_width = min(new_width, term_size.columns // 2)  # Half the width for the album art

    # Calculate the new height to maintain the aspect ratio
    width, height = img.size
    aspect_ratio = height / width
    new_height = int(aspect_ratio * max_width)  # Now only considering width-to-height ratio

    img = img.resize((max_width, new_height))

    # Convert the image to RGB mode if it's not
    img = img.convert("RGB")

    # Iterate over the pixels and print ASCII with color
    ascii_art = ""
    for y in range(new_height):
        for x in range(max_width):
            r, g, b = img.getpixel((x, y))
            ascii_art += pixel_to_ansi(r, g, b) + " "
        ascii_art += "\n"  # Newline after each row

    return ascii_art

# Get current album art from Spotify
def get_current_album_art():
    try:
        # Get current playback state
        playback = sp.current_playback()
        
        if playback and playback.get('item'):
            # Get the album art URL from the current track
            album_art_url = playback['item']['album']['images'][0]['url']
            return album_art_url
        else:
            print("No track is currently playing.")
            return None
    except Exception as e:
        print(f"Error fetching album art: {e}")
        return None

# Download and save the album art image
def download_image(url):
    try:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        return img
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None

# Function to display the album art and song name
def display_now_playing():
    try:
        last_played_song_id = None  # Track the last played song to update only when the song changes

        while True:
            # Get the current playback state
            playback = sp.current_playback()

            if playback and playback.get('item'):
                song_id = playback['item']['id']
                song_name = playback['item']['name']
                song_artists = ', '.join([artist['name'] for artist in playback['item']['artists']])  # Get song artists

                # If the song is still the same, don't update
                if song_id == last_played_song_id:
                    time.sleep(1)
                    continue  # Skip the rest of the loop until the song changes

                # Get the album art URL
                album_art_url = get_current_album_art()
                if album_art_url:
                    img = download_image(album_art_url)
                    clear_screen()  # Clear the screen before updating

                    # Display the album art as ASCII on the left
                    album_art_ascii = display_image_as_ascii(img)

                    # Display the song name as ASCII on the right
                    ascii_song_name = pyfiglet.figlet_format(song_name, font="slant")

                    # Split the album art ASCII and song name into lines
                    album_art_lines = album_art_ascii.split("\n")
                    song_name_lines = ascii_song_name.split("\n")

                    # Ensure the entire word stays on the same line or moves to the next line if it overflows
                    max_width = os.get_terminal_size().columns
                    adjusted_song_name_lines = []
                    for line in song_name_lines:
                        while len(line) > max_width:
                            adjusted_song_name_lines.append(line[:max_width])
                            line = line[max_width:]
                        adjusted_song_name_lines.append(line)  # Add the remaining part

                    # Print the album art and song name side by side, preserving color
                    max_lines = max(len(album_art_lines), len(adjusted_song_name_lines))

                    for i in range(max_lines):
                        album_line = album_art_lines[i] if i < len(album_art_lines) else " " * len(album_art_lines[0])
                        song_line = adjusted_song_name_lines[i] if i < len(adjusted_song_name_lines) else " " * len(adjusted_song_name_lines[0])

                        # Print album art line with color, then reset color for song name
                        print(f"{album_line}{Style.RESET_ALL}   {song_line}")

                    # Print the song creators (artists) below the song name, in plain text
                    print(f"\n{Style.RESET_ALL}By: {song_artists}")

                    # Update the last played song ID
                    last_played_song_id = song_id

            time.sleep(1)  # Check every second for song changes

    except Exception as e:
        print(f"Error: {e}")

# Start displaying the now playing song
display_now_playing()
