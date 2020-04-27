import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import ui
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common import keys
from selenium.webdriver.common.action_chains import ActionChains

def enter_value(driver, field_id, value, scroll_into_view=False, select_on_dropdown=False):
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


def select_dropdown_visible_text(driver, field_id, value):
    menu = WebDriverWait(driver, 3).until(
        EC.presence_of_element_located((By.ID, field_id)))
    dropdown = ui.Select(menu)
    dropdown.select_by_visible_text(value)


def click_element(driver, xpath):
    elem = driver.find_element_by_xpath(xpath)
    driver.execute_script("arguments[0].scrollIntoView();", elem)
    time.sleep(.1)
    elem.click()
