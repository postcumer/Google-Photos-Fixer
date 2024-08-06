---

## 🚀 Google Photos Fixer

Python scripts to restore EXIF data of media files using .JSON files provided by Google Photos Takeout.

### 🛠️ Requirements

- **General:**
  - Python 3.7+
  - `pip` (Python package installer)

- **For Debian-based systems:**
  ```bash
  sudo apt update
  sudo apt install python3-full python3-pip exiftool
  pip3 install Pillow pyexiftool
  ```

- **For Arch-based systems:**
  ```bash
  sudo pacman -Syu
  sudo pacman -S python-full python-pip exiftool
  pip install Pillow pyexiftool
  ```

### 📥 Downloading Google Photos Takeout

1. **Go to [Google Takeout](https://takeout.google.com).**
2. **Select the data you want to download.** Make sure to include “Google Photos.”
3. **Choose your export options and click "Next."**
4. **Click "Create export" and wait for the process to complete.**
5. **Download the ZIP file containing your data.**

### 📂 Extracting Takeout Data

1. **Move the downloaded ZIP file to your preferred directory, e.g., `~/Downloads`.**
2. **Extract the ZIP file to `~/takeout`:**
   ```bash
   mkdir -p ~/takeout
   unzip ~/Downloads/your_takeout_file.zip -d ~/takeout
   ```

### 📜 Usage

1. **Clone the repository:**
   ```bash
   git clone https://github.com/postcumer/Google-Takeout-Proccesor
   cd Google-Takeout-Proccesor
   ```

2. **Run the scripts:**
   ```bash
   python3 process_images.py
   python3 check_no_of_processed_images.py
   ```

### 🛠️ Troubleshooting

If the script doesn't work due to security issues, try running it in a Python virtual environment:

1. **Create a virtual environment:**
   ```bash
   python3 -m venv myenv
   ```

2. **Activate the virtual environment:**
   ```bash
   source myenv/bin/activate
   ```

3. **Install the required packages:**
   ```bash
   pip install pyexiftool Pillow
   ```

4. **Run the scripts within the virtual environment.**

### 📝 License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/postcumer/Google-Takeout-Proccesor/docs/license) file for details.

---
