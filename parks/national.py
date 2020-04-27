#!/usr/bin/env python

import calendar
import datetime
import re
import time

from collections import defaultdict

from selenium.webdriver.common import keys


import pandas as pd

from utils import enter_value


DATE_PICKER_ID = "single-date-picker-1"

def check_natl_sites(driver, name, dates_list):
    """Automation for checking the recreation.gov website."""
    available_sites = defaultdict(list)
    date = dates_list[0]
    value = date + 10*keys.Keys.ARROW_LEFT + 12* keys.Keys.BACKSPACE + keys.Keys.ARROW_DOWN
    enter_value(driver, DATE_PICKER_ID, value)
    results = get_available_sites_in_gov_table(driver)
    for date in results.keys():
        available_sites[date].append(name)
    return available_sites

def month_index_from_str(month):
    short_m = list(calendar.month_abbr)
    long_m = list(calendar.month_name)
    try:
        return short_m.index(month)
    except ValueError:
        return long_m.index(month)

def get_date_from_col(column):
    month, day = column
    match = re.match(r"[a-z]+([0-9]+)", day, re.I)
    m = month_index_from_str(month)
    d = int(match.groups()[0])
    return datetime.date(datetime.date.today().year, m, d)

def get_available_sites_in_gov_table(driver):
    time.sleep(2)
    tab = driver.find_element_by_id('availability-table')
    tab_html = tab.get_attribute('outerHTML')
    df = pd.read_html(tab_html)[0]
    sites = defaultdict(list)
    for column in df.columns[2:]:
        date = get_date_from_col(column)
        if spots := sum(v not in ('X', 'R') for v in df[column]):
            sites[date] = spots
    return sites
