"""Tests for notification helpers and statistics persistence."""

from chairrorist import notifications, paths, status


def test_random_alert_line(tmp_path):
    path = tmp_path / "alerts.txt"
    path.write_text("one\ntwo\n\nthree\n", encoding="utf-8")
    for _ in range(20):
        assert notifications.get_random_alert_line(str(path)) in {
            "one",
            "two",
            "three",
        }


def test_random_alert_line_empty_file(tmp_path):
    path = tmp_path / "empty.txt"
    path.write_text("\n   \n", encoding="utf-8")
    assert notifications.get_random_alert_line(str(path)) == "File empty"


def test_random_alert_line_missing_file(tmp_path):
    assert (
        notifications.get_random_alert_line(str(tmp_path / "nope.txt"))
        == "Cannot find file"
    )


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    data_path = tmp_path / "data.chairRorist"
    monkeypatch.setattr(paths, "get_data_file_path", lambda: str(data_path))

    notifications.save_data(3, 7)
    assert notifications.load_data() == (3, 7)


def test_load_data_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(
        paths, "get_data_file_path", lambda: str(tmp_path / "missing.chairRorist")
    )
    assert notifications.load_data() == (0, 0)


def test_load_data_truncated_file(tmp_path, monkeypatch):
    data_path = tmp_path / "bad.chairRorist"
    data_path.write_bytes(b"\x01\x00")
    monkeypatch.setattr(paths, "get_data_file_path", lambda: str(data_path))
    assert notifications.load_data() == (0, 0)


def test_send_warning_muted_no_notify(monkeypatch):
    st = status.StatusManager()
    st.set_muted(True)
    calls = []
    monkeypatch.setattr(notifications, "notify", lambda *a, **k: calls.append(a))
    monkeypatch.setattr(notifications, "save_data", lambda *a: calls.append(("save", a)))
    notifications.send_warning(st)
    assert calls == []


def test_send_warning_notifies_when_not_muted(monkeypatch):
    st = status.StatusManager()
    calls = []
    monkeypatch.setattr(notifications, "get_random_alert_line", lambda: "test line")
    monkeypatch.setattr(notifications, "notify", lambda *a, **k: calls.append(a))
    monkeypatch.setattr(notifications, "save_data", lambda *a: None)
    notifications.send_warning(st)
    assert calls == [("test line", "Sitting time 0s")]


def test_send_warning_increments_ignored(monkeypatch):
    st = status.StatusManager(alert_interval=3600)
    st.set_sitting_time(4000)  # > 3600 * 1.1
    saved = []
    monkeypatch.setattr(notifications, "get_random_alert_line", lambda: "test line")
    monkeypatch.setattr(notifications, "notify", lambda *a, **k: None)
    monkeypatch.setattr(
        notifications, "save_data", lambda i, r: saved.append((i, r))
    )
    notifications.send_warning(st)
    assert st.ignored_notifications == 1
    assert saved == [(1, 0)]
