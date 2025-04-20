import json
from tkinter import ttk
import tkinter as tk
from PIL import Image, ImageTk
from customtkinter import *
from .header_panel import HeaderPanel
from .info_panel import InfoPanel
from .tooltip import Tooltip
from customtkinter import ThemeManager

from utils.helper import get_resource_path

class App:
    def __init__(self):
        self.root = CTk()
        self.setup_window()
        self.load_data()
        self.setup_styles()
        self.load_images()
        self.treeviews = {}
        self.tooltips = {}

    def setup_window(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = int(screen_width * 0.6)
        height = int(screen_height * 0.7)
        x = int((screen_width - width) / 2)
        y = int((screen_height - height) / 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(640, 480)

    def load_data(self):
        path = get_resource_path("..", "data", "servers.json")
        self.data_from_gw = json.load(open(path))
        self.servers = self.data_from_gw["network"]
        self.info = self.data_from_gw["info"]
        self.index_servers = {i: k["ID"] for i, k in zip(range(len(self.servers)), self.servers)}
        self.favorites = self.data_from_gw["favorites"]

    def setup_styles(self):
        bg_color = self.root._apply_appearance_mode(ThemeManager.theme["CTkFrame"]["fg_color"])
        text_color = self.root._apply_appearance_mode(ThemeManager.theme["CTkLabel"]["text_color"])
        treestyle = ttk.Style()
        treestyle.theme_use('default')
        treestyle.configure("Treeview", background=bg_color, foreground=text_color, fieldbackground=bg_color, borderwidth=0, font=('arial', 10))
        treestyle.map('Treeview', background=[('selected', text_color)], foreground=[('selected', bg_color)], borderwidth=[('selected', 2)], font=[('selected', ('arial', 12, "bold"))])
        treestyle.configure("Treeview.Heading", background=text_color, foreground=bg_color, fieldbackground=bg_color, borderwidth=0, font=('arial', 13, 'bold'))

    def load_images(self):
        img_path = get_resource_path("..","imgs","online.png")
        self.online_img = ImageTk.PhotoImage(Image.open(img_path))
        img_path = get_resource_path("..","imgs","offline.png")
        self.offline_img = ImageTk.PhotoImage(Image.open(img_path))

    def draw(self):
        self.height = self.root.winfo_height()
        self.width = self.root.winfo_width()
        self.headerFrame = CTkFrame(self.root, fg_color="gray")
        self.mainFrame = CTkFrame(self.root)
        self.footerFrame = CTkFrame(self.root, fg_color="gray")
        self.header = HeaderPanel(self, self.headerFrame)
        self.header.draw()
        self.mainDraw(self.mainFrame)
        self.footer(self.footerFrame)

    def mainDraw(self, frame):
        frame.pack(fill='both', expand=True)
        self.serverlistFrame = CTkFrame(frame)
        self.serverinfoFrame = CTkFrame(frame)
        self.infoPanel = InfoPanel(self, self.serverinfoFrame)
        self.mainFrame.update_idletasks()
        self.tabviewDraw(self.serverlistFrame)

    def footer(self, frame):
        frame.pack(fill='x', side='bottom', expand=False)
        CTkLabel(frame, text="Footer").pack()

    def tabviewDraw(self, frame):
        frame.pack(fill='both', side='left', expand=True)
        self.tabview = CTkTabview(frame)
        self.network_tab = self.tabview.add("Network")
        self.serverlistdraw(self.network_tab, "Network")
        self.favorites_tab = self.tabview.add("Favorites")
        self.serverlistdraw(self.favorites_tab, "Favorites")
        self.tabview.pack(side='bottom', fill="both", expand=True)

    def refreshTreeview(self):
        sorted_servers = sorted(self.servers, key=lambda s: s["ID"])
        for item in self.treeviews["Network"].get_children():
            self.treeviews["Network"].delete(item)
        for server in sorted_servers:
            self.treeviews["Network"].insert(
                "", "end",
                values=(
                    server["ID"],
                    server["status"],
                    server["name"],
                    server["mode"],
                    server["map"],
                    f'{server["players"]}/{server["max_players"]}'
                )
            )

    def addServer(self, server):
        # Sunucunun ID'si ile mevcut sunucular arasında kontrol yapalım
        existing_server_index = None
        for index, server_id in self.index_servers.items():
            if server_id == server["ID"]:
                existing_server_index = index
                return existing_server_index, server

        if existing_server_index is not None:
            # Mevcut sunucu bulunmuşsa, verilerini güncelle
            self.updateServerInTreeview(existing_server_index, server)
            return existing_server_index, server
        else:
            # Yeni sunucu ekle
            next_index = max(self.index_servers.keys(), default=6) + 3
            self.index_servers[next_index] = server["ID"]
            self.addServerToTreeview(next_index, server)
            return next_index, server

    def updateServerInTreeview(self, index, server):
        # Treeview'de mevcut sunucuyu güncelle
        self.treeviews["Network"].item(index, values=(
            index,
            server["status"],
            server["name"],
            server["mode"],
            server["map"],
            f'{server["players"]}/{server["max_players"]}'
        ))

    def addServerToTreeview(self, index, server):
        # Treeview'e yeni sunucu ekle
        self.servers.append(server)
        self.treeviews["Network"].insert(
            "", "end",
            values=(
                index,
                server["status"],
                server["name"],
                server["mode"],
                server["map"],
                f'{server["players"]}/{server["max_players"]}'
            )
        )

    def serverlistdraw(self, frame, TabName="Network"):
        columns = ("ID", "Status", "Name", "Mode", "Map", "Players")
        self.treeviews[TabName] = ttk.Treeview(frame, columns=columns, show="headings", selectmode='extended')
        self.tooltips[TabName] = Tooltip(self.treeviews[TabName])
        self.treeviews[TabName].heading("ID", text="#")
        self.treeviews[TabName].heading("Status", text="Status")
        self.treeviews[TabName].heading("Name", text="Name")
        self.treeviews[TabName].heading("Mode", text="Mode")
        self.treeviews[TabName].heading("Map", text="Map")
        self.treeviews[TabName].heading("Players", text="Players")
        self.treeviews[TabName].column("ID", width=16, anchor="center")
        self.treeviews[TabName].column("Status", width=80, anchor="center")
        self.treeviews[TabName].column("Name", width=150, anchor="w")
        self.treeviews[TabName].column("Mode", width=80, anchor="center")
        self.treeviews[TabName].column("Map", width=80, anchor="center")
        self.treeviews[TabName].column("Players", width=100, anchor="w")
        if TabName == "Network":
            for server in self.servers:
                status_icon = self.offline_img if server["status"].lower() == "offline" else self.online_img
                item = self.treeviews[TabName].insert(
                    "", "end",
                    values=(
                        server["ID"],
                        server["status"],
                        server["name"],
                        server["mode"],
                        server["map"],
                        f'{server["players"]}/{server["max_players"]}'
                    )
                )
                self.treeviews[TabName].item(item, image=status_icon)
        elif TabName == "Favorites":
            for server in self.favorites:
                index, _ = self.addServer(server)
                status_icon = self.offline_img if server["status"].lower() == "offline" else self.online_img
                item = self.treeviews[TabName].insert(
                    "", "end",
                    values=(
                        index,
                        server["status"],
                        server["name"],
                        server["mode"],
                        server["map"],
                        f'{server["players"]}/{server["max_players"]}'
                    )
                )
        self.scrollbar = CTkScrollbar(frame, orientation="vertical", command=self.treeviews[TabName].yview)
        self.treeviews[TabName].configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.treeviews[TabName].pack(fill="both", expand=True, side='left')
        self.treeviews[TabName].update_idletasks()
        self.treeviews[TabName].bind("<<TreeviewSelect>>", lambda e: self.treeviewSelected(e, TabName))
        self.treeviews[TabName].bind("<Motion>", self.tooltips[TabName].on_motion)
        self.treeviews[TabName].bind("<Leave>", self.tooltips[TabName].on_leave)

    def treeviewSelected(self, event, tabname):
        selected = self.treeviews[tabname].selection()
        if selected:
            for item in selected:
                itemid = self.treeviews[tabname].item(item, 'values')[0]
                self.infoPanel.updateServerInfo(itemid)
                self.header.updateServerInfo(itemid)

    def start(self):
        set_appearance_mode("system")
        set_default_color_theme("blue")
        self.draw()
        self.root.mainloop()