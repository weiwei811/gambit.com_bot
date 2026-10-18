"""Locate visible betting controls rather than unrelated page text."""
import re
import sys
from selenium.common.exceptions import (
    ElementClickInterceptedException, ElementNotInteractableException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait


# Gambit's React Native Web controls are focusable divs, not HTML buttons.
# Match a leaf label, then return its interactive ancestor in a group of at
# least two betting actions. This also excludes coaching/header occurrences.
FIND_ACTION_CONTROLS = r"""
const wanted = arguments[0];
const root = arguments[1] || document;
// Require an amount for All-in: the bare "All-In" sizing preset is not
// the final action button and must never be mistaken for submission.
const label = /^(?:(Fold|Check|Call|Raise|Bet)(?:\s*:\s*[\d,.]+)?|(All[-\u2010\u2011 ]?in)\s*:\s*[\d,.]+)$/i;
const selector = 'button,[role="button"],[tabindex="0"]';
const labels = Array.from(root.querySelectorAll('span,div,button'))
    .filter(el => el.children.length === 0 && label.test(el.textContent.trim()));
const controls = labels.map(el => ({
    el, action: el.textContent.trim().match(label)[2] ? 'all_in'
        : el.textContent.trim().match(label)[1].toLowerCase(),
    control: el.closest(selector),
})).filter(item => item.control && !item.control.closest('header,nav'));
const matches = [];
for (const item of controls) {
    if (!wanted.includes(item.action)) continue;
    let group = item.control.parentElement;
    for (let depth = 0; group && depth < 5; depth++, group = group.parentElement) {
        if (['BODY', 'HTML', 'MAIN', 'HEADER', 'NAV'].includes(group.tagName)) break;
        const actions = new Set(controls.filter(c => group.contains(c.control)).map(c => c.action));
        if (actions.size >= 2) {
            if (!matches.includes(item.control)) matches.push(item.control);
            break;
        }
    }
}
return matches;
"""

HIT_TEST = """
const el = arguments[0];
if (el.closest('[aria-disabled="true"],[disabled]')) return false;
el.scrollIntoView({block:'center', inline:'nearest'});
const r = el.getBoundingClientRect();
const hit = document.elementFromPoint(r.left + r.width/2, r.top + r.height/2);
return Boolean(hit && (hit === el || el.contains(hit)));
"""

FIND_RAISE_INPUTS = """
const control = arguments[0];
for (let group = control.parentElement, depth = 0; group && depth < 7;
     group = group.parentElement, depth++) {
    if (['BODY','HTML','MAIN'].includes(group.tagName)) break;
    const inputs = Array.from(group.querySelectorAll('input'))
        .filter(el => !el.disabled && !el.readOnly &&
            ['text','number','tel'].includes(el.type));
    if (inputs.length) return inputs;
}
return [];
"""


def _raise_inputs(browser):
    controls = browser.execute_script(FIND_ACTION_CONTROLS, ["raise", "bet", "all_in"])
    for control in controls:
        for field in browser.execute_script(FIND_RAISE_INPUTS, control):
            if (field.is_displayed() and field.is_enabled() and
                    browser.execute_script(HIT_TEST, field)):
                yield field


def set_raise_amount(driver, amount, timeout=3):
    """Type in the betting panel, then confirm the controlled input accepted it."""
    amount = str(int(amount))
    platform = str(driver.capabilities.get("platformName", sys.platform)).lower()
    modifier = Keys.COMMAND if platform in ("mac", "macos", "darwin") else Keys.CONTROL

    def enter(browser):
        try:
            for field in _raise_inputs(browser):
                field.click()
                # Replace the selection directly: a separate Backspace can
                # trigger React's minimum-value correction before we type.
                field.send_keys(modifier, "a")
                field.send_keys(amount)
                return True
        except (StaleElementReferenceException, ElementNotInteractableException,
                ElementClickInterceptedException):
            pass
        return False

    wait = WebDriverWait(driver, timeout, poll_frequency=0.15)
    wait.until(enter, message="No interactable raise input in the betting panel")

    def accepted(browser):
        try:
            return any(str(field.get_property("value")) == amount for field in _raise_inputs(browser))
        except StaleElementReferenceException:
            return False
    wait.until(accepted, message=f"Raise input did not accept {amount}; action was not submitted")


def click_action(driver, *actions, timeout=3, expected_amount=None):
    """Retry a normal WebDriver click while overlays/transitions settle."""
    def attempt(browser):
        for control in browser.execute_script(FIND_ACTION_CONTROLS, list(actions)):
            try:
                if not control.is_displayed() or not control.is_enabled():
                    continue
                if expected_amount is not None:
                    label = re.fullmatch(r"(?:Raise|Bet|All[-\u2010\u2011 ]?in)\s*:\s*([\d,.]+)",
                                         control.text.strip(), re.IGNORECASE)
                    if not label or float(label[1].replace(",", "")) != float(expected_amount):
                        continue
                if not browser.execute_script(HIT_TEST, control):
                    continue
                control.click()
                return True
            except (StaleElementReferenceException, ElementClickInterceptedException,
                    ElementNotInteractableException):
                continue
        return False
    return WebDriverWait(driver, timeout, poll_frequency=0.15).until(
        attempt, message=f"No unobscured betting control for {actions}, expected amount {expected_amount}")
