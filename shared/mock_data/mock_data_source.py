# shared/mock_data/mock_data_source.py

# This is not code to be run, but a central place to store the raw data.
# By defining it here, we guarantee both populator scripts use the exact same values.

MOCK_PEOPLE_DATA = [
    {'first': 'آقا محمد', 'last': 'مدیر', 'nid': '1111111111', 'role': 'admin', 'username': 'admin',
     'payment': 'Full-time', 'salary_rials': 90000000},

    {'first': 'سارا', 'last': 'کارمند', 'nid': '2222222222', 'role': 'clerk', 'username': 'clerk1',
     'payment': 'Full-time', 'salary_rials': 60000000},

    {'first': 'رضا', 'last': 'رضایی', 'nid': '3333333333', 'role': 'translator', 'username': 'rezaei',
     'payment': 'Commission', 'rate': 0.25},

    {'first': 'مریم', 'last': 'حسینی', 'nid': '4444444444', 'role': 'translator', 'username': 'hosseini',
     'payment': 'Commission', 'rate': 0.30},

    {'first': 'احمد', 'last': 'احمدی', 'nid': '5555555555', 'role': 'accountant', 'username': 'ahmadi',
     'payment': 'Part-time', 'salary_rials': 40000000},
]