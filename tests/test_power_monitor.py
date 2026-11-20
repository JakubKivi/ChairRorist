"""Tests for the pure power-state machine (no Win32 required)."""

from chairrorist import power_monitor as pm


def _make():
    events = []
    return pm.PowerState(events.append), events


def test_screen_off_then_on():
    state, events = _make()
    state.handle_display_state(0)
    state.handle_display_state(1)
    assert events == [True, False]


def test_dimmed_display_is_not_away():
    state, events = _make()
    state.handle_display_state(2)
    assert events == []
    assert state.away is False


def test_suspend_then_resume():
    state, events = _make()
    state.handle_power_event(pm.PBT_APMSUSPEND)
    state.handle_power_event(pm.PBT_APMRESUMEAUTOMATIC)
    assert events == [True, False]


def test_resume_suspend_clears_stale_display_off():
    state, events = _make()
    state.handle_display_state(0)  # screen off
    state.handle_power_event(pm.PBT_APMSUSPEND)  # then sleep
    state.handle_power_event(pm.PBT_APMRESUMESUSPEND)  # user woke the PC
    assert events == [True, False]


def test_still_away_after_resume_when_screen_stays_off():
    state, events = _make()
    state.handle_display_state(0)
    state.handle_power_event(pm.PBT_APMSUSPEND)
    state.handle_power_event(pm.PBT_APMRESUMEAUTOMATIC)  # e.g. maintenance wake
    assert state.away is True
    assert events == [True]


def test_duplicate_events_notify_once():
    state, events = _make()
    state.handle_display_state(0)
    state.handle_display_state(0)
    state.handle_power_event(pm.PBT_APMSUSPEND)
    assert events == [True]


def test_unknown_power_event_ignored():
    state, events = _make()
    state.handle_power_event(0x0A)  # PBT_APMPOWERSTATUSCHANGE
    assert events == []
