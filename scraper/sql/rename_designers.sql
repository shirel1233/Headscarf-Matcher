-- מיגרציה חד-פעמית: מעבר משמות עבריים למזהים באנגלית בעמודה "designer".
-- חייבים להריץ את זה ב-Supabase (SQL Editor) לפני ההרצה הבאה של הסורק בלי --dry-run.
-- בטוח להרצה חוזרת: אחרי הריצה הראשונה אין שורות עם השמות הישנים, אז אין מה לשנות.

BEGIN;

UPDATE scarf SET designer = 'hadara'      WHERE designer = 'הדרא';
UPDATE scarf SET designer = 'etcasia'     WHERE designer = 'אתכסיא';
UPDATE scarf SET designer = 'avia_sason'  WHERE designer = 'אביה ששון';

-- בדיקה: אמורה להחזיר 0 שורות. אם לא, כנראה יש שם אחר שלא נכלל כאן.
SELECT designer, COUNT(*) FROM scarf
WHERE designer NOT IN ('hadara', 'etcasia', 'avia_sason') OR designer IS NULL
GROUP BY designer;

COMMIT;
