import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import asyncio
import threading
import json
from datetime import datetime
from pathlib import Path
from manga_grabber_enhanced import MangaGrabberEnhanced, FileInfo
from manga_utils import MangaUtils

class MangaGrabberGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Manga Grabber - Telegram")
        self.root.geometry("1000x700")
        
        # Initialize variables
        self.grabber = None
        self.current_files = []
        self.search_running = False
        
        # Create GUI elements
        self.create_widgets()
        
        # Event loop for async operations
        self.loop = None
        self.thread = None
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configuration frame
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # API ID
        ttk.Label(config_frame, text="API ID:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.api_id_var = tk.StringVar()
        ttk.Entry(config_frame, textvariable=self.api_id_var, width=20).grid(row=0, column=1, padx=(0, 20))
        
        # API Hash
        ttk.Label(config_frame, text="API Hash:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.api_hash_var = tk.StringVar()
        ttk.Entry(config_frame, textvariable=self.api_hash_var, width=30).grid(row=0, column=3, padx=(0, 20))
        
        # Phone
        ttk.Label(config_frame, text="Phone:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.phone_var = tk.StringVar()
        ttk.Entry(config_frame, textvariable=self.phone_var, width=20).grid(row=1, column=1, padx=(0, 20))
        
        # Connect button
        self.connect_btn = ttk.Button(config_frame, text="Connect", command=self.connect_to_telegram)
        self.connect_btn.grid(row=1, column=2, padx=(0, 10))
        
        # Load/Save config buttons
        ttk.Button(config_frame, text="Load Config", command=self.load_config).grid(row=1, column=3, padx=(0, 5))
        ttk.Button(config_frame, text="Save Config", command=self.save_config).grid(row=1, column=4)
        
        # Search frame
        search_frame = ttk.LabelFrame(main_frame, text="Search", padding="10")
        search_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Channel
        ttk.Label(search_frame, text="Channel:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.channel_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.channel_var, width=30).grid(row=0, column=1, padx=(0, 20))
        
        # Search term
        ttk.Label(search_frame, text="Search Term:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_var, width=30).grid(row=0, column=3, padx=(0, 20))
        
        # Search button
        self.search_btn = ttk.Button(search_frame, text="Search", command=self.start_search)
        self.search_btn.grid(row=0, column=4, padx=(0, 10))
        
        # Progress bar
        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(search_frame, textvariable=self.progress_var).grid(row=1, column=0, columnspan=5, sticky=tk.W, pady=(10, 0))
        
        self.progress_bar = ttk.Progressbar(search_frame, mode='indeterminate')
        self.progress_bar.grid(row=2, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        results_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Treeview for results
        columns = ('filename', 'size', 'type', 'date')
        self.tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=15)
        
        # Define headings
        self.tree.heading('filename', text='Filename')
        self.tree.heading('size', text='Size')
        self.tree.heading('type', text='Type')
        self.tree.heading('date', text='Date')
        
        # Configure column widths
        self.tree.column('filename', width=400)
        self.tree.column('size', width=100)
        self.tree.column('type', width=100)
        self.tree.column('date', width=150)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))\n        
        # Actions frame
        actions_frame = ttk.LabelFrame(main_frame, text="Actions", padding="10")
        actions_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Download buttons
        ttk.Button(actions_frame, text="Download Selected", command=self.download_selected).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(actions_frame, text="Download All", command=self.download_all).grid(row=0, column=1, padx=(0, 10))
        
        # Export buttons
        ttk.Button(actions_frame, text="Export JSON", command=self.export_json).grid(row=0, column=2, padx=(0, 10))
        ttk.Button(actions_frame, text="Export CSV", command=self.export_csv).grid(row=0, column=3, padx=(0, 10))
        
        # Statistics
        self.stats_var = tk.StringVar(value="No search performed yet")
        ttk.Label(actions_frame, textvariable=self.stats_var).grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(10, 0))
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Load saved config
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        try:
            with open('telegram_config.json', 'r') as f:
                config = json.load(f)
                self.api_id_var.set(str(config.get('api_id', '')))
                self.api_hash_var.set(config.get('api_hash', ''))
                self.phone_var.set(config.get('phone_number', ''))
        except FileNotFoundError:
            pass
    
    def save_config(self):
        """Save configuration to file"""
        try:
            api_id = int(self.api_id_var.get()) if self.api_id_var.get() else None
        except ValueError:
            messagebox.showerror("Error", "Invalid API ID")
            return
        
        config = {
            'api_id': api_id,
            'api_hash': self.api_hash_var.get(),
            'phone_number': self.phone_var.get()
        }
        
        with open('telegram_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        messagebox.showinfo("Success", "Configuration saved!")
    
    def connect_to_telegram(self):
        """Connect to Telegram"""
        if not all([self.api_id_var.get(), self.api_hash_var.get(), self.phone_var.get()]):
            messagebox.showerror("Error", "Please fill in all configuration fields")
            return
        
        try:
            api_id = int(self.api_id_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid API ID")
            return
        
        self.progress_var.set("Connecting to Telegram...")
        self.progress_bar.start()
        
        # Run connection in separate thread
        thread = threading.Thread(target=self._connect_async, args=(api_id, self.api_hash_var.get(), self.phone_var.get()))
        thread.daemon = True
        thread.start()
    
    def _connect_async(self, api_id, api_hash, phone):
        """Async connection to Telegram"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            self.grabber = MangaGrabberEnhanced(api_id, api_hash, phone, headless=True)
            loop.run_until_complete(self.grabber.start())
            
            self.root.after(0, self._connection_success)
        except Exception as e:
            self.root.after(0, self._connection_error, str(e))
        finally:
            loop.close()
    
    def _connection_success(self):
        """Handle successful connection"""
        self.progress_bar.stop()
        self.progress_var.set("Connected to Telegram!")
        self.connect_btn.config(text="Connected", state="disabled")
        messagebox.showinfo("Success", "Connected to Telegram successfully!")
    
    def _connection_error(self, error):
        """Handle connection error"""
        self.progress_bar.stop()
        self.progress_var.set("Connection failed")
        messagebox.showerror("Error", f"Failed to connect: {error}")
    
    def start_search(self):
        """Start searching for files"""
        if not self.grabber:
            messagebox.showerror("Error", "Please connect to Telegram first")
            return
        
        if not self.channel_var.get() or not self.search_var.get():
            messagebox.showerror("Error", "Please enter channel and search term")
            return
        
        if self.search_running:
            messagebox.showwarning("Warning", "Search is already running")
            return
        
        self.search_running = True
        self.search_btn.config(text="Searching...", state="disabled")
        self.progress_var.set("Searching for files...")
        self.progress_bar.start()
        
        # Clear previous results
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Start search in separate thread
        channel = self.channel_var.get()
        if not channel.startswith('@'):
            channel = '@' + channel
        
        thread = threading.Thread(target=self._search_async, args=(channel, self.search_var.get()))
        thread.daemon = True
        thread.start()
    
    def _search_async(self, channel, search_term):
        """Async search for files"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            files = loop.run_until_complete(self.grabber.search_files(channel, search_term))
            self.current_files = files
            self.root.after(0, self._search_success, files)
        except Exception as e:
            self.root.after(0, self._search_error, str(e))
        finally:
            loop.close()
    
    def _search_success(self, files):
        """Handle successful search"""
        self.progress_bar.stop()
        self.search_running = False
        self.search_btn.config(text="Search", state="normal")
        
        # Populate treeview
        for file in files:
            self.tree.insert('', 'end', values=(
                file.filename,
                MangaUtils.format_size(file.size),
                file.mime_type.split('/')[-1].upper(),
                file.date.strftime('%Y-%m-%d %H:%M')
            ))
        
        # Update statistics
        if self.grabber.stats:
            stats_text = f"Found {len(files)} files in {self.grabber.stats['search_time']:.2f}s"
            stats_text += f" | Scanned {self.grabber.stats['messages_scanned']} messages"
            stats_text += f" | Cache hits: {self.grabber.stats['cache_hits']}"
            self.stats_var.set(stats_text)
        
        self.progress_var.set(f"Found {len(files)} files")
        
        if not files:
            messagebox.showinfo("Info", "No files found matching your search")
    
    def _search_error(self, error):
        """Handle search error"""
        self.progress_bar.stop()
        self.search_running = False
        self.search_btn.config(text="Search", state="normal")
        self.progress_var.set("Search failed")
        messagebox.showerror("Error", f"Search failed: {error}")
    
    def download_selected(self):
        """Download selected files"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select files to download")
            return
        
        indices = [self.tree.index(item) for item in selection]
        self._download_files(indices)
    
    def download_all(self):
        """Download all files"""
        if not self.current_files:
            messagebox.showwarning("Warning", "No files to download")
            return
        
        self._download_files(None)
    
    def _download_files(self, indices):
        """Download files with progress"""
        if not self.grabber:
            messagebox.showerror("Error", "Please connect to Telegram first")
            return
        
        # Ask for download directory
        download_dir = filedialog.askdirectory(title="Select download directory")
        if not download_dir:
            return
        
        self.grabber.download_folder = Path(download_dir)
        
        self.progress_var.set("Downloading files...")
        self.progress_bar.start()
        
        # Start download in separate thread
        thread = threading.Thread(target=self._download_async, args=(indices,))
        thread.daemon = True
        thread.start()
    
    def _download_async(self, indices):
        """Async download files"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            files_to_download = self.current_files
            if indices is not None:
                files_to_download = [self.current_files[i] for i in indices]
            
            downloaded = loop.run_until_complete(self.grabber.download_multiple(files_to_download))
            self.root.after(0, self._download_success, len(downloaded))
        except Exception as e:
            self.root.after(0, self._download_error, str(e))
        finally:
            loop.close()
    
    def _download_success(self, count):
        """Handle successful download"""
        self.progress_bar.stop()
        self.progress_var.set(f"Downloaded {count} files")
        messagebox.showinfo("Success", f"Downloaded {count} files successfully!")
    
    def _download_error(self, error):
        """Handle download error"""
        self.progress_bar.stop()
        self.progress_var.set("Download failed")
        messagebox.showerror("Error", f"Download failed: {error}")
    
    def export_json(self):
        """Export results to JSON"""
        if not self.current_files:
            messagebox.showwarning("Warning", "No files to export")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            self._export_async('json', filename)
    
    def export_csv(self):
        """Export results to CSV"""
        if not self.current_files:
            messagebox.showwarning("Warning", "No files to export")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            self._export_async('csv', filename)
    
    def _export_async(self, format_type, filename):
        """Async export files"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self.grabber.export_results(
                self.current_files, format_type, Path(filename).name
            ))
            self.root.after(0, lambda: messagebox.showinfo("Success", f"Exported to {filename}"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Export failed: {str(e)}"))
        finally:
            loop.close()

def main():
    root = tk.Tk()
    app = MangaGrabberGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
