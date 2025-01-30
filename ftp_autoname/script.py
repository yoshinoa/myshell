import ftplib
import os
from openai import OpenAI
import time
import logging
from datetime import datetime
import json
from dotenv import load_dotenv

load_dotenv()


# Set up logging
def setup_logging():
    """Configure logging to both file and console"""
    # Create logs directory if it doesn't exist
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # Create a unique log file name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/media_organizer_{timestamp}.log"

    # Set up logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),  # This will print to console too
        ],
    )

    logging.info("Starting media organization process")
    return log_file


def connect_ftp(host, username, password):
    """Establish FTP connection"""
    try:
        logging.info(f"Attempting to connect to FTP server: {host}")
        ftp = ftplib.FTP(host)
        ftp.login(username, password)
        logging.info("Successfully connected to FTP server")
        return ftp
    except Exception as e:
        logging.error(f"FTP connection error: {e}")
        return None


def should_delete_file(filename):
    """Determine if a file should be deleted"""
    unwanted_files = ["RARBG.txt", ".nfo", "readme.txt", "sample.mp4"]
    should_delete = any(filename.lower().endswith(f) for f in unwanted_files)
    if should_delete:
        logging.info(f"Marked for deletion: {filename}")
    return should_delete


def load_processed_dirs():
    """Load the list of already processed directories"""
    try:
        with open("processed_dirs.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_processed_dir(path):
    """Save a directory as processed"""
    dirs = load_processed_dirs()
    if path not in dirs:
        dirs.append(path)
        with open("processed_dirs.json", "w") as f:
            json.dump(dirs, f)


def get_standardized_name(original_name, is_directory, client):
    """Use LLM to generate a standardized name based on whether it's a file or directory"""
    try:
        logging.info(
            f"Requesting standardized name for {'directory' if is_directory else 'file'}: {original_name}"
        )

        # Get the extension if it's a file
        extension = os.path.splitext(original_name)[1] if not is_directory else ""

        system_content = """You are a media file organizer. First determine if this is a movie or TV show episode.

For movies:
- Format as "Movie Title (Year)" WITHOUT the extension
- Example: "A Silent Voice (2016)"

For TV show directories:
- Include show name and season number
- Format as "Show Name Season XX" where XX is the season number
- Example: "Parks and Recreation Season 02"
- If no season number is found, just return the show name

For TV episode files:
- Format as "Show Name S01E02 Episode Title" WITHOUT the extension
- If there is no episode title available, just use the episode number and don't include "Episode Title"
- Keep SxxExx format for proper sorting
- Use spaces, not dots
- Include only show name, season/episode, and title

First output either MOVIE: or TVSHOW: followed by the standardized name. Nothing else."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_content},
                {
                    "role": "user",
                    "content": f"Standardize this {'directory' if is_directory else 'filename'}: {original_name}",
                },
            ],
            max_tokens=100,
        )
        result = response.choices[0].message.content.strip()
        logging.info(f"AI response: {result}")

        # Split the type and name
        media_type, new_name = result.split(": ", 1)

        # Add back the extension for files
        if not is_directory:
            new_name = f"{new_name}{extension}"

        logging.info(f"Detected type: {media_type}, New name: {new_name}")
        return new_name
    except Exception as e:
        logging.error(f"OpenAI API error for {original_name}: {e}")
        return original_name


def process_directory_recursive(ftp, path, client):
    """Recursively process directories and files"""
    processed_dirs = load_processed_dirs()
    if path in processed_dirs:
        logging.info(f"Skipping already processed directory: {path}")
        return

    try:
        logging.info(f"Processing directory: {path}")
        old_dir = ftp.pwd()  # Save current directory
        items = ftp.nlst()
        logging.info(f"Found {len(items)} items in directory")

        # Handle deletions first
        for item in items:
            if should_delete_file(item):
                try:
                    ftp.delete(item)
                    logging.info(f"Deleted: {item}")
                except Exception as e:
                    logging.error(f"Failed to delete {item}: {e}")
                continue

        # Process files and directories
        for item in items:
            try:
                # Try to CWD to check if it's a directory
                try:
                    ftp.cwd(item)
                    is_dir = True
                    ftp.cwd(old_dir)  # Go back
                except:
                    is_dir = False

                if is_dir:
                    new_name = get_standardized_name(
                        item, is_directory=True, client=client
                    )
                    if new_name != item:
                        try:
                            ftp.rename(item, new_name)
                            logging.info(f"Renamed directory: {item} -> {new_name}")
                            item = new_name  # Update item name for recursion
                        except Exception as e:
                            logging.error(f"Error renaming directory {item}: {e}")

                    # Process the subdirectory
                    ftp.cwd(item)
                    process_directory_recursive(ftp, f"{path}/{item}", client)
                    ftp.cwd(old_dir)
                else:
                    if item.lower().endswith((".mkv", ".mp4", ".avi")):
                        new_name = get_standardized_name(
                            item, is_directory=False, client=client
                        )
                        if new_name != item:
                            try:
                                ftp.rename(item, new_name)
                                logging.info(f"Renamed file: {item} -> {new_name}")
                            except Exception as e:
                                logging.error(f"Error renaming file {item}: {e}")

            except Exception as e:
                logging.error(f"Error processing item {item}: {e}")
                continue

        # Mark directory as processed
        save_processed_dir(path)
        logging.info(f"Marked directory as processed: {path}")

    except Exception as e:
        logging.error(f"Error processing directory {path}: {e}")


def main():
    # Set up logging first
    log_file = setup_logging()
    logging.info("Media organization script started")

    # Configuration
    FTP_HOST = os.getenv("FTP_HOST")
    FTP_USER = os.getenv("FTP_USER")
    FTP_PASS = os.getenv("FTP_PASS")
    START_PATH = os.getenv("FTP_START_PATH")

    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    logging.info("OpenAI client initialized")

    # Connect to FTP
    ftp = connect_ftp(FTP_HOST, FTP_USER, FTP_PASS)
    if not ftp:
        logging.error("Failed to connect to FTP server. Exiting.")
        return

    try:
        # Start recursive processing from root directory
        ftp.cwd(START_PATH)
        process_directory_recursive(ftp, "", client)
        logging.info("Processing completed successfully")
    except Exception as e:
        logging.error(f"Fatal error during processing: {e}")
    finally:
        ftp.quit()
        logging.info("FTP connection closed")
        logging.info(f"Log file created at: {log_file}")


if __name__ == "__main__":
    main()
