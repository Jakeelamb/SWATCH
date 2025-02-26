import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import subprocess
import threading
import time
import re
from datetime import datetime
import os
import json
import getpass
import paramiko
from PIL import Image, ImageTk, ImageDraw, ImageFont
import argparse
from dataclasses import dataclass
import queue

# Define a custom style theme class
class DarkTheme:
    # Main colors - Softer macOS-like palette
    BG_COLOR = "#333333"  # Lighter dark gray for background
    SECONDARY_BG = "#404040"  # Slightly lighter secondary background
    TEXT_COLOR = "#FFFFFF"  # White text for contrast
    ACCENT_COLOR = "#007AFF"  # macOS blue for accents (like buttons and highlights)
    
    # Status colors - Softer, macOS-like palette
    RUNNING_COLOR = "#34C759"  # Soft green
    PENDING_COLOR = "#FF9500"  # Soft orange
    COMPLETED_COLOR = "#007AFF"  # Blue (same as accent)
    FAILED_COLOR = "#FF3B30"  # Soft red
    
    # Title colors using status colors
    TITLE_COLORS = {
        'S': RUNNING_COLOR,
        'W': PENDING_COLOR,
        'A': COMPLETED_COLOR,
        'T': FAILED_COLOR,
        'C': ACCENT_COLOR,
        'H': TEXT_COLOR
    }
    
    # Updated fonts (macOS San Francisco-like)
    MAIN_FONT = ("Helvetica Neue", 11)  # Default text
    HEADER_FONT = ("Helvetica Neue", 13, "bold")  # Headings
    SMALL_FONT = ("Helvetica Neue", 10)
    
    # Updated spacing
    PADDING = 10  # Consistent macOS padding
    CORNER_RADIUS = 12  # Larger radius for smoother corners
    
    # Treeview configuration
    TREEVIEW_CONFIG = {
        "columns": ("job_id", "name", "status", "time", "nodes", "cpus", "memory"),
        "widths": {
            "job_id": 80,
            "name": 150,
            "status": 80,
            "time": 80,
            "nodes": 60,
            "cpus": 60,
            "memory": 90
        }
    }

# Custom rounded frame class
class RoundedFrame(tk.Canvas):
    def __init__(self, parent, bg=DarkTheme.SECONDARY_BG, corner_radius=DarkTheme.CORNER_RADIUS, **kwargs):
        super().__init__(parent, bg=DarkTheme.BG_COLOR, highlightthickness=0, **kwargs)
        self.corner_radius = corner_radius
        self.bg_color = bg
        
        # Bind resize event to redraw the rounded rectangle
        self.bind("<Configure>", self._on_resize)
        self.create_rounded_rect()
        
    def _on_resize(self, event):
        self.update_idletasks()
        self.create_rounded_rect()
        
    def create_rounded_rect(self):
        self.delete("all")
        width, height = self.winfo_width(), self.winfo_height()
        # Add a subtle shadow effect
        self.create_rounded_rectangle(2, 2, width-2, height-2, radius=self.corner_radius, fill=self.bg_color, outline="#1C1C1C", width=1)
        self.create_rounded_rectangle(0, 0, width, height, radius=self.corner_radius, fill=self.bg_color)
        
    def create_rounded_rectangle(self, x1, y1, x2, y2, radius=10, **kwargs):
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

# Create status indicator circle
def create_circle_image(color, size=12):
    """Create a colored circle image for status indicators"""
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((0, 0, size, size), fill=color)
    return ImageTk.PhotoImage(image)

class CustomTreeview(ttk.Treeview):
    def __init__(self, master, **kwargs):
        style = ttk.Style()
        
        # Configure treeview with macOS-like styling
        style.configure("Custom.Treeview", 
            font=DarkTheme.MAIN_FONT,
            background=DarkTheme.SECONDARY_BG,
            foreground=DarkTheme.TEXT_COLOR,
            fieldbackground=DarkTheme.SECONDARY_BG,
            borderwidth=0,
            rowheight=24  # Slightly taller for macOS look
        )
        
        # Configure header
        style.configure("Custom.Treeview.Heading",
            font=DarkTheme.HEADER_FONT,
            background=DarkTheme.BG_COLOR,
            foreground=DarkTheme.ACCENT_COLOR,
            borderwidth=0
        )
        
        # Configure selection (subtle blue highlight like macOS)
        style.map("Custom.Treeview",
            background=[
                ("selected", DarkTheme.ACCENT_COLOR),
                ("!selected", ["#444444", DarkTheme.SECONDARY_BG])
            ],
            foreground=[("selected", DarkTheme.BG_COLOR)]
        )
        
        kwargs['style'] = "Custom.Treeview"
        super().__init__(master, **kwargs)

