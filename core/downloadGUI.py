import customtkinter as ctk
import threading
import sys
import asyncio
import io
import subprocess
import os
import aiohttp
from itertools import cycle
from core.downloadmanager import DownloadManager

#sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='ignore')

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class AppDownload(ctk.CTk):
    def __init__(self, url, output_path):
        super().__init__()
        self.title("Downloading...")
        self.geometry("600x200")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.attributes('-topmost', True)  # Pencereyi ön planda tut

        self.loadascii = cycle([9692, 9693, 9694, 9695, 9696, 9697])
        self.ref_val2 = 0
        self.running = True

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(pady=10, fill="x", padx=20)

        self.icon_label_frame = ctk.CTkFrame(self.main_frame)
        self.icon_label_frame.pack(side="left", padx=10)

        self.loadingIco = ctk.CTkButton(
            self.icon_label_frame, 
            text="♞", 
            width=40, 
            height=25, 
            fg_color="transparent", 
            font=("Arial", 17, "bold")
        )
        self.loadingIco.pack(side="left")

        self.progress_label = ctk.CTkLabel(self.icon_label_frame, text="Sync Files Progress")
        self.progress_label.pack(side="left", padx=10)

        self.progress_bar_main = ctk.CTkProgressBar(self, height=16)
        self.progress_bar_main.set(0)
        self.progress_bar_main.pack(pady=5, fill="x", padx=20)

        self.progress_bar_secondary = ctk.CTkProgressBar(self, height=10)
        self.progress_bar_secondary.set(0)
        self.progress_bar_secondary.pack(pady=5, fill="x", padx=20)

        self.speed_label = ctk.CTkLabel(self, text="Download Speed: 0.00 KB/s")
        self.speed_label.pack(pady=5, padx=20)

        self.console_box = ctk.CTkTextbox(self, height=100)
        self.console_box.pack(padx=10, pady=10, fill="both", expand=True)

        self.output_path = os.path.abspath(output_path)
        print(f"[DEBUG] AppDownload initialized with output_path: {self.output_path}")
        self.download_manager = DownloadManager(url, self.output_path, self)
        self.run_process()

    def console_box_insert(self, text):
        self.console_box.insert("end", text)
        self.console_box.see("end")

    def update_progress(self, total_progress, inner_progress, speed=0.0):
        self.progress_bar_main.set(total_progress / 100)
        self.progress_bar_secondary.set(inner_progress / 100)
        self.speed_label.configure(text=f"Download Speed: {speed:.2f} KB/s")
        if inner_progress - self.ref_val2 > 2:
            self.loadingIco.configure(text=str(chr(next(self.loadascii))))
            self.ref_val2 = inner_progress

    def run_process(self):
        self.console_box_insert("Please wait...\n")

        def thread_target():
            try:
                async def async_main():
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
                        files = self.download_manager.get_files_to_sync()
                        tasks = [self.download_manager.process_file(session, file) for file in files]
                        await asyncio.gather(*tasks)

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(async_main())
                loop.close()

                self.console_box_insert("\nİndirme tamamlandı.\n")
                exe_path = os.path.join(self.output_path, "silkroad.exe")
                print(f"[DEBUG] Checking for silkroad.exe at: {exe_path}")
                if os.path.exists(exe_path):
                    print(f"[DEBUG] Starting silkroad.exe")
                    self.console_box_insert("silkroad.exe başlatılıyor...\n")
                    subprocess.Popen(exe_path)
                    self.running = False
                    self.destroy()
                else:
                    print(f"[ERROR] silkroad.exe not found at: {exe_path}")
                    self.console_box_insert(f"[ERROR] silkroad.exe bulunamadı: {exe_path}\n")
            except Exception as e:
                print(f"[ERROR] Download error: {str(e)}")
                self.console_box_insert(f"[ERROR] İndirme hatası: {str(e)}\n")

        threading.Thread(target=thread_target, daemon=True).start()

    def on_closing(self):
        self.running = False
        self.destroy()

if __name__ == "__main__":
    test_url = "https://raw.githubusercontent.com/kantrveysel/SRO-SB_Client_Data/master/"
    test_output_path = "./Client"
    app = AppDownload(test_url, test_output_path)
    app.mainloop()