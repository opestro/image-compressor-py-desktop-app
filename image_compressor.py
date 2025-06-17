import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
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

# Try to import tkinterdnd2 with fallback
DRAG_DROP_AVAILABLE = False
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DRAG_DROP_AVAILABLE = True
    print("Drag and drop functionality available")
except ImportError as e:
    print(f"Drag and drop not available: {e}")
    # Fallback to regular tkinter
    class TkinterDnD:
        @staticmethod
        def Tk():
            return tk.Tk()
    DND_FILES = None

# Set up logging
import tempfile
from pathlib import Path

# Create log file in user's home directory for packaged app
if hasattr(sys, '_MEIPASS'):
    # Running as packaged app - use user's home directory
    log_dir = Path.home() / '.imagecompressor'
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / 'app.log'
else:
    # Running in development - use current directory
    log_file = 'app.log'

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

class CollapsibleFrame(ttk.Frame):
    """A frame that can be collapsed and expanded"""
    def __init__(self, parent, text="", *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        
        self.show = tk.BooleanVar(value=True)
        self.text = text
        
        # Create header button that shows/hides content
        self.toggle_button = ttk.Checkbutton(
            self, text=text,  # Use text directly instead of StringVar
            command=self.toggle, 
            style='Toggle.TCheckbutton',
            variable=self.show)
        self.toggle_button.grid(row=0, column=0, sticky="ew")
        
        # Create sub-frame for content
        self.sub_frame = ttk.Frame(self, padding=(15, 5, 5, 5))  # Added padding
        self.sub_frame.grid(row=1, column=0, sticky="nsew")
        self.grid_columnconfigure(0, weight=1)
    
    def toggle(self):
        """Toggle the visibility of the sub-frame"""
        if self.show.get():
            self.sub_frame.grid()
        else:
            self.sub_frame.grid_remove()

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
        self.supported_formats = {
            "JPEG": ".jpg",
            "PNG": ".png",
            "WebP": ".webp",
            "ICO": ".ico"  # Added ICO support
        }
        
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
        # Configure modern styles
        style = ttk.Style()
        
        # Modern button style
        style.configure('TButton', 
                       padding=5, 
                       font=('Helvetica', 9))
        
        # Modern checkbutton style
        style.configure('TCheckbutton', 
                       font=('Helvetica', 9))
        
        # Collapsible frame header style
        style.configure('Toggle.TCheckbutton', 
                       font=('Helvetica', 10, 'bold'),
                       padding=8,
                       background='#f0f0f0',  # Light gray background
                       relief='flat')
        
        # Entry style
        style.configure('TEntry', 
                       padding=5)
        
        # Label style
        style.configure('TLabel', 
                       font=('Helvetica', 9),
                       padding=2)
        
        # Frame style
        style.configure('TFrame', 
                       background='white')
        
        # Scale (slider) style
        style.configure('Horizontal.TScale', 
                       sliderlength=15)
        
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # Left panel for drop zone, preview, and file list
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Drop zone with modern look
        self.drop_frame = ttk.LabelFrame(left_panel, text="Drop Images Here", padding=10)
        self.drop_frame.pack(padx=5, pady=5, fill="x")  # Changed to fill="x"
        
        self.drop_label = ttk.Label(
            self.drop_frame, 
            text="Drop images here or click to browse",
            font=('Helvetica', 10))
        self.drop_label.pack(pady=20)
        
        # Preview section
        preview_frame = ttk.LabelFrame(left_panel, text="Preview", padding=5)
        preview_frame.pack(padx=5, pady=5, fill="both", expand=True)
        
        # Preview label for image
        self.preview_label = ttk.Label(preview_frame)
        self.preview_label.pack(pady=5)
        
        # File info label
        self.file_info_label = ttk.Label(preview_frame, justify="left")
        self.file_info_label.pack(pady=5)
        
        # File list with modern look
        list_frame = ttk.LabelFrame(left_panel, text="Selected Files", padding=5)
        list_frame.pack(padx=5, pady=5, fill="both")  # Reduced size
        
        # Modern scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Modern listbox with selection binding
        self.file_listbox = tk.Listbox(
            list_frame, 
            yscrollcommand=scrollbar.set,
            font=('Helvetica', 9),
            selectmode='extended',
            activestyle='none',
            borderwidth=0,
            height=6,  # Reduced height
            highlightthickness=0)
        self.file_listbox.pack(fill="both", expand=True)
        scrollbar.config(command=self.file_listbox.yview)
        
        # Bind selection event
        self.file_listbox.bind('<<ListboxSelect>>', self.on_select_file)
        
        # Clear button with modern look
        self.clear_btn = ttk.Button(
            left_panel, 
            text="Clear All Files",
            command=self.clear_files,  # Added command
            style='TButton')
        self.clear_btn.pack(pady=5)
        
        # Right scrollable panel
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side="right", fill="y")
        
        # Canvas for scrolling
        canvas = tk.Canvas(right_panel, width=300, highlightthickness=0)
        scrollbar = ttk.Scrollbar(right_panel, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=300)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Collapsible sections with modern styling
        sections = [
            ("Format Options", self.setup_format_section),
            ("Quality Settings", self.setup_quality_section),
            ("Resize Options", self.setup_resize_section),
            ("Compression Profiles", self.setup_profile_section),
            ("Metadata Options", self.setup_metadata_section),
            ("Batch Rename", self.setup_rename_section),
            ("Progress", self.setup_progress_section)
        ]
        
        for title, setup_func in sections:
            frame = CollapsibleFrame(scrollable_frame, text=title)
            frame.pack(fill="x", pady=2)
            setup_func(frame.sub_frame)
        
        # Compress button at bottom
        self.compress_btn = ttk.Button(
            scrollable_frame,
            text="Compress Images",
            style='TButton',
            command=self.compress_images)
        self.compress_btn.pack(pady=10)

    def on_select_file(self, event):
        """Handle file selection and update preview"""
        selection = self.file_listbox.curselection()
        if selection:
            index = selection[0]
            file_path = self.files_to_compress[index]
            self.show_preview(file_path)
            self.update_file_info(file_path)
    
    def show_preview(self, file_path):
        """Show image preview and update info"""
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
        """Update file information display"""
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
                
                # Convert RGBA to RGB if necessary for JPEG
                if img.mode == 'RGBA' and self.output_format.get() == 'jpeg':
                    img = img.convert('RGB')
                
                # Generate output filename
                if self.rename_enabled.get():
                    filename = self.generate_filename(file_path, i)
                else:
                    filename = Path(file_path).stem
                
                output_path = os.path.join(output_dir, 
                    f"{filename}.{self.output_format.get()}")
                
                # Special handling for ICO format
                if self.output_format.get() == 'ico':
                    # ICO format requires specific sizes
                    sizes = [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]
                    img.save(output_path, format='ICO', sizes=sizes)
                else:
                    # Save with format-specific options
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
                    
                    # Format-specific options
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
        global DRAG_DROP_AVAILABLE
        if DRAG_DROP_AVAILABLE:
            try:
                self.drop_frame.drop_target_register('DND_Files')
                self.drop_frame.dnd_bind('<<Drop>>', self.handle_drop)
                logging.info("Drag and drop functionality enabled")
            except Exception as e:
                logging.warning(f"Failed to setup drag and drop: {e}")
                DRAG_DROP_AVAILABLE = False
        
        if not DRAG_DROP_AVAILABLE:
            # Update label to indicate click-only mode
            self.drop_label.config(text="Click here to browse and select images")
            logging.info("Running in click-only mode (no drag and drop)")
        
        # Always bind click events
        self.drop_label.bind("<Button-1>", self.browse_files)
    
    def handle_drop(self, event):
        files = self.drop_frame.tk.splitlist(event.data)
        valid_files = [f for f in files if self.is_valid_image(f)]
        self.files_to_compress.extend(valid_files)
        self.update_file_list()
    
    def is_valid_image(self, file_path):
        return file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.ico'))
    
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

    def setup_format_section(self, parent):
        ttk.Label(parent, text="Output Format:").pack(padx=10, pady=2)
        for fmt in ["JPEG", "PNG", "WebP", "ICO"]:  # Added ICO to format options
            ttk.Radiobutton(parent, text=fmt, value=fmt.lower(),
                           variable=self.output_format).pack(padx=10, pady=2)

    def setup_quality_section(self, parent):
        ttk.Label(parent, text="Quality:").pack(padx=10, pady=2)
        self.quality_slider = ttk.Scale(
            parent, from_=1, to=100,
            variable=self.quality, 
            orient="horizontal")
        self.quality_slider.pack(padx=10, pady=5, fill="x")

    def setup_resize_section(self, parent):
        ttk.Checkbutton(parent, text="Enable Resize",
                       variable=self.resize_enabled).pack(padx=10, pady=2)
        
        dim_frame = ttk.Frame(parent)
        dim_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(dim_frame, text="Width:").pack(side="left")
        ttk.Entry(dim_frame, textvariable=self.width, width=8).pack(side="left", padx=5)
        ttk.Label(dim_frame, text="Height:").pack(side="left")
        ttk.Entry(dim_frame, textvariable=self.height, width=8).pack(side="left", padx=5)
        
        ttk.Checkbutton(parent, text="Maintain Aspect Ratio",
                       variable=self.maintain_aspect).pack(padx=10, pady=2)
        
        ttk.Label(parent, text="Presets:").pack(padx=10, pady=2)
        for text, value in [
            ("Custom", "custom"),
            ("HD (1920x1080)", "hd"),
            ("4K (3840x2160)", "4k"),
            ("Thumbnail (300x300)", "thumbnail"),
            ("Social (1200x1200)", "social")
        ]:
            ttk.Radiobutton(parent, text=text, value=value,
                          variable=self.selected_preset,
                          command=self.apply_preset).pack(padx=10, pady=2)

    def setup_profile_section(self, parent):
        profiles = ["Custom"] + list(self.profiles.keys())
        ttk.Label(parent, text="Select Profile:").pack(padx=10, pady=2)
        profile_menu = ttk.OptionMenu(parent, self.selected_profile,
                                    "Custom", *profiles,
                                    command=self.apply_profile)
        profile_menu.pack(padx=10, pady=2, fill="x")
        
        ttk.Button(parent, text="Save Current as Profile",
                  command=self.save_profile).pack(padx=10, pady=2, fill="x")

    def setup_metadata_section(self, parent):
        ttk.Checkbutton(parent, text="Preserve Metadata",
                       variable=self.preserve_metadata).pack(padx=10, pady=2)
        ttk.Button(parent, text="View Metadata",
                  command=self.view_metadata).pack(padx=10, pady=2)

    def setup_rename_section(self, parent):
        ttk.Checkbutton(parent, text="Enable Batch Rename",
                       variable=self.rename_enabled).pack(padx=10, pady=2)
        
        ttk.Label(parent, text="Pattern:").pack(padx=10, pady=(5,0))
        pattern_entry = ttk.Entry(parent, textvariable=self.rename_pattern)
        pattern_entry.pack(padx=10, pady=(0,5), fill="x")
        
        ttk.Label(parent, 
                 text="Available variables:\n{original_name}, {number},\n{date}, {width}, {height}",
                 justify="left").pack(padx=10)
        
        number_frame = ttk.Frame(parent)
        number_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(number_frame, text="Start Number:").pack(side="left")
        ttk.Entry(number_frame, textvariable=self.start_number, width=8).pack(side="left", padx=5)

    def setup_progress_section(self, parent):
        self.progress_bar = ttk.Progressbar(parent, mode='determinate')
        self.progress_bar.pack(padx=10, pady=5, fill="x")

