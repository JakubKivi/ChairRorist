"""Tests for thread-safe application state."""

from chairrorist import status


def _sit(st, ticks):
    """Advance by *ticks* one-second sitting ticks through the app loop."""
    for _ in range(ticks):
        st.increment_sitting_time()
        if st.should_alert():
            st.mark_alerted()


def test_initial_state():
    st = status.StatusManager(polling_interval=1, alert_interval=20)
    assert st.connected is False
    assert st.sitting_time == 0
    assert st.sitting_time_formatted == "0s"
    assert st.ignored_notifications == 0
    assert st.realised_notifications == 0
    assert st.muted is False


def test_connection_toggle():
    st = status.StatusManager()
    st.set_connected(True)
    assert st.connected is True
    st.set_connected(False)
    assert st.connected is False


def test_increment_sitting_time():
    st = status.StatusManager(polling_interval=5)
    st.increment_sitting_time()
    assert st.sitting_time == 5
    assert st.sitting_time_formatted == "5s"
    st.increment_sitting_time()
    assert st.sitting_time == 10


def test_should_alert_and_mark_alerted():
    st = status.StatusManager(polling_interval=1, alert_interval=20)
    assert st.should_alert() is False

    for _ in range(19):
        st.increment_sitting_time()
    assert st.should_alert() is False

    st.increment_sitting_time()  # sitting_time == 20
    assert st.should_alert() is True

    st.mark_alerted()
    assert st.should_alert() is False

    for _ in range(19):
        st.increment_sitting_time()
    assert st.should_alert() is False
    st.increment_sitting_time()  # sitting_time == 40
    assert st.should_alert() is True


def test_ignored_counted_when_next_alert_fires():
    st = status.StatusManager(polling_interval=1, alert_interval=20)

    # The reminder at 20s is ignored when the next one fires at 40s.
    _sit(st, 40)
    assert st.ignored_notifications == 1
    assert st.realised_notifications == 0

    # The reminder at 40s is ignored when the next one fires at 60s.
    _sit(st, 20)
    assert st.ignored_notifications == 2


def test_respected_counted_when_standing_before_next_alert():
    st = status.StatusManager(polling_interval=1, alert_interval=20)
    _sit(st, 20)  # reminder fires at 20s
    _sit(st, 19)  # still sitting at 39s, just before the next reminder
    assert st.mark_standing() is True
    assert st.realised_notifications == 1
    assert st.ignored_notifications == 0


def test_ignored_reminder_is_not_retroactively_respected():
    st = status.StatusManager(polling_interval=1, alert_interval=20)
    _sit(st, 40)  # reminder at 20s ignored at 40s; reminder at 40s now pending
    assert st.ignored_notifications == 1

    # Standing now respects the 40s reminder, not the ignored 20s one.
    assert st.mark_standing() is True
    assert st.realised_notifications == 1
    assert st.ignored_notifications == 1


def test_standing_without_alert_not_counted():
    st = status.StatusManager(polling_interval=1, alert_interval=20)
    _sit(st, 5)  # no alert fired yet
    assert st.mark_standing() is False
    assert st.realised_notifications == 0
    assert st.ignored_notifications == 0


def test_multiple_sessions():
    st = status.StatusManager(polling_interval=1, alert_interval=20)

    # Session 1: ignore the reminder, then stand (respecting the next one).
    _sit(st, 40)
    assert st.ignored_notifications == 1
    assert st.mark_standing() is True
    assert st.realised_notifications == 1

    # Session 2: respect the reminder.
    _sit(st, 21)
    assert st.mark_standing() is True
    assert st.realised_notifications == 2
    assert st.ignored_notifications == 1


def test_reset_timer():
    st = status.StatusManager(polling_interval=1, alert_interval=20)
    _sit(st, 25)  # reminder fired at 20s, still pending
    st.reset_timer()
    assert st.sitting_time == 0
    assert st.sitting_time_formatted == "0s"
    assert st.should_alert() is False
    # A pending reminder is discarded on reset.
    assert st.mark_standing() is False


def test_mute_toggle():
    st = status.StatusManager()
    assert st.muted is False
    st.set_muted(True)
    assert st.muted is True


