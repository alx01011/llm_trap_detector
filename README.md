# LLM Trap Detection
Pretty much dumps white text and metadata of a PDF file.

Might consider adding HTML and MD in the future.


You need the python dependencies prior to running:
    `pip install -r requirements.txt`

Run using:
    `python detector.py <file.pdf>`

It will report any white text found and the metadata of the file.

It will also generate a new file with the hidden text, now in red.
