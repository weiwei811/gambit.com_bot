from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from src.play import decision, exec_deci
from src.get_data import get_board_state
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By


def reset(driver):
    driver.get('https://gambit.com')


def wait_until_element(driver,xpath):
    return  WebDriverWait(driver, 30).until(ec.presence_of_element_located((By.XPATH, xpath)))

def login(driver):
    print
    # html=driver.page_source
    print("try login")
    login_page = wait_until_element(driver,"//*[@id=\"root\"]/div/div/div/div/div[2]/div/div/div/div/div[1]/div[2]/div[2]/div")
    login_page.click()
    usernameblank=wait_until_element(driver,"//*[@id=\"root\"]/div/div/div/div/div[2]/div[2]/div/div/div/div[2]/div/div/div/div/div/div/div[2]/div/div/div[2]/div[1]/div[1]/div[1]/input" )
    usernameblank.send_keys("REDACTED_CREDENTIAL")
    passwordblank=wait_until_element(driver,"//*[@id=\"root\"]/div/div/div/div/div[2]/div[2]/div/div/div/div[2]/div/div/div/div/div/div/div[2]/div/div/div[2]/div[1]/div[1]/div[2]/input")
    passwordblank.send_keys("REDACTED_CREDENTIAL")
    login_button=wait_until_element(driver,"//*[@id=\"root\"]/div/div/div/div/div[2]/div[2]/div/div/div/div[2]/div/div/div/div/div/div/div[2]/div/div/div[2]/div[1]/div[2]/div/div")
    login_button.click()


def in_game(driver):
    while True:
        state=get_board_state(driver)
        if state.end:
            break
        if state.myturn:
            dec=decision(state)
            exec_deci(dec)
def enter_game(driver,mode):
    if mode=="bot_game":
        bot_game_button=wait_until_element(driver,"/html/body/div[1]/div/div/div/div/div[2]/div/div/div/div/div[1]/a[2]")
        bot_game_button.click()



