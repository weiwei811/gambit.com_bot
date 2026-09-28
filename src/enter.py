from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By


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