class CustomStyle(ttk.Style):
    def __init__(self):
        super().__init__()
        self.configure('TFrame', background=DarkTheme.BG_COLOR)
        self.configure('TLabel', background=DarkTheme.BG_COLOR, foreground=DarkTheme.TEXT_COLOR)
        self.configure('TButton', background=DarkTheme.SECONDARY_BG, foreground=DarkTheme.TEXT_COLOR, font=DarkTheme.MAIN_FONT, borderwidth=1, relief="flat")
        self.configure('TCheckbutton', background=DarkTheme.BG_COLOR, foreground=DarkTheme.TEXT_COLOR, font=DarkTheme.MAIN_FONT)
        self.configure('TEntry', fieldbackground=DarkTheme.SECONDARY_BG, foreground=DarkTheme.TEXT_COLOR, font=DarkTheme.MAIN_FONT)
        
        # Add hover effect for buttons
        self.map('TButton', background=[('active', DarkTheme.ACCENT_COLOR)], foreground=[('active', DarkTheme.BG_COLOR)])

class LoginDialog(simpledialog.Dialog):
    def __init__(self, parent, title=None, default_username="", default_hostname="login.cluster.edu"):
        self.default_username = default_username
        self.default_hostname = default_hostname
        self.bg_color = DarkTheme.BG_COLOR
        self.text_color = DarkTheme.TEXT_COLOR
        
        # Ensure dialog is created as a Toplevel window
        self.root = parent
        super().__init__(parent, title)
    
    def body(self, master):
        master.configure(bg=self.bg_color)
        
        # Calculate position relative to main window
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 175
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 100
        
        # Set dialog size and position
        self.geometry(f"350x200+{x}+{y}")
        
        # Ensure dialog stays on top
        self.transient(self.root)
        self.lift()
        self.focus_force()
        
        # Rest of the existing body code...
        frame = RoundedFrame(master, width=330, height=180, corner_radius=DarkTheme.CORNER_RADIUS)
        frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Create content frame
        content_frame = tk.Frame(frame, bg=DarkTheme.SECONDARY_BG)
        content_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=310, height=160)
        
        ttk.Label(content_frame, text="Username:", background=DarkTheme.SECONDARY_BG).grid(
            row=0, column=0, sticky=tk.W, pady=5, padx=5)
        ttk.Label(content_frame, text="Password:", background=DarkTheme.SECONDARY_BG).grid(
            row=1, column=0, sticky=tk.W, pady=5, padx=5)
        ttk.Label(content_frame, text="Hostname:", background=DarkTheme.SECONDARY_BG).grid(
            row=2, column=0, sticky=tk.W, pady=5, padx=5)
        
        self.username_entry = ttk.Entry(content_frame, width=25)
        self.username_entry.grid(row=0, column=1, pady=5, padx=5)
        self.username_entry.insert(0, self.default_username)
        
        self.password_entry = ttk.Entry(content_frame, width=25, show="•")
        self.password_entry.grid(row=1, column=1, pady=5, padx=5)
        
        self.hostname_entry = ttk.Entry(content_frame, width=25)
        self.hostname_entry.grid(row=2, column=1, pady=5, padx=5)
        self.hostname_entry.insert(0, self.default_hostname)
        
        self.save_credentials = tk.BooleanVar(value=False)
        ttk.Checkbutton(content_frame, text="Remember credentials", 
                      variable=self.save_credentials,
                      style="TCheckbutton").grid(
            row=3, column=0, columnspan=2, pady=5, padx=5, sticky=tk.W)
        
        return self.username_entry  # Initial focus
    
    def buttonbox(self):
        box = tk.Frame(self, bg=self.bg_color)
        
        w = ttk.Button(box, text="Login", width=10, command=self.ok, default=tk.ACTIVE)
        w.pack(side=tk.LEFT, padx=5, pady=5)
        w = ttk.Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        
        box.pack(fill=tk.X, expand=True, anchor=tk.S, pady=5)
    
    def apply(self):
        self.result = {
            "username": self.username_entry.get(),
            "password": self.password_entry.get(),
            "hostname": self.hostname_entry.get(),
            "save": self.save_credentials.get()
        }

