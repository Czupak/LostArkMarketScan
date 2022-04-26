import os.path
import time
import datetime
import pyautogui
import pytesseract
import cv2 as cv
import numpy as np
import winsound
import sqlite3


class OutSQLite:

    def __init__(self, db_name=None):
        self.db_name = db_name or 'snap.db'
        self._db = None
        self.name = 'OutSQLite'
        self.setup()

    def setup(self):
        tables = {
            'items':
                '''CREATE TABLE items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100),
                bundle INTEGER,
                price FLOAT,
                price_per_one FLOAT,
                UNIQUE(name))''',
            'prices':
                '''CREATE TABLE prices (
                price_id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                date DATE,
                price FLOAT,
                FOREIGN KEY(item_id) REFERENCES items(item_id),
                UNIQUE(item_id, date))''',
            'crafts':
                '''CREATE TABLE crafts (
                craft_id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                quantity INTEGER,
                cost FLOAT,
                cost_per_one FLOAT,
                FOREIGN KEY(item_id) REFERENCES items(item_id),
                UNIQUE(item_id))''',
            'mats':
                '''CREATE TABLE mats (
                mat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                craft_id INTEGER,
                item_id INTEGER,
                quantity INTEGER,
                FOREIGN KEY(craft_id) REFERENCES crafts(craft_id),
                FOREIGN KEY(item_id) REFERENCES items(item_id),
                UNIQUE(craft_id, item_id))''',
            'prices_history_v': [
                'DROP VIEW IF EXISTS prices_history_v',
                '''CREATE VIEW prices_history_v AS 
               SELECT i.name, i.bundle, p.date, p.price FROM items i
               LEFT JOIN prices p ON i.item_id = p.item_id
               ORDER BY i.name, p.date'''
            ]
        }
        self._db = sqlite3.connect(self.db_name)
        res = self._db.execute(
            "SELECT name FROM sqlite_master WHERE type in ('table')")
        db_tables = [row[0] for row in res]
        for table in tables.keys():
            if table not in db_tables:
                print(f"[{self.name}] Creating {table}")
                queries = tables[table]
                if type(queries) != list:
                    queries = [queries]
                for query in queries:
                    self._db.execute(query)

        self._db.commit()

    def save(self, data):
        db = sqlite3.connect(self.db_name)
        cursor = db.cursor()
        for row in data:
            query = (
                'INSERT INTO items (name, bundle, price, price_per_one)'
                'VALUES (?, ?, ?, ?) ON CONFLICT(name) DO UPDATE SET price = ?, price_per_one = ?'
            )
            cursor.execute(
                query,
                (row['name'], row['bundle'], row['price'], row['price_per_one'],
                 row['price'], row['price_per_one']))
            res = cursor.execute('SELECT item_id FROM items WHERE name = ?',
                                 (row['name'],))
            last_insert_id = res.fetchone()[0]
            date = datetime.date.today().strftime("%Y-%m-%d")
            query = (
                'INSERT INTO prices (item_id, date, price) VALUES (?, ?, ?)'
                'ON CONFLICT(item_id, date) DO UPDATE SET price = ?')
            cursor.execute(query,
                           (last_insert_id, date, row['price'], row['price']))
            db.commit()


class OutCSV:

    def __init__(self, file_name=None):
        self.name = 'OutCSV'
        self.file_name = file_name or 'snap.csv'

    def save(self, data):
        with open(self.file_name, "w") as fh:
            fh.write("Name,Bundle,Price,PricePerOne\n")
            for row in data:
                bundle = 1
                price_per_one = row['price']
                if 'bundle' in row:
                    bundle = row['bundle']
                    price_per_one = row['price_per_one']
                fh.write(
                    f"{row['name']},{bundle},{row['price']},{price_per_one}\n")


class OutPrint:

    def __init__(self):
        self.name = 'OutPrint'

    def save(self, data):
        for row in data:
            bundle = 1
            price_per_one = row['price']
            if 'bundle' in row:
                bundle = row['bundle']
                price_per_one = row['price_per_one']
            print(
                f"[{self.name}] {row['name']}: {row['price']}/{bundle}={price_per_one}"
            )


