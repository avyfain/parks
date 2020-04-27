#!/usr/bin/env python
import argparse
import calendar
import datetime
import difflib
import json
import multiprocessing
import os
import re
import time

from functools import wraps
from itertools import chain
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

CALIFORNIA_URL = "https://www.reservecalifornia.com/CaliforniaWebHome/"
NATIONAL_URL_TEMPLATE = "https://www.recreation.gov/camping/campgrounds/{}/availability"

ALL_SITES_DICT = {
    "Wawona (Yosemite)": {"url": NATIONAL_URL_TEMPLATE.format(232446), "tags": ["yosemite", "weekend"]},
    "Hodgdon Meadows (Yosemite)": {"url": NATIONAL_URL_TEMPLATE.format(232451), "tags": ["yosemite", "weekend"]},
    "North Pines (Yosemite)": {"url": NATIONAL_URL_TEMPLATE.format(232449), "tags": ["yosemite", "weekend"]},
    "Lower Pines (Yosemite)": {"url": NATIONAL_URL_TEMPLATE.format(232450), "tags": ["yosemite", "weekend"]},
    "Upper Pines (Yosemite)": {"url": NATIONAL_URL_TEMPLATE.format(232447), "tags": ["yosemite", "weekend"]},
    "Tuolomne Meadows (Yosemite)": {"url": NATIONAL_URL_TEMPLATE.format(232448), "tags": ["yosemite", "weekend"]},
    "Crane Flat (Yosemite)": {"url": NATIONAL_URL_TEMPLATE.format(232452), "tags": ["yosemite", "weekend"]},
    "Dimond O (Hetch Hetchy)": {"url": NATIONAL_URL_TEMPLATE.format(233772), "tags": ["yosemite", "weekend"]},
    "South Campground (Zion)": {"url": NATIONAL_URL_TEMPLATE.format(272266), "tags": ["utah", "zion"]},
    "Watchman's Campground (Zion)": {"url": NATIONAL_URL_TEMPLATE.format(232445), "tags": ["utah", "zion"]},
    "Devil's Garden Campground (Arches)": {"url": NATIONAL_URL_TEMPLATE.format(234059), "tags": ["utah", "arches"]},
    "Needles District (Canyonlands)": {"url": NATIONAL_URL_TEMPLATE.format(251535), "tags": ["utah", "canyonlands"]},
    "Fruita Campground (Capitol Reef)": {"url": NATIONAL_URL_TEMPLATE.format(272245), "tags": ["utah", "capitol_reef"]},
    "Mather's Campground (Grand Canyon)": {"url": NATIONAL_URL_TEMPLATE.format(232490), "tags": ["utah", "grand_canyon", "south_rim"]},
    "North Rim Campground (Grand Canyon)": {"url": NATIONAL_URL_TEMPLATE.format(232489), "tags": ["utah", "grand_canyon", "north_rim"]},
    "Demotte (NR Grand Canyon)": {"url": NATIONAL_URL_TEMPLATE.format(234722), "tags": ["utah", "grand_canyon", "north_rim"]},
    "Ten-X Campground (Grand Canyon)": {"url": NATIONAL_URL_TEMPLATE.format(234488), "tags": ["utah", "grand_canyon", "north_rim"]},
    "Bicentenniel (Marin Headlands)": {"url": NATIONAL_URL_TEMPLATE.format(272229), "tags": ["weekend", "north_bay"]},
    "Kirby Cove (SF)": {"url": NATIONAL_URL_TEMPLATE.format(232491), "tags": ["weekend", "north_bay"]},
    "Point Reyes": {"url": NATIONAL_URL_TEMPLATE.format(233359), "tags": ["weekend", "point_reyes", "north_bay"]},
    # "Samuel P. Taylor SP": {"url": CALIFORNIA_URL, "tags": ["weekend", "north_bay"]},
    # "China Camp SP": {"url": CALIFORNIA_URL, "tags": ["weekend", "north_bay"]},
    # "Mount Tamalpais SP": {"url": CALIFORNIA_URL, "tags": ["weekend", "north_bay"]},
    # "Angel Island SP": {"url": CALIFORNIA_URL, "tags": ["weekend", "north_bay"]},
    # "Henry Cowell Redwoods": {"url": CALIFORNIA_URL, "tags": ["weekend", "santa_cruz"]},
    "Plaskett Creek Campground (Big Sur)": {"url": NATIONAL_URL_TEMPLATE.format(231959), "tags": ["weekend", "big_sur"]},
    "Kirk Creek Campground (Big Sur)": {"url": NATIONAL_URL_TEMPLATE.format(233116), "tags": ["weekend", "big_sur"]},
    # "Limekiln SP": {"url": CALIFORNIA_URL, "tags": ["weekend", "big_sur"]},
    # "Pfeiffer": {"url": CALIFORNIA_URL, "tags": ["weekend", "big_sur"]},
    # "Pfeiffer Big Sur": {"url": CALIFORNIA_URL, "tags": ["weekend", "big_sur"]},
    "Arroyo Seco (Los Padres)": {"url": NATIONAL_URL_TEMPLATE.format(231958), "tags": ["weekend", "big_sur"]},
    "Wishon Point (Bass Lake)": {"url": NATIONAL_URL_TEMPLATE.format(232911), "tags": ["bass_lake"]},
    "Cedar Bluff (Bass Lake)": {"url": NATIONAL_URL_TEMPLATE.format(232912), "tags": ["bass_lake"]},
    "Forks Campground (Bass Lake)": {"url": NATIONAL_URL_TEMPLATE.format(232878), "tags": ["bass_lake"]},
    "Spring Cover (Bass Lake)": {"url": NATIONAL_URL_TEMPLATE.format(232801), "tags": ["bass_lake"]},
    # "Big Basin": {"url": CALIFORNIA_URL, "tags": ["weekend", "big_basin"]},
    # "Little Basin": {"url": CALIFORNIA_URL, "tags": ["weekend", "big_basin"]},
    # "Seacliff SB": {"url": CALIFORNIA_URL, "tags": ["weekend", "beach", "santa_cruz", "hwy1"]},
    # "Manresa SB": {"url": CALIFORNIA_URL, "tags": ["weekend", "beach", "santa_cruz", "hwy1"]},
    # "Sunset SB": {"url": CALIFORNIA_URL, "tags": ["weekend", "beach", "santa_cruz", "hwy1"]},
    # "Half Moon Bay SB": {"url": CALIFORNIA_URL, "tags": ["weekend", "beach", "hwy1"]},
    # "Russian Gulch": {"url": CALIFORNIA_URL, "tags": ["beach", "hwy1", "north_hwy1", "rg"]},
    # "Van Damme": {"url": CALIFORNIA_URL, "tags": ["northern_cal", "hwy1", "north_hwy1"]},
    # "Prairie Creek Redwoods SP Elk": {"url": CALIFORNIA_URL, "tags": ["northern_cal", "hwy1", "north_hwy1"]},
    # "Prairie Creek Redwoods SP Gold": {"url": CALIFORNIA_URL, "tags": ["northern_cal", "hwy1", "north_hwy1"]},
    # "Patricks Point SP": {"url": CALIFORNIA_URL, "tags": ["northern_cal", "hwy1", "north_hwy1"]},
    # "Mackerricher SP": {"url": CALIFORNIA_URL, "tags": ["northern_cal", "hwy1", "north_hwy1"]},
    # "Grizzly Creek Redwoods SP": {"url": CALIFORNIA_URL, "tags": ["northern_cal"]},
    # "Humboldt Redwoods SP": {"url": CALIFORNIA_URL, "tags": ["northern_cal"]},
}

