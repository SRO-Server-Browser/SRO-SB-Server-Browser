import sys
from gui.app import App
from utils.admin_check import is_admin, request_admin

if __name__ == "__main__":
    if not is_admin():
        request_admin(sys.executable, __file__)
        sys.exit()
    app = App()
    app.start()