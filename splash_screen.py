import tkinter as tk
from tkinter import ttk
import time

class SplashScreen:
    def __init__(self):
        self.splash = tk.Tk()
        self.splash.overrideredirect(True)  # Remove window decorations
        
        # Get screen dimensions
        screen_width = self.splash.winfo_screenwidth()
        screen_height = self.splash.winfo_screenheight()
        
        # Set splash window dimensions
        width = 400
        height = 300
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.splash.geometry(f'{width}x{height}+{x}+{y}')
        
        # Create main frame
        main_frame = ttk.Frame(self.splash)
        main_frame.pack(fill="both", expand=True)
        
        # Configure style
        style = ttk.Style()
        style.configure("Splash.TLabel", font=("Helvetica", 12))
        style.configure("Title.TLabel", font=("Helvetica", 20, "bold"))
        style.configure("Contact.TLabel", font=("Helvetica", 10))
        
        # Add app title
        ttk.Label(main_frame, text="Image Compressor", 
                 style="Title.TLabel").pack(pady=20)
        
        # Add loading bar
        self.progress = ttk.Progressbar(main_frame, length=300, mode='determinate')
        self.progress.pack(pady=20)
        
        # Add developer info
        ttk.Label(main_frame, text="Developed by:", 
                 style="Splash.TLabel").pack(pady=(20,5))
        ttk.Label(main_frame, text="MEHDI HARZALLAH", 
                 style="Title.TLabel").pack()
        
        # Add contact info
        contact_frame = ttk.Frame(main_frame)
        contact_frame.pack(pady=20)
        
        ttk.Label(contact_frame, text="WhatsApp: +213 778191078", 
                 style="Contact.TLabel").pack()
        ttk.Label(contact_frame, text="GitHub: github.com/opestro", 
                 style="Contact.TLabel").pack()
        
        # Add version info
        ttk.Label(main_frame, text="Version 1.0.0", 
                 style="Contact.TLabel").pack(side="bottom", pady=10)
        
        self.splash.update()
        
        # Keep reference to prevent garbage collection
        self._photo_references = []
    
    def progress_bar(self):
        for i in range(101):
            self.progress['value'] = i
            self.splash.update()
            time.sleep(0.02)
    
    def destroy(self):
        # Clean up references before destroying
        self._photo_references.clear()
        self.splash.destroy() 