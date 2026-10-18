from unittest.mock import Mock

from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
import pytest

from src.game_controls import FIND_ACTION_CONTROLS, HIT_TEST, click_action


def _control():
    control = Mock()
    control.is_displayed.return_value = True
    control.is_enabled.return_value = True
    return control


def test_skips_obscured_and_hidden_elements_before_clicking():
    driver = Mock()
    hidden, covered, call = _control(), _control(), _control()
    hidden.is_displayed.return_value = False
    def execute(script, arg):
        if script == FIND_ACTION_CONTROLS:
            assert arg == ["call"]
            return [hidden, covered, call]
        assert script == HIT_TEST
        return arg is call
    driver.execute_script.side_effect = execute
    assert click_action(driver, "call")
    hidden.click.assert_not_called()
    covered.click.assert_not_called()
    call.click.assert_called_once()


def test_retries_interception_after_reacquiring_the_control():
    driver = Mock()
    old, current = _control(), _control()
    old.click.side_effect = ElementClickInterceptedException()
    controls = iter([[old], [current]])
    driver.execute_script.side_effect = lambda script, arg: next(controls) if script == FIND_ACTION_CONTROLS else True
    assert click_action(driver, "call", timeout=1)
    current.click.assert_called_once()


def test_never_force_clicks_a_covered_control():
    driver = Mock()
    covered = _control()
    driver.execute_script.side_effect = lambda script, arg: [covered] if script == FIND_ACTION_CONTROLS else False
    with pytest.raises(TimeoutException):
        click_action(driver, "call", timeout=0)
    covered.click.assert_not_called()
