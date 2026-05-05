# LLM Trap Detection
Dumps any text that is close (or equal) to the background color. Also catches tiny text and rendering tricks.

Might consider adding HTML and MD in the future.


You need the python dependencies prior to running:
    `pip install -r requirements.txt`

Run using:
    `python detector.py <file.pdf>`

You may also clean the file (remove hidden text):
    `python detector --clean <file.pdf>`

It will report any white text found and the metadata of the file.

It will also generate a new file with the hidden text, now in red.
