import pymupdf
import sys
from collections import Counter


class location:
    def __init__(self, page_num, line):
        self.page_num = page_num
        self.line = line


pdf_file = None

ZOOM = 2
TINY_FONT_PT = 1.0
VISIBILITY_RATIO = 0.01
BG_SIMILARITY = 20


def color_int_to_rgb(color):
    return ((color >> 16) & 0xFF, (color >> 8) & 0xFF, color & 0xFF)


def colors_similar(c1, c2, threshold):
    return all(abs(a - b) <= threshold for a, b in zip(c1, c2))


# Sample pixels in a thin frame just outside the text bbox; mode filters out
# stray glyph pixels from neighboring text.
def sample_local_background(pix, bbox, zoom, margin=3):
    x0, y0, x1, y1 = [v * zoom for v in bbox]
    samples = []

    for py in (int(y0 - margin), int(y1 + margin)):
        if 0 <= py < pix.height:
            for px in range(max(0, int(x0)), min(pix.width, int(x1) + 1)):
                samples.append(pix.pixel(px, py))

    for px in (int(x0 - margin), int(x1 + margin)):
        if 0 <= px < pix.width:
            for py in range(max(0, int(y0)), min(pix.height, int(y1) + 1)):
                samples.append(pix.pixel(px, py))

    if not samples:
        return None
    return Counter(samples).most_common(1)[0][0]


# Fraction of pixels inside the bbox that differ from the local background.
# Hidden text (color-matched, covered, or rendered at zero size)
def visibility_ratio(pix, bbox, local_bg, zoom, step=2):
    x0, y0, x1, y1 = [int(v * zoom) for v in bbox]
    x0, x1 = max(0, x0), min(pix.width, x1)
    y0, y1 = max(0, y0), min(pix.height, y1)

    if x1 <= x0 or y1 <= y0:
        return 0.0

    differing = 0
    total = 0
    for py in range(y0, y1, step):
        for px in range(x0, x1, step):
            total += 1
            if not colors_similar(pix.pixel(px, py), local_bg, BG_SIMILARITY):
                differing += 1

    return differing / total if total else 0.0


def detect_hidden(span, pix, page_rect, zoom):
    bbox = span['bbox']

    if span['size'] < TINY_FONT_PT:
        return "tiny font"

    span_rect = pymupdf.Rect(bbox)
    if span_rect.is_empty or not span_rect.intersects(page_rect):
        return "off-page"

    local_bg = sample_local_background(pix, bbox, zoom)
    if local_bg is None:
        return None

    text_color = color_int_to_rgb(span['color'])
    if colors_similar(text_color, local_bg, BG_SIMILARITY):
        return "color match"

    if visibility_ratio(pix, bbox, local_bg, zoom) < VISIBILITY_RATIO:
        return "covered"

    return None


def get_hidden_text(pdf_path):
    doc = pymupdf.open(pdf_path)
    hidden_texts = {}
    matrix = pymupdf.Matrix(ZOOM, ZOOM)

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_dict = page.get_text("dict")
        blocks = page_dict["blocks"]
        pix = page.get_pixmap(matrix=matrix, colorspace=pymupdf.csRGB)

        hidden_spans = []
        for block in blocks:
            if 'lines' not in block:
                continue
            for line in block["lines"]:
                line_hits = []
                for span in line["spans"]:
                    text = span['text']
                    if not text.strip():
                        continue

                    reason = detect_hidden(span, pix, page.rect, ZOOM)
                    if reason:
                        line_hits.append((span, reason))
                        hidden_spans.append(span)
                        page.add_redact_annot(pymupdf.Rect(span['bbox']))

                if line_hits:
                    phrase = " ".join(s['text'].strip() for s, _ in line_hits)
                    reasons = sorted({r for _, r in line_hits})
                    hidden_texts.setdefault(page_num + 1, []).append((phrase, ", ".join(reasons)))

        if hidden_spans:
            page.apply_redactions()
            for span in hidden_spans:
                page.insert_text(
                    span['origin'],
                    span['text'],
                    fontsize=max(span['size'], 8),
                    fontname="helv",
                    color=(1, 0, 0)
                )

    if hidden_texts:
        doc.save("modified_" + pdf_path)
    doc.close()
    return hidden_texts


def extract_metadata(pdf_path):
    doc = pymupdf.open(pdf_path)
    metadata = doc.metadata
    doc.close()
    return metadata


def main():
    global pdf_file
    if len(sys.argv) != 2:
        print("Usage: python detector.py <pdf_file>")
        return

    file = sys.argv[1]

    hidden_text = get_hidden_text(file)
    metadata = extract_metadata(file)

    if hidden_text:
        print("Suspicious hidden text found in the PDF:")
        for page_num, entries in hidden_text.items():
            print(f"Page {page_num}:")
            for text, reason in entries:
                print(f"  [{reason}] {text}")
            print()

    print("\nPDF Metadata:")
    for key, value in metadata.items():
        print(f"\t{key}: {value}")


if __name__ == "__main__":
    main()
