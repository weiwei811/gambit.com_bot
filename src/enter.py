from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from src.config import login_credentials


def reset(driver):
    driver.get("https://gambit.com")


def wait_until_element(driver, xpath: str, timeout: int = 5):
    return WebDriverWait(driver, timeout).until(
        ec.presence_of_element_located((By.XPATH, xpath))
    )


def login(driver):
    print("Attempting login...")
    try:
        driver.get("https://www.gambit.com/login")
        username, password = login_credentials()
        if username and password:
            def visible_field(xpath):
                return WebDriverWait(driver, 5).until(
                    lambda browser: next((field for field in browser.find_elements(By.XPATH, xpath)
                                          if field.is_displayed() and field.is_enabled()), False))
            username_field = visible_field(
                "//input[@autocomplete='username' or @type='email' or @name='username' or @name='email' "
                "or @type='text' or not(@type)]")
            password_field = visible_field("//input[@type='password']")
            username_field.clear()
            username_field.send_keys(username)
            password_field.clear()
            password_field.send_keys(password)
        elif username or password:
            print("Set both GAMBIT_USERNAME and GAMBIT_PASSWORD in .env, or sign in manually.")
        login_button = wait_until_element(
            driver,
            "/html/body/div[1]/div/div/div/div/div[2]/div[2]/div/div/div/div[2]/div/div/div/div/div[2]/div/div[3]/div/div[1]/div/div[2]/div",
            timeout=5,
        )
        login_button.click()
        print("Login success.")
    except Exception as e:
        print(f"Login bypassed or already authenticated: {type(e).__name__}")


def enter_game(driver, mode: str = "bot_game"):
    if mode == "bot_game":
        print("Entering bot game...")
        driver.get("https://www.gambit.com/play/bots")
        print("Entered bot game.")
    elif mode == "human_game":
        print("Entering humane game...")
        driver.get("https://www.gambit.com/play/live")
        print("Entered human game")
