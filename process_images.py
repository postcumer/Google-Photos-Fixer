import subprocess
import json
import datetime
import os
from pathlib import Path
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import time

# Define source and destination directories
source_dir = Path('~/takeout').expanduser()
destination_dir = Path('~/takeout-put').expanduser()
no_exif_data_dir = destination_dir / 'noexifdata'
error_log_file = destination_dir / 'process-error.log'

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
        log_error(f"No valid EXIF data found in {json_path}.")
        return False

    command = [
        'exiftool',
        f'-DateTimeOriginal={photo_taken_time}',
        f'-CreateDate={creation_time}',
        f'-ModifyDate={creation_time}',  # Update modified date
        str(file_path)
    ]

    try:
        result = subprocess.run(command, check=True, text=True, capture_output=True, timeout=30)
        if result.returncode == 0:
            log_info(f"Applied EXIF data from {json_path} to {file_path}")  # Log processing details
            return True
        else:
            log_error(f"Failed to apply EXIF data: {result.stderr}")
            return False
    except subprocess.CalledProcessError as e:
        log_error(f"Error applying EXIF data: {e}")
        return False
    except subprocess.TimeoutExpired:
        log_error(f"Timed out while applying EXIF data to {file_path}")
        return False

def log_info(message):
    """Log informational messages to the error log file."""
    with open(error_log_file, 'a') as log_file:
        log_file.write(f"{message}\n")

def log_error(message):
    """Log error messages to the error log file."""
    with open(error_log_file, 'a') as log_file:
        log_file.write(f"ERROR: {message}\n")

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
    
    # Ignore files containing '_original_'
    if '_original_' in file_name:
        return None, False

    json_file = find_json_file(file_name)
    if json_file:
        log_info(f"Found JSON file: {json_file}")  # Log processing details
        log_info(f"Processing file: {file_name}")  # Log processing details
        exif_applied = apply_exif_data(file_path, json_file)
    else:
        log_info(f"No JSON file found for {file_name}")  # Log processing details
        exif_applied = False

    # Determine the destination folder based on whether EXIF data was applied
    dest_folder_path = destination_dir if exif_applied else no_exif_data_dir
    dest_folder_path.mkdir(parents=True, exist_ok=True)
    shutil.move(str(file_path), str(dest_folder_path / file_name))  # Move the file
    log_info(f"Moved {file_name} to {dest_folder_path}")  # Log processing details

    return file_path, exif_applied  # Return the file path and EXIF status

def show_exif_data(file_path):
    """Retrieve and display EXIF data of the file."""
    command = ['exiftool', str(file_path)]
    result = subprocess.run(command, text=True, capture_output=True, timeout=30)
    if result.returncode == 0:
        log_info(f"EXIF data for {file_path}:\n{result.stdout}")  # Log EXIF data
        print(f"EXIF data for {file_path}:\n{result.stdout}")  # Print EXIF data for user
    else:
        log_error(f"Failed to retrieve EXIF data: {result.stderr}")
        print(f"Failed to retrieve EXIF data for {file_path}")

def display_progress_bar(current, total):
    """Display a text-based progress bar."""
    progress = int((current / total) * 100)
    bar = '█' * (progress // 2) + '-' * (50 - (progress // 2))
    print(f"\rProgress |{bar}| {progress:.1f}% Complete", end='')

def process_files(check_individually):
    """Process files and handle user input after processing the initial batch of files."""
    no_exif_data_dir.mkdir(parents=True, exist_ok=True)

    # Gather all files to process
    files_to_process = [Path(root) / file_name for root, _, files in os.walk(source_dir) for file_name in files if not file_name.endswith('.json') and '_original_' not in file_name]
    total_files = len(files_to_process)

    # Initialize variables
    processed_files = []
    json_files_found = 0
    global suppress_logs
    suppress_logs = False
    continue_processing = True

    # Scan total number of files
    print("Scanning total number of files...")
    display_progress_bar(0, total_files)
    time.sleep(1)  # Simulate scanning delay
    print("\nTotal files to process:", total_files)

    processed_count = 0
    first_batch_processed = False

    while files_to_process and continue_processing:
        batch_size = min(5, len(files_to_process))
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(process_file, file_path) for file_path in files_to_process[:batch_size]]
            for future in as_completed(futures):
                file_path, exif_applied = future.result()
                if file_path:
                    processed_files.append(file_path)
                    if exif_applied:
                        json_files_found += 1

        files_to_process = files_to_process[batch_size:]  # Remove processed files from the list

        # Update processed count and progress bar
        processed_count += batch_size
        display_progress_bar(processed_count, total_files)

        if not first_batch_processed and json_files_found > 0:
            if processed_files:
                # Show EXIF data for the processed files
                valid_files = [file_path for file_path in processed_files if (destination_dir / file_path.name).exists()]
                if valid_files:
                    for file_path in valid_files:
                        show_exif_data(destination_dir / file_path.name)

            # Prompt user for input after processing the batch
            user_input = input("\nProcessed 5 files with JSON data. Type 'y' to continue processing, 'n' to stop: ").strip().lower()
            if user_input == 'n':
                log_info("User chose to stop. Please verify the files and restart the script.")
                continue_processing = False
            else:
                log_info("Continuing processing...")
                suppress_logs = True  # Suppress logs for further processing

            first_batch_processed = True  # Ensure we only ask once

    print("\nProcessing complete.")

if __name__ == "__main__":
    # Prompt user if they want to check files individually
    check_mode = input("Do you want to check EXIF data for files and stop after the initial batch of 5 files for user input? Type 'y' for yes, 'n' for no: ").strip().lower()
    check_individually = check_mode == 'y'
    
    process_files(check_individually)
