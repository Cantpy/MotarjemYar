import os
import pandas as pd
from shared import get_resource_path, to_persian_number
import sqlite3


DB_PATH = get_resource_path('databases', 'services.db')
EXCEL_FILE_PATH = get_resource_path('databases', 'services_data.xlsx')


def import_excel_to_services():
    """Import data from Excel file to Services table."""
    try:
        if not os.path.exists(EXCEL_FILE_PATH):
            print(f"در مسیر زیر فایل اکسلی وجود ندارد:\n{EXCEL_FILE_PATH}")
            return False

        print(f"در حال خواندن فایل اکسل در مسیر: {EXCEL_FILE_PATH}")
        df = pd.read_excel(EXCEL_FILE_PATH, sheet_name='Sheet1')

        expected_columns = ['name', 'base_price', 'dynamic_price_name_1', 'dynamic_price_1',
                            'dynamic_price_name_2', 'dynamic_price_2']

        # Validate and rename
        if len(df.columns) >= 6:
            df = df.iloc[:, :6].copy()
            df.columns = expected_columns
        else:
            print("تعداد ستون‌های فایل اکسل کمتر از ۶ تاست!")
            return False

        df = df.dropna(subset=['name'])

        # Convert prices to int safely
        for col in ['base_price', 'dynamic_price_1', 'dynamic_price_2']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

        # Nullify dynamic_price_name_* if price is 0
        df.loc[df['dynamic_price_1'] == 0, 'dynamic_price_name_1'] = None
        df.loc[df['dynamic_price_2'] == 0, 'dynamic_price_name_2'] = None

        print(f"تعداد {to_persian_number(len(df))} مدرک برای افزودن پیدا شد")

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM services")
            existing_names = {row[0] for row in cursor.fetchall()}

            df_unique = df.drop_duplicates(subset=['name'], keep='first')
            df_new = df_unique[~df_unique['name'].isin(existing_names)]

            duplicates_in_excel = len(df) - len(df_unique)
            duplicates_in_db = len(df_unique) - len(df_new)

            if duplicates_in_excel > 0:
                print(f"{to_persian_number(duplicates_in_excel)} مدرک تکراری در فایل اکسل یافت شد.")
            if duplicates_in_db > 0:
                print(f"{to_persian_number(duplicates_in_db)} مدرک تکراری در پایگاه داده یافت شد.")

            print(f"تعداد {to_persian_number(len(df_new))} مدرک جدید پیدا شد")

            if len(df_new) == 0:
                print("مدرک جدیدی برای افزودن وجود ندارد.")
                return True

            insert_query = """
            INSERT OR IGNORE INTO services 
            (name, base_price, dynamic_price_name_1, dynamic_price_1, dynamic_price_name_2, dynamic_price_2)
            VALUES (?, ?, ?, ?, ?, ?)
            """

            records_inserted = 0
            records_skipped = 0

            for _, row in df_new.iterrows():
                try:
                    cursor.execute(insert_query, (
                        str(row['name']),
                        int(row['base_price']),
                        row['dynamic_price_name_1'],
                        int(row['dynamic_price_1']),
                        row['dynamic_price_name_2'],
                        int(row['dynamic_price_2']),
                    ))
                    if cursor.rowcount > 0:
                        records_inserted += 1
                    else:
                        records_skipped += 1
                except sqlite3.Error as e:
                    print(f"خطا در افزودن مدرک {row['name']}: {str(e)}")
                    records_skipped += 1

            conn.commit()
            print(f"تعداد {to_persian_number(records_inserted)} مدرک با موفقیت افزوده شد.")
            if records_skipped > 0:
                print(f"{to_persian_number(records_skipped)} مدرک نادیده گرفته شد (تکراری یا مشکل‌دار).")

            cursor.execute("SELECT COUNT(*) FROM services")
            total_count = cursor.fetchone()[0]
            print(f"تعداد کل مدارک در پایگاه داده: {to_persian_number(total_count)}")

        return True

    except Exception as e:
        print(f"خطا در بارگذاری مدارک از طریق فایل اکسل:\n{str(e)}")
        return False
