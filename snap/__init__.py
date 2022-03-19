import os.path
import time
import datetime
import pyautogui
import pytesseract
import winsound
import sqlite3


class OutSQLite:
    def __init__(self, db_name=None):
        self.db_name = db_name or 'snap.db'
        self._db = None
        self.name = 'OutSQLite'
        self.setup()

    def setup(self):
        tables = {'items': '''CREATE TABLE items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100),
                bundle INTEGER,
                price FLOAT,
                price_per_one FLOAT,
                UNIQUE(name))''',
                  'prices': '''CREATE TABLE prices (
                price_id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                date DATE,
                price FLOAT,
                FOREIGN KEY(item_id) REFERENCES items(item_id),
                UNIQUE(item_id, date))''',
                  'crafts': '''CREATE TABLE crafts (
                craft_id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                quantity INTEGER,
                cost FLOAT,
                cost_per_one FLOAT,
                FOREIGN KEY(item_id) REFERENCES items(item_id),
                UNIQUE(item_id))''',
                  'mats': '''CREATE TABLE mats (
                mat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                craft_id INTEGER,
                item_id INTEGER,
                quantity INTEGER,
                FOREIGN KEY(craft_id) REFERENCES crafts(craft_id),
                FOREIGN KEY(item_id) REFERENCES items(item_id),
                UNIQUE(craft_id, item_id))''',
                  'prices_history_v': 'CREATE OR UPDATE VIEW prices_history_v AS '
                                      'SELECT i.name, i.bundle, p.date, p.price FROM items i '
                                      'LEFT JOIN prices p ON i.item_id = p.item_id '
                                      'ORDER BY i.name, p.date'
                  }
        self._db = sqlite3.connect(self.db_name)
        res = self._db.execute("SELECT name FROM sqlite_master WHERE type in ('table', 'view')")
        db_tables = [row[0] for row in res]
        for table in tables.keys():
            if table not in db_tables:
                print(f"[{self.name}] Creating {table}")
                self._db.execute(tables[table])

        self._db.commit()

    def save(self, data):
        db = sqlite3.connect(self.db_name)
        cursor = db.cursor()
        for row in data:
            query = ('INSERT INTO items (name, bundle, price, price_per_one)'
                     'VALUES (?, ?, ?, ?) ON CONFLICT(name) DO UPDATE SET price = ?, price_per_one = ?')
            cursor.execute(query, (
                row['name'], row['bundle'], row['price'], row['price_per_one'], row['price'], row['price_per_one']))
            res = cursor.execute('SELECT item_id FROM items WHERE name = ?', (row['name'],))
            last_insert_id = res.fetchone()[0]
            date = datetime.date.today().strftime("%Y-%m-%d")
            query = ('INSERT INTO prices (item_id, date, price) VALUES (?, ?, ?)'
                     'ON CONFLICT(item_id, date) DO UPDATE SET price = ?')
            cursor.execute(query, (last_insert_id, date, row['price'], row['price']))
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
                fh.write(f"{row['name']},{bundle},{row['price']},{price_per_one}\n")


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
            print(f"[{self.name}] {row['name']}: {row['price']}/{bundle}={price_per_one}")


class Snap:
    def __init__(self, scans=1, outputs=None, tesseract_cmd=None, tmp_dir=None):
        self._outputs = outputs or (OutPrint())
        self._tesseract_cmd = tesseract_cmd
        self.tmp_dir = tmp_dir or 'tmp'
        self.scans = scans
        self._row_height = 76
        self._items_location = {'x': 450, 'y': 275, 'width': 300, 'height': self._row_height}
        self._prices_location = {'x': 850, 'y': 275, 'width': 213, 'height': self._row_height}
        self.data = []
        self._setup()

    def _setup(self):
        if not os.path.isdir(self.tmp_dir):
            os.mkdir(self.tmp_dir)
        pytesseract.pytesseract.tesseract_cmd = self._tesseract_cmd

    def _snap(self):
        image_org = pyautogui.screenshot()
        image_org.save(f"{self.tmp_dir}/image.png")
        winsound.Beep(440, 500)
        raw_data = []
        for a in range(10):
            x1 = self._items_location['x']
            x2 = x1 + self._items_location['width']
            y1 = a * self._items_location['height'] + self._items_location['y']
            y2 = (a + 1) * self._items_location['height'] + self._items_location['y']
            image = image_org.crop((x1, y1, x2, y2))

            x1 = self._prices_location['x']
            x2 = x1 + self._prices_location['width']
            y1 = a * self._prices_location['height'] + self._prices_location['y']
            y2 = (a + 1) * self._prices_location['height'] + self._prices_location['y']
            image2 = image_org.crop((x1, y1, x2, y2))

            image = image.convert("L")
            image2 = image2.convert("L")
            image.save(f"{self.tmp_dir}/image{a}_name.png")
            image2.save(f"{self.tmp_dir}/image{a}_price.png")
            result = pytesseract.image_to_string(image, lang='eng', config='')
            result2 = pytesseract.image_to_string(image2, config='-c tessedit_char_whitelist=0123456789@')

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
                            print(f"[Skip] Possible trashy recognition: {row}: {price}")
                        elif price:
                            print(f"[Add] Found new entry: {row}: {price}")
                            price = int(price)
                            price = price / 10
                            self.data.append({'name': row,
                                              'price': price})
                            winsound.Beep(760, 50)
                            new_entry = True
                        else:
                            print(f"[Skip] Found new entry, couldn't recognize price: {row}")
                            winsound.Beep(320, 50)
                    else:
                        winsound.Beep(320, 50)
                elif row != '' and new_entry:
                    bundle = row
                    bundle = int(bundle.split("bundles of ")[1].split(" units")[0])
                    self.data[-1]['bundle'] = bundle
                    new_entry = False

    def run(self):
        time.sleep(2)
        for i in range(self.scans):
            self._snap()
        self._parse()

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