ALL_TAGS = set(chain(*(site['tags'] for site in ALL_SITES_DICT.values())))
TAG_TO_SITES = defaultdict(list)
for site, data in ALL_SITES_DICT.items():
    for tag in data['tags']:
        TAG_TO_SITES[tag].append(site)

OUTPUT_FILE = "availability_{}_{}_to_{}.txt"

# Recreation.gov variables
DATE_PICKER_ID = "single-date-picker-1"

# Reserve California variables
# First Page
SITE_PICKER_ID = "txtSearchparkautocomplete"
DATE_ARRIVAL_ID = "mainContent_txtArrivalDate"
NUMBER_OF_NIGHTS_ID = "ddlHomeNights"
DROPDOWN_TYPE_ID = "ddl_homeCategories"
DROPDOWN_CAMPING_TYPE = "ddl_homeCampingUnit"

# Second Page
DATE_ARRIVAL_ID2 = "mainContent_SearchUnitAvailbity_txtArrivalDate"
SEND_BUTTON_XPATH = '//*[@id="divMainSearchControl"]/div[1]/div[4]/div/a'
SECOND_SITE_PICKER_ID = "txtCityParkSearch"
SECOND_SEND_BUTTON_XPATH = '//*[@id="divPlaceSearchParameter"]/div/div[2]/div[1]/div[4]/a'
SECOND_AVAILABILITY_ROW_PATH = '//*[@id="divUnitGridlist"]/div/table/tbody/tr'

