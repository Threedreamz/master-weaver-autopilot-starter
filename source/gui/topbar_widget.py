import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import time
import threading
from PIL import Image, ImageTk
import os

# CustomTkinter Konfiguration
ctk.set_appearance_mode("dark")  # "light" oder "dark"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

CHECK_INTERVAL_MS = 50
TOP_TRIGGER_PX = 3
HIDE_DELAY_MS = 300

class TopAutoBar:
    def __init__(self, master, width=800, height=65):
        self.master = master
        self.width = width
        self.height = height
        self.visible = False
        self.hide_after_id = None
        self.animation_running = False
        
        # Hauptfenster Setup
        master.overrideredirect(True)
        master.attributes("-topmost", True)
        master.withdraw()
        
        # Transparenz und moderne Effekte
        try:
            master.attributes('-alpha', 0.0)  # Start unsichtbar für Animation
            master.attributes('-transparentcolor', '')
        except:
            pass
        
        # Hauptcontainer mit Glasmorphism-Effekt
        self.main_frame = ctk.CTkFrame(
            master,
            corner_radius=12,
            bg_color="transparent",
            fg_color=("#f0f0f0", "#1a1a1a"),
            border_width=1,
            border_color=("#d0d0d0", "#404040")
        )
        self.main_frame.pack(fill="both", expand=True, padx=8, pady=4)
        
        # Header mit App-Branding
        self.header_frame = ctk.CTkFrame(
            self.main_frame,
            height=65,
            corner_radius=0,
            fg_color="transparent"
        )
        self.header_frame.pack(fill="x", padx=12, pady=8)
        self.header_frame.pack_propagate(False)
        
        # Logo/Brand Bereich
        self.brand_frame = ctk.CTkFrame(
            self.header_frame,
            fg_color="transparent",
            width=120
        )
        self.brand_frame.pack(side="left", fill="y")
        self.brand_frame.pack_propagate(False)
        
        # Logo Icon (Sie können hier Ihr Logo einsetzen)
        self.logo_label = ctk.CTkLabel(
            self.brand_frame,
            text="⚡",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=("#2563eb", "#3b82f6")
        )
        self.logo_label.pack(side="left", padx=(8, 4))
        
        # App Name
        self.brand_label = ctk.CTkLabel(
            self.brand_frame,
            text="3Dreamz AutoPilot",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("#1f2937", "#e5e7eb")
        )
        self.brand_label.pack(side="left", padx=4)
        
        # Hauptbuttons Container
        self.buttons_frame = ctk.CTkFrame(
            self.header_frame,
            fg_color="transparent"
        )
        self.buttons_frame.pack(side="left", expand=True, fill="both", padx=20)
        
        # Navigation Buttons mit Icons und modernem Design
        button_config = {
            "corner_radius": 8,
            "height": 40,
            "font": ctk.CTkFont(size=12, weight="bold"),
            "hover_color": ("#e2e8f0", "#374151"),
            "border_width": 0
        }
        
        self.home_btn = ctk.CTkButton(
            self.buttons_frame,
            text="🏠 Dashboard",
            fg_color=("#3b82f6", "#2563eb"),
            **button_config,
            command=lambda: self.handle_button_click("Dashboard")
        )
        
        self.files_btn = ctk.CTkButton(
            self.buttons_frame,
            text="📁 Projekte",
            fg_color=("#10b981", "#059669"),
            **button_config,
            command=lambda: self.handle_button_click("Projekte")
        )
        
        self.settings_btn = ctk.CTkButton(
            self.buttons_frame,
            text="⚙️ Einstellungen",
            fg_color=("#6366f1", "#4f46e5"),
            **button_config,
            command=lambda: self.handle_button_click("Einstellungen")
        )
        
        self.tools_btn = ctk.CTkButton(
            self.buttons_frame,
            text="🔧 Tools",
            fg_color=("#f59e0b", "#d97706"),
            **button_config,
            command=lambda: self.handle_button_click("Tools")
        )
        
        # Button Layout
        for i, btn in enumerate([self.home_btn, self.files_btn, self.settings_btn, self.tools_btn]):
            btn.pack(side="left", padx=(0, 8), pady=4)
        
        # Rechte Seite - Status und Controls
        self.right_frame = ctk.CTkFrame(
            self.header_frame,
            fg_color="transparent",
            width=160
        )
        self.right_frame.pack(side="right", fill="y", padx=(20, 0))
        self.right_frame.pack_propagate(False)
        
        # Status Indicator
        self.status_frame = ctk.CTkFrame(
            self.right_frame,
            fg_color=("transparent"),
            height=25
        )
        self.status_frame.pack(side="left", fill="y", padx=(0, 12))
        
        self.status_dot = ctk.CTkLabel(
            self.status_frame,
            text="●",
            font=ctk.CTkFont(size=12),
            text_color=("#22c55e", "#16a34a")  # Grün für "Online"
        )
        self.status_dot.pack(side="left", pady=8)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Online",
            font=ctk.CTkFont(size=10),
            text_color=("#6b7280", "#9ca3af")
        )
        self.status_label.pack(side="left", padx=(2, 0), pady=8)
        
        # Window Controls
        self.controls_frame = ctk.CTkFrame(
            self.right_frame,
            fg_color="transparent"
        )
        self.controls_frame.pack(side="right", fill="y")
        
        # Minimize Button
        self.min_btn = ctk.CTkButton(
            self.controls_frame,
            text="─",
            width=32,
            height=32,
            corner_radius=6,
            fg_color=("#f3f4f6", "#2d3748"),
            text_color=("#6b7280", "#9ca3af"),
            hover_color=("#e5e7eb", "#374151"),
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.do_minimize
        )
        self.min_btn.pack(side="left", padx=(0, 4), pady=8)
        
        # Close Button
        self.close_btn = ctk.CTkButton(
            self.controls_frame,
            text="✕",
            width=32,
            height=32,
            corner_radius=6,
            fg_color=("#f3f4f6", "#2d3748"),
            text_color=("#6b7280", "#9ca3af"),
            hover_color=("#ef4444", "#dc2626"),
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.do_close
        )
        self.close_btn.pack(side="right", padx=4, pady=8)
        
        # Hover Events für alle Widgets
        self._bind_hover_events()
        
        # Position setzen
        self.update_geometry()
        
        # Mouse Polling starten
        self.start_mouse_polling()
        
    def handle_button_click(self, action):
        """Handle button clicks with visual feedback"""
        print(f"{action} wurde geklickt")
        # Hier können Sie Ihre eigene Logik einfügen
        
    def _bind_hover_events(self):
        """Bind hover events to prevent auto-hide"""
        def bind_recursive(widget):
            widget.bind("<Enter>", self.on_enter)
            widget.bind("<Leave>", self.on_leave)
            for child in widget.winfo_children():
                try:
                    bind_recursive(child)
                except:
                    pass
        
        bind_recursive(self.main_frame)
        
    def update_geometry(self):
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        
        actual_width = min(self.width, screen_width - 40)
        x_pos = (screen_width - actual_width) // 2
        y_pos = 8  # Kleiner Abstand von oben
        
        geometry = f"{actual_width}x{self.height}+{x_pos}+{y_pos}"
        self.master.geometry(geometry)
        
    def show(self):
        if not self.visible and not self.animation_running:
            self.visible = True
            self.update_geometry()
            self.master.deiconify()
            self.fade_in()
            
    def hide(self):
        if self.visible and not self.animation_running:
            self.fade_out()
            
    def fade_in(self):
        """Smooth fade-in animation"""
        if self.animation_running:
            return
            
        self.animation_running = True
        target_alpha = 0.95
        current_alpha = 0.0
        step = 0.05
        
        def animate():
            nonlocal current_alpha
            try:
                if current_alpha < target_alpha:
                    current_alpha = min(target_alpha, current_alpha + step)
                    self.master.attributes('-alpha', current_alpha)
                    self.master.after(16, animate)  # ~60 FPS
                else:
                    self.animation_running = False
            except:
                self.animation_running = False
                
        animate()
        
    def fade_out(self):
        """Smooth fade-out animation"""
        if self.animation_running:
            return
            
        self.animation_running = True
        current_alpha = 0.95
        step = 0.08
        
        def animate():
            nonlocal current_alpha
            try:
                if current_alpha > 0:
                    current_alpha = max(0, current_alpha - step)
                    self.master.attributes('-alpha', current_alpha)
                    self.master.after(16, animate)
                else:
                    self.master.withdraw()
                    self.visible = False
                    self.animation_running = False
            except:
                self.visible = False
                self.animation_running = False
                
        animate()
        
    def schedule_hide(self):
        if self.hide_after_id is not None:
            self.master.after_cancel(self.hide_after_id)
            self.hide_after_id = None
        self.hide_after_id = self.master.after(HIDE_DELAY_MS, self.hide)
        
    def cancel_scheduled_hide(self):
        if self.hide_after_id is not None:
            self.master.after_cancel(self.hide_after_id)
            self.hide_after_id = None
            
    def on_enter(self, event=None):
        self.cancel_scheduled_hide()
        
    def on_leave(self, event=None):
        self.schedule_hide()
        
    def do_minimize(self):
        try:
            self.master.iconify()
            self.visible = False
        except:
            self.hide()
            
    def do_close(self):
        self.fade_out()
        self.master.after(500, self.master.destroy)  # Delay to complete animation
        
    def start_mouse_polling(self):
        """Start mouse position polling"""
        def poll_mouse():
            if not hasattr(self, 'master') or not self.master.winfo_exists():
                return
                
            try:
                x = self.master.winfo_pointerx()
                y = self.master.winfo_pointery()
            except:
                x, y = -1, -1
                
            # Show when mouse at top
            if 0 <= y <= TOP_TRIGGER_PX and not self.visible:
                self.cancel_scheduled_hide()
                self.show()
            elif self.visible and not self.animation_running:
                # Check if mouse is over window
                try:
                    win_x = self.master.winfo_x()
                    win_y = self.master.winfo_y()
                    win_w = self.master.winfo_width()
                    win_h = self.master.winfo_height()
                    
                    if not (win_x <= x <= win_x + win_w and win_y <= y <= win_y + win_h):
                        self.schedule_hide()
                    else:
                        self.cancel_scheduled_hide()
                except:
                    pass
                    
            # Continue polling
            self.master.after(CHECK_INTERVAL_MS, poll_mouse)
            
        poll_mouse()

def main():
    # Hauptfenster erstellen
    root = ctk.CTk()
    root.title("3Dreamz AutoPilot - Modern TopBar")
    
    # App Icon setzen (falls vorhanden)
    try:
        root.iconbitmap("icon.ico")
    except:
        pass
    
    # TopBar erstellen
    app = TopAutoBar(root, width=900, height=70)
    
    # Keyboard shortcuts
    root.bind("<Escape>", lambda e: root.destroy())
    root.bind("<Control-q>", lambda e: root.destroy())
    root.bind("<F11>", lambda e: print("Fullscreen toggle"))
    
    print("🚀 3Dreamz AutoPilot TopBar gestartet!")
    print("💡 Bewegen Sie die Maus an den oberen Bildschirmrand um die Bar anzuzeigen")
    print("⌨️  Tastenkürzel: ESC oder Ctrl+Q zum Beenden")
    
    root.mainloop()

if __name__ == "__main__":
    main()