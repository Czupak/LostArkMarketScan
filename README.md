# LostArkMarketScan
Experimental tool, capturing screenshots of Market window and saving results to different outputs.

# Dependencies
Python 3 and Tesseract are required.

You need to install Tesseract and setup the path in snap.py.

https://github.com/UB-Mannheim/tesseract/wiki

# Usage
Currently coordinates to look for items are hardcoded, therefore will probably work for a very specific resolution.

Tested on 2560x1440.

21:9 might work with changes in `snap/__init__.py`

        self._row_height = 57
        self._items_location = {'x': 340, 'y': 275 + 110, 'width': 300, 'height': self._row_height}
        self._prices_location = {'x': 645, 'y': 275 + 110, 'width': 150, 'height': self._row_height}

Market window needs to be moved to the top-left corner, then search for the items you are interested in.
Run snap.py and ALT-TAB quickly to the game window. The script will make a beep sound, which means the screenshot has been captured.
After a second the script will try to recognize items (OCR) and will beep 10 times. High beep means, an item has been recognized. Low beep means that item has not been recognized.

You can scan several pages without running the script for each of them. To do that, change "scans=1" parameter in Snap.py to number of pages.
The script will run in a loop, so prepare the first page, run the script and ALT-TAB. Repeat those steps:
1. Wait for initial beep, which means the screenshot has been taken.
2. Change the page.
3. Wait for 10 beeps (low or high), which means the previous page is being recognized.

Results will be saved to snap.csv file and SQLite snap.db

# SQLite [TODO]
Tables: items, prices

View: prices_history_v

# Images
![image](https://user-images.githubusercontent.com/10432092/159123791-bec9a77f-133b-4a0a-a7d8-0fadebd61ac1.png)
![image](https://user-images.githubusercontent.com/10432092/159123817-f1e813f9-dd84-493f-a56a-2de4790ba6d5.png)
![image](https://user-images.githubusercontent.com/10432092/159123841-72750299-dfa0-4757-a569-5d732c09f2ae.png)


