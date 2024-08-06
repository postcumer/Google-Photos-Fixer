import os
from PIL import Image
from datetime import datetime
import sys
import logging

# Setup logging
log_file = os.path.expanduser('~/takeout-put/check.log')
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to print a text-based progress bar
def print_progress_bar(iteration, total, prefix='', length=40, fill='█', print_end="\r"):
    """Print a text-based progress bar."""
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% Complete')
    sys.stdout.flush()
    if iteration == total:
        print()

# Try to import tqdm for progress bar
try:
    from tqdm import tqdm
    tqdm_installed = True
except ImportError:
    tqdm_installed = False

# Directory path to scan
directory_to_scan = os.path.expanduser('~/takeout-put')

# Initialize counters
count_today_exif_data = 0
count_other_dates_exif_data = 0
count_no_exif_data = 0

# Get today's date in the format used by EXIF
today_date_str = datetime.now().strftime('%Y:%m')

# Function to check if a date is today's date
def is_today(date_str):
    return date_str.startswith(today_date_str) if date_str else False

# Function to check if a date is not today's date
def is_not_today(date_str):
    return not is_today(date_str)

# Collect all files to process
all_files = []
for root, dirs, files in os.walk(directory_to_scan):
    for file in files:
        if file.lower().endswith(('.jpg', '.jpeg', '.tiff', '.png', '.heic')):
            all_files.append(os.path.join(root, file))

# Process files with or without tqdm
total_files = len(all_files)
current_file = 0

if tqdm_installed:
    with tqdm(total=total_files, file=sys.stdout, desc="Processing files") as pbar:
        for file_path in all_files:
            try:
                # Open the image file
                image = Image.open(file_path)
                
                # Extract EXIF data
                exif_data = image._getexif()

                # Check if EXIF data is available
                if exif_data:
                    # Try to get the DateTimeOriginal or DateTimeDigitized
                    date_time_original = exif_data.get(36867)  # 36867 is the tag for DateTimeOriginal
                    date_time_digitized = exif_data.get(36868) # 36868 is the tag for DateTimeDigitized

                    # Use the first available date
                    date_to_check = date_time_original or date_time_digitized
                    
                    if date_to_check:
                        if is_today(date_to_check):
                            count_today_exif_data += 1
                            logging.info(f'Today\'s date EXIF file: {file_path}')
                        elif is_not_today(date_to_check):
                            count_other_dates_exif_data += 1
                    else:
                        count_no_exif_data += 1
                        logging.info(f'No EXIF data: {file_path}')
                else:
                    count_no_exif_data += 1
                    logging.info(f'No EXIF data: {file_path}')
            except Exception as e:
                print(f"Error processing {file_path}: {e}", file=sys.stderr)
                count_no_exif_data += 1
                logging.error(f'Error processing {file_path}: {e}')
            
            # Update the progress bar
            pbar.update(1)
else:
    for file_path in all_files:
        try:
            # Open the image file
            image = Image.open(file_path)
            
            # Extract EXIF data
            exif_data = image._getexif()

            # Check if EXIF data is available
            if exif_data:
                # Try to get the DateTimeOriginal or DateTimeDigitized
                date_time_original = exif_data.get(36867)  # 36867 is the tag for DateTimeOriginal
                date_time_digitized = exif_data.get(36868) # 36868 is the tag for DateTimeDigitized

                # Use the first available date
                date_to_check = date_time_original or date_time_digitized
                
                if date_to_check:
                    if is_today(date_to_check):
                        count_today_exif_data += 1
                        logging.info(f'Today\'s date EXIF file: {file_path}')
                    elif is_not_today(date_to_check):
                        count_other_dates_exif_data += 1
                else:
                    count_no_exif_data += 1
                    logging.info(f'No EXIF data: {file_path}')
            else:
                count_no_exif_data += 1
                logging.info(f'No EXIF data: {file_path}')
        except Exception as e:
            print(f"Error processing {file_path}: {e}", file=sys.stderr)
            count_no_exif_data += 1
            logging.error(f'Error processing {file_path}: {e}')

        # Simple text-based progress indicator
        current_file += 1
        print_progress_bar(current_file, total_files, prefix='Progress')

# Print the results
print("\nProcessing complete.")
print(f"Files with EXIF data of today's date: {count_today_exif_data}")
print(f"Files with EXIF data of other dates: {count_other_dates_exif_data}")
print(f"Files with NO EXIF data: {count_no_exif_data}")
