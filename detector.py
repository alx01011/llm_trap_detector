import fitz
import sys

from matplotlib import text

class location:
    def __init__ (self, page_num, line):
        self.page_num = page_num
        self.line = line

pdf_file = None

# check if the color is near white 
# assuming a white background, near white text would be hard to read
def is_near_white(color, threshold=10):
    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = color & 0xFF
    
    return r >= 255 - threshold and g >= 255 - threshold and b >= 255 - threshold

def get_white_text(pdf_path):
    doc = fitz.open(pdf_path)
    white_texts = {}

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_dict = page.get_text("dict")
        blocks = page_dict["blocks"]
        
        font_list = page.get_fonts()

        for block in blocks:
            if 'lines' in block:
                for line in block["lines"]:
                    has_white = False
                    for span in line["spans"]:
                        # get color and text
                        color = span['color']
                        text = span['text']
                        # is color white?
                        if is_near_white(color):
                            white_texts[page_num + 1] = white_texts.get(page_num + 1, []) + [text]
                            # replace in the file with red text
                            page.insert_text(
                                span['origin'], 
                                span['text'], 
                                fontsize=span['size'], 
                                fontname="helv",
                                color=(1, 0, 0)
                            )
                            
                            

    if white_texts:
        doc.save("modified_" + pdf_path)     
    doc.close()
    return white_texts


def extract_metadata(pdf_path):
    doc = fitz.open(pdf_path)
    metadata = doc.metadata
    doc.close()
    return metadata


def main():
    global pdf_file
    if len(sys.argv) != 2:
        print("Usage: python pdf_check.py <pdf_file>")
        return

    file = sys.argv[1]

    white_text = get_white_text(file)
    metadata   = extract_metadata(file)

    if white_text:
        print("Suspicious white text found in the PDF:")
        for page_num, texts in white_text.items():
            print(f"Page {page_num}:")
            for text in texts:
                print(text, end='')
            print("\n")
            
            
            
    
    print("\n\nPDF Metadata:")
    for key, value in metadata.items():
        print(f"\t{key}: {value}")


if __name__ == "__main__":
    main()