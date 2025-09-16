# motarjemyar/admin_reports/descriptive_search_parser.py

import jdatetime
import re
from datetime import date, timedelta


class DescriptiveSearchParser:
    """
    Parses a Persian natural language query into a structured
    dictionary for the advanced search _logic.
    """

    def __init__(self):
        self.KEYWORDS = {
            'unpaid': ['پرداخت نشده', 'معوق', 'بدهکار', 'وصول نشده'],
            'frequent': ['پرتکرار', 'پرکار', 'همیشگی', 'دائمی'],
            'docs': ['سند', 'مدرک', 'اسناد', 'مدارک']
        }
        self.MONTHS = {
            'فروردین': 1, 'اردیبهشت': 2, 'خرداد': 3, 'تیر': 4,
            'مرداد': 5, 'شهریور': 6, 'مهر': 7, 'آبان': 8,
            'آذر': 9, 'دی': 10, 'بهمن': 11, 'اسفند': 12
        }

    def _find_search_type(self, query: str) -> str | None:
        """Determines the main intent of the query."""
        for search_type, keywords in self.KEYWORDS.items():
            for keyword in keywords:
                if keyword in query:
                    return search_type
        return None

    def _extract_date_range(self, query: str) -> tuple[date, date] | None:
        """Extracts date ranges from the query (e.g., 'سال 1402', 'امسال')."""
        today = jdatetime.date.today()

        for month_name, month_num in self.MONTHS.items():
            if month_name in query:
                # A month was found. Now, was a year specified?
                year_match = re.search(r'\d{4}', query)
                year = int(year_match.group(0)) if year_match else today.year

                start_date_j = jdatetime.date(year, month_num, 1)
                # Go to the start of the next month and subtract one day
                end_date_j = (start_date_j + timedelta(days=31)).replace(day=1) - timedelta(days=1)

                return start_date_j.togregorian(), end_date_j.togregorian()

        # Look for a specific year like "سال 1402"
        year_match = re.search(r'سال (\d{4})', query)
        if year_match:
            year = int(year_match.group(1))
            start_date = jdatetime.date(year, 1, 1).togregorian()
            # --- FIX: Use timedelta for subtraction ---
            end_date_j = jdatetime.date(year + 1, 1, 1) - timedelta(days=1)
            return start_date, end_date_j.togregorian()

        if 'امسال' in query:
            start_date = jdatetime.date(today.year, 1, 1).togregorian()
            # --- FIX: Use timedelta for subtraction ---
            end_date_j = jdatetime.date(today.year + 1, 1, 1) - timedelta(days=1)
            return start_date, end_date_j.togregorian()

        if 'ماه گذشته' in query:
            last_month_start_j = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            start_date = last_month_start_j.togregorian()
            # --- FIX: Use timedelta for subtraction ---
            end_date_j = today.replace(day=1) - timedelta(days=1)
            return start_date, end_date_j.togregorian()

        return None

    def _extract_number(self, query: str) -> int | None:
        """Extracts the first number found in the query."""
        match = re.search(r'\d+', query)
        return int(match.group(0)) if match else None

    def parse(self, query: str) -> dict | None:
        """
        The main method to parse a query and return a criteria dictionary.
        """
        search_type = self._find_search_type(query)
        if not search_type:
            return None

        criteria = {'type': search_type}

        # --- Check if the query contains a month name ---
        # This is a key piece of context for the parser.
        has_month = any(month in query for month in self.MONTHS)

        if search_type == 'unpaid':
            date_range = self._extract_date_range(query)
            if not date_range:
                end_date = date.today()
                start_date = end_date - timedelta(days=30)
                criteria['start_date'] = start_date
                criteria['end_date'] = end_date
            else:
                criteria['start_date'], criteria['end_date'] = date_range

        elif search_type == 'frequent':
            # --- FIX: Only extract a number if a month is NOT specified ---
            # If the user says "frequent customers in Khordad," they are not specifying a visit count.
            if not has_month:
                min_visits = self._extract_number(query)
                criteria['min_visits'] = min_visits if min_visits else 2
            else:
                # If a month is present, we are actually looking for customers within that month.
                # We can default to a minimum of 2 visits within that month.
                criteria['min_visits'] = 2
                date_range = self._extract_date_range(query)
                if date_range:
                    criteria['start_date'], criteria['end_date'] = date_range

        elif search_type == 'docs':
            doc_query = query
            for kw_list in self.KEYWORDS.values():
                for kw in kw_list:
                    doc_query = doc_query.replace(kw, '')
            criteria['doc_names'] = [name.strip() for name in doc_query.split() if name.strip()]

        return criteria
