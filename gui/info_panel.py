import threading
import webbrowser
from customtkinter import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from utils.image_utils import load_image_from_url
from utils.helper import check_ping, get_resource_path

class InfoPanel:
    def __init__(self, app, frame):
        self.frame = frame
        self.app = app
        self.infoTable = {
            "Rule": {
                "language": "UK",
                "Mode": "Pvp",
                "Map": "CH",
                "Web": "www.google.com.tr",
                "Time": "10:10",
                "Ping": "50"
            }
        }
        self.selectedserver = None
        self.serverinfodraw()

    def serverinfodraw(self):
        self.frame.pack(fill='y', side='right', expand=False)
        BannerFrame = CTkFrame(self.frame)
        BannerFrame.pack(side='top', fill='x', padx=5, pady=5)
        img_path = get_resource_path("..","imgs","placeholder_server.png")
        placeholder = load_image_from_url(None, img_path, (240, 300))
        self.banner_server = CTkLabel(BannerFrame, text="", image=placeholder)
        self.banner_server.pack(padx=5, pady=10)
        self.banner_server.image = placeholder
        InfoTextFrame = CTkFrame(self.frame)
        InfoTextFrame.pack(side='top', fill='x', padx=5, pady=5)
        InfoTextFrame.grid_columnconfigure((0, 1), weight=1)
        CTkLabel(InfoTextFrame, text="Rule", fg_color="gray", text_color="black", anchor="center").grid(row=0, column=0, padx=5, pady=1, sticky="nsew")
        CTkLabel(InfoTextFrame, text="Value", fg_color="gray", text_color="black", anchor="center").grid(row=0, column=1, padx=1, pady=1, sticky="nsew")
        for i, element in enumerate(self.infoTable["Rule"]):
            CTkLabel(InfoTextFrame, text=element, fg_color="lightgray", text_color="black", anchor="center").grid(row=i+1, column=0, padx=5, pady=1, sticky="nsew")
            self.infoTable["Rule"][element] = CTkLabel(InfoTextFrame, text="N/A", anchor="center")
            self.infoTable["Rule"][element].grid(row=i+1, column=1, padx=1, pady=1, sticky="nsew")
        self.infoTable["Rule"]["Web"].bind("<Button-1>", self.clickWebLink)
        self.ping_frame = CTkFrame(self.frame)
        self.ping_frame.pack(side='top', fill='both', expand=True, padx=10, pady=10)
        self.pingGraph = None

    def clickWebLink(self, e):
        if self.selectedserver:
            webbrowser.open_new(self.selectedserver["web"])

    def updateServerInfo(self, itemid):
        self.selectedserver = None
        for server in self.app.servers:
            if server["ID"] == self.app.index_servers[int(itemid)]:
                threading.Thread(target=self.load_banner_image, args=(server["banner"],), daemon=True).start()
                self.selectedserver = server
                break
        if self.selectedserver:
            self.infoTable["Rule"]["language"].configure(text=server["language"])
            self.infoTable["Rule"]["Mode"].configure(text=server["mode"])
            self.infoTable["Rule"]["Web"].configure(text=server["web"])
            self.infoTable["Rule"]["Time"].configure(text="00:00")
            self.infoTable["Rule"]["Ping"].configure(text=server["ping"])
            self.infoTable["Rule"]["Map"].configure(text=server["map"])
            self.draw_ping_graph(server["ping_last_1_hours"])

    def draw_ping_graph(self, ping_data):
        for widget in self.ping_frame.winfo_children():
            widget.destroy()

        def draw():
            raw_width = self.ping_frame.winfo_width() or 400
            raw_height = self.ping_frame.winfo_height() or 300
            expected_height = int(raw_width * 3 / 4)
            self.ping_frame.configure(height=expected_height)
            target_width = raw_width
            target_height = int(target_width * 3 / 4)
            if target_height > raw_height:
                target_height = raw_height
                target_width = int(target_height * 4 / 3)
            target_width = max(300, min(target_width, 800))
            target_height = max(225, min(target_height, 600))
            fig, ax = plt.subplots(figsize=(target_width / 100, target_height / 100), dpi=100)
            ax.plot(ping_data, color='lime', linewidth=2)
            ax.set_facecolor('#222222')
            fig.patch.set_facecolor('#222222')
            ax.get_xaxis().set_visible(False)
            ax.tick_params(axis='y', colors='white')
            ax.spines['left'].set_color('white')
            ax.spines['bottom'].set_color('white')
            ax.yaxis.grid(True, color='gray', linestyle='--', linewidth=0.5)
            ax.xaxis.grid(False)
            canvas = FigureCanvasTkAgg(fig, master=self.ping_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True)
        self.ping_frame.after(100, draw)

    def load_banner_image(self, url):
        img = load_image_from_url(url, "imgs/placeholder_server.png", (240, 300))
        self.app.root.after(0, lambda: self.update_image(img))
        try:
            self.selectedserver["ping"] = check_ping(self.selectedserver["IP"]) 
        except:
            pass

    def update_image(self, img):
        self.banner_server.configure(image=img)
        self.banner_server.image = img