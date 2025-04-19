#!/usr/bin/env python3
"""
Module to download bird species audio files from Xeno-Canto.

This script prompts the user to enter a bird species name and downloads audio files of that species from Xeno-Canto. It saves the files in a folder named after the species. The user can interrupt the download process by pressing Ctrl+C.
"""

import requests
import os
import signal

# Global flag to stop downloading when interrupted
stop_downloading = False


def signal_handler(sig, frame):
    """
    Signal handler to set the stop_downloading flag when the user interrupts.

    Args:
        sig: Signal number.
        frame: Current stack frame.
    """
    global stop_downloading
    print("\nStopping downloads...")
    stop_downloading = True


signal.signal(signal.SIGINT, signal_handler)


def download_bird_audio(species_name):
    """
    Search for the bird species and download audio files from Xeno-Canto.

    Args:
        species_name (str): The name of the bird species to search for.
    """
    global stop_downloading
    url = f"https://www.xeno-canto.org/api/2/recordings?query={species_name}"

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Xeno-Canto API: {e}")
        return

    data = response.json()

    if not data['recordings']:
        print(f"No recordings found for the species: {species_name}")
        return

    if not os.path.exists(species_name):
        os.makedirs(species_name)

    for recording in data['recordings']:
        if stop_downloading:
            break

        if species_name.lower() in recording['en'].lower():
            audio_url = recording['file']
            recording_id = recording['id']

            # Construct descriptive filename if species or subspecies exists
            if recording['gen'] and recording['sp']:
                file_name = f"{recording['gen']}_{recording['sp']}_{recording_id}.mp3"
            else:
                file_name = f"XC{recording_id}.mp3"  # Fallback to ID-based name if genus or species is missing

            file_path = os.path.join(species_name, file_name)

            try:
                print(f"Downloading {file_name}...")
                audio_response = requests.get(audio_url)
                audio_response.raise_for_status()
                with open(file_path, 'wb') as f:
                    f.write(audio_response.content)
                print(f"Saved {file_name} to {file_path}")
            except requests.exceptions.RequestException as e:
                print(f"Failed to download {file_name}: {e}")
            except Exception as e:
                print(f"Error saving {file_name}: {e}")

    if stop_downloading:
        print("Downloads stopped by user.")
    else:
        print("Download complete.")


def main():
    """
    Main function to prompt the user and start the download process.
    """
    species_name = input("Enter the bird species to search for: ")
    print("Press Ctrl+C to stop the download at any time.")
    download_bird_audio(species_name)


if __name__ == "__main__":
    main()