class Snap:

    def __init__(self, outputs=None, tesseract_cmd=None, tmp_dir=None):
        self.key_terminate = 'Num Lock'
        self.key_snapshot = 'Scroll Lock'
        self._outputs = outputs or (OutPrint())
        self._tesseract_cmd = tesseract_cmd
        self.tmp_dir = tmp_dir or 'tmp'
        # self._row_height = 57
        # self._items_location = {'x': 340, 'y': 275 + 110, 'width': 300, 'height': self._row_height}
        # self._prices_location = {'x': 645, 'y': 275 + 110, 'width': 150, 'height': self._row_height}
        self._row_height = 76
        self._items_location = {
            'x': 450,
            'y': 275,
            'width': 300,
            'height': self._row_height
        }
        self._prices_location = {
            'x': 850,
            'y': 275,
            'width': 213,
            'height': self._row_height
        }
        self.data = []
        self._setup()

    def _setup(self):
        if not os.path.isdir(self.tmp_dir):
            os.mkdir(self.tmp_dir)
        pytesseract.pytesseract.tesseract_cmd = self._tesseract_cmd

    def get_key_state(self, state):
        import ctypes
        hll_dll = ctypes.WinDLL("User32.dll")
        states = {
            'Scroll Lock': 0x91,
            'Num Lock': 0x90,
            'Caps Lock': 0x14,
        }
        return hll_dll.GetKeyState(states[state])

    def image_noise_reduction(self, file):
        img = cv.imread(file, 0)
        blur = cv.GaussianBlur(img, (5, 5), 0)
        # find normalized_histogram, and its cumulative distribution function
        hist = cv.calcHist([blur], [0], None, [256], [0, 256])
        hist_norm = hist.ravel() / hist.sum()
        Q = hist_norm.cumsum()
        bins = np.arange(256)
        fn_min = np.inf
        thresh = -1
        for i in range(1, 256):
            p1, p2 = np.hsplit(hist_norm, [i])  # probabilities
            q1, q2 = Q[i], Q[255] - Q[i]  # cum sum of classes
            if q1 < 1.e-6 or q2 < 1.e-6:
                continue
            b1, b2 = np.hsplit(bins, [i])  # weights
            # finding means and variances
            m1, m2 = np.sum(p1 * b1) / q1, np.sum(p2 * b2) / q2
            v1, v2 = np.sum(((b1 - m1)**2) * p1) / q1, np.sum(
                ((b2 - m2)**2) * p2) / q2
            # calculates the minimization function
            fn = v1 * q1 + v2 * q2
            if fn < fn_min:
                fn_min = fn
                thresh = i
        # find otsu's threshold value with OpenCV function
        ret, otsu = cv.threshold(blur, 0, 255,
                                 cv.THRESH_BINARY + cv.THRESH_OTSU)
        print("{} {}".format(thresh, ret))
        return otsu

    def _snap(self):
        image_org = pyautogui.screenshot()
        image_org.save(f"{self.tmp_dir}/image.png")
        # from PIL import Image
        # image_org = Image.open(f'{self.tmp_dir}/image.png')
        winsound.Beep(440, 500)
        raw_data = []
        for a in range(10):
            x1 = self._items_location['x']
            x2 = x1 + self._items_location['width']
            y1 = a * self._items_location['height'] + self._items_location['y']
            y2 = (a + 1
                 ) * self._items_location['height'] + self._items_location['y']
            image = image_org.crop((x1, y1, x2, y2))

            x1 = self._prices_location['x']
            x2 = x1 + self._prices_location['width']
            y1 = a * self._prices_location['height'] + self._prices_location['y']
            y2 = (a + 1) * self._prices_location[
                'height'] + self._prices_location['y']
            image2 = image_org.crop((x1, y1, x2, y2))

            image = image.convert("L")
            # image2 = image2.convert("L")
            image.save(f"{self.tmp_dir}/image{a}_name.png")
            image2.save(f"{self.tmp_dir}/image{a}_price.png")

            # n = self.image_noise_reduction(f"{self.tmp_dir}/image{a}_name.png")
            # p = self.image_noise_reduction(f"{self.tmp_dir}/image{a}_price.png")
            # cv.imwrite(f"{self.tmp_dir}/image{a}_ns_name.png", n)
            # cv.imwrite(f"{self.tmp_dir}/image{a}_ns_price.png", p)

            # cv_img = cv.imread(f"{self.tmp_dir}/image{a}_name.png")
            # cv_img = cv.medianBlur(cv_img, 5)
            # ret, thresh1 = cv.threshold(cv_img, 127, 255, cv.THRESH_TRUNC)
            # cv.imwrite(f'{self.tmp_dir}/cv_{a}_image.png', thresh1)
            # cv.imwrite(f'{self.tmp_dir}/cv_{a}_image_ret.png', ret)
            #
            # cv_img = cv.imread(f"{self.tmp_dir}/image{a}_price.png")
            # cv_img = cv.medianBlur(cv_img, 5)
            # ret, thresh1 = cv.threshold(cv_img, 127, 255, cv.THRESH_TRUNC)
            # cv.imwrite(f'{self.tmp_dir}/cv_{a}_price.png', thresh1)
            # cv.imwrite(f'{self.tmp_dir}/cv_{a}_price_ret.png', ret)

            result = pytesseract.image_to_string(image, lang='eng', config='')
            result2 = pytesseract.image_to_string(
                image2, config='-c tessedit_char_whitelist=0123456789@')

            raw_data.append([result, result2])
        for entry in raw_data:
            parsed = entry[0].split("\n")
            new_entry = False
            for row in parsed:
                if row != '' and row[0] != "[":
                    already = [a for a in self.data if a['name'] == row]
                    if len(already) == 0:
                        price = entry[1].strip().replace("@", "")
                        if row[0] == row[0].lower():
                            print(
                                f"[Skip] Possible trashy recognition: {row}: {price}"
                            )
                        elif price:
                            print(f"[Add] Found new entry: {row}: {price}")
                            price = int(price)
                            price = price / 10
                            self.data.append({'name': row, 'price': price})
                            winsound.Beep(760, 50)
                            new_entry = True
                        else:
                            print(
                                f"[Skip] Found new entry, couldn't recognize price: {row}"
                            )
                            winsound.Beep(320, 50)
                    else:
                        winsound.Beep(320, 50)
                elif row != '' and new_entry:
                    parsed_subtext = self._parse_subtext(row)
                    if 'bundle' in parsed_subtext:
                        self.data[-1]['bundle'] = parsed_subtext['bundle']
                    new_entry = False

    def _parse_subtext(self, row):
        parsed = {}
        if "bundles of " in row:
            parsed['bundle'] = int(
                row.split("bundles of ")[1].split(" units")[0])
        return parsed

    def run(self):
        winsound.Beep(640, 200)
        snap_key_state = self.get_key_state(self.key_snapshot)
        end_key_state = self.get_key_state(self.key_terminate)
        new_end_key_state = end_key_state
        print(
            f'Awaiting command: [Screenshot: {self.key_snapshot}] [Save and quit: {self.key_terminate}]'
        )
        while end_key_state == new_end_key_state:
            new_snap_key_state = self.get_key_state(self.key_snapshot)
            new_end_key_state = self.get_key_state(self.key_terminate)
            if snap_key_state != new_snap_key_state:
                snap_key_state = new_snap_key_state
                print(f"[{self.key_snapshot}] detected, taking screenshot...")
                self._snap()
                self._parse()
                self.save()
            time.sleep(0.2)
        winsound.Beep(640, 100)
        winsound.Beep(640, 100)
        print(f"[{self.key_terminate}] detected, terminating...")

    def get_data(self):
        return self.data

    def _parse(self):
        for row in self.data:
            if 'bundle' not in row:
                row['bundle'] = 1
            row['price_per_one'] = row['price'] / row['bundle']

    def save(self):
        for output in self._outputs:
            print(f'Output: {output.name}')
            output.save(self.data)
