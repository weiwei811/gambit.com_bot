from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from time import sleep
import traceback

def reset(driver):
    driver.get('https://gambit.com')


def wait_until_element(driver,xpath,timeout=5):
    return  WebDriverWait(driver, timeout).until(ec.presence_of_element_located((By.XPATH, xpath)))

def login(driver):
    # html=driver.page_source
    print("try login")

    try:
        # login_page = wait_until_element(driver,"//*[@id=\"root\"]/div/div/div/div/div[2]/div/div/div/div/div[1]/div[2]/div[2]/div",timeout=5)
        # login_page.click()
        driver.get("https://www.gambit.com/login")
        # usernameblank=wait_until_element(driver,"//*[@id=\"root\"]/div/div/div/div/div[2]/div[2]/div/div/div/div[2]/div/div/div/div/div/div/div[2]/div/div/div[2]/div[1]/div[1]/div[1]/input" )
        # usernameblank.send_keys("REDACTED_CREDENTIAL")
        # passwordblank=wait_until_element(driver,"//*[@id=\"root\"]/div/div/div/div/div[2]/div[2]/div/div/div/div[2]/div/div/div/div/div/div/div[2]/div/div/div[2]/div[1]/div[1]/div[2]/input")
        # passwordblank.send_keys("REDACTED_CREDENTIAL")
        login_button=wait_until_element(driver,"/html/body/div[1] /div/div/div/div/div[2]/div[2]/div/div/div/div[2]/div/div/div/div/div[2]/div/div[3]/div/div[1]/div/div[2]/div")
        login_button.click()
        print("login scucces")
    except Exception as e:
        # print(e)
        exception_type=type(e).__name__
        tb=e.__traceback__
        summary = traceback.extract_tb(tb)

        # line_number = summary.lineno
        # line_content=summary.line

        print(f"execption type {exception_type}")
        print(f"summary {summary}")

        print("already login")


def enter_game(driver,mode):
    if mode=="bot_game":
        print("entering bot game")
        driver.get("https://www.gambit.com/play/bots")
        # sleep(0.5)
        print("entered bot game")



