import threading
import time
import ctypes
import math
import tkinter as tk
import customtkinter as ctk
from pynput import keyboard

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("mycompany.myproduct.subproduct.version")

# ---------------------------------------------------------------------------
# Core State Engine (unchanged logic)
# ---------------------------------------------------------------------------
clicking = False
target_cps = 100
click_location_mode = "current"
fixed_x = 0
fixed_y = 0
current_hotkey = keyboard.Key.f6
hotkey_string = "F6"
listening_for_hotkey = False
total_clicks = 0

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP   = 0x0004


def perform_click():
    global total_clicks
    if click_location_mode == "fixed":
        ctypes.windll.user32.SetCursorPos(int(fixed_x), int(fixed_y))
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP,   0, 0, 0, 0)
    total_clicks += 1


def clicker_loop():
    global clicking, target_cps
    while True:
        if clicking:
            delay = 1.0 / max(target_cps, 1)
            next_click = time.perf_counter()
            while clicking:
                now = time.perf_counter()
                if now >= next_click:
                    perform_click()
                    next_click = now + delay
                time_left = next_click - time.perf_counter()
                if time_left > 0.002:
                    time.sleep(0.001)
        else:
            time.sleep(0.05)


threading.Thread(target=clicker_loop, daemon=True).start()


# ---------------------------------------------------------------------------
# Astro Bot Colour Palette
# ---------------------------------------------------------------------------
AB = {
    "bg":           "#080E1C",   # deep space navy
    "surface":      "#101827",   # card surface
    "surface2":     "#182236",   # slightly lighter card
    "cyan":         "#00C8FF",   # main accent  – Astro Bot visor blue
    "cyan_dim":     "#0077AA",   # muted cyan for borders
    "orange":       "#FF6B2B",   # secondary accent
    "orange_dim":   "#99400E",   # muted orange
    "white":        "#E8F4FF",   # near-white text
    "muted":        "#5A7A99",   # muted text
    "active_green": "#00FF88",   # active/running state
    "inactive_red": "#FF3A3A",   # inactive state
    "slider_bg":    "#0D1A2B",
}


# ---------------------------------------------------------------------------
# Animated Robot Canvas Widget
# ---------------------------------------------------------------------------
class AstroBotHead(tk.Canvas):
    """A tiny animated robot head drawn entirely with tkinter Canvas primitives."""

    def __init__(self, parent, size=72, **kw):
        super().__init__(parent, width=size, height=size,
                         bg=AB["bg"], highlightthickness=0, **kw)
        self.size = size
        self._t = 0.0
        self._active = False
        self._draw()
        self._animate()

    def set_active(self, state: bool):
        self._active = state

    def _animate(self):
        self._t += 0.08
        self._draw()
        self.after(40, self._animate)   # ~25 fps – very lightweight

    def _draw(self):
        s = self.size
        self.delete("all")
        cx, cy = s // 2, s // 2

        # Hover bob
        bob = int(math.sin(self._t) * 2.5)
        cy += bob

        # Antenna
        ax = cx
        ay_base = cy - 22
        self.create_line(ax, ay_base, ax, ay_base - 8, fill=AB["muted"], width=2)
        r = 4 if not self._active else 5
        color = AB["active_green"] if self._active else AB["cyan"]
        self.create_oval(ax - r, ay_base - 8 - r, ax + r, ay_base - 8 + r,
                         fill=color, outline="")

        # Head body
        head_w, head_h = 36, 28
        hx = cx - head_w // 2
        hy = cy - head_h // 2
        self.create_rectangle(hx, hy, hx + head_w, hy + head_h,
                               fill=AB["surface2"], outline=AB["cyan_dim"], width=1)

        # Visor
        visor_col = AB["cyan"] if not self._active else AB["active_green"]
        visor_glow = AB["cyan_dim"] if not self._active else "#006644"
        self.create_rectangle(cx - 12, cy - 6, cx + 12, cy + 3,
                               fill=visor_glow, outline=visor_col, width=1)
        # Pupil scan line (moves when active)
        if self._active:
            px = int(cx - 10 + ((math.sin(self._t * 3) + 1) / 2) * 20)
            self.create_line(px, cy - 5, px, cy + 2, fill=AB["active_green"], width=2)

        # Ear nubs
        for ex in [hx - 3, hx + head_w]:
            self.create_rectangle(ex, cy - 4, ex + 3, cy + 4,
                                  fill=AB["surface"], outline=AB["muted"], width=1)

        # Chin vents
        for i in range(3):
            vx = cx - 8 + i * 8
            self.create_rectangle(vx, hy + head_h - 6, vx + 4, hy + head_h - 2,
                                  fill=AB["cyan_dim"], outline="")


