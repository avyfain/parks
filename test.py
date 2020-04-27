import calendar
import datetime
import difflib
import json
import multiprocessing
import os
import re
import time

from functools import wraps
from itertools import repeat
from collections import defaultdict

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import ui
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common import keys
from selenium.common import exceptions
from selenium.webdriver.common.action_chains import ActionChains

# Recreation.gov variables
DATE_PICKER_ID = "single-date-picker-1"
ROW_PATH = '//*[@id="availability-table"]/tbody/tr'
ANOTHER_XPATH = '//*[@id="campsite-filter-search"]'

url = "https://www.recreation.gov/camping/campgrounds/232448/availability"
CAMPSITE_URL = "https://www.recreation.gov/camping/campsites/"

def _click_element(driver, xpath):
    elem = driver.find_element_by_xpath(xpath)
    driver.execute_script("arguments[0].scrollIntoView();", elem)
    time.sleep(.1)
    elem.click()

def _enter_value(driver, field_id, value, scroll_into_view=False, select_on_dropdown=False):
    field = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, field_id)))
    if scroll_into_view:
        driver.execute_script("arguments[0].scrollIntoView();", field)
        ActionChains(driver).move_to_element(field).perform()
        field.click()
    field.click()
    field.clear()
    field.send_keys(value)
    time.sleep(.5)
    if select_on_dropdown:
        field.send_keys(keys.Keys.DOWN)
        time.sleep(.2)
        field.send_keys(keys.Keys.RETURN)
    body = driver.find_element_by_id('page-body')
    body.click()

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
    return datetime.date(2020, m, d)

def _get_available_sites_in_gov_table(driver, name):
    time.sleep(2)
    tab = driver.find_element_by_id('availability-table')
    tab_html = tab.get_attribute('outerHTML')
    df = pd.read_html(tab_html)[0]
    sites = defaultdict(list)
    for column in df.columns[2:]:
        date = get_date_from_col(column)
        if spots := sum(v not in ('X', 'R') for v in df[column]):
            sites[date] = f'{spots} spots available!'
    return sites

driver = webdriver.Chrome()
driver.get(url)

date = '08-31-2020'
name = "Tuolomne Meadows(Yosemite)"
value = date + 10*keys.Keys.ARROW_LEFT + 12* keys.Keys.BACKSPACE + keys.Keys.ARROW_DOWN
_enter_value(driver, DATE_PICKER_ID, value)
results = _get_available_sites_in_gov_table(driver, name)
import pprint
pprint.pprint(results)