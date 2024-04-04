import json
import os
import subprocess

WHITEPAPERS_DATA_FILE = "data/whitepapers_data.json"
DOWNLOAD_DIRECTORY = "data/whitepapers/"


def download_pdfs():
    with open(WHITEPAPERS_DATA_FILE, "r", encoding="utf-8") as f:
        whitepapers_data = json.load(f)

    os.makedirs(DOWNLOAD_DIRECTORY, exist_ok=True)

    counter = 1
    for whitepaper in whitepapers_data:
        pdf_link = whitepaper["pdf_link"]
        if pdf_link != "No PDF Link":
            file_name = f"{counter}.pdf"
            file_path = os.path.join(DOWNLOAD_DIRECTORY, file_name)
            try:
                subprocess.run(["wget", "-O", file_path, pdf_link], check=True)
                print(f"Downloaded: {file_name}")
                counter += 1
            except subprocess.CalledProcessError:
                print(f"Failed to download: {pdf_link}")


if __name__ == "__main__":
    download_pdfs()
