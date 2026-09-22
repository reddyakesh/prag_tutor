import fitz
import os

# PDF file
pdf_path = "data/os_unit1.pdf"

# Output folder
output_folder = "images/os_unit1"

os.makedirs(output_folder, exist_ok=True)

pdf = fitz.open(pdf_path)

total_images = 0

for page_number in range(len(pdf)):
    page = pdf[page_number]

    images = page.get_images(full=True)

    print(f"Page {page_number + 1}: {len(images)} image(s)")

    for index, img in enumerate(images):

        xref = img[0]

        base_image = pdf.extract_image(xref)

        image_bytes = base_image["image"]

        image_ext = base_image["ext"]

        image_name = f"page_{page_number+1}_img_{index+1}.{image_ext}"

        image_path = os.path.join(output_folder, image_name)

        with open(image_path, "wb") as f:
            f.write(image_bytes)

        total_images += 1

print("\n==========================")
print("Extraction Completed")
print("==========================")
print("Total Images Extracted:", total_images)