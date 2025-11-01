import keyboard


def func(a, b):
    a()
    b()


def listen_hotkey(hotkey: str, callback, messssageFunction):
    # ctrl + shift + alt + d
    keyboard.add_hotkey(hotkey, lambda: func(callback, messssageFunction))
    keyboard.wait()  # blocks only this thread
