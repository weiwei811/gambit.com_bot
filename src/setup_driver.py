import os
import socket
import subprocess
import shutil
import sys
from pathlib import Path
from time import sleep
from selenium import webdriver


def is_chrome_debug_port_open(host: str = "127.0.0.1", port: int = 9222) -> bool:
    """Checks if Chrome remote debugging port is open via native socket."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def launch_chrome():
    """Launches Google Chrome with remote debugging enabled."""
    candidates = [shutil.which(name) for name in ("chrome", "google-chrome", "chromium", "chromium-browser")]
    if sys.platform == "darwin":
        candidates.append("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    elif os.name == "nt":
        for base in (os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)"),
                     os.environ.get("LOCALAPPDATA")):
            if base:
                candidates.append(str(Path(base) / "Google/Chrome/Application/chrome.exe"))
    chrome_path = next((path for path in candidates if path and Path(path).is_file()), None)
    if not chrome_path:
        raise FileNotFoundError("Chrome executable not found; install Chrome or launch it with remote debugging port 9222")
    user_data_dir = os.path.expanduser("~/chrome-selenium")
    cmd = [
        chrome_path,
        "--remote-debugging-port=9222",
        f"--user-data-dir={user_data_dir}",
    ]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0)


def init_driver() -> webdriver.Chrome:
    """
    Initializes a Chrome webdriver connected to the remote debugging port.
    If Chrome is not currently running with debugging, it launches an instance.
    """
    options = webdriver.ChromeOptions()
    options.debugger_address = "127.0.0.1:9222"
    print("Connecting to Chrome on 127.0.0.1:9222...")

    if not is_chrome_debug_port_open():
        print("Chrome debugging port not detected, launching Chrome instance...")
        launch_chrome()
        # Wait briefly for the browser process and port to be ready
        for _ in range(10):
            sleep(0.5)
            if is_chrome_debug_port_open():
                break

    driver = webdriver.Chrome(options=options)
    print("Chrome driver connected successfully.")
    return driver