def main():
    global DRAG_DROP_AVAILABLE
    logging.info("Starting application")
    root = None
    try:
        # Initialize tkdnd only if available
        if DRAG_DROP_AVAILABLE and hasattr(sys, '_MEIPASS'):
            try:
                tkdnd_path = os.path.join(sys._MEIPASS, 'tkinterdnd2', 'tkdnd')
                os.environ['TKDND_LIBRARY'] = tkdnd_path
                logging.debug("Set TKDND_LIBRARY path")
            except Exception as e:
                logging.warning(f"Failed to set TKDND_LIBRARY: {e}")
        
        # Create main window with fallback handling
        try:
            root = TkinterDnD.Tk()
            logging.debug("Main window created with TkinterDnD")
        except Exception as e:
            logging.warning(f"TkinterDnD.Tk() failed: {e}, falling back to tk.Tk()")
            root = tk.Tk()
            DRAG_DROP_AVAILABLE = False
        
        root.withdraw()
        logging.debug("Main window created")
        
        # Show splash screen
        splash = SplashScreen(root)  # Pass root as parent
        splash.progress_bar()
        logging.debug("Splash screen displayed")
        
        # Initialize app
        app = ImageCompressorApp(root)
        logging.debug("App initialized")
        
        # Destroy splash screen and show main window
        splash.destroy()
        root.deiconify()
        
        # Ensure window appears prominently
        root.lift()  # Bring window to front
        root.attributes('-topmost', True)  # Make window stay on top temporarily
        root.focus_force()  # Force focus on the window
        root.update()
        root.after(100, lambda: root.attributes('-topmost', False))  # Remove topmost after 100ms
        
        logging.debug("Main window displayed")
        
        root.mainloop()
        
    except Exception as e:
        logging.error(f"Critical error in main: {str(e)}")
        logging.error(traceback.format_exc())
        if root:
            try:
                root.quit()
            except:
                pass
        raise

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Application crashed: {str(e)}")
        logging.critical(traceback.format_exc())
        sys.exit(1) 