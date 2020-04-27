import argparse
import calendar
import datetime
import json
import multiprocessing

from itertools import chain
from collections import defaultdict

from selenium import webdriver

from national import check_natl_sites

with open('/Users/avy/src/parks/config.json') as f:
    ALL_SITES = json.loads(f.read())


ALL_TAGS = set(chain(*(site['tags'] for site in ALL_SITES.values())))
TAG_TO_SITES = defaultdict(list)
for site, data in ALL_SITES.items():
    for tag in data['tags']:
        TAG_TO_SITES[tag].append(site)

WEEKDAYS = tuple(d.lower() for d in list(calendar.day_name))


def get_date_list(start, end, weekday=None):
    delta = 1
    day = start
    if weekday:
        day += datetime.timedelta(days=WEEKDAYS.index(weekday.lower()) - day.weekday())
        delta = 7

    dates = []
    while day <= end:
        dates.append(day.strftime('%m-%d-%Y'))
        day += datetime.timedelta(days=delta)
    return dates


def check_sites(dates, sites_dict):
    sites = ((site, url, dates) for site, url in sites_dict.items())
    pool = multiprocessing.Pool()
    results = defaultdict(list)
    for d in pool.starmap(check_site, sites):
        for k, v in d.items():
            results[k].extend(v)
    return results


def check_site(name, url, dates):
    driver = webdriver.Chrome()
    date_availability = defaultdict(list)
    try:
        # need to add the same thing for califonia.
        driver.get(url)
        date_availability = check_natl_sites(driver, name, dates)
    except Exception:
        pass
    finally:
        try:
            driver.close()
            driver.quit()
        except Exception:
            pass
    return date_availability


def check_date_range(start_date, end_date, tag, weekday):
    dates = get_date_list(start_date, end_date, weekday)

    sites_dict = {}
    for site in TAG_TO_SITES[tag]:
        sites_dict[site] = ALL_SITES[site]["url"]
    available = check_sites(dates, sites_dict)

    output_file = "availability_{}_{}_to_{}.txt".format(tag, start_date, end_date)

    with open(output_file, "w") as f:
        serializeable = {str(k): v for k, v in available.items()}
        f.write(json.dumps(serializeable, indent=4, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--start', required=True)
    parser.add_argument('-e', '--end')
    parser.add_argument('-w', '--weekday', choices=WEEKDAYS)
    parser.add_argument('-t', '--tag', choices=ALL_TAGS, default="zion")
    args = parser.parse_args()

    start = datetime.datetime.strptime(args.start, "%Y-%m-%d").date()
    if args.end is not None:
        end = datetime.datetime.strptime(args.end, "%Y-%m-%d").date()
    else:
        end = start
    check_date_range(start, end, weekday=args.weekday, tag=args.tag)

if __name__ == '__main__':
    main()
