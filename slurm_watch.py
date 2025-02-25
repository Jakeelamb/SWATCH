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

# Define a custom style theme class
class DarkTheme:
    # Main colors - Updated for softer look
    BG_COLOR = "#2E2E3E"  # Lighter dark background
    SECONDARY_BG = "#3F3F53"  # Softer secondary background
    TEXT_COLOR = "#E0E0E8"  # Slightly brighter text
    ACCENT_COLOR = "#7AA2F7"  # Softer blue accent
    
    # Status colors - Softer palette
    RUNNING_COLOR = "#98D8A8"  # Softer green
    PENDING_COLOR = "#F8B98F"  # Softer orange
    COMPLETED_COLOR = "#7AA2F7"  # Softer blue
    FAILED_COLOR = "#F08BA0"  # Softer red
    
    # Title colors using status colors
    TITLE_COLORS = {
        'S': RUNNING_COLOR,
        'W': PENDING_COLOR,
        'A': COMPLETED_COLOR,
        'T': FAILED_COLOR,
        'C': ACCENT_COLOR,
        'H': TEXT_COLOR
    }
    
    # Updated fonts and dimensions
    MAIN_FONT = ("Helvetica Neue", 11)  # macOS-like font
    HEADER_FONT = ("Helvetica Neue", 12, "bold")  # For consistency
    SMALL_FONT = ("Helvetica Neue", 10)
    
    # Updated spacing
    PADDING = 8  # Tighter spacing
    CORNER_RADIUS = 6  # Softer rounding
    
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
        
    def _on_resize(self, event):
        self.update_idletasks()
        self.create_rounded_rect()
        
    def create_rounded_rect(self):
        self.delete("all")
        width, height = self.winfo_width(), self.winfo_height()
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
        
        # Configure the main treeview style with updated colors and fonts
        style.configure("Custom.Treeview", 
            font=DarkTheme.MAIN_FONT,
            background=DarkTheme.SECONDARY_BG,
            foreground=DarkTheme.TEXT_COLOR,
            fieldbackground=DarkTheme.SECONDARY_BG,
            borderwidth=0,
            rowheight=22  # Adjusted for new font
        )
        
        # Configure the header style
        style.configure("Custom.Treeview.Heading",
            font=DarkTheme.MAIN_FONT,
            background=DarkTheme.BG_COLOR,
            foreground=DarkTheme.ACCENT_COLOR,
            borderwidth=0
        )
        
        # Configure selection colors with alternating row colors
        style.map("Custom.Treeview",
            background=[
                ("selected", DarkTheme.ACCENT_COLOR),
                ("!selected", ["#353544", DarkTheme.SECONDARY_BG])
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
        self.configure('TButton', background=DarkTheme.SECONDARY_BG, foreground=DarkTheme.TEXT_COLOR)
        self.configure('TCheckbutton', background=DarkTheme.BG_COLOR, foreground=DarkTheme.TEXT_COLOR)
        self.configure('TEntry', fieldbackground=DarkTheme.SECONDARY_BG, foreground=DarkTheme.TEXT_COLOR)

class LoginDialog(simpledialog.Dialog):
    def __init__(self, parent, title=None, default_username=""):
        self.default_username = default_username
        self.bg_color = DarkTheme.BG_COLOR
        self.text_color = DarkTheme.TEXT_COLOR
        super().__init__(parent, title)
    
    def body(self, master):
        master.configure(bg=self.bg_color)
        
        # Set dialog size and position
        self.geometry(f"350x200+{self.winfo_rootx()+50}+{self.winfo_rooty()+50}")
        
        # Create frames
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
        self.hostname_entry.insert(0, "login.cluster.edu")  # Default hostname
        
        self.save_credentials = tk.BooleanVar(value=False)
        ttk.Checkbutton(content_frame, text="Remember credentials", 
                      variable=self.save_credentials).grid(
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
        self.test_mode = test_mode
        
        # Remove default title bar and window decorations
        self.root.overrideredirect(True)
        self.root.geometry("800x500")
        self.root.resizable(True, True)
        self.root.configure(bg=DarkTheme.BG_COLOR)
        
        # Create custom title bar
        self.title_bar = tk.Frame(self.root, bg=DarkTheme.SECONDARY_BG, height=30)
        self.title_bar.pack(fill=tk.X)
        
        # Add title label
        ttk.Label(
            self.title_bar,
            text="Slurm Job Watch",
            foreground=DarkTheme.TEXT_COLOR,
            background=DarkTheme.SECONDARY_BG,
            font=("JetBrains Mono", 12, "bold")
        ).pack(side=tk.LEFT, padx=10, pady=5)
        
        # Add close button
        close_btn = ttk.Button(
            self.title_bar,
            text="×",
            command=self.on_closing,
            style="TButton",
            width=2
        )
        close_btn.pack(side=tk.RIGHT, padx=5)
        
        # Bind dragging functionality
        self.title_bar.bind("<Button-1>", self.start_drag)
        self.title_bar.bind("<B1-Motion>", self.drag_window)
        
        # Apply theme
        CustomStyle()
        
        # Authentication variables
        self.username = ""
        self.password = ""
        self.hostname = ""
        self.authenticated = False
        
        # Load saved credentials if available
        self.config_dir = os.path.join(os.path.expanduser("~"), ".hpcjobmonitor")
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.load_credentials()
        
        # Create status icons
        self.status_icons = {
            "Running": create_circle_image(DarkTheme.RUNNING_COLOR),
            "Pending": create_circle_image(DarkTheme.PENDING_COLOR),
            "Completed": create_circle_image(DarkTheme.COMPLETED_COLOR),
            "Failed": create_circle_image(DarkTheme.FAILED_COLOR)
        }
        
        # Create main frame with rounded corners
        self.main_container = tk.Frame(self.root, bg=DarkTheme.BG_COLOR)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.main_frame = RoundedFrame(self.main_container, bg=DarkTheme.SECONDARY_BG)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create content frame inside the rounded canvas
        self.content_frame = tk.Frame(self.main_frame, bg=DarkTheme.SECONDARY_BG)
        self.content_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER, relwidth=0.95, relheight=0.95)
        
        # Modify header frame
        header_frame = tk.Frame(self.content_frame, bg=DarkTheme.SECONDARY_BG)
        header_frame.pack(fill=tk.X, pady=(5, 10), padx=DarkTheme.PADDING)
        
        # User status (left side)
        self.user_label = ttk.Label(
            header_frame,
            text="Not logged in",
            font=DarkTheme.SMALL_FONT,
            background=DarkTheme.SECONDARY_BG
        )
        self.user_label.pack(side=tk.LEFT)
        
        # Last updated (right side)
        self.last_updated = ttk.Label(
            header_frame,
            text="Last updated: Never",
            font=DarkTheme.SMALL_FONT,
            background=DarkTheme.SECONDARY_BG
        )
        self.last_updated.pack(side=tk.RIGHT)
        
        # Legend frame
        legend_frame = tk.Frame(self.content_frame, bg=DarkTheme.SECONDARY_BG)
        legend_frame.pack(fill=tk.X, padx=DarkTheme.PADDING, pady=(5, 10))
        
        statuses = [("Running", DarkTheme.RUNNING_COLOR), 
                   ("Pending", DarkTheme.PENDING_COLOR), 
                   ("Completed", DarkTheme.COMPLETED_COLOR), 
                   ("Failed", DarkTheme.FAILED_COLOR)]
        
        for status, color in statuses:
            status_frame = tk.Frame(legend_frame, bg=DarkTheme.SECONDARY_BG)
            status_frame.pack(side=tk.LEFT, padx=5)
            
            # Create small colored circle
            canvas = tk.Canvas(status_frame, width=12, height=12, bg=DarkTheme.SECONDARY_BG, highlightthickness=0)
            canvas.create_oval(2, 2, 10, 10, fill=color, outline="")
            canvas.pack(side=tk.LEFT, padx=(0, 3))
            
            # Status label
            ttk.Label(status_frame, text=status, background=DarkTheme.SECONDARY_BG).pack(side=tk.LEFT)
        
        # Create job list frame with scrollbar
        job_list_container = tk.Frame(self.content_frame, bg=DarkTheme.SECONDARY_BG)
        job_list_container.pack(fill=tk.BOTH, expand=True, padx=DarkTheme.PADDING)
        
        # Create treeview for jobs with custom styling
        self.tree = CustomTreeview(
            job_list_container, 
            columns=("job_id", "name", "status", "time", "nodes", "cpus", "memory"), 
            show="headings",
            height=10
        )
        
        # Configure headings
        self.tree.heading("job_id", text="JOB ID")
        self.tree.heading("name", text="NAME")
        self.tree.heading("status", text="STATUS")
        self.tree.heading("time", text="RUNTIME")
        self.tree.heading("nodes", text="NODES")
        self.tree.heading("cpus", text="CPUS")
        self.tree.heading("memory", text="MEMORY")
        
        # Configure column widths
        self.tree.column("job_id", width=80, anchor="center")
        self.tree.column("name", width=150, anchor="w")
        self.tree.column("status", width=90, anchor="center")
        self.tree.column("time", width=80, anchor="center")
        self.tree.column("nodes", width=60, anchor="center")
        self.tree.column("cpus", width=60, anchor="center")
        self.tree.column("memory", width=90, anchor="center")
        
        # Create custom scrollbar
        scrollbar_style = ttk.Style()
        scrollbar_style.configure("Custom.Vertical.TScrollbar", 
                              background=DarkTheme.BG_COLOR, 
                              troughcolor=DarkTheme.SECONDARY_BG, 
                              borderwidth=0,
                              arrowcolor=DarkTheme.TEXT_COLOR)
        
        scrollbar = ttk.Scrollbar(
            job_list_container, 
            orient="vertical", 
            command=self.tree.yview,
            style="Custom.Vertical.TScrollbar"
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack tree and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bottom control frame
        control_frame = tk.Frame(self.content_frame, bg=DarkTheme.SECONDARY_BG)
        control_frame.pack(fill=tk.X, pady=10, padx=DarkTheme.PADDING)
        
        # Refresh button
        refresh_btn = ttk.Button(control_frame, text="Refresh", command=self.refresh_jobs)
        refresh_btn.pack(side=tk.LEFT)
        
        # Login button
        self.login_btn = ttk.Button(control_frame, text="Login", command=self.show_login_dialog)
        self.login_btn.pack(side=tk.LEFT, padx=5)
        
        # Auto-refresh checkbox with updated command
        self.auto_refresh = tk.BooleanVar(value=True)
        auto_refresh_cb = ttk.Checkbutton(
            control_frame, 
            text="Auto-refresh", 
            variable=self.auto_refresh,
            command=self.toggle_auto_refresh
        )
        auto_refresh_cb.pack(side=tk.LEFT, padx=5)
        
        # Refresh interval dropdown
        ttk.Label(control_frame, text="Interval:", background=DarkTheme.SECONDARY_BG).pack(side=tk.LEFT, padx=(10, 0))
        
        self.refresh_options = {
            "5 seconds": 5,
            "30 seconds": 30,
            "1 minute": 60,
            "5 minutes": 300,
            "10 minutes": 600,
            "30 minutes": 1800
        }
        
        self.refresh_var = tk.StringVar()
        self.refresh_var.set("30 seconds")  # Default
        
        refresh_dropdown = ttk.Combobox(
            control_frame, 
            textvariable=self.refresh_var,
            values=list(self.refresh_options.keys()),
            state="readonly",
            width=10
        )
        refresh_dropdown.pack(side=tk.LEFT, padx=5)
        refresh_dropdown.bind("<<ComboboxSelected>>", self.change_refresh_interval)
        
        # Status summary
        self.status_summary = ttk.Label(
            control_frame,
            text="Running: 0 | Pending: 0 | Completed: 0",
            font=DarkTheme.SMALL_FONT,
            background=DarkTheme.SECONDARY_BG
        )
        self.status_summary.pack(side=tk.RIGHT)
        
        # Refresh interval (in seconds)
        self.refresh_interval = 30
        self.refresh_timer = None
        
        # Start auto-refresh if enabled
        self.start_auto_refresh()
        
        # Show login dialog if no saved credentials
        if not self.authenticated and not self.test_mode:
            self.root.after(500, self.show_login_dialog)
    
    def load_credentials(self):
        """Load saved credentials if available"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    
                    if 'username' in config and 'hostname' in config:
                        self.username = config['username']
                        self.hostname = config['hostname']
                        
                        # If password is saved
                        if 'password' in config:
                            self.password = config['password']  # In a real implementation, this would be decrypted
                            
                            # Test connection with saved credentials
                            if self.test_connection():
                                self.authenticated = True
                                return True
        except Exception as e:
            print(f"Error loading credentials: {e}")
        
        return False
    
    def save_credentials(self, credentials):
        """Save credentials"""
        try:
            # Create config directory if it doesn't exist
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
            
            config = {
                "username": credentials['username'],
                "hostname": credentials['hostname']
            }
            
            if credentials['save']:
                config["password"] = credentials['password']
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Error saving credentials: {e}")
            messagebox.showerror("Error", f"Could not save credentials: {e}")
    
    def show_login_dialog(self):
        """Show the login dialog"""
        dialog = LoginDialog(self.root, "HPC Login", default_username=self.username)
        if hasattr(dialog, 'result') and dialog.result:
            credentials = dialog.result
            self.username = credentials['username']
            self.password = credentials['password']
            self.hostname = credentials['hostname']
            
            # Test connection
            if self.test_connection():
                self.authenticated = True
                self.user_label.config(text=f"{self.username}@{self.hostname}")
                self.login_btn.config(text="Change Login")
                
                # Save credentials if requested
                if credentials['save']:
                    self.save_credentials(credentials)
                
                # Refresh job list
                self.refresh_jobs()
            else:
                self.authenticated = False
                messagebox.showerror("Authentication Failed", "Could not authenticate with the provided credentials.")
    
    def test_connection(self):
        """Test SSH connection with the credentials"""
        if self.test_mode:
            return True  # Always return success in test mode
        
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=self.hostname, 
                username=self.username, 
                password=self.password,
                timeout=5
            )
            client.close()
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
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
        
        try:
            # Real SSH connection code here
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=self.hostname,
                username=self.username,
                password=self.password
            )
            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode()
            client.close()
            return output
        except Exception as e:
            print(f"Error running remote command: {e}")
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
                self.show_login_dialog()
            return
        
        # Clear current items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            jobs = self.get_jobs()
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
            self.status_summary.config(text=summary)
            
            # Update timestamp
            now = datetime.now().strftime("%H:%M:%S")
            self.last_updated.config(text=f"Updated: {now}")
            
        except Exception as e:
            print(f"Error refreshing jobs: {e}")
            messagebox.showerror("Error", f"Failed to refresh jobs: {e}")
    
    def change_refresh_interval(self, event=None):
        """Change the refresh interval based on dropdown selection"""
        selected = self.refresh_var.get()
        self.refresh_interval = self.refresh_options.get(selected, 30)
        
        # Restart auto-refresh with new interval if enabled
        if self.auto_refresh.get():
            self.start_auto_refresh()
    
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
    
    root = tk.Tk()
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