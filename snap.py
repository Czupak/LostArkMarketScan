from snap import Snap, OutCSV, OutPrint, OutSQLite

if __name__ == '__main__':
    snap = Snap(outputs=(
                    OutCSV(file_name='snap.csv'),
                    OutPrint(),
                    OutSQLite(db_name='snap.db')
                ),
                tesseract_cmd=r'C:\Program Files\Tesseract-OCR\tesseract.exe')
    snap.run()

