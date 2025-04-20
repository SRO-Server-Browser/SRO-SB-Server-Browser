import tkinter as tk
from customtkinter import *

class Tooltip:
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None

    def show(self, text, x, y):
        self.hide()
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry(f"+{x+20}+{y+10}")
        tw.configure(bg="black")
        frame = CTkFrame(tw, corner_radius=8, fg_color="#2a2a2a")
        frame.pack(padx=1, pady=1)
        label = CTkLabel(
            frame,
            text=text,
            text_color="white",
            fg_color="transparent",
            font=CTkFont(size=12)
        )
        label.pack(padx=10, pady=6)

    def hide(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

    def on_motion(self, event):
        item_id = self.widget.identify_row(event.y)
        if item_id:
            values = self.widget.item(item_id, "values")
            tooltip_text = f"{values[2]}\n{values[1]}\n{values[3]}"
            self.show(tooltip_text, event.x_root, event.y_root)

    def on_leave(self, event):
        self.hide()