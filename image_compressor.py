import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk
import os
from pathlib import Path
import humanize
import json
from PIL.ExifTags import TAGS
import piexif
import re
from splash_screen import SplashScreen
from datetime import datetime
import logging
import traceback
import sys
import time

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class ImageCompressorApp:
    def __init__(self, root):
        logging.info("Initializing ImageCompressorApp")
        self.root = root
        self.root.title("Image Compressor")
        self.root.geometry("1200x800")
        
        # Initialize variables
        self.output_format = tk.StringVar(value="webp")
        self.quality = tk.IntVar(value=85)
        self.resize_enabled = tk.BooleanVar(value=False)
        self.maintain_aspect = tk.BooleanVar(value=True)
        self.width = tk.StringVar(value="")
        self.height = tk.StringVar(value="")
        self.selected_preset = tk.StringVar(value="custom")
        self.selected_profile = tk.StringVar(value="Custom")
        self.preserve_metadata = tk.BooleanVar(value=True)
        self.rename_enabled = tk.BooleanVar(value=False)
        self.rename_pattern = tk.StringVar(value="{original_name}")
        self.start_number = tk.IntVar(value=1)
        
        # Initialize compression profiles
        self.profiles = {
            "Web Optimized": {
                "format": "webp",
                "quality": 75,
                "resize": True,
                "width": 1920,
                "height": 1080
            },
            "Social Media": {
                "format": "jpeg",
                "quality": 85,
                "resize": True,
                "width": 1200,
                "height": 1200
            },
            "High Quality": {
                "format": "png",
                "quality": 95,
                "resize": False,
                "width": 0,
                "height": 0
            }
        }
        
        # Initialize image references
        self.preview_photo = None
        self._photo_references = set()
        self._is_closing = False
        self.files_to_compress = []
        
        # Try to load saved profiles
        try:
            if os.path.exists("compression_profiles.json"):
                with open("compression_profiles.json", "r") as f:
                    saved_profiles = json.load(f)
                    self.profiles.update(saved_profiles)
                logging.debug("Loaded saved compression profiles")
        except Exception as e:
            logging.error(f"Error loading saved profiles: {str(e)}")
        
        # Ensure root is ready
        self.root.update_idletasks()
        
        logging.debug("Setting up window close protocol")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        try:
            self.setup_ui()
            self.setup_drag_drop()
            logging.info("Application initialized successfully")
        except Exception as e:
            logging.error(f"Error during initialization: {str(e)}")
            logging.error(traceback.format_exc())
            raise
    
    def setup_ui(self):
        # Add menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Images", command=self.browse_files)
        file_menu.add_command(label="Clear All", command=self.clear_files)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left panel for drop zone and file list
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side="left", fill="both", expand=True)
        
        # Drop zone
        self.drop_frame = ttk.LabelFrame(left_panel, text="Drag & Drop Images Here")
        self.drop_frame.pack(padx=5, pady=5, fill="both", expand=True)
        
        self.drop_label = ttk.Label(self.drop_frame, text="Drop images here or click to browse")
        self.drop_label.pack(pady=20)
        
        # File list
        list_frame = ttk.LabelFrame(left_panel, text="Selected Files")
        list_frame.pack(padx=5, pady=5, fill="both", expand=True)
        
        # Scrollbar for file list
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.file_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.file_listbox.pack(fill="both", expand=True)
        scrollbar.config(command=self.file_listbox.yview)
        
        # Bind listbox selection
        self.file_listbox.bind('<<ListboxSelect>>', self.on_select_file)
        
        # Clear files button
        self.clear_btn = ttk.Button(left_panel, text="Clear All Files", command=self.clear_files)
        self.clear_btn.pack(pady=5)
        
        # Center panel for preview
        center_panel = ttk.Frame(main_frame)
        center_panel.pack(side="left", fill="both", expand=True, padx=10)
        
        # Preview frame
        preview_frame = ttk.LabelFrame(center_panel, text="Preview")
        preview_frame.pack(fill="both", expand=True)
        
        self.preview_label = ttk.Label(preview_frame)
        self.preview_label.pack(pady=10)
        
        # File info frame
        self.info_frame = ttk.LabelFrame(center_panel, text="File Information")
        self.info_frame.pack(fill="x", pady=5)
        
        self.file_info_label = ttk.Label(self.info_frame, text="No file selected")
        self.file_info_label.pack(pady=5)
        
        # Right panel for controls
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side="right", fill="y")
        
        # Format selection
        format_frame = ttk.LabelFrame(right_panel, text="Output Format")
        format_frame.pack(pady=5, fill="x")
        
        formats = [("WebP", "webp"), ("JPEG", "jpeg"), ("PNG", "png")]
        for text, value in formats:
            ttk.Radiobutton(format_frame, text=text, value=value, 
                           variable=self.output_format).pack(padx=10, pady=2)
        
        # Quality slider
        quality_frame = ttk.LabelFrame(right_panel, text="Quality")
        quality_frame.pack(pady=5, fill="x")
        
        self.quality_slider = ttk.Scale(quality_frame, from_=1, to=100, 
                                      variable=self.quality, orient="horizontal")
        self.quality_slider.pack(padx=10, pady=5, fill="x")
        
        # Progress bar
        self.progress_frame = ttk.LabelFrame(right_panel, text="Progress")
        self.progress_frame.pack(pady=5, fill="x")
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate')
        self.progress_bar.pack(padx=10, pady=5, fill="x")
        
        # Add resize options to right panel
        resize_frame = ttk.LabelFrame(right_panel, text="Resize Options")
        resize_frame.pack(pady=5, fill="x")
        
        ttk.Checkbutton(resize_frame, text="Enable Resize", 
                       variable=self.resize_enabled).pack(padx=10, pady=2)
        
        # Dimensions frame
        dim_frame = ttk.Frame(resize_frame)
        dim_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(dim_frame, text="Width:").pack(side="left")
        ttk.Entry(dim_frame, textvariable=self.width, width=8).pack(side="left", padx=5)
        
        ttk.Label(dim_frame, text="Height:").pack(side="left")
        ttk.Entry(dim_frame, textvariable=self.height, width=8).pack(side="left", padx=5)
        
        ttk.Checkbutton(resize_frame, text="Maintain Aspect Ratio", 
                       variable=self.maintain_aspect).pack(padx=10, pady=2)
        
        # Preset sizes
        preset_frame = ttk.Frame(resize_frame)
        preset_frame.pack(fill="x", padx=10, pady=5)
        
        presets = [
            ("Custom", "custom"),
            ("HD (1920x1080)", "hd"),
            ("4K (3840x2160)", "4k"),
            ("Thumbnail (300x300)", "thumbnail"),
            ("Social (1200x1200)", "social")
        ]
        
        ttk.Label(preset_frame, text="Presets:").pack(anchor="w")
        for text, value in presets:
            ttk.Radiobutton(preset_frame, text=text, value=value,
                          variable=self.selected_preset,
                          command=self.apply_preset).pack(anchor="w")
        
        # Compression profiles
        profile_frame = ttk.LabelFrame(right_panel, text="Compression Profiles")
        profile_frame.pack(pady=5, fill="x")
        
        profiles = ["Custom"] + list(self.profiles.keys())
        ttk.Label(profile_frame, text="Select Profile:").pack(padx=10, pady=2)
        profile_menu = ttk.OptionMenu(profile_frame, self.selected_profile, 
                                    "Custom", *profiles, 
                                    command=self.apply_profile)
        profile_menu.pack(padx=10, pady=2, fill="x")
        
        # Save profile button
        ttk.Button(profile_frame, text="Save Current as Profile",
                  command=self.save_profile).pack(padx=10, pady=2, fill="x")
        
        # Metadata options
        metadata_frame = ttk.LabelFrame(right_panel, text="Metadata Options")
        metadata_frame.pack(pady=5, fill="x")
        
        ttk.Checkbutton(metadata_frame, text="Preserve Metadata",
                       variable=self.preserve_metadata).pack(padx=10, pady=2)
        
        ttk.Button(metadata_frame, text="View Metadata",
                  command=self.view_metadata).pack(padx=10, pady=2)
        
        # Batch rename options
        rename_frame = ttk.LabelFrame(right_panel, text="Batch Rename")
        rename_frame.pack(pady=5, fill="x")
        
        ttk.Checkbutton(rename_frame, text="Enable Batch Rename",
                       variable=self.rename_enabled).pack(padx=10, pady=2)
        
        ttk.Label(rename_frame, text="Pattern:").pack(padx=10, pady=(5,0))
        pattern_entry = ttk.Entry(rename_frame, textvariable=self.rename_pattern)
        pattern_entry.pack(padx=10, pady=(0,5), fill="x")
        
        ttk.Label(rename_frame, text="Available variables:\n{original_name}, {number},\n{date}, {width}, {height}").pack(padx=10)
        
        number_frame = ttk.Frame(rename_frame)
        number_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(number_frame, text="Start Number:").pack(side="left")
        ttk.Entry(number_frame, textvariable=self.start_number, width=8).pack(side="left", padx=5)
        
        # Compress button
        self.compress_btn = ttk.Button(right_panel, text="Compress Images", 
                                     command=self.compress_images)
        self.compress_btn.pack(pady=10)

    def on_select_file(self, event):
        selection = self.file_listbox.curselection()
        if selection:
            index = selection[0]
            file_path = self.files_to_compress[index]
            self.show_preview(file_path)
            self.update_file_info(file_path)
    
    def show_preview(self, file_path):
        logging.debug(f"Attempting to show preview for: {file_path}")
        try:
            self.clear_preview()
            
            if not self._is_closing:
                with Image.open(file_path) as img:
                    logging.debug(f"Image opened: {img.size}, {img.mode}")
                    aspect_ratio = img.width / img.height
                    preview_height = 300
                    preview_width = int(preview_height * aspect_ratio)
                    
                    img_resized = img.resize((preview_width, preview_height), Image.Resampling.LANCZOS)
                    logging.debug("Image resized successfully")
                    
                    # Create new PhotoImage and add to references
                    self.preview_photo = ImageTk.PhotoImage(img_resized)
                    self._photo_references.add(self.preview_photo)
                    logging.debug("PhotoImage created and added to references")
                    
                    # Update label
                    self.preview_label.config(image=self.preview_photo)
                    logging.debug("Preview label updated")
        
        except Exception as e:
            logging.error(f"Error showing preview: {str(e)}")
            logging.error(traceback.format_exc())
            self.clear_preview()
            if not self._is_closing:
                messagebox.showerror("Error", f"Cannot preview image: {str(e)}")
    
    def clear_preview(self):
        """Safely clear preview image"""
        logging.debug("Clearing preview")
        try:
            if self.preview_photo:
                self.preview_label.config(image='')
                self._photo_references.discard(self.preview_photo)
                self.preview_photo = None
                logging.debug("Preview cleared successfully")
        except Exception as e:
            logging.error(f"Error clearing preview: {str(e)}")
            logging.error(traceback.format_exc())
    
    def update_file_info(self, file_path):
        try:
            file_size = os.path.getsize(file_path)
            with Image.open(file_path) as img:
                info_text = (
                    f"Filename: {os.path.basename(file_path)}\n"
                    f"Size: {humanize.naturalsize(file_size)}\n"
                    f"Dimensions: {img.width}x{img.height}\n"
                    f"Format: {img.format}"
                )
                self.file_info_label.config(text=info_text)
        except Exception as e:
            self.file_info_label.config(text=f"Error reading file info: {str(e)}")

    def compress_images(self):
        if not self.files_to_compress:
            messagebox.showwarning("Warning", "Please select images first!")
            return
        
        output_dir = filedialog.askdirectory(title="Select Output Directory")
        if not output_dir:
            return
        
        total_files = len(self.files_to_compress)
        self.progress_bar['maximum'] = total_files
        
        for i, file_path in enumerate(self.files_to_compress):
            try:
                # Open image
                img = Image.open(file_path)
                
                # Handle resize if enabled
                if self.resize_enabled.get():
                    try:
                        new_width = int(self.width.get()) if self.width.get() else img.width
                        new_height = int(self.height.get()) if self.height.get() else img.height
                        
                        if self.maintain_aspect.get():
                            # Calculate new dimensions maintaining aspect ratio
                            aspect_ratio = img.width / img.height
                            if new_width and new_height:
                                if new_width / new_height > aspect_ratio:
                                    new_width = int(new_height * aspect_ratio)
                                else:
                                    new_height = int(new_width / aspect_ratio)
                        
                        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    except ValueError:
                        messagebox.showerror("Error", "Invalid dimensions provided")
                        return
                
                # Convert RGBA to RGB if necessary
                if img.mode == 'RGBA' and self.output_format.get() == 'jpeg':
                    img = img.convert('RGB')
                
                # Generate output filename
                if self.rename_enabled.get():
                    filename = self.generate_filename(file_path, i)
                else:
                    filename = Path(file_path).stem
                
                output_path = os.path.join(output_dir, 
                    f"{filename}.{self.output_format.get()}")
                
                # Preserve metadata if enabled
                save_kwargs = {
                    'quality': self.quality.get(),
                    'optimize': True
                }
                
                if self.preserve_metadata.get():
                    try:
                        if img.info.get('exif'):
                            save_kwargs['exif'] = img.info['exif']
                        if img.info.get('icc_profile'):
                            save_kwargs['icc_profile'] = img.info['icc_profile']
                    except:
                        pass
                
                # Save with format-specific options
                if self.output_format.get() == 'webp':
                    save_kwargs['method'] = 6
                    save_kwargs['lossless'] = False
                
                img.save(output_path, format=self.output_format.get().upper(), **save_kwargs)
                
                # Update progress
                self.progress_bar['value'] = i + 1
                self.root.update_idletasks()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error processing {file_path}: {str(e)}")
        
        messagebox.showinfo("Success", "Images compressed successfully!")
        self.progress_bar['value'] = 0
        self.files_to_compress = []
        self.update_file_list()

    def setup_drag_drop(self):
        self.drop_frame.drop_target_register('DND_Files')
        self.drop_frame.dnd_bind('<<Drop>>', self.handle_drop)
        
        # Bind drop zone events
        self.drop_label.bind("<Button-1>", self.browse_files)
    
    def handle_drop(self, event):
        files = self.drop_frame.tk.splitlist(event.data)
        valid_files = [f for f in files if self.is_valid_image(f)]
        self.files_to_compress.extend(valid_files)
        self.update_file_list()
    
    def is_valid_image(self, file_path):
        return file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))
    
    def clear_files(self):
        """Clear all files and preview"""
        self.files_to_compress = []
        self.update_file_list()
        self.clear_preview()
    
    def update_file_list(self):
        self.file_listbox.delete(0, tk.END)
        for file_path in self.files_to_compress:
            filename = os.path.basename(file_path)
            self.file_listbox.insert(tk.END, filename)
        self.update_drop_label()
    
    def browse_files(self, event=None):
        files = filedialog.askopenfilenames(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.webp")])
        self.files_to_compress.extend(files)
        self.update_file_list()
    
    def update_drop_label(self):
        self.drop_label.config(text=f"{len(self.files_to_compress)} images selected")

    def apply_preset(self):
        preset = self.selected_preset.get()
        if preset == "hd":
            self.width.set("1920")
            self.height.set("1080")
        elif preset == "4k":
            self.width.set("3840")
            self.height.set("2160")
        elif preset == "thumbnail":
            self.width.set("300")
            self.height.set("300")
        elif preset == "social":
            self.width.set("1200")
            self.height.set("1200")
        self.resize_enabled.set(True)

    def apply_profile(self, profile_name):
        if profile_name != "Custom" and profile_name in self.profiles:
            profile = self.profiles[profile_name]
            self.output_format.set(profile["format"])
            self.quality.set(profile["quality"])
            self.resize_enabled.set(profile["resize"])
            if profile["resize"]:
                self.width.set(str(profile["width"]))
                self.height.set(str(profile["height"]))

    def save_profile(self):
        name = simpledialog.askstring("Save Profile", "Enter profile name:")
        if name:
            self.profiles[name] = {
                "format": self.output_format.get(),
                "quality": self.quality.get(),
                "resize": self.resize_enabled.get(),
                "width": int(self.width.get()) if self.width.get().isdigit() else 0,
                "height": int(self.height.get()) if self.height.get().isdigit() else 0
            }
            # Save profiles to file
            with open("compression_profiles.json", "w") as f:
                json.dump(self.profiles, f)
            messagebox.showinfo("Success", f"Profile '{name}' saved successfully!")

    def view_metadata(self):
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an image first!")
            return
            
        file_path = self.files_to_compress[selection[0]]
        try:
            metadata = self.get_image_metadata(file_path)
            
            # Create metadata viewer window
            viewer = tk.Toplevel(self.root)
            viewer.title(f"Metadata - {os.path.basename(file_path)}")
            viewer.geometry("400x500")
            
            # Create text widget with scrollbar
            text_frame = ttk.Frame(viewer)
            text_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            scrollbar = ttk.Scrollbar(text_frame)
            scrollbar.pack(side="right", fill="y")
            
            text_widget = tk.Text(text_frame, yscrollcommand=scrollbar.set)
            text_widget.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=text_widget.yview)
            
            # Insert metadata
            for key, value in metadata.items():
                text_widget.insert("end", f"{key}: {value}\n")
            
            text_widget.config(state="disabled")
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not read metadata: {str(e)}")

    def get_image_metadata(self, image_path):
        metadata = {}
        try:
            with Image.open(image_path) as img:
                # Get basic image info
                metadata["Format"] = img.format
                metadata["Mode"] = img.mode
                metadata["Size"] = f"{img.width}x{img.height}"
                
                # Get EXIF data
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    for tag_id in exif:
                        tag = TAGS.get(tag_id, tag_id)
                        data = exif.get(tag_id)
                        if isinstance(data, bytes):
                            data = data.decode(errors='replace')
                        metadata[tag] = data
                
                # Get other image info
                if hasattr(img, 'info'):
                    for key, value in img.info.items():
                        if isinstance(value, (str, int, float)):
                            metadata[key] = value
                
        except Exception as e:
            metadata["Error"] = str(e)
            
        return metadata

    def generate_filename(self, original_path, index):
        original_name = os.path.splitext(os.path.basename(original_path))[0]
        date = datetime.now().strftime("%Y%m%d")
        
        try:
            with Image.open(original_path) as img:
                width, height = img.size
        except:
            width, height = 0, 0
        
        # Replace variables in pattern
        pattern = self.rename_pattern.get()
        number = self.start_number.get() + index
        
        filename = pattern.format(
            original_name=original_name,
            number=f"{number:03d}",
            date=date,
            width=width,
            height=height
        )
        
        # Clean filename
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        return filename

    def show_about(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("About Image Compressor")
        about_window.geometry("400x300")
        
        # Center the window
        about_window.transient(self.root)
        about_window.grab_set()
        
        # Add developer info
        ttk.Label(about_window, text="Image Compressor", 
                 font=("Helvetica", 16, "bold")).pack(pady=20)
        ttk.Label(about_window, text=f"Version {self.VERSION}").pack()
        ttk.Label(about_window, text="Developed by MEHDI HARZALLAH", 
                 font=("Helvetica", 12)).pack(pady=20)
        
        # Contact info
        ttk.Label(about_window, text="Contact:").pack()
        ttk.Label(about_window, text="WhatsApp: +213 778191078").pack()
        ttk.Label(about_window, text="GitHub: github.com/opestro").pack()
        
        # Close button
        ttk.Button(about_window, text="Close", 
                  command=about_window.destroy).pack(pady=20)

    def on_closing(self):
        """Handle window closing event"""
        logging.info("Application closing")
        try:
            self._is_closing = True
            self.clear_preview()
            self._photo_references.clear()
            logging.debug("Cleaned up photo references")
            
            # Schedule destroy after a short delay
            self.root.after(100, self._destroy_window)
            
        except Exception as e:
            logging.error(f"Error during closing: {str(e)}")
            logging.error(traceback.format_exc())
            self.root.destroy()
    
    def _destroy_window(self):
        """Safely destroy the window"""
        try:
            logging.debug("Destroying window")
            self.root.quit()
            self.root.destroy()
        except Exception as e:
            logging.error(f"Error destroying window: {str(e)}")
            logging.error(traceback.format_exc())
    
    def __del__(self):
        """Cleanup when object is deleted"""
        logging.debug("ImageCompressorApp being deleted")
        try:
            self.clear_preview()
            self._photo_references.clear()
        except Exception as e:
            logging.error(f"Error in __del__: {str(e)}")

def main():
    logging.info("Starting application")
    root = None
    try:
        # Create main window first
        root = TkinterDnD.Tk()
        root.withdraw()
        logging.debug("Main window created")
        
        # Show splash screen
        splash = SplashScreen()
        splash.progress_bar()
        logging.debug("Splash screen displayed")
        
        # Initialize app
        app = ImageCompressorApp(root)
        logging.debug("App initialized")
        
        # Destroy splash screen and show main window
        splash.destroy()
        root.deiconify()
        root.update()  # Ensure window is fully initialized
        logging.debug("Main window displayed")
        
        # Start main loop
        root.mainloop()
        logging.info("Application mainloop ended")
        
    except Exception as e:
        logging.error(f"Critical error in main: {str(e)}")
        logging.error(traceback.format_exc())
        if root:
            try:
                root.quit()
            except:
                pass
        raise
    finally:
        logging.info("Application shutdown")
        try:
            if root:
                root.destroy()
        except Exception as e:
            logging.error(f"Error during final cleanup: {str(e)}")

class SplashScreen:
    def __init__(self):
        self.root = tk.Tk()  # Create a separate root for splash screen
        self.splash = tk.Toplevel(self.root)
        self.root.withdraw()  # Hide the root window
        self.splash.overrideredirect(True)
        
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
        
        # Add progress bar
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
    
    def progress_bar(self):
        """Update progress bar"""
        for i in range(101):
            self.progress['value'] = i
            self.splash.update()
            time.sleep(0.02)  # Add small delay for visual effect
    
    def destroy(self):
        """Clean up and destroy splash screen"""
        try:
            self.root.destroy()
        except Exception as e:
            logging.error(f"Error destroying splash screen: {str(e)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Application crashed: {str(e)}")
        logging.critical(traceback.format_exc())
        sys.exit(1) 