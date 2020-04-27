import time

from selenium.webdriver.common.action_chains import ActionChains
from utils import enter_value, select_dropdown_visible_text, click_element

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


def check_california_sites(driver, name, date, available_sites):
    # Starting page
    time.sleep(.2)
    enter_value(driver, SITE_PICKER_ID, name, select_on_dropdown=True)
    time.sleep(1)
    for i in ["Camping", "Remote Camping"]:
        try:
            select_dropdown_visible_text(driver, DROPDOWN_TYPE_ID, i)
        except Exception:
            pass
    time.sleep(.8)
    enter_value(driver, DATE_ARRIVAL_ID, date)
    time.sleep(.1)
    select_dropdown_visible_text(driver, NUMBER_OF_NIGHTS_ID, "1")
    time.sleep(1.2)
    click_element(driver, SEND_BUTTON_XPATH)
    time.sleep(2)
    # Page 2
    return _get_available_sites_in_california_table(
        driver, name, date, available_sites)


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
    click_element(driver, '//*[@id="aHomeBlueiconh"]')

    return available_sites

def _get_available_sites_in_california_table(driver, name, date, available_sites):
    original_length = len(available_sites[date])
    children = driver.find_elements_by_class_name("btn_green")
    bad_children = driver.find_elements_by_class_name("btn_green_brd")
    good_children = [child for child in children if child not in bad_children]
    if good_children:
        for idx, _ in enumerate(good_children):
            children = driver.find_elements_by_class_name("btn_green")
            bad_children = driver.find_elements_by_class_name("btn_green_brd")
            good_children = [child for child in children if child not in bad_children]
            try:
                time.sleep(.3)
                ActionChains(driver).move_to_element(good_children[idx]).perform()
                good_children[idx].click()
                _check_out_california_campsite_page(driver, name, date, available_sites)
            except Exception as err:
                pass
            time.sleep(1)
    final_length = len(available_sites[date])
    num_new_sites = final_length - original_length
    if num_new_sites:
        print("\tFound {} sites for {} ({})".format(num_new_sites, date, name))
    return available_sites
