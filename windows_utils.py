import ctypes


# ============================================================
# Windows constants
# ============================================================

WDA_NONE = 0x00000000
WDA_EXCLUDEFROMCAPTURE = 0x00000011

GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_LAYERED = 0x00080000
LWA_ALPHA = 0x00000002

SW_HIDE = 0
SW_SHOW = 5

SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004
SWP_FRAMECHANGED = 0x0020
SWP_NOACTIVATE = 0x0010

WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

# Virtual key codes
VK_RETURN = 0x0D
VK_A = 0x41
VK_L = 0x4C
VK_P = 0x50
VK_T = 0x54

# Hotkey IDs
HOTKEY_ID_TRANSPARENT = 9001
HOTKEY_ID_LISTEN = 9002
HOTKEY_ID_PROTECT = 9003
HOTKEY_ID_ASK_AI = 9004
HOTKEY_ID_ASK_AI_ALT = 9005

COINIT_MULTITHREADED = 0x0
RPC_E_CHANGED_MODE = -2147417850


# ============================================================
# Capture protection
# ============================================================

def set_capture_protection(window, enabled=True):
    """
    Enable or disable Windows capture exclusion
    for the given window.
    """

    hwnd = int(window.winId())

    affinity = (
        WDA_EXCLUDEFROMCAPTURE
        if enabled
        else WDA_NONE
    )

    result = ctypes.windll.user32.SetWindowDisplayAffinity(
        hwnd,
        affinity,
    )

    return bool(result)


# ============================================================
# Tool window / Taskbar visibility
# ============================================================

def set_tool_window(window, enabled=True):
    """
    Enable or disable WS_EX_TOOLWINDOW extended style for the window.
    Hides the window from the Windows Taskbar and Alt+Tab switcher when enabled.
    """

    hwnd = int(window.winId())
    user32 = ctypes.windll.user32

    if hasattr(user32, "GetWindowLongPtrW"):
        get_window_long = user32.GetWindowLongPtrW
        set_window_long = user32.SetWindowLongPtrW
    else:
        get_window_long = user32.GetWindowLongW
        set_window_long = user32.SetWindowLongW

    get_window_long.argtypes = [ctypes.c_void_p, ctypes.c_int]
    get_window_long.restype = ctypes.c_ssize_t
    set_window_long.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_ssize_t]
    set_window_long.restype = ctypes.c_ssize_t

    style = get_window_long(hwnd, GWL_EXSTYLE)

    if enabled:
        new_style = (style | WS_EX_TOOLWINDOW) & ~WS_EX_APPWINDOW
    else:
        new_style = (style & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW

    # In Windows, hiding and restoring the window forces Explorer
    # to update taskbar buttons and Alt+Tab registrations.
    user32.ShowWindow(hwnd, SW_HIDE)
    set_window_long(hwnd, GWL_EXSTYLE, new_style)
    user32.SetWindowPos(
        hwnd,
        0,
        0,
        0,
        0,
        0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED | SWP_NOACTIVATE,
    )
    user32.ShowWindow(hwnd, SW_SHOW)

    return True


# ============================================================
# Transparent / Click-through window
# ============================================================

def set_click_through(window, enabled=True, opacity=0.7):
    """
    Enable or disable WS_EX_TRANSPARENT and WS_EX_LAYERED for mouse click-through
    and visual transparency.
    """

    hwnd = int(window.winId())
    user32 = ctypes.windll.user32

    if hasattr(user32, "GetWindowLongPtrW"):
        get_window_long = user32.GetWindowLongPtrW
        set_window_long = user32.SetWindowLongPtrW
    else:
        get_window_long = user32.GetWindowLongW
        set_window_long = user32.SetWindowLongW

    get_window_long.argtypes = [ctypes.c_void_p, ctypes.c_int]
    get_window_long.restype = ctypes.c_ssize_t
    set_window_long.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_ssize_t]
    set_window_long.restype = ctypes.c_ssize_t

    style = get_window_long(hwnd, GWL_EXSTYLE)

    if enabled:
        # Enable WS_EX_TRANSPARENT (click-through) and WS_EX_LAYERED (alpha transparency)
        new_style = style | WS_EX_TRANSPARENT | WS_EX_LAYERED
        set_window_long(hwnd, GWL_EXSTYLE, new_style)
        alpha = int(255 * opacity)
        user32.SetLayeredWindowAttributes(hwnd, 0, alpha, LWA_ALPHA)
    else:
        # Remove WS_EX_TRANSPARENT (clickable again) and restore 100% opacity
        new_style = style & ~WS_EX_TRANSPARENT
        set_window_long(hwnd, GWL_EXSTYLE, new_style)
        user32.SetLayeredWindowAttributes(hwnd, 0, 255, LWA_ALPHA)

    # Frame changed notification
    user32.SetWindowPos(
        hwnd,
        0,
        0,
        0,
        0,
        0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED | SWP_NOACTIVATE,
    )

    return True


