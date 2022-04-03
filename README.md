# LostArkMarketScan
Experimental tool, capturing screenshots of Market window and saving results to different outputs.

# Dependencies
Python 3 and Tesseract are required.

You need to install Tesseract and setup the path in snap.py.

https://github.com/UB-Mannheim/tesseract/wiki

# Usage
Currently coordinates to look for items are hardcoded, therefore will probably work for a very specific resolution.
Working on self-calibration, so the coordinates could be pointed by the user.

Tested on 2560x1440.

21:9 might work with changes in `snap/__init__.py`

        self._row_height = 57
        self._items_location = {'x': 340, 'y': 275 + 110, 'width': 300, 'height': self._row_height}
        self._prices_location = {'x': 645, 'y': 275 + 110, 'width': 150, 'height': self._row_height}

Market window needs to be moved to the top-left corner.
1. Run snap.py, you'll hear a beep. Alt-tab to the game.
2. Make a search.
3. Toggle Scroll-Lock to capture results.
- The script will try to recognize items (OCR) and will beep for each item found.
- High beep means, an item has been recognized. Low beep means that item has not been recognized.
4. Repeat step 2-3.
5. Toggle Num-Lock to terminate the script.


Results will be saved to snap.csv file and SQLite snap.db

# SQLite [TODO]
Tables: items, prices

View: prices_history_v

# Images
![image](https://user-images.githubusercontent.com/10432092/159123791-bec9a77f-133b-4a0a-a7d8-0fadebd61ac1.png)
![image](https://user-images.githubusercontent.com/10432092/159123817-f1e813f9-dd84-493f-a56a-2de4790ba6d5.png)
![image](https://user-images.githubusercontent.com/10432092/159123841-72750299-dfa0-4757-a569-5d732c09f2ae.png)

# In the future
![image](https://user-images.githubusercontent.com/10432092/161422469-793bf8a3-f9b7-437c-9e14-e819b60fb5e2.png)


