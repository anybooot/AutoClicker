import customtkinter as ctk
import threading
import time
import random
import sys
import os
from pynput.mouse import Button, Controller
from pynput.keyboard import Listener, KeyCode
from PIL import Image

# --- FUNCȚIE PENTRU COMPILARE (RESURSE INTERNE) ---
def resource_path(relative_path):
    """ Obține calea către resurse, necesară pentru PyInstaller --onefile """
    try:
        # PyInstaller creează un folder temporar în _MEIPASS la rulare
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

mouse = Controller()

class NovaHUD(ctk.CTk):
    def __init__(self):
        super().__init__()

        # CONFIGURAȚIE FEREASTRĂ
        self.title("NOVA HUD")
        self.geometry("320x550")
        self.resizable(False, False)
        self.attributes("-topmost", True)  # Mereu deasupra
        self.attributes("-alpha", 0.95)

        # Variabile logice
        self.running = False
        self.start_key = KeyCode.from_char('r')
        self.click_button = Button.left
        self.mode = "TOGGLE"

        # --- BACKGROUND ENGINE ---
        try:
            # Folosim resource_path pentru a găsi imaginea în interiorul EXE
            img_path = resource_path("background.png")
            bg_img = Image.open(img_path)
            self.bg_ctk = ctk.CTkImage(bg_img, size=(320, 550))
            self.bg_label = ctk.CTkLabel(self, image=self.bg_ctk, text="")
            self.bg_label.place(x=0, y=0)
        except Exception as e:
            print(f"Imaginea de fundal nu a fost găsită: {e}")

        # --- DESIGN ELEMENTS ---
        # Sidebar/Overlay pentru lizibilitate
        self.sidebar = ctk.CTkFrame(self, fg_color="#0a0a0a", width=280, corner_radius=20)
        self.sidebar.place(relx=0.5, rely=0.5, anchor="center", relheight=0.9, relwidth=0.85)

        # Titlu
        self.title_lbl = ctk.CTkLabel(self.sidebar, text="NOVA.IO", font=("Inter", 26, "bold"), text_color="#ff0055")
        self.title_lbl.pack(pady=20)

        # Selecție Buton Mouse
        self.tab_btns = ctk.CTkSegmentedButton(self.sidebar, values=["LEFT", "RIGHT"], 
                                               command=self.change_mouse_btn,
                                               selected_color="#ff0055", unselected_color="#1a1a1a")
        self.tab_btns.set("LEFT")
        self.tab_btns.pack(pady=10, padx=20, fill="x")

        # CPS Slider
        self.cps_lbl = ctk.CTkLabel(self.sidebar, text="SPEED: 12 CPS", font=("Inter", 12, "bold"))
        self.cps_lbl.pack(pady=(20, 0))
        self.slider = ctk.CTkSlider(self.sidebar, from_=1, to=22, number_of_steps=21, 
                                    button_color="#ff0055", progress_color="#ff0055", command=self.update_cps)
        self.slider.set(12)
        self.slider.pack(pady=10, padx=20, fill="x")

        # Mod Activare (Toggle/Hold)
        self.mode_btns = ctk.CTkSegmentedButton(self.sidebar, values=["TOGGLE", "HOLD"], 
                                                command=self.set_mode,
                                                selected_color="#ff0055", unselected_color="#1a1a1a")
        self.mode_btns.set("TOGGLE")
        self.mode_btns.pack(pady=20, padx=20, fill="x")

        # Hotkey Info
        self.key_frame = ctk.CTkFrame(self.sidebar, fg_color="#151515", corner_radius=10)
        self.key_frame.pack(pady=10, padx=20, fill="x")
        self.key_btn = ctk.CTkButton(self.key_frame, text="BIND: R", fg_color="transparent", 
                                     hover_color="#222", command=self.change_key)
        self.key_btn.pack(fill="x")

        # Stealth Switch
        self.stealth_sw = ctk.CTkSwitch(self.sidebar, text="STEALTH MODE", progress_color="#ff0055")
        self.stealth_sw.select()
        self.stealth_sw.pack(pady=20)

        # Status Indicator
        self.status_indicator = ctk.CTkLabel(self.sidebar, text="● DISCONNECTED", text_color="#444", font=("Inter", 11, "bold"))
        self.status_indicator.pack(side="bottom", pady=20)

        # Start Logica Clicker în fundal
        threading.Thread(target=self.clicker_loop, daemon=True).start()
        self.setup_listener()

    # --- FUNCȚII LOGICE ---
    def update_cps(self, val):
        self.cps_lbl.configure(text=f"SPEED: {int(val)} CPS")

    def change_mouse_btn(self, val):
        self.click_button = Button.left if val == "LEFT" else Button.right

    def set_mode(self, val):
        self.mode = val
        self.running = False
        self.update_ui()

    def update_ui(self):
        if self.running:
            self.status_indicator.configure(text="● ACTIVE", text_color="#ff0055")
            self.title_lbl.configure(text_color="#ff0055")
        else:
            self.status_indicator.configure(text="● STANDBY", text_color="#444")
            self.title_lbl.configure(text_color="#ffffff")

    def change_key(self):
        threading.Thread(target=self._listen, daemon=True).start()

    def _listen(self):
        self.key_btn.configure(text="LISTENING...", text_color="#ff0055")
        def on_p(key):
            self.start_key = key
            name = str(key).replace("'", "").replace("Key.", "").upper()
            self.after(0, lambda: self.key_btn.configure(text=f"BIND: {name}", text_color="white"))
            return False
        with Listener(on_press=on_p) as l:
            l.join()

    def clicker_loop(self):
        while True:
            if self.running:
                cps = self.slider.get()
                delay = 1.0 / cps
                
                # Jitter pentru a evita detectarea (Stealth)
                if self.stealth_sw.get():
                    delay += random.uniform(-0.15, 0.15) * delay
                
                mouse.press(self.click_button)
                # Simulează timpul de apăsare fizică a butonului
                time.sleep(random.uniform(0.01, 0.03)) 
                mouse.release(self.click_button)
                time.sleep(max(0.001, delay))
            else:
                time.sleep(0.1)

    def setup_listener(self):
        def on_press(key):
            if key == self.start_key:
                if self.mode == "TOGGLE":
                    self.running = not self.running
                else:
                    self.running = True
                self.after(0, self.update_ui)

        def on_release(key):
            if key == self.start_key and self.mode == "HOLD":
                self.running = False
                self.after(0, self.update_ui)

        Listener(on_press=on_press, on_release=on_release).start()

if __name__ == "__main__":
    app = NovaHUD()
    app.mainloop()