import os
import sys
import asyncio
import threading
import json
from itertools import cycle
from random import randint
from customtkinter import *
from PIL import Image
from time import sleep
import pystray
import webbrowser

from core.ClientHub import HUB
from utils.helper import get_hub_ip, get_resource_path
from core.downloadGUI import AppDownload

class HeaderPanel:
    def __init__(self, app, frame):
        self.app = app
        self.frame = frame
        self.loadascii = cycle([9692, 9693, 9694, 9695, 9696, 9697])
        self.hub_ip = get_hub_ip()
        self.port = int(os.getenv("HUB_Port", 0))
        self.hub = HUB(self.hub_ip, self.port)
        self.selectedserver = None
        self.state = 0
        self.frame.after(500, self.startHUB)

    def hide_to_tray(self):
        self.app.root.withdraw()

        def on_show(icon, item):
            self.app.root.deiconify()
            icon.stop()

        def on_quit(icon, item):
            icon.stop()
            self.app.root.quit()

        menu = pystray.Menu(
            pystray.MenuItem("Göster", on_show),
            pystray.MenuItem("Çıkış", on_quit),
        )
        img_path = get_resource_path("..","imgs","SROSB.ico")
        icon_image = Image.open(img_path)
        icon = pystray.Icon("TrayIcon", icon_image, "SRO:SB", menu)
        threading.Thread(target=icon.run, daemon=True).start()
        
    def run_process(self, url, output):
        try:
            url = url.rstrip('/') + '/'
            output = os.path.abspath(os.path.join(os.path.dirname(__file__), output))
            print(f"[DEBUG] Starting AppDownload with url={url}, output={output}")
            download_window = AppDownload(url, output)
            print("[DEBUG] AppDownload window created")
            download_window.mainloop()
            print("[DEBUG] Download process completed")
        except Exception as e:
            print(f"[ERROR] Failed to start download window: {str(e)}")

    def startHUB(self):
        def runner():
            self.hub_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.hub_loop)
            self.hub.loop = self.hub_loop  # ÖNCE LOOP'U AYARLA
            self.hub_loop.run_until_complete(self.hub.start())
            
        self.hub_thread = threading.Thread(target=runner, daemon=True)
        self.hub_thread.start()

        self.frame.after(1000, self.updateServerList)
        self.frame.after(5000, lambda:self.hub.start_broadcast_listener())
        

    def updateServerInfo(self, itemid):
        self.selectedserver = None
        for server in self.app.servers:
            if server["ID"] == self.app.index_servers[int(itemid)]:
                self.selectedserver = server

    def updateServerList(self):
        delay = 3000 + self.state * 10000
        try:
            self.hub.scanServer()
            for new in self.hub.servers_cache:
                self.app.addServer(new)
        except Exception as e:
            delay += 6000
            print(e)
        self.frame.after(delay, self.updateServerList)


    def startButton(self):
        if self.selectedserver:
            print("Start Server")
            ips = self.selectedserver["IP"]
            Port = self.selectedserver["Port"]
            self.gateway = self.hub.startGateWay(ips, Port)
            print(self.selectedserver)
            username, password = (self.username.get(), self.password.get())
            self.hub.joinServer(self.selectedserver,username, password)
            self.save_username_password(username, password)
            self.state = 1
            self.hide_to_tray()
            self.run_process(self.selectedserver["repository"], "../Client") # download manageri açar

    def save_username_password(self, username, password):
        path = get_resource_path("..", "data", "servers.json")
        _data = json.load(open(path))
        _data["info"]["username"] = username
        _data["info"]["password"] = password
        with open(path, "w") as f:
            json.dump(_data, f, indent=4)

    def saveFavorites(self):
        path = get_resource_path("..", "data", "servers.json")
        _data = json.load(open(path))
        _data["favorites"] = self.app.favorites
        with open(path, "w") as f:
            json.dump(_data, f, indent=4)

    def addFavorite(self):
        if not self.selectedserver:
            return
        server = self.selectedserver
        inverse_index = {j: k for k, j in self.app.index_servers.items()}
        server_id = server["ID"]
        server_index = inverse_index[server_id]
        favorites_tree = self.app.treeviews["Favorites"]
        for item in favorites_tree.get_children():
            item_values = favorites_tree.item(item, "values")
            if item_values and int(item_values[0]) == int(server_index):
                favorites_tree.delete(item)
                self.app.favorites.remove(server)
                return
        favorites_tree.insert(
            "", "end",
            values=(
                server_index,
                server["status"],
                server["name"],
                server["mode"],
                server["map"],
                f'{server["players"]}/{server["max_players"]}'
            )
        )
        self.app.favorites.append(server)
        self.saveFavorites()

    def load_username_password(self):
        path = get_resource_path("..", "data", "servers.json")
        _data = json.load(open(path))
        self.username.insert(0, _data["info"]["username"])
        self.password.insert(0, _data["info"]["password"])


    def draw(self):
        self.frame.pack(fill='x', side='top', expand=False)
        buttonFrame = CTkFrame(self.frame)
        EntryFrame = CTkFrame(self.frame)
        buttonFrame.pack(fill='both', side='left', expand=True)
        EntryFrame.pack(fill='both', side='right', expand=True)
        CTkButton(buttonFrame, text="▶", width=25, height=25, corner_radius=25, command=self.startButton).grid(row=0, column=0, padx=5, pady=5)
        CTkButton(buttonFrame, text="♞", width=25, height=25, corner_radius=25, command=self.hide_to_tray).grid(row=0, column=1, padx=5, pady=5)
        #CTkButton(buttonFrame, text="☁", width=25, height=25, corner_radius=25).grid(row=0, column=2, padx=5, pady=5)
        CTkButton(buttonFrame, text="★", width=25, height=25, corner_radius=25, command=self.addFavorite).grid(row=0, column=3, padx=5, pady=5)
        CTkButton(buttonFrame, text="☎", width=25, height=25, corner_radius=25, command=self.sendFeedback ).grid(row=0, column=4, padx=5, pady=5)
        #CTkButton(buttonFrame, text="🖬", width=25, height=25, corner_radius=25).grid(row=0, column=5, padx=5, pady=5)
        #CTkButton(buttonFrame, text="🖿", width=25, height=25, corner_radius=25).grid(row=0, column=6, padx=5, pady=5)
        #CTkButton(buttonFrame, text="🗫", width=25, height=25, corner_radius=25).grid(row=0, column=7, padx=15, pady=5)
        CTkLabel(EntryFrame, text="Username").grid(row=0, column=0, padx=15, pady=2)
        self.username = CTkEntry(EntryFrame)
        self.username.grid(row=0, column=1, padx=0, pady=2)
        CTkLabel(EntryFrame, text="Password").grid(row=0, column=2, padx=15, pady=2)
        self.password = CTkEntry(EntryFrame, show='*')
        self.password.grid(row=0, column=3, padx=0, pady=2)
        self.loadingIco = CTkButton(buttonFrame, text=str(chr(next(self.loadascii))), width=40, height=25, fg_color="transparent", font=("Arial", 17, "bold"), command=self.app.refreshTreeview)
        self.loadingIco.grid(row=0, column=8, padx=20, pady=5)
        self.frame.after(100, self.loadingIconUpdate)
        self.load_username_password()

    def sendFeedback(self):
        url = "https://github.com/SRO-Server-Browser/SRO-SB-Server-Browser/issues/new?template=bug_report.md"
        webbrowser.open(url)

    def loadingIconUpdate(self):
        self.loadingIco.configure(text=str(chr(next(self.loadascii))))
        self.frame.after(randint(200, 800), self.loadingIconUpdate)