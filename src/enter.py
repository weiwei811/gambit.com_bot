from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By


def reset(driver):
    driver.get('https://gambit.com')


def wait_until_element(driver,xpath):
    return  WebDriverWait(driver, 5).until(ec.presence_of_element_located((By.XPATH, xpath)))

def login(driver):
    # html=driver.page_source
    print("try login")
    try:
        login_page = wait_until_element(driver,"//*[@id=\"root\"]/div/div/div/div/div[2]/div/div/div/div/div[1]/div[2]/div[2]/div")
        login_page.click()
        usernameblank=wait_until_element(driver,"//*[@id=\"root\"]/div/div/div/div/div[2]/div[2]/div/div/div/div[2]/div/div/div/div/div/div/div[2]/div/div/div[2]/div[1]/div[1]/div[1]/input" )
        usernameblank.send_keys("REDACTED_CREDENTIAL")
        passwordblank=wait_until_element(driver,"//*[@id=\"root\"]/div/div/div/div/div[2]/div[2]/div/div/div/div[2]/div/div/div/div/div/div/div[2]/div/div/div[2]/div[1]/div[1]/div[2]/input")
        passwordblank.send_keys("REDACTED_CREDENTIAL")
        login_button=wait_until_element(driver,"//*[@id=\"root\"]/div/div/div/div/div[2]/div[2]/div/div/div/div[2]/div/div/div/div/div/div/div[2]/div/div/div[2]/div[1]/div[2]/div/div")
        login_button.click()
        print("login scucces")
    except:
        print("already login")


def enter_game(driver,mode):
    if mode=="bot_game":
        bot_game_button=wait_until_element(driver,"/html/body/div[1]/div/div/div/div/div[2]/div/div/div/div/div[1]/a[2]")
        bot_game_button.click()



