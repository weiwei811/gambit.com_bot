from src.setup_driver import init_driver
from src.enter import reset,login

def main():
    driver=init_driver()
    reset(driver)
    login(driver)

    input()

main()