"""Tests for thread-safe application state."""

from chairrorist import status


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def test_initial_state():
    clock = FakeClock()
    st = status.StatusManager(polling_interval=5, alert_interval=100, clock=clock)
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


def test_is_alert_due():
    clock = FakeClock()
    st = status.StatusManager(alert_interval=100, clock=clock)
    # last_alert_time is initialised to clock() == 0.
    clock.now = 99
    assert st.is_alert_due() is False
    clock.now = 100
    assert st.is_alert_due() is True


def test_mark_standing_counts_respected():
    st = status.StatusManager(polling_interval=5, alert_interval=10)
    st.increment_sitting_time()  # 5
    st.increment_sitting_time()  # 10
    assert st.mark_standing() is True
    assert st.realised_notifications == 1
    assert st.sitting_time == 0
    assert st.sitting_time_formatted == "0s"


def test_mark_standing_below_threshold_not_counted():
    st = status.StatusManager(polling_interval=5, alert_interval=10)
    st.increment_sitting_time()  # 5
    assert st.mark_standing() is False
    assert st.realised_notifications == 0


def test_mark_standing_not_double_counted():
    st = status.StatusManager(polling_interval=5, alert_interval=10)
    st.increment_sitting_time()
    st.increment_sitting_time()
    assert st.mark_standing() is True
    assert st.mark_standing() is False  # still standing
    assert st.realised_notifications == 1


def test_reset_timer():
    st = status.StatusManager(polling_interval=5)
    st.increment_sitting_time()
    st.increment_sitting_time()
    st.reset_timer()
    assert st.sitting_time == 0
    assert st.sitting_time_formatted == "0s"


def test_mute_toggle():
    st = status.StatusManager()
    assert st.muted is False
    st.set_muted(True)
    assert st.muted is True


def test_increment_ignored_notifications():
    st = status.StatusManager()
    assert st.increment_ignored_notifications() == 1
    assert st.increment_ignored_notifications() == 2
    assert st.ignored_notifications == 2