def _register_hotkey(hwnd, hotkey_id, fs_modifiers, vk):
    user32 = ctypes.windll.user32
    # Attempt with MOD_NOREPEAT to prevent repeat triggers when holding keys
    res = user32.RegisterHotKey(hwnd, hotkey_id, fs_modifiers | MOD_NOREPEAT, vk)
    if not res:
        res = user32.RegisterHotKey(hwnd, hotkey_id, fs_modifiers, vk)
    return bool(res)


def register_global_hotkeys(window):
    """
    Register all global Windows shortcuts:
    - Ctrl + Alt + T: Toggle click-through transparency
    - Ctrl + Alt + L: Toggle audio listening
    - Ctrl + Alt + P: Toggle capture protection
    - Ctrl + Alt + Enter: Send prompt to AI
    - Ctrl + Alt + A: Send prompt to AI (alternative)
    """
    hwnd = int(window.winId())
    mod = MOD_CONTROL | MOD_ALT

    hotkeys = [
        (HOTKEY_ID_TRANSPARENT, VK_T, "Transparent (Ctrl+Alt+T)"),
        (HOTKEY_ID_LISTEN, VK_L, "Listen (Ctrl+Alt+L)"),
        (HOTKEY_ID_PROTECT, VK_P, "Protect (Ctrl+Alt+P)"),
        (HOTKEY_ID_ASK_AI, VK_RETURN, "Ask AI (Ctrl+Alt+Enter)"),
        (HOTKEY_ID_ASK_AI_ALT, VK_A, "Ask AI Alt (Ctrl+Alt+A)"),
    ]

    results = {}
    for hid, vk, name in hotkeys:
        ok = _register_hotkey(hwnd, hid, mod, vk)
        results[name] = ok

    return results


def unregister_global_hotkeys(window):
    """
    Unregister all global shortcuts.
    """
    hwnd = int(window.winId())
    user32 = ctypes.windll.user32
    for hid in (
        HOTKEY_ID_TRANSPARENT,
        HOTKEY_ID_LISTEN,
        HOTKEY_ID_PROTECT,
        HOTKEY_ID_ASK_AI,
        HOTKEY_ID_ASK_AI_ALT,
    ):
        try:
            user32.UnregisterHotKey(hwnd, hid)
        except Exception:
            pass


def register_transparent_hotkey(window, hotkey_id=HOTKEY_ID_TRANSPARENT):
    """
    Register global shortcut (Ctrl + Alt + T) to toggle click-through transparency.
    """
    hwnd = int(window.winId())
    return _register_hotkey(hwnd, hotkey_id, MOD_CONTROL | MOD_ALT, VK_T)


def unregister_transparent_hotkey(window, hotkey_id=HOTKEY_ID_TRANSPARENT):
    """
    Unregister global transparent shortcut.
    """
    hwnd = int(window.winId())
    return bool(
        ctypes.windll.user32.UnregisterHotKey(
            hwnd,
            hotkey_id,
        )
    )


# ============================================================
# COM
# ============================================================

def initialize_com():
    """
    Initialize COM for the current thread.

    SoundCard uses Windows COM/WASAPI.
    """

    ole32 = ctypes.windll.ole32

    hr = ole32.CoInitializeEx(
        None,
        COINIT_MULTITHREADED,
    )

    # S_OK = 0
    # S_FALSE = 1
    # RPC_E_CHANGED_MODE = 0x80010106

    if hr not in (
        0,
        1,
        RPC_E_CHANGED_MODE,
    ):
        raise ctypes.WinError(hr)

    return hr


def uninitialize_com(hr):
    """
    Release COM if this thread initialized it.
    """

    if hr in (0, 1):
        ctypes.windll.ole32.CoUninitialize()