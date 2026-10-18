"""Locate visible betting controls rather than unrelated page text."""
from selenium.common.exceptions import (
    ElementClickInterceptedException, StaleElementReferenceException,
)
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


def click_action(driver, *actions, timeout=3):
    """Retry a normal WebDriver click while overlays/transitions settle."""
    def attempt(browser):
        for control in browser.execute_script(FIND_ACTION_CONTROLS, list(actions)):
            try:
                if not control.is_displayed() or not control.is_enabled():
                    continue
                if not browser.execute_script(HIT_TEST, control):
                    continue
                control.click()
                return True
            except (StaleElementReferenceException, ElementClickInterceptedException):
                continue
        return False
    return WebDriverWait(driver, timeout, poll_frequency=0.15).until(attempt)