# ---------------------------------------------------------------------------
# Pulsing status ring
# ---------------------------------------------------------------------------
class PulseRing(tk.Canvas):
    def __init__(self, parent, **kw):
        super().__init__(parent, width=14, height=14,
                         bg=AB["bg"], highlightthickness=0, **kw)
        self._active = False
        self._t = 0.0
        self._animate()

    def set_active(self, state: bool):
        self._active = state

    def _animate(self):
        self._t += 0.12
        self.delete("all")
        color = AB["active_green"] if self._active else AB["inactive_red"]
        if self._active:
            alpha_r = 7 - int(math.sin(self._t) * 3)
            self.create_oval(7 - alpha_r, 7 - alpha_r, 7 + alpha_r, 7 + alpha_r,
                             fill="", outline=color, width=1)
        self.create_oval(3, 3, 11, 11, fill=color, outline="")
        self.after(50, self._animate)


# ---------------------------------------------------------------------------
# Styled card frame helper
# ---------------------------------------------------------------------------
def make_card(parent, label: str = ""):
    outer = ctk.CTkFrame(parent, fg_color=AB["surface"],
                         corner_radius=10,
                         border_width=1, border_color=AB["cyan_dim"])
    outer.pack(fill="x", padx=24, pady=6)
    if label:
        ctk.CTkLabel(outer, text=label.upper(),
                     font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
                     text_color=AB["cyan_dim"]).pack(anchor="w", padx=14, pady=(10, 0))
    return outer


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------
class SwiftAutoClicker(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window setup
        self.title("SwiftAutoClicker")
        self.geometry("460x620")
        self.resizable(False, False)
        try:
            self.iconbitmap("SwiftAKlogo.ico")
        except Exception:
            pass
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=AB["bg"])

        self._build_header()
        self._build_cps_card()
        self._build_location_card()
        self._build_hotkey_card()
        self._build_status_bar()
        self._build_counter()

        # Start UI refresh loop (lightweight – only updates counter label)
        self._refresh()

    # ------------------------------------------------------------------ #
    # Layout builders
    # ------------------------------------------------------------------ #
    def _build_header(self):
        header = tk.Frame(self, bg=AB["bg"])
        header.pack(fill="x", padx=24, pady=(20, 4))

        self.robot_canvas = AstroBotHead(header, size=72)
        self.robot_canvas.pack(side="left", padx=(0, 16))

        title_block = tk.Frame(header, bg=AB["bg"])
        title_block.pack(side="left", fill="y")

        tk.Label(title_block, text="SWIFT AK", bg=AB["bg"],
                 fg=AB["cyan"], font=("Consolas", 22, "bold")).pack(anchor="w")
        tk.Label(title_block, text="ASTRO THEMED", bg=AB["bg"],
                 fg=AB["orange"], font=("Consolas", 11)).pack(anchor="w")
        tk.Label(title_block, text="Auto-Clicker · v1.0", bg=AB["bg"],
                 fg=AB["muted"], font=("Consolas", 9)).pack(anchor="w")

    def _build_cps_card(self):
        card = make_card(self, "click speed")
        row = tk.Frame(card, bg=AB["surface"])
        row.pack(fill="x", padx=14, pady=12)

        tk.Label(row, text="Clicks / second", bg=AB["surface"],
                 fg=AB["white"], font=("Consolas", 12)).pack(side="left")

        self.cps_entry = ctk.CTkEntry(row, width=80, justify="center",
                                      font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
                                      fg_color=AB["slider_bg"],
                                      border_color=AB["cyan_dim"],
                                      text_color=AB["cyan"])
        self.cps_entry.insert(0, "100")
        self.cps_entry.pack(side="right")
        self.cps_entry.bind("<KeyRelease>", self._update_cps)

        # Slider
        self.cps_slider = ctk.CTkSlider(card,
                                         from_=1, to=1000, number_of_steps=999,
                                         fg_color=AB["slider_bg"],
                                         progress_color=AB["cyan_dim"],
                                         button_color=AB["cyan"],
                                         button_hover_color=AB["orange"],
                                         command=self._slider_changed)
        self.cps_slider.set(100)
        self.cps_slider.pack(fill="x", padx=14, pady=(0, 12))

        # Speed presets
        preset_row = tk.Frame(card, bg=AB["surface"])
        preset_row.pack(fill="x", padx=14, pady=(0, 14))
        for label, val in [("Slow  10", 10), ("Med  100", 100), ("Fast  300", 300), ("MAX 1000", 1000)]:
            ctk.CTkButton(preset_row, text=label, width=80,
                          font=ctk.CTkFont(family="Consolas", size=10),
                          fg_color=AB["surface2"],
                          hover_color=AB["cyan_dim"],
                          border_color=AB["cyan_dim"], border_width=1,
                          text_color=AB["white"],
                          anchor="center",
                          command=lambda v=val: self._set_cps_preset(v)).pack(side="left", padx=3)

    def _build_location_card(self):
        card = make_card(self, "click target")
        self.loc_var = ctk.StringVar(value="current")

        self.radio_current = ctk.CTkRadioButton(card, text="Current cursor position",
                                                 variable=self.loc_var, value="current",
                                                 command=self._toggle_loc_mode,
                                                 font=ctk.CTkFont(family="Consolas", size=12),
                                                 fg_color=AB["cyan"],
                                                 hover_color=AB["cyan_dim"],
                                                 text_color=AB["white"])
        self.radio_current.pack(anchor="w", padx=14, pady=(12, 6))

        coord_row = tk.Frame(card, bg=AB["surface"])
        coord_row.pack(fill="x", padx=14, pady=(0, 14))

        self.radio_fixed = ctk.CTkRadioButton(coord_row, text="Fixed  X:",
                                               variable=self.loc_var, value="fixed",
                                               command=self._toggle_loc_mode,
                                               font=ctk.CTkFont(family="Consolas", size=12),
                                               fg_color=AB["orange"],
                                               hover_color=AB["orange_dim"],
                                               text_color=AB["white"])
        self.radio_fixed.pack(side="left")

        entry_kw = dict(width=58, justify="center",
                        font=ctk.CTkFont(family="Consolas", size=12),
                        fg_color=AB["slider_bg"],
                        border_color=AB["orange_dim"],
                        text_color=AB["orange"],
                        state="disabled")

        self.x_entry = ctk.CTkEntry(coord_row, **entry_kw)
        self.x_entry.insert(0, "1920")
        self.x_entry.pack(side="left", padx=6)

        tk.Label(coord_row, text="Y:", bg=AB["surface"],
                 fg=AB["muted"], font=("Consolas", 12)).pack(side="left")

        self.y_entry = ctk.CTkEntry(coord_row, **entry_kw)
        self.y_entry.insert(0, "1080")
        self.y_entry.pack(side="left", padx=6)

        self.x_entry.bind("<KeyRelease>", self._update_coordinates)
        self.y_entry.bind("<KeyRelease>", self._update_coordinates)

    def _build_hotkey_card(self):
        card = make_card(self, "activation key")
        row = tk.Frame(card, bg=AB["surface"])
        row.pack(fill="x", padx=14, pady=14)

        tk.Label(row, text="Toggle clicker with:", bg=AB["surface"],
                 fg=AB["white"], font=("Consolas", 12)).pack(side="left")

        self.hotkey_btn = ctk.CTkButton(row, text="F6", width=100,
                                         font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
                                         fg_color=AB["surface2"],
                                         hover_color=AB["cyan_dim"],
                                         border_color=AB["cyan"],
                                         border_width=1,
                                         text_color=AB["cyan"],
                                         anchor="center",
                                         command=self._start_listening_for_hotkey)
        self.hotkey_btn.pack(side="right")

    def _build_status_bar(self):
        bar = tk.Frame(self, bg=AB["surface2"], height=46)
        bar.pack(fill="x", padx=24, pady=(12, 0))
        bar.pack_propagate(False)

        self.pulse = PulseRing(bar)
        self.pulse.pack(side="left", padx=(14, 8), pady=0)

        self.status_label = tk.Label(bar, text="INACTIVE", bg=AB["surface2"],
                                     fg=AB["inactive_red"],
                                     font=("Consolas", 14, "bold"))
        self.status_label.pack(side="left", pady=0)

        self.cps_live = tk.Label(bar, text="", bg=AB["surface2"],
                                 fg=AB["muted"], font=("Consolas", 10))
        self.cps_live.pack(side="right", padx=14)

    def _build_counter(self):
        ctr = tk.Frame(self, bg=AB["bg"])
        ctr.pack(fill="x", padx=24, pady=(8, 20))

        tk.Label(ctr, text="SESSION CLICKS", bg=AB["bg"],
                 fg=AB["muted"], font=("Consolas", 9)).pack(side="left")

        self.counter_label = tk.Label(ctr, text="0", bg=AB["bg"],
                                      fg=AB["orange"], font=("Consolas", 13, "bold"))
        self.counter_label.pack(side="left", padx=8)

        ctk.CTkButton(ctr, text="Reset", width=60, height=24,
                      font=ctk.CTkFont(family="Consolas", size=10),
                      fg_color=AB["surface"],
                      hover_color=AB["orange_dim"],
                      border_color=AB["orange_dim"],
                      border_width=1,
                      text_color=AB["muted"],
                      anchor="center",
                      command=self._reset_counter).pack(side="right")

    # ------------------------------------------------------------------ #
    # UI logic helpers
    # ------------------------------------------------------------------ #
    def _update_cps(self, event=None):
        global target_cps
        try:
            val = int(self.cps_entry.get())
            if 1 <= val <= 1000:
                target_cps = val
                self.cps_slider.set(val)
        except ValueError:
            pass

    def _slider_changed(self, val):
        global target_cps
        target_cps = int(val)
        self.cps_entry.delete(0, "end")
        self.cps_entry.insert(0, str(target_cps))

    def _set_cps_preset(self, val):
        global target_cps
        target_cps = val
        self.cps_entry.delete(0, "end")
        self.cps_entry.insert(0, str(val))
        self.cps_slider.set(val)

    def _toggle_loc_mode(self):
        global click_location_mode
        mode = self.loc_var.get()
        click_location_mode = mode
        state = "normal" if mode == "fixed" else "disabled"
        self.x_entry.configure(state=state)
        self.y_entry.configure(state=state)
        if mode == "fixed":
            self._update_coordinates()

    def _update_coordinates(self, event=None):
        global fixed_x, fixed_y
        try:
            fixed_x = int(self.x_entry.get())
            fixed_y = int(self.y_entry.get())
        except ValueError:
            pass

    def _start_listening_for_hotkey(self):
        global listening_for_hotkey
        listening_for_hotkey = True
        self.hotkey_btn.configure(text="[ Press Key ]",
                                  fg_color=AB["orange_dim"],
                                  border_color=AB["orange"],
                                  text_color=AB["orange"])

    def update_hotkey_ui(self, key_str):
        self.hotkey_btn.configure(text=key_str,
                                  fg_color=AB["surface2"],
                                  border_color=AB["cyan"],
                                  text_color=AB["cyan"],
                                  anchor="center")

    def refresh_status(self):
        if clicking:
            self.status_label.configure(text="CLICKING  ▶", fg=AB["active_green"])
            self.cps_live.configure(text=f"@ {target_cps} CPS")
        else:
            self.status_label.configure(text="INACTIVE", fg=AB["inactive_red"])
            self.cps_live.configure(text="")
        self.pulse.set_active(clicking)
        self.robot_canvas.set_active(clicking)

    def _reset_counter(self):
        global total_clicks
        total_clicks = 0

    def _refresh(self):
        """Lightweight polling loop – updates counter and live CPS badge."""
        self.counter_label.configure(text=f"{total_clicks:,}")
        if clicking:
            self.cps_live.configure(text=f"@ {target_cps} CPS")
        self.after(200, self._refresh)


# ---------------------------------------------------------------------------
# Global keyboard hook
# ---------------------------------------------------------------------------
def on_press(key):
    global clicking, current_hotkey, listening_for_hotkey, hotkey_string

    if listening_for_hotkey:
        current_hotkey = key
        if hasattr(key, 'name') and key.name:
            hotkey_string = key.name.upper()
        elif hasattr(key, 'char') and key.char:
            hotkey_string = key.char.upper()
        else:
            hotkey_string = str(key).replace("'", "").upper().replace("KEY.", "")
        listening_for_hotkey = False
        app.after(0, lambda: app.update_hotkey_ui(hotkey_string))
        return

    is_match = (current_hotkey == key) or (
        hasattr(current_hotkey, 'char') and hasattr(key, 'char')
        and current_hotkey.char == key.char
    )
    if is_match:
        clicking = not clicking
        app.after(0, app.refresh_status)


listener = keyboard.Listener(on_press=on_press)
listener.start()

if __name__ == "__main__":
    app = SwiftAutoClicker()
    app.mainloop()