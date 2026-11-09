"""
טוען קבצי JSON שנשמרו בתיקיית output/ לטבלת scarf ב-Supabase.

שימוש (מתוך תיקיית scraper, עם ה-venv):
    python load_json.py

כל קובץ נטען בנפרד. ההעלאה משתמשת באותו upsert של db.py (לפי purchaseUrl),
לכן אפשר להריץ את הסקריפט שוב בלי לקבל כפילויות.
"""
import glob
import json
import os
from datetime import datetime, timezone

from db import get_conn, save_scarves

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


def main():
    files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "*.json")))
    if not files:
        print(f"לא נמצאו קבצי JSON בתיקייה {OUTPUT_DIR}")
        return

    conn = get_conn()
    try:
        for path in files:
            with open(path, encoding="utf-8") as f:
                scarves = json.load(f)
            if not scarves:
                print(f"{os.path.basename(path)}: הקובץ ריק, מדלגים")
                continue

            # שם המעצבת נלקח מהנתונים עצמם, כדי שיתאים לערך שנשמר ב-DB
            designer = scarves[0]["designer"]
            run_started = datetime.now(timezone.utc)
            stats = save_scarves(conn, scarves, designer, run_started)
            print(f"{os.path.basename(path)}: {len(scarves)} מוצרים, {stats}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