# Create a colored title logo
def create_swatch_logo():
    """Create a colored swatch logo with each letter corresponding to job status"""
    # Define dimensions
    font_size = 24
    padding = 5
    title_text = "SWATCH"
    subtitle_text = "(Slurm Watch)"
    
    try:
        # Attempt to load a font, fall back to default if not available
        try:
            font = ImageFont.truetype("Arial Bold", font_size)
            small_font = ImageFont.truetype("Arial", font_size // 2)
        except:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Calculate image size
        title_width = len(title_text) * font_size + padding * 2
        image = Image.new('RGBA', (title_width * 2, font_size * 2), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Colors for each letter (matching job status colors)
        colors = [
            DarkTheme.RUNNING_COLOR,   # S
            DarkTheme.PENDING_COLOR,   # A
            DarkTheme.COMPLETED_COLOR, # T
            DarkTheme.FAILED_COLOR,    # C
            DarkTheme.ACCENT_COLOR     # H
        ]
        
        # Draw each letter with its color
        x_offset = padding
        for i, letter in enumerate(title_text):
            draw.text((x_offset, padding), letter, fill=colors[i], font=font)
            x_offset += font_size
        
        # Draw subtitle
        draw.text((padding, font_size + padding), subtitle_text, fill=DarkTheme.TEXT_COLOR, font=small_font)
        
        return ImageTk.PhotoImage(image)
    except Exception as e:
        print(f"Error creating logo: {e}")
        return None

@dataclass
class JobInfo:
    job_id: str
    name: str
    status: str
    time: str
    nodes: str
    cpus: str
    memory: str

    @property
    def tag(self) -> str:
        """Return the appropriate tag for the job's status"""
        if self.status == "RUNNING":
            return 'running'
        elif self.status == "PENDING":
            return 'pending'
        elif self.status in ["COMPLETED", "COMPLETING"]:
            return 'completed'
        elif self.status in ["FAILED", "TIMEOUT", "CANCELLED"]:
            return 'failed'
        return 'pending'  # Default case

    @staticmethod
    def format_memory(memory: str) -> str:
        """Format memory string to MB/GB format"""
        try:
            if isinstance(memory, str) and ("MB" in memory or "GB" in memory):
                return memory
            memory_val = int(memory.strip())
            return f"{memory_val/1024:.1f}GB" if memory_val >= 1024 else f"{memory_val}MB"
        except (ValueError, AttributeError):
            return memory

class HPCJobMonitor:
    def __init__(self, root, test_mode=False):
        self.root = root
        self.root.geometry("800x550")  # Slightly increased height for legend
        self.root.configure(bg=DarkTheme.BG_COLOR)
        
        # Set window title
        self.root.title("SWATCH - (Slurm Job Watcher)")
        
        # Add test_mode
        self.test_mode = test_mode
        
        # Initialize auto-refresh variables first
        self.auto_refresh = tk.BooleanVar(value=True)
        self.refresh_interval = 30  # seconds
        self.refresh_intervals = {
            "5 seconds": 5,
            "30 seconds": 30,
            "1 minute": 60,
            "5 minutes": 300,
            "15 minutes": 900,
            "1 hour": 3600
        }
        self.refresh_interval_var = tk.StringVar(value="30 seconds")
        self.refresh_timer = None
        
        # Authentication
        self.username = ""
        self.password = ""
        self.hostname = ""
        self.authenticated = False
        self.ssh_client = None
        
        # Add thread safety and result queue
        self.ssh_lock = threading.Lock()
        self.result_queue = queue.Queue()
        
        # Load saved credentials
        self.config_file = os.path.join(os.path.expanduser("~"), ".hpcjobmonitor", "config.json")
        self._load_credentials_async()
        
        # Configure scrollbar style
        scrollbar_style = ttk.Style()
        scrollbar_style.configure("Custom.Vertical.TScrollbar", 
                                background=DarkTheme.SECONDARY_BG, 
                                troughcolor=DarkTheme.BG_COLOR, 
                                borderwidth=0,
                                arrowcolor=DarkTheme.TEXT_COLOR)
        
        # Build GUI
        self.setup_gui()
        
        # Start auto-refresh after GUI is built
        self.start_auto_refresh()
    
    def setup_gui(self):
        # Main frame
        self.main_frame = tk.Frame(self.root, bg=DarkTheme.SECONDARY_BG)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        header_frame = tk.Frame(self.main_frame, bg=DarkTheme.SECONDARY_BG)
        header_frame.pack(fill=tk.X, pady=5)
        
        self.user_label = ttk.Label(header_frame, text="Not logged in", 
                                  background=DarkTheme.SECONDARY_BG,
                                  font=DarkTheme.MAIN_FONT)
        self.user_label.pack(side=tk.LEFT, padx=5)
        
        self.last_updated = ttk.Label(header_frame, text="Last updated: Never",
                                    background=DarkTheme.SECONDARY_BG,
                                    font=DarkTheme.MAIN_FONT)
        self.last_updated.pack(side=tk.RIGHT, padx=5)
        
        # Add legend above the job tree
        legend_frame = tk.Frame(self.main_frame, bg=DarkTheme.SECONDARY_BG)
        legend_frame.pack(fill=tk.X, pady=5)
        
        # Create legend items
        legend_items = [
            ("Running", DarkTheme.RUNNING_COLOR),
            ("Pending", DarkTheme.PENDING_COLOR),
            ("Completed", DarkTheme.COMPLETED_COLOR),
            ("Failed", DarkTheme.FAILED_COLOR)
        ]
        
        # Add legend label
        ttk.Label(legend_frame, text="Legend:", 
                background=DarkTheme.SECONDARY_BG,
                font=DarkTheme.MAIN_FONT).pack(side=tk.LEFT, padx=5)
        
        # Add color indicators and labels
        for text, color in legend_items:
            # Create a small colored square
            indicator = tk.Canvas(legend_frame, width=12, height=12, bg=DarkTheme.SECONDARY_BG, 
                                highlightthickness=0)
            indicator.pack(side=tk.LEFT, padx=2)
            indicator.create_rectangle(0, 0, 12, 12, fill=color, outline="")
            
            # Add label
            ttk.Label(legend_frame, text=text, 
                    background=DarkTheme.SECONDARY_BG,
                    foreground=color,
                    font=DarkTheme.MAIN_FONT).pack(side=tk.LEFT, padx=5)
        
        # Job tree
        self.tree = CustomTreeview(self.main_frame, 
                               columns=("job_id", "name", "status", "time", "nodes", "cpus", "memory"),
                               show="headings", height=15)
        self.init_tree_columns()
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Control frame
        control_frame = tk.Frame(self.main_frame, bg=DarkTheme.SECONDARY_BG)
        control_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(control_frame, text="Refresh", command=self.refresh_jobs).pack(side=tk.LEFT, padx=5)
        self.login_btn = ttk.Button(control_frame, text="Login", command=self.handle_login)
        self.login_btn.pack(side=tk.LEFT, padx=5)
        
        # Auto-refresh checkbox
        auto_refresh_frame = tk.Frame(control_frame, bg=DarkTheme.SECONDARY_BG)
        auto_refresh_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Checkbutton(auto_refresh_frame, text="Auto-refresh", variable=self.auto_refresh,
                       command=self.toggle_auto_refresh).pack(side=tk.LEFT)
        
        # Refresh interval dropdown
        ttk.Label(auto_refresh_frame, text="Interval:", 
                background=DarkTheme.SECONDARY_BG,
                font=DarkTheme.MAIN_FONT).pack(side=tk.LEFT, padx=(10, 2))
        
        refresh_dropdown = ttk.Combobox(auto_refresh_frame, 
                                      textvariable=self.refresh_interval_var,
                                      values=list(self.refresh_intervals.keys()),
                                      width=10,
                                      state="readonly")
        refresh_dropdown.pack(side=tk.LEFT)
        refresh_dropdown.bind("<<ComboboxSelected>>", self.update_refresh_interval)
    
    def init_tree_columns(self):
        """Initialize tree columns and headings"""
        # Configure all columns
        columns_config = {
            "job_id": {"width": 80, "text": "JOB ID", "anchor": "center"},
            "name": {"width": 150, "text": "NAME", "anchor": "w"},
            "status": {"width": 90, "text": "STATUS", "anchor": "center"},
            "time": {"width": 80, "text": "RUNTIME", "anchor": "center"},
            "nodes": {"width": 60, "text": "NODES", "anchor": "center"},
            "cpus": {"width": 60, "text": "CPUS", "anchor": "center"},
            "memory": {"width": 90, "text": "MEMORY", "anchor": "center"}
        }
        
        # Apply configuration for each column
        for col, config in columns_config.items():
            self.tree.heading(col, text=config["text"])
            self.tree.column(col, width=config["width"], anchor=config["anchor"])

    def _load_credentials_async(self):
        """Asynchronously load and test credentials"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    
                    if 'username' in config and 'hostname' in config:
                        self.username = config.get('username', '')
                        self.hostname = config.get('hostname', 'login.cluster.edu')
                        
                        # If password is saved
                        if 'password' in config:
                            self.password = config.get('password', '')
                            
                            # Test connection with saved credentials
                            if self.test_connection():
                                self.authenticated = True
                                # Update UI in main thread
                                self.root.after(0, lambda: self.update_login_status(True))
        except Exception as e:
            print(f"Error loading credentials: {e}")

    def handle_login(self):
        """Handle login button click - show dialog and process login"""
        print("Login button clicked")
        
        # Create a new top-level window for login
        login_window = tk.Toplevel(self.root)
        login_window.title("HPC Login")
        login_window.configure(bg=DarkTheme.BG_COLOR)
        login_window.transient(self.root)
        login_window.grab_set()  # Make window modal
        
        # Position the window
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 175
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 100
        login_window.geometry(f"350x200+{x}+{y}")
        
        # Create frame
        frame = RoundedFrame(login_window, width=330, height=180, corner_radius=DarkTheme.CORNER_RADIUS)
        frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Create content frame
        content_frame = tk.Frame(frame, bg=DarkTheme.SECONDARY_BG)
        content_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=310, height=160)
        
        # Username
        ttk.Label(content_frame, text="Username:", background=DarkTheme.SECONDARY_BG).grid(
            row=0, column=0, sticky=tk.W, pady=5, padx=5)
        username_entry = ttk.Entry(content_frame, width=25)
        username_entry.grid(row=0, column=1, pady=5, padx=5)
        username_entry.insert(0, self.username)
        
        # Password
        ttk.Label(content_frame, text="Password:", background=DarkTheme.SECONDARY_BG).grid(
            row=1, column=0, sticky=tk.W, pady=5, padx=5)
        password_entry = ttk.Entry(content_frame, width=25, show="•")
        password_entry.grid(row=1, column=1, pady=5, padx=5)
        
        # Hostname
        ttk.Label(content_frame, text="Hostname:", background=DarkTheme.SECONDARY_BG).grid(
            row=2, column=0, sticky=tk.W, pady=5, padx=5)
        hostname_entry = ttk.Entry(content_frame, width=25)
        hostname_entry.grid(row=2, column=1, pady=5, padx=5)
        hostname_entry.insert(0, self.hostname)
        
        # Remember credentials
        save_credentials = tk.BooleanVar(value=False)
        ttk.Checkbutton(content_frame, text="Remember credentials", 
                      variable=save_credentials,
                      style="TCheckbutton").grid(
            row=3, column=0, columnspan=2, pady=5, padx=5, sticky=tk.W)
        
        # Status label
        status_label = ttk.Label(content_frame, text="", background=DarkTheme.SECONDARY_BG)
        status_label.grid(row=4, column=0, columnspan=2, pady=5, padx=5)
        
        # Button frame
        button_frame = tk.Frame(content_frame, bg=DarkTheme.SECONDARY_BG)
        button_frame.grid(row=5, column=0, columnspan=2, pady=5, padx=5)
        
        def on_login():
            """Handle login button click"""
            # Get values
            username = username_entry.get()
            password = password_entry.get()
            hostname = hostname_entry.get()
            save = save_credentials.get()
            
            if not username or not password or not hostname:
                status_label.config(text="Please fill in all fields", foreground="red")
                return
            
            # Update status
            status_label.config(text="Connecting...", foreground=DarkTheme.TEXT_COLOR)
            login_button.config(state="disabled")
            cancel_button.config(state="disabled")
            
            # Process login in background thread
            def process_login():
                try:
                    # Disconnect existing connection if any
                    if self.authenticated:
                        self.disconnect()
                        self.authenticated = False
                    
                    # Update credentials
                    self.username = username
                    self.password = password
                    self.hostname = hostname
                    
                    # Test connection
                    connection_success = self.test_connection()
                    
                    # Update UI in main thread
                    login_window.after(0, lambda: update_ui(connection_success, save))
                except Exception as e:
                    print(f"Login error: {e}")
                    login_window.after(0, lambda: status_label.config(
                        text=f"Error: {str(e)}", foreground="red"))
                    login_window.after(0, lambda: login_button.config(state="normal"))
                    login_window.after(0, lambda: cancel_button.config(state="normal"))
            
            def update_ui(success, save):
                if success:
                    self.authenticated = True
                    
                    # Save credentials if requested
                    if save:
                        self.save_credentials({
                            "username": username,
                            "password": password if save else "",
                            "hostname": hostname,
                            "save": save
                        })
                    
                    # Close login window
                    login_window.destroy()
                    
                    # Update main UI
                    self.update_login_status(True)
                    self.refresh_jobs()
                else:
                    status_label.config(
                        text="Authentication failed. Check credentials.", 
                        foreground="red")
                    login_button.config(state="normal")
                    cancel_button.config(state="normal")
            
            # Start login process
            threading.Thread(target=process_login, daemon=True).start()
        
        # Buttons
        login_button = ttk.Button(button_frame, text="Login", command=on_login)
        login_button.pack(side=tk.LEFT, padx=5)
        
        cancel_button = ttk.Button(button_frame, text="Cancel", 
                                 command=login_window.destroy)
        cancel_button.pack(side=tk.LEFT, padx=5)
        
        # Set focus to username entry
        username_entry.focus_set()
        
        # Bind Enter key to login button
        login_window.bind("<Return>", lambda event: on_login())
        
        # Bind Escape key to cancel
        login_window.bind("<Escape>", lambda event: login_window.destroy())

    def test_connection(self):
        """Test SSH connection with the credentials"""
        if self.test_mode:
            return True  # Always return success in test mode
        
        print(f"Attempting connection to {self.hostname}...")
        try:
            # Create new connection
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            print("Initiating SSH connection...")
            # Connect with timeout
            ssh_client.connect(
                hostname=self.hostname, 
                username=self.username, 
                password=self.password,
                timeout=5
            )
            
            print("Testing connection with echo command...")
            # Test a simple command
            stdin, stdout, stderr = ssh_client.exec_command("echo Connection test successful")
            result = stdout.read().decode().strip()
            
            print(f"Connection test result: {result}")
            
            # Store the client if successful
            self.ssh_client = ssh_client
            return "Connection test successful" in result
        except Exception as e:
            print(f"Connection test failed with error: {e}")
            return False
    
    def run_remote_command(self, command):
        """Run a command on the remote server via SSH"""
        if not self.authenticated:
            return None
        
        if self.test_mode:
            # Return test data when in test mode - FIXED FORMAT
            if command.startswith("squeue"):
                # Format matches what get_jobs expects to parse
                return """JOBID|NAME|STATE|TIME|NODES|CPUS|MEMORY
12345|tensorflow_train|RUNNING|10:23|2|32|64000
12346|data_preprocessing|PENDING|00:00|1|8|16000
12347|genome_analysis|RUNNING|5:45|4|128|256000
12348|pytorch_model|COMPLETED|12:30|8|256|512000
12349|ml_training|PENDING|00:00|2|16|32000
12350|batch_process|RUNNING|2:15|1|4|8000
12351|failed_job|FAILED|05:21|2|64|128000
12352|image_processing|RUNNING|8:33|4|96|192000
12353|awaiting_resources|PENDING|00:00|8|512|1024000"""
            return ""
        
        # Use lock for thread safety
        with self.ssh_lock:
            try:
                # Check if we have an active connection
                if not self.ssh_client or not self.ssh_client.get_transport() or not self.ssh_client.get_transport().is_active():
                    # Reconnect if needed
                    if not self.test_connection():
                        print("SSH connection lost and reconnection failed")
                        self.update_login_status(False)
                        self.authenticated = False
                        return None
                
                # Execute command
                stdin, stdout, stderr = self.ssh_client.exec_command(command)
                output = stdout.read().decode()
                error = stderr.read().decode()
                
                if error and not output:
                    print(f"Command error: {error}")
                    return None
                    
                return output
            except Exception as e:
                print(f"Error running remote command: {e}")
                # Try to reconnect on next command
                self.disconnect()
                return None
    
    def get_jobs(self):
        """Get job information from the HPC system"""
        if not self.authenticated:
            return []
        
        squeue_output = self.run_remote_command(
            f"squeue -u {self.username} -o '%A|%j|%T|%M|%D|%C|%m'"
        )
        
        if not squeue_output:
            return []
        
        jobs = []
        for line in squeue_output.strip().split('\n'):
            if line and not line.startswith("JOBID"):
                try:
                    parts = line.split('|')
                    if len(parts) >= 7:
                        job_id, name, status, runtime, nodes, cpus, memory = parts[:7]
                        jobs.append(JobInfo(
                            job_id=job_id.strip(),
                            name=name.strip(),
                            status=status.strip(),
                            time=runtime.strip(),
                            nodes=nodes.strip(),
                            cpus=cpus.strip(),
                            memory=JobInfo.format_memory(memory)
                        ))
                except ValueError as e:
                    print(f"Error parsing job data: {e}, line: {line}")
                    continue
        
        return jobs
    
    def refresh_jobs(self):
        """Refresh the job list display"""
        if not self.authenticated:
            if not self.test_mode:
                messagebox.showinfo("Not Authenticated", "Please log in first")
                self.handle_login()
            return
        
        # Use threading for job refresh to keep UI responsive
        threading.Thread(target=self._async_refresh_jobs, daemon=True).start()
        self.root.after(100, self._check_refresh_result)
    
    def _async_refresh_jobs(self):
        """Asynchronously fetch job data"""
        try:
            jobs = self.get_jobs()
            self.result_queue.put(("refresh", jobs))
        except Exception as e:
            print(f"Error in async refresh: {e}")
            self.result_queue.put(("refresh", None))
    
    def _check_refresh_result(self):
        """Check for results from the async job refresh"""
        try:
            while not self.result_queue.empty():
                action, jobs = self.result_queue.get_nowait()
                if action == "refresh" and jobs is not None:
                    # Clear current items
                    for item in self.tree.get_children():
                        self.tree.delete(item)
                    
                    status_counts = {"running": 0, "pending": 0, "completed": 0, "failed": 0}
                    
                    # Create tags for different status colors
                    self.tree.tag_configure('running', foreground=DarkTheme.RUNNING_COLOR)
                    self.tree.tag_configure('pending', foreground=DarkTheme.PENDING_COLOR)
                    self.tree.tag_configure('completed', foreground=DarkTheme.COMPLETED_COLOR)
                    self.tree.tag_configure('failed', foreground=DarkTheme.FAILED_COLOR)
                    
                    for job in jobs:
                        tag = job.tag
                        status_counts[tag] += 1
                        
                        # Insert job with appropriate tag
                        self.tree.insert("", "end",
                            values=(
                                job.job_id,
                                job.name,
                                job.status,
                                job.time,
                                job.nodes,
                                job.cpus,
                                job.memory
                            ),
                            tags=(tag,)
                        )
                    
                    # Update summary with Unicode box drawing characters
                    summary = (f"Running: {status_counts['running']:2d} │ "
                              f"Pending: {status_counts['pending']:2d} │ "
                              f"Completed: {status_counts['completed']:2d} │ "
                              f"Failed: {status_counts['failed']:2d}")
                    self.last_updated.config(text=f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
                    
                    # Update timestamp
                    now = datetime.now().strftime("%H:%M:%S")
                    self.user_label.config(text=f"{self.username}@{self.hostname}")
                    return
        except queue.Empty:
            self.root.after(100, self._check_refresh_result)

    def toggle_auto_refresh(self):
        """Toggle auto-refresh on/off"""
        if self.auto_refresh.get():
            self.start_auto_refresh()
        else:
            self.stop_auto_refresh()
    
    def start_auto_refresh(self):
        """Start the auto-refresh timer"""
        self.stop_auto_refresh()  # Stop any existing timer
        
        if self.auto_refresh.get() and self.authenticated:
            # Schedule refresh
            self.refresh_timer = self.root.after(self.refresh_interval * 1000, self.auto_refresh_callback)
    
    def stop_auto_refresh(self):
        """Stop the auto-refresh timer"""
        if self.refresh_timer:
            self.root.after_cancel(self.refresh_timer)
            self.refresh_timer = None
    
    def auto_refresh_callback(self):
        """Callback for auto-refresh timer"""
        if self.auto_refresh.get() and self.authenticated:
            self.refresh_jobs()
            # Reschedule
            self.refresh_timer = self.root.after(self.refresh_interval * 1000, self.auto_refresh_callback)
    
    def on_closing(self):
        """Clean up before closing"""
        self.stop_auto_refresh()
        self.disconnect()
        self.root.destroy()

    def start_drag(self, event):
        """Start window drag operation"""
        self.x = event.x
        self.y = event.y

    def drag_window(self, event):
        """Handle window dragging"""
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def _process_login_async(self, credentials):
        """Process login credentials asynchronously"""
        print("Processing login asynchronously")  # Debug print
        try:
            # Update credentials
            self.username = credentials['username']
            self.password = credentials['password']
            self.hostname = credentials['hostname']
            
            print("Testing connection...")  # Debug print
            # Show a "connecting" message
            self.root.after(0, lambda: self.user_label.config(text="Connecting..."))
            
            # Test connection
            connection_success = self.test_connection()
            print(f"Connection test result: {connection_success}")  # Debug print
            
            # Update UI in the main thread
            def update_ui():
                print("Updating UI after connection test")  # Debug print
                if connection_success:
                    self.authenticated = True
                    self.update_login_status(True)
                    
                    # Save credentials if requested
                    if credentials['save']:
                        print("Saving credentials")  # Debug print
                        self.save_credentials(credentials)
                    
                    # Refresh job list
                    self.refresh_jobs()
                else:
                    print("Authentication failed")  # Debug print
                    self.authenticated = False
                    self.update_login_status(False)
                    messagebox.showerror("Authentication Failed", 
                                       "Could not authenticate with the provided credentials.\n"
                                       "Please check your username, password, and hostname.")
            
            self.root.after(0, update_ui)
            
        except Exception as e:
            print(f"Login processing error: {e}")
            self.root.after(0, lambda: messagebox.showerror("Login Error", 
                                                           f"An error occurred during login: {str(e)}"))

    def save_credentials(self, credentials):
        """Save credentials"""
        try:
            # Create config directory if it doesn't exist
            if not os.path.exists(os.path.dirname(self.config_file)):
                os.makedirs(os.path.dirname(self.config_file))
            
            config = {
                "username": credentials['username'],
                "hostname": credentials['hostname']
            }
            
            if credentials['save']:
                config["password"] = credentials['password']
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
                
            return True
        except Exception as e:
            print(f"Error saving credentials: {e}")
            messagebox.showerror("Error", f"Could not save credentials: {e}")
            return False

    def update_login_status(self, is_logged_in):
        """Update UI elements to reflect login status"""
        if is_logged_in:
            self.user_label.config(text=f"{self.username}@{self.hostname}")
            self.login_btn.config(text="Change Login")
            # Start auto-refresh if enabled
            if self.auto_refresh.get():
                self.start_auto_refresh()
        else:
            self.user_label.config(text="Not logged in")
            self.login_btn.config(text="Login")
            # Stop auto-refresh
            self.stop_auto_refresh()
    
    def disconnect(self):
        """Disconnect SSH client if connected"""
        print("Disconnecting...")
        try:
            if self.ssh_client:
                self.ssh_client.close()
                self.ssh_client = None
            print("Disconnected")
        except Exception as e:
            print(f"Error disconnecting: {e}")

    def update_refresh_interval(self, event=None):
        """Update the refresh interval based on dropdown selection"""
        selected = self.refresh_interval_var.get()
        if selected in self.refresh_intervals:
            self.refresh_interval = self.refresh_intervals[selected]
            
            # Restart auto-refresh with new interval if enabled
            if self.auto_refresh.get():
                self.stop_auto_refresh()
                self.start_auto_refresh()

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Slurm Watch - A job monitoring tool')
    parser.add_argument('-t', '--test', 
                       action='store_true',
                       help='Run in test mode with sample data')
    args = parser.parse_args()
    
    # Make sure required packages are installed
    try:
        from PIL import Image, ImageTk, ImageDraw
    except ImportError:
        messagebox.showerror(
            "Missing Dependency", 
            "PIL/Pillow is required for this application.\n"
            "Please install it using: pip install pillow"
        )
        return
    
    try:
        import paramiko
    except ImportError:
        if not args.test:  # Only show error if not in test mode
            messagebox.showerror(
                "Missing Dependency", 
                "Paramiko is required for SSH connections.\n"
                "Please install it using: pip install paramiko"
            )
            return
    
    # Add queue import
    try:
        import queue
    except ImportError:
        messagebox.showerror(
            "Missing Dependency",
            "Python queue module is required.\n"
            "This should be part of the standard library."
        )
        return
    
    root = tk.Tk()
    root.title("SWATCH - (Slurm Job Watcher)")  # Set window title
    app = HPCJobMonitor(root, test_mode=args.test)
    
    # Center the window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()