YEAR = 2020
WEEKDAYS_DICT = {"saturday": 5,
                 "sunday": 6,
                 "monday": 0,
                 "tuesday": 1,
                 "wednesday": 2,
                 "thursday": 3,
                 "friday": 4}


def _get_date_list(start, end=None, weekday=None):
    delta = 1
    day = start
    if end is None:
        end = start
    if weekday:
        if weekday.lower() not in weekdays_dict:
            raise ValueError(f"weekday {weekday} is not recognized. "
                             f"Possible: {weekdays_dict.keys()}")

        day += datetime.timedelta(days=weekdays_dict[weekday.lower()] - day.weekday())
        delta = 7

    dates = []
    while day <= end:
        dates.append(day.strftime('%m-%d-%Y'))
        day += datetime.timedelta(days=delta)
    return dates

def get_sites_dict_from_tag(tag=None):
    if tag is None:
        return ALL_SITES_DICT
    else:
        return {k: v for k, v in ALL_SITES_DICT
                if k in TAG_TO_SITES[tag]}

def check_date_range(start_date, end_date, tag=None, output_file=None, weekday=None):
    dates = _get_date_list(start_date, end_date, weekday)
    sites_dict = get_sites_dict_from_tag(tag)
    if not output_file:
        output_file = OUTPUT_FILE.format(tag, start_date, end_date)
    available = check_sites(dates, sites_dict)
    _print_to_file(available, output_file)

def check_sites(dates_list, sites_dict):
    start_time = time.time()
    sites = ((site, url, dates_list) for site, url in sites_dict.items())
    pool = multiprocessing.Pool()
    results = defaultdict(list)
    for d in pool.starmap(_subprocess_check_site, sites):
        for k, v in d.items():
            results[k].extend(v)
    total_time = time.time() - start_time
    print(f"It took {int(total_time / 60)} min")
    return results


def _subprocess_check_site(name, url, dates_list):
    driver = webdriver.Chrome()
    date_availability = defaultdict(list)
    try:
        driver.get(url)
        # should do same thing for _check_california_sites
        date_availability = _check_gov_sites(driver, name, dates_list)
    except Exception:
        pass
    finally:
        try:
            driver.close()
            driver.quit()
        except Exception:
            pass
    return date_availability

def _check_california_sites(driver, name, date, available_sites):
    # Starting page
    time.sleep(.2)
    _enter_value(driver, SITE_PICKER_ID, name, select_on_dropdown=True)
    time.sleep(1)
    for i in ["Camping", "Remote Camping"]:
        try:
            _select_dropdown_visible_text(driver, DROPDOWN_TYPE_ID, i)
        except Exception:
            pass
    time.sleep(.8)
    _enter_value(driver, DATE_ARRIVAL_ID, date)
    time.sleep(.1)
    _select_dropdown_visible_text(driver, NUMBER_OF_NIGHTS_ID, "1")
    time.sleep(1.2)
    _click_element(driver, SEND_BUTTON_XPATH)
    time.sleep(2)
    # Page 2
    return _get_available_sites_in_california_table(
        driver, name, date, available_sites)


def _enter_value(driver, field_id, value, scroll_into_view=False, select_on_dropdown=False):
    field = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, field_id)))
    if scroll_into_view:
        driver.execute_script("arguments[0].scrollIntoView();", field)
        ActionChains(driver).move_to_element(field).perform()
        field.click()
    field.click()
    field.send_keys(value)
    time.sleep(.5)
    if select_on_dropdown:
        field.send_keys(keys.Keys.DOWN)
        time.sleep(.2)
        field.send_keys(keys.Keys.RETURN)
    body = driver.find_element_by_id('page-body')
    body.click()


