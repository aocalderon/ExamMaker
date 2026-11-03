import fitz  # PyMuPDF
import os

def extract_answer_sheets(pdf_path, output_dir="as"):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)

    count = 0
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()

        # Filter: Identify answer sheets by looking for specific text
        if "Nombre Completo" in text:
            # Extract at 300 DPI for optimal OpenCV/Barcode processing
            pix = page.get_pixmap(dpi=300)
            output_filename = os.path.join(output_dir, f"sheet_page_{page_num + 1}.jpg")

            # Save as JPEG
            pix.save(output_filename)
            print(f"Saved: {output_filename}")
            count += 1

    print(f"Extraction complete. Successfully extracted {count} answer sheets.")

if __name__ == "__main__":
    extract_answer_sheets("as/ExamsML.pdf")