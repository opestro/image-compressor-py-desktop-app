import tkinter as tk
from tkinter import ttk
import time
import webbrowser
from PIL import Image, ImageTk

class SplashScreen:
    def __init__(self, parent):
        self.root = parent
        self.splash = tk.Toplevel(parent)
        self.splash.overrideredirect(True)
        
        # Get screen dimensions
        screen_width = self.splash.winfo_screenwidth()
        screen_height = self.splash.winfo_screenheight()
        
        # Set splash window dimensions
        width = 400
        height = 400  # Increased height for better spacing
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.splash.geometry(f'{width}x{height}+{x}+{y}')
        
        # Configure modern style
        style = ttk.Style()
        bg_color = '#ffffff'
        accent_color = '#25D366'  # WhatsApp green
        
        # Main frame with white background and rounded corners
        main_frame = ttk.Frame(self.splash, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # App logo/icon (you can replace with your actual logo)
        try:
            logo = Image.open("assets/logo.png")
            logo = logo.resize((100, 100), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo)
            ttk.Label(main_frame, image=self.logo_photo).pack(pady=20)
        except:
            # Fallback if no logo found
            ttk.Label(
                main_frame, 
                text="IC", 
                font=("SF Pro Display", 40, "bold"),
                foreground=accent_color
            ).pack(pady=20)
        
        # App title with modern font
        ttk.Label(
            main_frame, 
            text="Image Compressor",
            font=("SF Pro Display", 24, "bold"),
            foreground="#2C2C2C"
        ).pack(pady=(0,10))
        
        # Version info
        ttk.Label(
            main_frame,
            text="Version 1.0.0",
            font=("SF Pro Display", 10),
            foreground="#666666"
        ).pack()
        
        # Modern progress bar
        self.progress = ttk.Progressbar(
            main_frame, 
            length=300, 
            mode='determinate',
            style='Accent.Horizontal.TProgressbar'
        )
        self.progress.pack(pady=30)
        
        style.configure(
            'Accent.Horizontal.TProgressbar',
            troughcolor='#E8E8E8',
            background=accent_color,
            thickness=6
        )
        
        # Developer info
        ttk.Label(
            main_frame,
            text="Developed by Mehdi Harzallah",
            font=("SF Pro Display", 12),
            foreground="#2C2C2C"
        ).pack(pady=(20,5))
        
        # Country info with flag
        ttk.Label(
            main_frame,
            text="Algeria 🇩🇿",
            font=("SF Pro Display", 11),
            foreground="#666666"
        ).pack()
        
        # WhatsApp button
        whatsapp_frame = ttk.Frame(main_frame)
        whatsapp_frame.pack(pady=20)
        
        def open_whatsapp():
            webbrowser.open('https://wa.me/213778191078')
        
        whatsapp_btn = ttk.Button(
            whatsapp_frame,
            text="Contact on WhatsApp",
            command=open_whatsapp,
            style='Accent.TButton'
        )
        whatsapp_btn.pack(side="left", padx=5)
        
        # Configure WhatsApp button style
        style.configure(
            'Accent.TButton',
            background=accent_color,
            foreground='white',
            padding=(20, 10),
            font=("SF Pro Display", 10, "bold")
        )
        
        # GitHub link
        github_label = ttk.Label(
            main_frame,
            text="github.com/opestro",
            font=("SF Pro Display", 10),
            foreground="#666666",
            cursor="hand2"
        )
        github_label.pack(side="bottom", pady=10)
        github_label.bind("<Button-1>", 
                         lambda e: webbrowser.open("https://github.com/opestro"))
        
        self.splash.update()
        self._photo_references = []
    
    def progress_bar(self):
        """Animate progress bar with smooth motion"""
        for i in range(101):
            self.progress['value'] = i
            self.splash.update()
            time.sleep(0.02)
    
    def destroy(self):
        """Clean up and destroy splash screen"""
        self._photo_references.clear()
        self.splash.destroy() 