def _select_dropdown_visible_text(driver, field_id, value):
    menu = WebDriverWait(driver, 3).until(
        EC.presence_of_element_located((By.ID, field_id)))
    dropdown = ui.Select(menu)
    dropdown.select_by_visible_text(value)


def _click_element(driver, xpath):
    elem = driver.find_element_by_xpath(xpath)
    driver.execute_script("arguments[0].scrollIntoView();", elem)
    time.sleep(.1)
    elem.click()


def _check_out_california_campsite_page(driver, name, date, available_sites):
    time.sleep(.2)
    rows = driver.find_elements_by_css_selector("table>tbody>tr")
    for row in rows:
        children = row.find_elements_by_xpath(".//*")
        if children[2].get_attribute("class") == "blue_brd_box":
            driver.execute_script("arguments[0].scrollIntoView();", children[2])
            site_name = children[1].text
            if not any(adj in site_name for adj in ["ADA", "Group", "Day"]):
                msg = "{}: {} is available".format(name, site_name)
                if msg not in available_sites[date]:
                    available_sites[date].append(msg)
    time.sleep(.2)
    _click_element(driver, '//*[@id="aHomeBlueiconh"]')

    return available_sites


def _check_gov_sites(driver, name, dates_list):
    """Automation for checking the recreation.gov website."""
    dates_to_process = set(dates_list)
    available_sites = defaultdict(list)
    while dates_to_process:
        date = dates_to_process.pop()
        print(f'Processing {date} for {name}')
        value = date + 10*keys.Keys.ARROW_LEFT + \
                       12* keys.Keys.BACKSPACE + \
                       keys.Keys.ARROW_DOWN
        _enter_value(driver, DATE_PICKER_ID, value)
        results = _get_available_sites_in_gov_table(driver, name)
        for date in results.keys():
            available_sites[date].append(name)
            if date in dates_to_process:
                dates_to_process.remove(date)
    return available_sites


def _get_available_sites_in_california_table(driver, name, date, available_sites):
    original_length = len(available_sites[date])
    children = driver.find_elements_by_class_name("btn_green")
    bad_children = driver.find_elements_by_class_name("btn_green_brd")
    good_children = [child for child in children if child not in bad_children]
    if good_children:
        for i in range(len(good_children)):
            children = driver.find_elements_by_class_name("btn_green")
            bad_children = driver.find_elements_by_class_name("btn_green_brd")
            good_children = [child for child in children if child not in bad_children]
            try:
                time.sleep(.3)
                ActionChains(driver).move_to_element(good_children[i]).perform()
                good_children[i].click()
                _check_out_california_campsite_page(driver, name, date, available_sites)
            except Exception as err:
                pass
            time.sleep(1)
    final_length = len(available_sites[date])
    num_new_sites = final_length - original_length
    if num_new_sites:
        print("\tFound {} sites for {} ({})".format(num_new_sites, date, name))
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
    return datetime.date(2020, m, d)

def _get_available_sites_in_gov_table(driver, name):
    time.sleep(1)
    tab = driver.find_element_by_id('availability-table')
    tab_html = tab.get_attribute('outerHTML')
    df = pd.read_html(tab_html)[0]
    sites = defaultdict(list)
    for column in df.columns[2:]:
        date = get_date_from_col(column)
        if spots := sum(v not in ('X', 'R') for v in df[column]):
            sites[date] = spots
    return sites


def _print_to_file(available_sites_dict, output_file=OUTPUT_FILE):
    print("Site IDs and dates saved to {}".format(output_file))
    with open(output_file, "w") as open_file:
        for date, sites in available_sites_dict.items():
            msg = f"{date} has the following sites available:\n"
            for site in sites:
                msg += f'\t{site}\n'
            msg += '\n'
            open_file.write(msg)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--start', required=True)
    parser.add_argument('-e', '--end')
    parser.add_argument('-w', '--weekday', choices=WEEKDAYS_DICT)
    parser.add_argument('-t', '--tag', choices=ALL_TAGS)

    args = parser.parse_args()
    start = datetime.datetime.strptime(args.start, "%Y-%m-%d").date()
    if args.end is not None:
        end = datetime.datetime.strptime(args.end, "%Y-%m-%d").date()
    else:
        end = start
    check_date_range(start, end, weekday=args.weekday, tag=args.tag)
