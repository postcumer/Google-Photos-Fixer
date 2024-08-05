import subprocess
import json
import datetime
import os
from pathlib import Path
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

# Define source and destination directories
source_dir = Path('~/takeout').expanduser()
destination_dir = Path('~/takeout-put').expanduser()
no_exif_data_dir = destination_dir / 'noexifdata'

def timestamp_to_exif_date(timestamp):
    """Convert Unix timestamp to EXIF date-time format."""
    if timestamp:
        dt = datetime.datetime.utcfromtimestamp(int(timestamp))
        return dt.strftime('%Y:%m:%d %H:%M:%S')
    return ''

def apply_exif_data(file_path, json_path):
    """Apply EXIF data from JSON to the image file using exiftool."""
    with open(json_path, 'r') as file:
        data = json.load(file)

    creation_time = timestamp_to_exif_date(data.get('creationTime', {}).get('timestamp', ''))
    photo_taken_time = timestamp_to_exif_date(data.get('photoTakenTime', {}).get('timestamp', ''))

    if not creation_time and not photo_taken_time:
        print(f"No valid EXIF data found in {json_path}.")
        return False

    command = [
        'exiftool',
        f'-DateTimeOriginal={photo_taken_time}',
        f'-CreateDate={creation_time}',
        str(file_path)
    ]

    try:
        result = subprocess.run(command, check=True, text=True, capture_output=True, timeout=30)
        if result.returncode == 0:
            print(f"Applied EXIF data from {json_path} to {file_path}")
            return True
        else:
            print(f"Failed to apply EXIF data: {result.stderr}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"Error applying EXIF data: {e}")
        return False
    except subprocess.TimeoutExpired:
        print(f"Timed out while applying EXIF data to {file_path}")
        return False

def show_exif_data(file_path):
    """Retrieve and display EXIF data of the file."""
    command = ['exiftool', str(file_path)]
    result = subprocess.run(command, text=True, capture_output=True, timeout=30)
    if result.returncode == 0:
        print(f"EXIF data for {file_path}:\n{result.stdout}")
    else:
        print(f"Failed to retrieve EXIF data: {result.stderr}")

def find_json_file(image_file):
    """Search for the corresponding JSON file in all subdirectories of source_dir."""
    for root, _, files in os.walk(source_dir):
        json_filename = image_file + '.json'
        if json_filename in files:
            return Path(root) / json_filename
    return None

def process_file(file_path):
    """Process a single file: apply EXIF data and move it to the destination folder."""
    file_name = file_path.name
    json_file = find_json_file(file_name)
    if json_file:
        print(f"Found JSON file: {json_file}")
        print(f"Processing file: {file_name}")
        exif_applied = apply_exif_data(file_path, json_file)
    else:
        print(f"No JSON file found for {file_name}")
        exif_applied = False

    # Determine the destination folder based on whether EXIF data was applied
    dest_folder_path = destination_dir if exif_applied else no_exif_data_dir
    dest_folder_path.mkdir(parents=True, exist_ok=True)
    shutil.move(str(file_path), str(dest_folder_path / file_name))
    print(f"Moved {file_name} to {dest_folder_path}")

    return file_path  # Return the file path for later EXIF data checking

def process_files(check_individually):
    """Process files and handle user input after processing the initial batch of files."""
    no_exif_data_dir.mkdir(parents=True, exist_ok=True)

    # Gather all files to process
    files_to_process = [Path(root) / file_name for root, _, files in os.walk(source_dir) for file_name in files if not file_name.endswith('.json')]

    processed_files = []
    total_processed_files = 0
    ask_for_input = True  # Flag to handle user input prompt

    while files_to_process:
        # Process a batch of files
        batch_size = min(5, len(files_to_process))
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(process_file, file_path) for file_path in files_to_process[:batch_size]]
            for future in as_completed(futures):
                processed_file_path = future.result()
                processed_files.append(processed_file_path)
                total_processed_files += 1

        files_to_process = files_to_process[batch_size:]  # Remove processed files from the list

        if ask_for_input:
            # Show EXIF data for the processed files
            for file_path in processed_files:
                updated_file_path = destination_dir / file_path.name
                # Ensure file exists in destination directory
                if updated_file_path.exists():
                    show_exif_data(updated_file_path)
                else:
                    print(f"File not found for EXIF data retrieval: {updated_file_path}")

            # Prompt user for input after processing the initial batch
            user_input = input("Processed 5 files. Type 'y' to continue processing, 'n' to stop: ").strip().lower()
            if user_input == 'n':
                print("You chose to stop. Please verify the files and restart the script.")
                break
            ask_for_input = False  # Only ask once

        # Clear the list of processed files for the next batch
        processed_files.clear()

if __name__ == "__main__":
    # Prompt user if they want to check files individually
    check_mode = input("Do you want to check EXIF data for files and stop after the initial batch of 5 files for user input? Type 'y' for yes, 'n' for no: ").strip().lower()
    check_individually = check_mode == 'y'
    
    process_files(check_individually)
