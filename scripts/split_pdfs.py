import argparse
import os

from PyPDF2 import PdfReader, PdfWriter


def parser_args():
    """
    Parses command line arguments.

    """
    args = argparse.ArgumentParser()
    args.add_argument("--folder", type=str, help="Folder path to process")
    return args.parse_args()


def split_pdf(input_file: str, output_path: str, max_pages: int = 500):
    """
    Splits a PDF file into multiple parts if it has more than a specified number of pages.

    Args:
        input_file (str): Path to the input PDF file.
        output_path (str): The directory where the split PDF parts will be saved.
        max_pages (int, optional): Maximum number of pages allowed per split file. Defaults to 500.
    """
    reader = PdfReader(input_file)  # Initialize a PDF reader object
    total_pages = len(reader.pages)  # Get the total number of pages in the PDF

    # If the PDF has less or equal pages than the maximum allowed, no need to split
    if total_pages <= max_pages:
        return

    part = 1
    for page_start in range(0, total_pages, max_pages):
        writer = PdfWriter()  # Initialize a PDF writer object for each part
        # Iterate through the page range for the current part and add pages to the writer object
        for page_num in range(page_start, min(page_start + max_pages, total_pages)):
            writer.add_page(reader.pages[page_num])

        # Construct the filename for the current part
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        part_file_name = f"{base_name}_part{part}.pdf"
        full_part_file_path = os.path.join(output_path, part_file_name)
        with open(full_part_file_path, "wb") as f:
            writer.write(f)

        print(f"Created {full_part_file_path} with up to {max_pages} pages.")
        part += 1  # Increment part number for the next iteration
        split_occurred = True

    if split_occurred:
        # Delete the original file only if at least one part was created.
        os.remove(input_file)
        print(f"Deleted original file: {input_file}")


def process_folder(folder_path: str):
    """
    Processes each PDF file in the specified folder and splits it if necessary.

    Args:
        folder_path (str): The path to the folder containing PDF files.
    """
    # Iterate through each file in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            # Split the PDF file if necessary
            split_pdf(os.path.join(folder_path, filename), folder_path)


if __name__ == "__main__":
    args = parser_args()
    # Process the specified folder
    process_folder(folder_path=args.folder)
