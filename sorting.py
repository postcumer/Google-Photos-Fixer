import os
import shutil
import re
import logging
import sys

# Configure logging
logging.basicConfig(filename=os.path.expanduser('~/takeout-put/sorting-error.log'),
                    level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Directories
source_dir = os.path.expanduser('~/takeout-put/')
output_dir = os.path.expanduser('~/takeout-put/final')

# Create output directories if they do not exist
os.makedirs(output_dir, exist_ok=True)
os.makedirs(os.path.join(output_dir, 'Camera'), exist_ok=True)
os.makedirs(os.path.join(output_dir, 'Screenshot'), exist_ok=True)
os.makedirs(os.path.join(output_dir, 'Snapchat'), exist_ok=True)
os.makedirs(os.path.join(output_dir, 'Others'), exist_ok=True)
os.makedirs(os.path.join(output_dir, 'WhatsApp Images'), exist_ok=True)
os.makedirs(os.path.join(output_dir, 'WhatsApp Videos'), exist_ok=True)

# Define patterns for sorting
prefix_patterns = {
    'WhatsApp Images': re.compile(r'^IMG.*WA'),
    'WhatsApp Videos': re.compile(r'^VID.*WA'),
    'Camera': re.compile(r'^(IMG|VID|LMC|PXL)'),
    'Screenshot': re.compile(r'^(Screenshot|Screenrecorder)'),
    'Snapchat': re.compile(r'^Snapchat')
}

def process_file(src_path):
    try:
        # Determine the destination folder
        filename = os.path.basename(src_path)
        for folder, pattern in prefix_patterns.items():
            if pattern.match(filename):
                dest_folder = os.path.join(output_dir, folder)
                break
        else:
            # If no pattern matched, default to 'Others'
            dest_folder = os.path.join(output_dir, 'Others')

        # Create destination folder if it does not exist
        os.makedirs(dest_folder, exist_ok=True)

        # Move file to the destination folder
        dest_path = os.path.join(dest_folder, filename)
        shutil.move(src_path, dest_path)

    except Exception as e:
        logging.error(f"Error processing file {src_path}: {e}")

def delete_original_files(directory):
    """Deletes files ending with '_original' in the given directory and its subdirectories."""
    count_deleted = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('_original'):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    count_deleted += 1
                except Exception as e:
                    logging.error(f"Error deleting file {file_path}: {e}")
    return count_deleted

def print_progress_bar(iteration, total, bar_length=50):
    """Prints a horizontal progress bar in the style of 'Progress |████████████████████████████████████████| 100.0% Complete'."""
    progress = iteration / total
    arrow = '█' * int(round(progress * bar_length))
    spaces = ' ' * (bar_length - len(arrow))
    percent = f"{progress * 100:.1f}"
    sys.stdout.write(f'\rProgress |{arrow}{spaces}| {percent}% Complete')
    sys.stdout.flush()

def main():
    try:
        # Collect all files from source directory and subdirectories
        file_paths = []
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_paths.append(os.path.join(root, file))

        # Process files with a text-based progress bar
        total_files = len(file_paths)
        for i, src_path in enumerate(file_paths):
            process_file(src_path)
            # Print progress
            print_progress_bar(i + 1, total_files)

        # Print final newline after progress bar
        print()

        # Delete files ending with '_original'
        count_deleted = delete_original_files(source_dir)
        if count_deleted > 0:
            logging.info(f"Deleted {count_deleted} files ending with '_original'.")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
