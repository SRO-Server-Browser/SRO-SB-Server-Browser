import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def request_admin(executable, file):
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", executable, file, None, 1
    )