import cv2
import easyocr
import os
import pandas as pd
import re
import sys
from pdf2image import convert_from_path 

if len(sys.argv) < 2:
    print("Usage: python automate.py <PDF_FILE>")
    sys.exit(1)
pdf_file = sys.argv[1]
os.makedirs('output_images', exist_ok=True)
try:
    images = convert_from_path(pdf_file, dpi=200)
except Exception as e:
    print(f"Error converting PDF to images: {e}")
    sys.exit(1) 

data = []

for i, image in enumerate(images):
    try:
        image_path = f'output_images/page_{i + 1}.jpeg'
        image.save(image_path, 'JPEG')
        print(f"Saved: {image_path}")
        image_str = os.path.abspath(image_path)
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.medianBlur(gray, 5) 
        _, thresh = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY_INV)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        reader = easyocr.Reader(['en'])  # Specify language(s)
        result = reader.readtext(thresh)  # Or your image variable
        text = ' '.join([res[1] for res in result])

        print(text)
        print("\n---\n ")

        royalty_pass_match = re.search(r'QL\w{18}', text)
        vehicle_no_match = re.search(r'\(HGV\)\s*([^\s]+)', text)
        issue_date = re.search(r'\b\w{2}-\w{3}-\w{4}\b', text)
        quantity_match = re.search(r'quantity[^0-9]*([\d]+\.[\d]+)', text, re.IGNORECASE)
        ssp_number = re.search(r'(.{2})KUTE\s*(.{7})', text, re.IGNORECASE)
        hyperlink = f'=HYPERLINK("file:///{image_str}", "page_{i + 1}.jpg")'
        data.append({
            'Page': i + 1,
            'Issue Date': issue_date.group(0) if issue_date else '',
            'Vehicle No': vehicle_no_match.group(1) if vehicle_no_match else '',
            'Royalty Pass No': royalty_pass_match.group() if royalty_pass_match else '' ,
            'Quantity': quantity_match.group(1) if quantity_match else '',
            'SSP Number': ssp_number.group(0) if ssp_number else '',
            'Image Link': hyperlink
        })
    except Exception as e:
        print(f"Error processing page {i + 1}: {e}")

try:
    df = pd.DataFrame(data)
    df.to_csv('output.csv', index=False)
    print("Data saved to output.csv")
except Exception as e:
    print(f"Error saving CSV: {e}")   


