"""
כתיבה לטבלת scarf ב-Supabase (PostgreSQL) ישירות מפייתון.

שמות העמודות מצוטטים (camelCase) כי כך Prisma 8 יוצר אותן כשאין @map.
אם ב-Supabase Table Editor העמודות אצלך נראות אחרת (למשל purchase_url), יש להתאים כאן.
"""
import os
import uuid

import psycopg
from dotenv import find_dotenv, load_dotenv

UPSERT_SQL = """
INSERT INTO scarf
    (id, name, color, pattern, "imageUrl", "purchaseUrl", designer,
     price, currency, "inStock", "externalId", "lastSeenAt", "createdAt")
VALUES
    (%(id)s, %(name)s, %(color)s, %(pattern)s, %(imageUrl)s, %(purchaseUrl)s, %(designer)s,
     %(price)s, %(currency)s, %(inStock)s, %(externalId)s, %(seen)s, %(seen)s)
ON CONFLICT ("purchaseUrl") DO UPDATE SET
    name         = EXCLUDED.name,
    color        = EXCLUDED.color,
    pattern      = EXCLUDED.pattern,
    "imageUrl"   = EXCLUDED."imageUrl",
    designer     = EXCLUDED.designer,
    price        = EXCLUDED.price,
    currency     = EXCLUDED.currency,
    "inStock"    = EXCLUDED."inStock",
    "externalId" = EXCLUDED."externalId",
    "lastSeenAt" = EXCLUDED."lastSeenAt"
RETURNING (xmax = 0) AS inserted
"""

STALE_SQL = """
UPDATE scarf SET "inStock" = false
WHERE designer = %s
  AND "inStock" = true
  AND ("lastSeenAt" IS NULL OR "lastSeenAt" < %s)
"""


def get_conn():
    load_dotenv(find_dotenv(usecwd=True))
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is missing. Add it to your .env file.")
    conn = psycopg.connect(url)
    conn.prepare_threshold = None  # נדרש כשמתחברים דרך ה-pooler של Supabase
    return conn


def save_scarves(conn, scarves, designer, run_started):
    """שומר/מעדכן מטפחות. מוצר שלא נמצא יותר באתר מסומן כאזל מהמלאי."""
    inserted = updated = 0
    with conn.cursor() as cur:
        for s in scarves:
            params = {**s, "id": uuid.uuid4(), "seen": run_started}
            cur.execute(UPSERT_SQL, params)
            if cur.fetchone()[0]:
                inserted += 1
            else:
                updated += 1

        stale = 0
        if scarves:  # הגנה: אם הסריקה החזירה 0 מוצרים כנראה משהו נשבר, לא מאפסים מלאי
            cur.execute(STALE_SQL, (designer, run_started))
            stale = cur.rowcount
    conn.commit()
    return {"inserted": inserted, "updated": updated, "marked_out_of_stock": stale}
