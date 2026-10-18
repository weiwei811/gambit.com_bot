from unittest.mock import Mock

from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
import pytest

from src.game_controls import FIND_ACTION_CONTROLS, FIND_RAISE_INPUTS, HIT_TEST, click_action, set_raise_amount
from selenium.webdriver.common.keys import Keys
from src.play import exec_deci
from src.dataclass import Board


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


def test_raise_accepts_final_all_in_action_label(monkeypatch):
    enter = Mock()
    monkeypatch.setattr("src.play.set_raise_amount", enter)
    click = Mock()
    monkeypatch.setattr("src.play.click_action", click)
    driver = Mock()
    exec_deci(driver, Board(), "raise_16")
    enter.assert_called_once_with(driver, "16")
    click.assert_called_once_with(driver, "raise", "bet", "all_in", expected_amount="16")


def test_failed_amount_entry_does_not_submit_old_raise(monkeypatch):
    enter = Mock(side_effect=TimeoutException("Input still shows 5, expected 7"))
    monkeypatch.setattr("src.play.set_raise_amount", enter, raising=False)
    click = Mock()
    monkeypatch.setattr("src.play.click_action", click)
    exec_deci(Mock(), Board(), "raise_7")
    click.assert_not_called()


def _input_driver(value):
    driver = Mock()
    driver.capabilities = {"platformName": "mac"}
    hidden, field = _control(), _control()
    hidden.is_displayed.return_value = False
    field.get_property.return_value = value
    def execute(script, arg):
        if script == FIND_ACTION_CONTROLS:
            return [_control()]
        if script == FIND_RAISE_INPUTS:
            return [hidden, field]
        assert script == HIT_TEST
        return True
    driver.execute_script.side_effect = execute
    return driver, hidden, field


def test_enters_visible_raise_input_with_mac_select_all():
    driver, hidden, field = _input_driver("7")
    set_raise_amount(driver, "7")
    hidden.send_keys.assert_not_called()
    field.click.assert_called_once()
    assert field.send_keys.call_args_list[0].args == (Keys.COMMAND, "a")
    assert field.send_keys.call_args_list[1].args == ("7",)


def test_old_input_value_causes_timeout_instead_of_submission():
    driver, hidden, field = _input_driver("5")
    with pytest.raises(TimeoutException, match="did not accept 7"):
        set_raise_amount(driver, "7", timeout=0)


def test_raise_button_amount_must_match_requested_amount():
    driver = Mock()
    old, updated = _control(), _control()
    old.text = "Raise: 5"
    updated.text = "All-in: 7"
    driver.execute_script.side_effect = lambda script, arg: [old, updated] if script == FIND_ACTION_CONTROLS else True
    click_action(driver, "raise", "bet", "all_in", expected_amount="7")
    old.click.assert_not_called()
    updated.click.assert_called_once()
