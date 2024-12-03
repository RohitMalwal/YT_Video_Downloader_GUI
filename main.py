from tkinter import *
from tkinter import ttk
from tkinter.messagebox import showerror
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError
import threading
from time import sleep

def main():
    app = Application()
    app.mainloop()

class Application(Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Downloader")
        self.geometry("800x460")
        self.resizable(FALSE, FALSE)
        self.configure(bg="#f5f5f5")
        self.iconbitmap(r"images/favicon.ico")

        self.columnconfigure(0, weight=1)

        self.frame = InputForm(self)
        self.frame.grid(row=0, column=0, sticky=NSEW)

class InputForm(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(padding=20, style="Custom.TFrame")
        self.columnconfigure(0, weight=1)

        # Styles
        style = ttk.Style()
        style.configure("Custom.TFrame", background="#f5f5f5")
        style.configure("Custom.TLabel", font=("Helvetica", 14), background="#f5f5f5", foreground="#333")
        style.configure("Custom.TEntry", font=("Helvetica", 14))
        style.configure("Custom.TButton", font=("Helvetica", 14), padding=5)
        style.configure("Custom.TCombobox", font=("Helvetica", 14))

        # Title
        self.lbl = ttk.Label(self, text="YouTube Downloader", font=("Helvetica", 24, "bold"), style="Custom.TLabel")
        self.lbl.grid(row=0, column=0, sticky=NS, padx=10, pady=(10, 20), columnspan=2)

        # URL Input
        self.lbl2 = ttk.Label(self, text="Enter YouTube URL:", style="Custom.TLabel")
        self.lbl2.grid(row=1, column=0, columnspan=2, sticky=W, padx=10, pady=5)

        self.lbl3 = ttk.Label(self, text="", style="Custom.TLabel")
        self.lbl3.grid(row=6, column=0, columnspan=2, sticky=W, padx=10, pady=5)

        self.entry = ttk.Entry(self, width=50, style="Custom.TEntry")
        self.entry.grid(row=2, column=0, columnspan=2, sticky=EW, padx=10, pady=10)

        # Media Type Selection (Audio or Video)
        self.media_type_label = ttk.Label(self, text="Select Media Type:", style="Custom.TLabel")
        self.media_type_label.grid(row=3, column=0, sticky=W, padx=10, pady=5)

        self.media_type = StringVar(value="audio")
        self.media_type_menu = ttk.Combobox(self, textvariable=self.media_type, state="readonly", width=20, style="Custom.TCombobox")
        self.media_type_menu["values"] = ["audio", "video"]
        self.media_type_menu.grid(row=4, column=0, padx=10, pady=5, sticky=W)
        self.media_type_menu.bind("<<ComboboxSelected>>", self.update_quality_options)

        # Quality Selection
        self.quality_label = ttk.Label(self, text="Select Quality:", style="Custom.TLabel")
        self.quality_label.grid(row=3, column=1, sticky=W, padx=10, pady=5)

        self.quality = StringVar(value="best")
        self.quality_menu = ttk.Combobox(self, textvariable=self.quality, state="readonly", width=20, style="Custom.TCombobox")
        self.quality_menu.grid(row=4, column=1, padx=10, pady=5, sticky=W)
        self.update_quality_options()

        # Download Button
        self.download_btn = ttk.Button(self, text="Download", command=self.start_download, style="Custom.TButton")
        self.download_btn.grid(row=7, column=0, columnspan=2, pady=(20, 10), sticky=EW, padx=10)

        # Cancel Button
        self.cancel_btn = ttk.Button(self, text="Cancel", command=self.cancel_download, style="Custom.TButton")
        self.cancel_btn.grid(row=8, column=0, columnspan=2, pady=(10, 10), sticky=EW, padx=10)

        self.progress_bar = ttk.Progressbar(self, orient="horizontal", mode="determinate", length=700)
        self.progress_bar.grid(row=5, column=0, columnspan=2, pady=(20, 10), padx=10)

        # Initialize cancel event
        self.cancel_event = threading.Event()

    def update_quality_options(self, event=None):
        """Update quality options based on selected media type."""
        if self.media_type.get() == "audio":
            self.quality_menu["values"] = ["best", "192kbps", "128kbps"]
            self.quality.set("best")
        elif self.media_type.get() == "video":
            self.quality_menu["values"] = ["best", "1080p", "720p", "480p", "360p"]
            self.quality.set("best")

    def start_download(self):
        url = self.entry.get().strip()
        if not url:
            showerror("Error", "Please enter a valid YouTube URL.")
            return
        else:
            media_type = self.media_type.get()
            quality = self.quality.get()
            self.lbl3.config(text="Started downloading..., please wait until download completed.")

            if url:
                # Reset progress bar and cancel event
                self.progress_bar["value"] = 0
                self.cancel_event.clear()
                # Start download in a separate thread
                thread = threading.Thread(target=self.download_media, args=(url, media_type, quality))
                thread.start()

    def cancel_download(self):
        """Cancel the ongoing download by setting the cancel event."""
        self.cancel_event.set()  # Signal to cancel the download
        print("\nDownload canceled!")
        self.lbl3.config(text="Download canceled.")

    def progress_hook(self, d):
        """Update the progress bar and check for cancellation."""
        if self.cancel_event.is_set():
            raise Exception("Download canceled by user.")  # Abort download
        
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            if total > 0:
                percentage = (downloaded / total) * 100
                self.after(0, self.update_progress, percentage)
        elif d['status'] == 'finished':
            self.after(0, self.update_progress, 100)
            
    def update_progress(self, value):
        """Update the progress bar's value safely in the main thread."""
        self.progress_bar["value"] = value

    def download_media(self, url, media_type, quality):
        """Download media based on user selection."""
        try:
            # Configure options based on media type
            ydl_opts = {
                'outtmpl': '%(title)s.%(ext)s',
                'progress_hooks': [self.progress_hook],
            }

            if media_type == "audio":
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': quality.split('kbps')[0] if 'kbps' in quality else '192',
                    }],
                })
            else:  # Video
                if quality == "best":
                    format_option = 'bestvideo+bestaudio/best'
                else:
                    # Extract height from quality (e.g., '1080p' -> 1080)
                    height = int(quality.replace('p', ''))
                    format_option = f'bestvideo[height<={height}]+bestaudio/best'

                ydl_opts.update({
                    'format': format_option,
                    'merge_output_format': 'mp4',  # Ensures video and audio are merged into a single MP4 file
                })

            try:
                with YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            except Exception as e:
                if str(e) == "Download canceled by user.":
                    print("\nDownload was canceled by the user.")
                    return  # Exit gracefully
                elif str(e) == "Download completed.":
                    print("\nDownload is completed.")
                    return  # Exit gracefully
                else:
                    raise  # Re-raise other exception
            finally:
                if not self.cancel_event.is_set():
                    self.after(0, self.lbl3.config, {"text": "Download complete!"})
                else:
                    self.after(0, self.lbl3.config, {"text": "Download canceled."})

        except DownloadError as e:
            self.lbl3.config(text="ERROR!")
            showerror(
                title="ERROR",
                message=f"Video failed to download: {e}"
            )

if __name__ == "__main__":
    main()
