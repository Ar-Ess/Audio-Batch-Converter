
import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

TO_PIPE = r"\\.\pipe\ToSrvPipe"
FROM_PIPE = r"\\.\pipe\FromSrvPipe"

OUTPUT_FORMATS = {
    "MP3": ".mp3",
    "WAV": ".wav",
    "FLAC": ".flac",
    "OGG": ".ogg",
    "AIFF": ".aiff",
    "M4A": ".m4a",
    "WMA": ".wma",
}

# Input support for this version.
INPUT_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".flac",
    ".ogg",
    ".aiff",
    ".aif",
    ".m4a",
    ".wma",
    ".aac",
    ".opus",
    ".mp4",
    ".m4b",
    ".ape",
    ".wv",
    ".amr",
    ".ac3",
}

def send_command(to_pipe, from_pipe, command):
    """Send one command and read Audacity's response."""
    to_pipe.write(command + "\n")
    to_pipe.flush()

    response = []

    while True:
        line = from_pipe.readline()

        if not line:
            raise RuntimeError(
                "Audacity closed the scripting pipe before responding."
            )

        response.append(line)

        if "BatchCommand finished:" in line:
            break

    result = "".join(response)
    print(result, end="")
    return result


def quote_path(path):
    """Format a Windows path for an Audacity scripting command."""
    return os.path.abspath(path).replace("\\", "/").replace('"', '\\"')


def unique_output_path(path):
    """Return a non-conflicting filename, e.g. song (1).mp3."""
    if not os.path.exists(path):
        return path

    folder = os.path.dirname(path)
    filename = os.path.basename(path)
    stem, extension = os.path.splitext(filename)
    number = 1

    while True:
        candidate = os.path.join(
            folder, f"{stem} ({number}){extension}"
        )
        if not os.path.exists(candidate):
            return candidate
        number += 1


class AudioConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Batch Converter")
        self.root.geometry("760x800")
        self.root.minsize(650, 570)

        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.output_format = tk.StringVar(value="MP3") # MP3 - WAV - FLAC - OGG - AIFF - M4A - WMA
        self.export_channels = tk.StringVar(value="Stereo") # Mono - Stereo
        
        # Format Dependent
        self.wav_sample_rate = tk.StringVar(value="Same as source")
        self.aiff_sample_rate = tk.StringVar(value="Same as source")
        
        self.mp3_bitrate_mode = tk.StringVar(value="CBR") # CBR - ABR - VBR - Preset
        self.mp3_bitrate = tk.StringVar(value="192")
        self.mp3_quality = tk.IntVar(value=2) 
        
        self.wav_encoding = tk.StringVar(value="16-bit PCM") # 16-bit PCM - 24-bit PCM - 32-bit PCM, same for AIFF
        self.aiff_encoding = tk.StringVar(value="16-bit PCM") # 16-bit PCM - 24-bit PCM - 32-bit PCM, same for AIFF
        
        self.flac_bit_depth = tk.StringVar(value="16-bit") # 16-bit - 24-bit
        self.flac_level = tk.IntVar(value=5) # 0 (fastest) to 8 (best)

        self.ogg_quality = tk.IntVar(value=50) # From 0 to 100

        self.m4a_bitrate = tk.IntVar(value=256)
        self.wma_bitrate = tk.IntVar(value="192")
        
        # Others
        self.include_subfolders = tk.BooleanVar(value=True)
        self.keep_structure = tk.BooleanVar(value=True)
        self.new_filenames = tk.BooleanVar(value=False)
        self.filename_template = tk.StringVar(value="{name}")
        self.overwrite_files = tk.BooleanVar(value=True)
        self.skip_same_extension = tk.BooleanVar(value=False)

        self.is_exporting = False
        self.cancel_requested = False
        
        self.build_gui()
        
        self.root.protocol("WM_DELETE_WINDOW", self.close_application)

    def build_gui(self):
        main = ttk.Frame(self.root, padding=20)
        main.pack(fill="both", expand=True)

        ttk.Label(
            main,
            text="Audio Batch Converter",
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w", pady=(0, 18))

        # Input folder
        ttk.Label(main, text="Input Folder:").pack(anchor="w")

        input_row = ttk.Frame(main)
        input_row.pack(fill="x", pady=(5, 14))

        ttk.Entry(
            input_row,
            textvariable=self.input_folder,
        ).pack(side="left", fill="x", expand=True)

        self.input_browse_button = ttk.Button(
            input_row,
            text="Browse...",
            command=self.browse_input_folder,
        )
        self.input_browse_button.pack(side="left", padx=(8, 0))
        
        # Output folder
        ttk.Label(main, text="Output Folder:").pack(anchor="w")

        output_row = ttk.Frame(main)
        output_row.pack(fill="x", pady=(5, 14))

        ttk.Entry(
            output_row,
            textvariable=self.output_folder,
        ).pack(side="left", fill="x", expand=True)

        self.output_browse_button = ttk.Button(
            output_row,
            text="Browse...",
            command=self.browse_output_folder,
        )
        self.output_browse_button.pack(side="left", padx=(8, 0))
        
        self.output_reset_button = ttk.Button(
            output_row,
            text="Reset",
            command=self.reset_output_folder,
        )
        self.output_reset_button.pack(side="left", padx=(8, 0))

        # Options
        options = ttk.LabelFrame(main, text="Options", padding=12)
        options.pack(fill="x", pady=(0, 14))

        ttk.Checkbutton(
            options,
            text="Include files in subfolders",
            variable=self.include_subfolders,
        ).pack(anchor="w", pady=3)
        
        ttk.Checkbutton(
            options,
            text="Keep folder structure",
            variable=self.keep_structure,
        ).pack(anchor="w", pady=3)

        self.new_filenames_check = ttk.Checkbutton(
            options,
            text="Set new filenames",
            variable=self.new_filenames,
            command=self.update_filename_template_state,
        )
        self.new_filenames_check.pack(anchor="w", pady=1)

        # Hidden unless custom filenames are enabled.
        self.filename_template_frame = ttk.Frame(options)
        
        template_row = ttk.Frame(self.filename_template_frame)
        template_row.pack(anchor="w", fill="x", padx=(20, 0))

        ttk.Label(
            self.filename_template_frame,
            text="Filename template:",
        ).pack(side="left", padx=(0, 5))

        ttk.Entry(
            self.filename_template_frame,
            textvariable=self.filename_template,
            width=56,
        ).pack(side="left")
        
        # Hint explaining the available placeholders.
        ttk.Label(
            self.filename_template_frame,
            text="{name} = original filename "
                 "{parent} = source folder   "
                 "{id} = batch number",
            wraplength=130,
            justify="left",
            font=("TkDefaultFont", 8),
        ).pack(anchor="w", padx=(20, 0), pady=(1, 2))
        
        # Apply the initial visibility.
        self.update_filename_template_state()

        ttk.Checkbutton(
            options,
            text="Overwrite existing output files",
            variable=self.overwrite_files,
        ).pack(anchor="w", pady=1)
        
        ttk.Checkbutton(
            options,
            text="Skip files with the same extension as output",
            variable=self.skip_same_extension,
        ).pack(anchor="w", pady=3)

        output_row = ttk.Frame(options)
        output_row.pack(fill="x", pady=(5, 0))

        # Format selector
        ttk.Label(main, text="Output Format:").pack(anchor="w")

        self.format_dropdown = ttk.Combobox(
            main,
            textvariable=self.output_format,
            values=list(OUTPUT_FORMATS.keys()),
            state="readonly",
        )
        self.format_dropdown.pack(fill="x", pady=(5, 14))
        self.format_dropdown.bind(
            "<<ComboboxSelected>>",
            self.on_format_changed,
        )
        
        # Format-specific settings panel
        self.format_options_frame = ttk.LabelFrame(
            main,
            text="Format Settings",
            padding=12,
        )
        self.format_options_frame.pack(
            fill="x",
            pady=(0, 14),
        )

        self.show_format_options()

        # Action buttons
        button_row = ttk.Frame(main)
        button_row.pack(fill="x", pady=(0, 14))

        self.export_button = ttk.Button(
            button_row,
            text="Export",
            command=self.export_files,
        )
        self.export_button.pack(side="left", fill="x", expand=True)

        self.reset_button = ttk.Button(
            button_row,
            text="Clear / Reset",
            command=self.reset_window,
        )
        self.reset_button.pack(side="left", fill="x", expand=True, padx=(8, 0))

        self.close_button = ttk.Button(
            button_row,
            text="Close",
            command=self.close_application,
        )
        self.close_button.pack(side="left", fill="x", expand=True, padx=(8, 0))
        
        self.cancel_button = ttk.Button(
            button_row,
            text="Cancel Batch",
            command=self.cancel_batch,
            state="disabled",
        )
        self.cancel_button.pack(side="left", fill="x", expand=True, padx=(8, 0))
        
        # Batch progress
        progress_frame = ttk.Frame(main)
        progress_frame.pack(fill="x", pady=(0, 10))
        
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            orient="horizontal",
            mode="determinate",
            maximum=100,
            variable=self.progress_var,
        )
        self.progress_bar.pack(fill="x", pady=(4, 0))
        
        # Results
        results_frame = ttk.Frame(main)
        results_frame.pack(fill="both", expand=True, pady=(5, 0))

        self.results = tk.Text(
            results_frame,
            height=10,
            wrap="word",
            state="disabled",
            font=("Consolas", 9),
        )
        scrollbar = ttk.Scrollbar(
            results_frame,
            orient="vertical",
            command=self.results.yview,
        )
        self.results.configure(yscrollcommand=scrollbar.set)

        self.results.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.log("Ready. Select an input folder to begin.")

    def log(self, text):
        self.results.configure(state="normal")
        self.results.insert("end", text + "\n")
        self.results.see("end")
        self.results.configure(state="disabled")
        self.root.update()
    
    def log_audacity_response(self, operation, response):
        """Log Audacity's response when an operation fails."""
        self.log(f"  Audacity response ({operation}):")

        if not response or not response.strip():
            self.log("    No response text received.")
            return

        for line in response.strip().splitlines():
            self.log(f"    {line}")
    
    def clear_results(self):
        self.results.configure(state="normal")
        self.results.delete("1.0", "end")
        self.results.configure(state="disabled")

    def browse_input_folder(self):
        folder = filedialog.askdirectory(
            parent=self.root,
            title="Select input folder",
        )
        if folder:
            self.input_folder.set(folder)
            self.log(f"Folder: {folder}")
            self.output_folder.set(folder)

    def browse_output_folder(self):
        folder = filedialog.askdirectory(
            parent=self.root,
            title="Select output folder",
        )
        if folder:
            self.output_folder.set(folder)
            self.log(f"Output folder: {folder}")

    def update_filename_template_state(self):
        """Show the template only when custom filenames are enabled."""
        if self.new_filenames.get():
            if not self.filename_template_frame.winfo_manager():
                self.filename_template_frame.pack(
                    after=self.new_filenames_check,
                    anchor="w",
                    pady=(0, 2),
                )
        else:
            self.filename_template_frame.pack_forget()
    
    def show_format_options(self):
        """Display settings appropriate for the selected output format."""

        for widget in self.format_options_frame.winfo_children():
            widget.destroy()

        fmt = self.output_format.get()

        # Channel selector for MP3 and WAV.
        if fmt in ("MP3", "WAV", "FLAC", "OGG", "AIFF", "M4A", "WMA"):
            ttk.Label(
                self.format_options_frame,
                text="Channels:",
            ).grid(row=0, column=0, sticky="w", padx=(0, 12), pady=4)

            ttk.Combobox(
                self.format_options_frame,
                textvariable=self.export_channels,
                values=["Mono", "Stereo"],
                state="readonly",
                width=16,
            ).grid(row=0, column=1, sticky="w", pady=4)

        if fmt == "WAV":
            ttk.Label(
                self.format_options_frame,
                text="Encoding:",
            ).grid(row=1, column=0, sticky="w", padx=(0, 12), pady=4)

            ttk.Combobox(
                self.format_options_frame,
                textvariable=self.wav_encoding,
                values=["16-bit PCM", "24-bit PCM", "32-bit PCM"],
                state="readonly",
                width=16,
            ).grid(row=1, column=1, sticky="w", pady=4)

            ttk.Label(
                self.format_options_frame,
                text="Sample Rate:",
            ).grid(row=2, column=0, sticky="w", padx=(0, 12), pady=4)

            ttk.Combobox(
                self.format_options_frame,
                textvariable=self.wav_sample_rate,
                values=[
                    "Same as source",
                    "8000 Hz",
                    "11025 Hz",
                    "16000 Hz",
                    "22050 Hz",
                    "32000 Hz",
                    "44100 Hz",
                    "48000 Hz",
                    "88200 Hz",
                    "96000 Hz",
                    "176400 Hz",
                    "192000 Hz",
                ],
                state="readonly",
                width=16,
            ).grid(row=2, column=1, sticky="w", pady=4)

        elif fmt == "MP3":
            ttk.Label(
                self.format_options_frame,
                text="Bitrate Mode:",
            ).grid(row=1, column=0, sticky="w", padx=(0, 12), pady=4)

            mode_dropdown = ttk.Combobox(
                self.format_options_frame,
                textvariable=self.mp3_bitrate_mode,
                values=["CBR", "ABR", "VBR", "Preset"],
                state="readonly",
                width=16,
            )
            mode_dropdown.grid(row=1, column=1, sticky="w", pady=4)

            ttk.Label(
                self.format_options_frame,
                text="Bitrate / Quality:",
            ).grid(row=2, column=0, sticky="w", padx=(0, 12), pady=4)

            self.mp3_value_dropdown = ttk.Combobox(
                self.format_options_frame,
                state="readonly",
                width=16,
            )
            self.mp3_value_dropdown.grid(
                row=2, column=1, sticky="w", pady=4
            )

            def update_mp3_options(event=None):
                mode = self.mp3_bitrate_mode.get()

                if mode in ("CBR", "ABR"):
                    self.mp3_value_dropdown.configure(
                        textvariable=self.mp3_bitrate,
                        values=[
                            "24", "32", "40", "48", "56","64",
                            "80", "96", "112", "128", "144",
                            "160", "192", "224", "256", "320",
                        ],
                    )
                    self.mp3_value_dropdown.set(self.mp3_bitrate.get())

                elif mode == "VBR":
                    vbr_options = [
                        "Best Quality (220–260 kbps)",
                        "200–250 kbps",
                        "170–210 kbps",
                        "155–195 kbps",
                        "145–185 kbps",
                        "110–150 kbps",
                        "95–135 kbps",
                        "80–120 kbps",
                        "65–105 kbps",
                        "Smaller Files (45–85 kbps)",
                    ]
                    self.mp3_value_dropdown.configure(
                        textvariable="",
                        values=vbr_options,
                    )
                    index = min(max(self.mp3_quality.get(), 0), 9)
                    self.mp3_value_dropdown.current(index)

                else:  # Preset
                    preset_options = [
                        "Excessive (320 kbps)",
                        "Extreme (220–260 kbps)",
                        "Standard (170–210 kbps)",
                        "Medium (145–185 kbps)",
                    ]
                    self.mp3_value_dropdown.configure(
                        textvariable="",
                        values=preset_options,
                    )
                    index = min(max(self.mp3_quality.get(), 0), 3)
                    self.mp3_value_dropdown.current(index)

            def save_mp3_selection(event=None):
                mode = self.mp3_bitrate_mode.get()
                selected_index = self.mp3_value_dropdown.current()

                if selected_index < 0:
                    return

                if mode in ("CBR", "ABR"):
                    self.mp3_bitrate.set(
                        self.mp3_value_dropdown.get()
                    )
                else:
                    self.mp3_quality.set(selected_index)

            mode_dropdown.bind(
                "<<ComboboxSelected>>", update_mp3_options
            )
            self.mp3_value_dropdown.bind(
                "<<ComboboxSelected>>", save_mp3_selection
            )

            update_mp3_options()

        elif fmt == "FLAC":
            ttk.Label(
                self.format_options_frame,
                text="Bit Depth:",
            ).grid(row=1, column=0, sticky="w", padx=(0, 12), pady=4)

            ttk.Combobox(
                self.format_options_frame,
                textvariable=self.flac_bit_depth,
                values=["16-bit", "24-bit"],
                state="readonly",
                width=16,
            ).grid(row=1, column=1, sticky="w", pady=4)
            
            self.create_int_slider(
                label_text="Compression Level:",
                variable=self.flac_level,
                minimum=0,
                maximum=8,
                row=2,
            )
        
        elif fmt == "OGG":
            
            self.create_int_slider(
                label_text="Quality (0–100):",
                variable=self.ogg_quality,
                minimum=0,
                maximum=100,
                row=1,
            )
        
        elif fmt == "WMA":
            self.create_int_slider(
                label_text="Bitrate (24–320 kbps):",
                variable=self.wma_bitrate,
                minimum=24,
                maximum=320,
                row=1,
            )
        
        elif fmt == "AIFF":
            ttk.Label(
                self.format_options_frame,
                text="Encoding:",
            ).grid(row=1, column=0, sticky="w", padx=(0, 12), pady=4)

            ttk.Combobox(
                self.format_options_frame,
                textvariable=self.aiff_encoding,
                values=["16-bit PCM", "24-bit PCM", "32-bit PCM"],
                state="readonly",
                width=16,
            ).grid(row=1, column=1, sticky="w", pady=4)

            tk.Label(
                self.format_options_frame,
                text="Sample Rate:",
            ).grid(row=2, column=0, sticky="w", padx=(0, 12), pady=4)

            ttk.Combobox(
                self.format_options_frame,
                textvariable=self.aiff_sample_rate,
                values=[
                    "Same as source",
                    "8000 Hz",
                    "11025 Hz",
                    "16000 Hz",
                    "22050 Hz",
                    "32000 Hz",
                    "44100 Hz",
                    "48000 Hz",
                    "88200 Hz",
                    "96000 Hz",
                    "176400 Hz",
                    "192000 Hz",
                ],
                state="readonly",
                width=16,
            ).grid(row=2, column=1, sticky="w", pady=4)
        
        elif fmt == "M4A":
            self.create_int_slider(
                label_text="Bitrate (98–320 kbps):",
                variable=self.m4a_bitrate,
                minimum=98,
                maximum=320,
                row=1,
            )
        
        else:
            if fmt not in ("WAV", "MP3"):
                ttk.Label(
                    self.format_options_frame,
                    text=f"{fmt} settings will be added in a later step.",
                ).grid(row=0, column=0, sticky="w", pady=4)

    def create_int_slider(self, label_text, variable, minimum, maximum, row):
        """Add a slider and Spinbox synchronized through a shared variable."""

        ttk.Label(
            self.format_options_frame,
            text=label_text,
        ).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=4)

        def on_change(value):
            v = round(float(value))
            variable.set(v)
            slider.configure(value=v)

        slider = ttk.Scale(
            self.format_options_frame,
            from_=minimum,
            to=maximum,
            orient="horizontal",
            command=on_change,
        )
        slider.set(variable.get())
        slider.grid(row=row, column=1, sticky="ew", pady=4)

        spinbox = ttk.Spinbox(
            self.format_options_frame,
            from_=minimum,
            to=maximum,
            increment=1,
            textvariable=variable,
            width=4,
            command=lambda: on_change(variable.get()),
        )
        spinbox.grid(row=row, column=2, sticky="w", padx=(8, 0), pady=4)

    def on_format_changed(self, _event=None):
        fmt = self.output_format.get()
        self.show_format_options()
        self.log(f"Output format selected: {fmt}.")

    def set_controls_enabled(self, enabled):
        self.export_button.configure(
            state="normal" if enabled else "disabled"
        )
        self.input_browse_button.configure(
            state="normal" if enabled else "disabled"
        )
        self.format_dropdown.configure(
            state="readonly" if enabled else "disabled"
        )
        self.cancel_button.configure(
            state="disabled" if enabled else "normal"
        )

    def update_progress(self, completed, total):
        """Update the progress bar and log batch progress."""

        self.progress_bar.configure(maximum=max(total, 1))
        self.progress_var.set(completed)

        self.log(f"Progress: {completed}/{total} files processed\n")

    def find_input_files(self, folder):
        found = []

        if self.include_subfolders.get():
            for current_folder, _dirs, filenames in os.walk(folder):
                for filename in filenames:
                    extension = os.path.splitext(filename)[1].lower()
                    if extension in INPUT_EXTENSIONS:
                        found.append(
                            os.path.join(current_folder, filename)
                        )
        else:
            for filename in os.listdir(folder):
                path = os.path.join(folder, filename)

                if not os.path.isfile(path):
                    continue

                extension = os.path.splitext(filename)[1].lower()
                if extension in INPUT_EXTENSIONS:
                    found.append(path)

        found.sort(key=str.lower)
        return found

    def get_output_path(self, input_path, input_root, batch_id=None):
        """Build an output path using the selected filename options."""
        extension = OUTPUT_FORMATS[self.output_format.get()]
        stem = os.path.splitext(os.path.basename(input_path))[0]

        if not self.new_filenames.get():
            filename_stem = stem
        else:
            template = self.filename_template.get().strip()
            parent = (
                os.path.basename(os.path.dirname(os.path.abspath(input_path)))
                or "root"
            )
            batch_number = 1 if batch_id is None else batch_id

            filename_stem = (
                template
                .replace("{name}", stem)
                .replace("{parent}", parent)
                .replace("{id}", f"{batch_number:03d}")
            )

        filename = filename_stem + extension
        destination_root = self.output_folder.get().strip()

        if self.keep_structure.get():
            relative_folder = os.path.relpath(
                os.path.dirname(input_path),
                input_root,
            )
            if relative_folder == ".":
                output_dir = destination_root
            else:
                output_dir = os.path.join(destination_root, relative_folder)
        else:
            output_dir = destination_root

        os.makedirs(output_dir, exist_ok=True)
        return os.path.join(output_dir, filename)
    
    def find_available_output(self, input_path, input_root, reserved_paths, batch_id):
        """Find and reserve an output filename according to overwrite settings."""

        output_path = self.get_output_path(input_path, input_root, batch_id)

        base, extension = os.path.splitext(output_path)
        candidate_path = output_path
        suffix = 1

        while True:
            normalized_path = os.path.normcase(
                os.path.abspath(candidate_path)
            )

            # Another input has already claimed this path.
            if normalized_path in reserved_paths:
                candidate_path = f"{base} ({suffix}){extension}"
                suffix += 1
                continue

            # Do not overwrite existing files when overwrite is disabled.
            if (
                os.path.exists(candidate_path)
                and not self.overwrite_files.get()
            ):
                candidate_path = f"{base} ({suffix}){extension}"
                suffix += 1
                continue

            reserved_paths.add(normalized_path)
            return candidate_path
    
    def validate_filename_template(self):
        """Validate the custom filename template before starting a batch."""
        if not self.new_filenames.get():
            return True

        template = self.filename_template.get().strip()

        if not template:
            messagebox.showwarning(
                "Filename Template Required",
                "Enter a filename template before starting the batch.",
                parent=self.root,
            )
            return False

        # Remove the supported placeholders before checking for unknown ones.
        remaining = template
        for placeholder in ("{name}", "{parent}", "{id}"):
            remaining = remaining.replace(placeholder, "")

        if "{" in remaining or "}" in remaining:
            messagebox.showwarning(
                "Invalid Filename Template",
                "Supported placeholders are {name}, {parent}, and {id}.",
                parent=self.root,
            )
            return False

        # Prevent characters that are invalid in Windows filenames.
        if any(char in template for char in '<>:"/\\|?*'):
            messagebox.showwarning(
                "Invalid Filename Template",
                "The template cannot contain these characters: "
                '< > : " / \\ | ? *',
                parent=self.root,
            )
            return False

        return True
    
    def export_files(self):
        
        if self.is_exporting:
            return

        input_root = self.input_folder.get().strip()

        if not input_root or not os.path.isdir(input_root):
            messagebox.showwarning(
                "Input Folder Required",
                "Please select a valid input folder.",
                parent=self.root,
            )
            return
            
        destination = self.output_folder.get().strip()

        if not destination or not os.path.isdir(destination):
            messagebox.showwarning(
                "Output Folder Required",
                "Please select a valid output folder.",
                parent=self.root,
            )
            return

        if not self.validate_filename_template():
            return

        selected_format = self.output_format.get()
        output_extension = OUTPUT_FORMATS[selected_format]

        try:
            files = self.find_input_files(input_root)
        except OSError as error:
            messagebox.showerror(
                "Folder Error", str(error), parent=self.root
            )
            return

        if not files:
            messagebox.showinfo(
                "No Audio Files",
                "No supported audio files were found in the selected folder.",
                parent=self.root,
            )
            return

        self.clear_results()
        self.log(f"Found {len(files)} audio file(s).")
        self.log(f"Output format: {selected_format}")
        self.log("Preparing conversion...\n")

        self.is_exporting = True
        self.cancel_requested = False
        self.set_controls_enabled(False)

        converted = 0
        skipped = 0
        failed = 0
        reserved_output_paths = set()
        self.progress_bar.configure(maximum=len(files))
        self.progress_var.set(0)
        self.log(f"Progress: 0/{len(files)} files processed\n")
        
        try:
            with open(TO_PIPE, "w") as to_pipe, open(FROM_PIPE, "r") as from_pipe:
                
                # Check the connection before starting the batch.
                connection_result = send_command(to_pipe, from_pipe, "Help: Command=GetInfo")

                if "BatchCommand finished:" not in connection_result:
                    raise RuntimeError("Could not verify the Audacity scripting connection.")

                for index, input_path in enumerate(files, start=1):
                    
                    if self.cancel_requested:
                        break
                        
                    self.log(f"[{index}/{len(files)}] "
                        f"{os.path.basename(input_path)}")

                    # Skip conversion when input and output formats match.
                    input_extension = os.path.splitext(input_path)[1].lower()

                    if (self.skip_same_extension.get() and input_extension == output_extension.lower()):
                        self.log("  SKIPPED: Same extension as output.")
                        skipped += 1
                        self.update_progress(index, len(files))
                        continue

                    # Find and reserve an available output filename.
                    output_path = self.find_available_output(input_path, input_root, reserved_output_paths, index)

                    # Never overwrite a source file.
                    if (os.path.abspath(output_path).lower() == os.path.abspath(input_path).lower()):
                        self.log("  SKIPPED: Output is the source file.")
                        skipped += 1
                        self.update_progress(index, len(files))
                        continue

                    if self.overwrite_files.get():
                        if os.path.exists(output_path):
                            try:
                                os.remove(output_path)
                            except OSError as error:
                                self.log(f"  FAILED: Could not remove existing output: {error}")
                                failed += 1
                                self.update_progress(index, len(files))
                                continue

                    import_result = ""
                    export_result = ""
                    imported = False

                    try:
                        import_result = send_command(to_pipe, from_pipe, 'Import2: Filename="' + quote_path(input_path) + '"')
                        
                        if "BatchCommand finished: Failed" in import_result:
                            self.log("  FAILED: Audacity could not import the file.")
                            self.log_audacity_response("Import2", import_result)
                            failed += 1
                            self.update_progress(index, len(files))
                            continue

                        imported = True

                        export_result = self.export_audio_file(to_pipe, from_pipe, output_path)

                        if ("BatchCommand finished: OK" in export_result and os.path.isfile(output_path) and os.path.getsize(output_path) > 0):
                            self.log("  OK: " + output_path)
                            converted += 1
                        else:
                            if "BatchCommand finished: Failed" in export_result:
                                reason = f"{selected_format} export failed in Audacity."
                            elif not os.path.isfile(output_path):
                                reason = (
                                    f"{selected_format} export did not create an output file."
                                )
                            elif os.path.getsize(output_path) == 0:
                                reason = f"{selected_format} export created an empty file."
                            else:
                                reason = (
                                    f"{selected_format} export did not report success."
                                )

                            self.log(f"  FAILED: {reason}")
                            self.log_audacity_response(
                                f"{selected_format} export",
                                export_result,
                            )
                            failed += 1

                    except Exception as error:
                        import traceback

                        self.log(f"  FAILED: {type(error).__name__}: {error}")
                        self.log(traceback.format_exc())
                        failed += 1

                    finally:
                        if imported:
                            try:
                                send_command(to_pipe, from_pipe, "SelectAll:")
                                send_command(to_pipe, from_pipe, "RemoveTracks:")
                            except Exception as cleanup_error:
                                self.log("  WARNING: Could not clear the "
                                        f"temporary tracks: {cleanup_error}")
                        self.update_progress(index, len(files))
                    
        except Exception as error:
            self.log(f"\nBATCH ERROR: {error}")
            messagebox.showerror("Batch Export Error", str(error), parent=self.root)

        finally:
            self.log("\n========== SUMMARY ==========")
            
            completed_count = int(self.progress_var.get())
            
            if self.cancel_requested and completed_count < len(files):
                self.log(
                    f"Cancelled: {completed_count}/{len(files)} files processed"
                )
            elif completed_count == len(files):
                self.log(
                    f"Finished: {completed_count}/{len(files)} files processed"
                )
            else:
                self.log(
                    f"Stopped: {completed_count}/{len(files)} files processed"
                )
                
            self.log(f"Converted: {converted}")
            self.log(f"Skipped:   {skipped}")
            self.log(f"Failed:    {failed}")
            self.log("Finished.")

            self.is_exporting = False
            self.set_controls_enabled(True)
            self.cancel_requested = False
            self.progress_var.set(0)
    
    def configure_export_settings(self, to_pipe, from_pipe):
        """Apply settings for the currently selected output format."""

        selected_format = self.output_format.get()

        if selected_format == "MP3":
            mode = self.mp3_bitrate_mode.get()
            bitrate = self.mp3_bitrate.get()

            # Map the GUI labels to Audacity's preference values.
            mode_values = {
                "CBR": "CBR",
                "ABR": "ABR",
                "VBR": "VBR",
                "Preset": "SET",
            }

            if mode not in mode_values:
                raise ValueError(f"Unsupported MP3 bitrate mode: {mode}")

            if mode in ("CBR", "ABR"):
                bitrate_preference = {
                    "CBR": "FileFormats/MP3CbrRate",
                    "ABR": "FileFormats/MP3AbrRate",
                }[mode]

                value = self.mp3_bitrate.get()

            elif mode == "VBR":
                bitrate_preference = "FileFormats/MP3VbrRate"
                value = str(self.mp3_quality.get())

            elif mode == "Preset":
                bitrate_preference = "FileFormats/MP3SetRate"
                value = str(self.mp3_quality.get())

            else:
                raise ValueError(f"Unsupported MP3 bitrate mode: {mode}")

            commands = [
                (
                    'SetPreference: Name="FileFormats/MP3RateModeChoice" '
                    f'Value="{mode_values[mode]}" Reload=1'
                ),
                (
                    f'SetPreference: Name="{bitrate_preference}" '
                    f'Value="{value}" Reload=1'
                ),
            ]

            for command in commands:
                result = send_command(to_pipe, from_pipe, command)
                self.log(f"Applied Audacity preference: {command}")
                self.log(f"Audacity response: {result.strip()}")

                if "BatchCommand finished: Failed" in result:
                    raise RuntimeError(
                        f"Audacity rejected an MP3 setting: {command}"
                    )

                for index, command in enumerate(commands):
                    if index == len(commands) - 1:
                        command += " Reload=1"

                    result = send_command(to_pipe, from_pipe, command)

                    if "BatchCommand finished: Failed" in result:
                        raise RuntimeError(
                            f"Audacity rejected an MP3 setting: {command}"
                        )
        
        elif selected_format == "AIFF":
            encoding = self.wav_aiff_encoding.get()

            encoding_values = {
                    "16-bit PCM": "2",
                    "24-bit PCM": "3",
                    "32-bit PCM": "4",
                }

            if encoding not in encoding_values:
                raise ValueError(
                    f"Unsupported AIFF encoding: {encoding}"
                )

            value = encoding_values[encoding]

            command = (
                'SetPreference: '
                'Name="FileFormats/ExportFormat_SF1_Type/AIFF_20000" '
                f'Value="{value}" Reload=1'
            )

            result = send_command(to_pipe, from_pipe, command)

            if "BatchCommand finished: Failed" in result:
                raise RuntimeError(
                    "Audacity rejected the AIFF encoding setting."
                )
        
        elif selected_format == "WAV":
            encoding_values = {
                    "16-bit PCM": "2",
                    "24-bit PCM": "3",
                    "32-bit PCM": "4",
                }

            value = encoding_values[self.wav_encoding.get()]

            command = (
                'SetPreference: '
                'Name="FileFormats/ExportFormat_SF1_Type/WAV_10000" '
                f'Value="{value}" Reload=1'
            )

            result = send_command(to_pipe, from_pipe, command)

            if "BatchCommand finished: Failed" in result:
                raise RuntimeError(
                    f"Audacity rejected the WAV encoding setting: {command}"
                )
            pass

        elif selected_format == "FLAC":
            bit_depth_values = {
                "16-bit": "16",
                "24-bit": "24",
            }

            bit_depth = bit_depth_values[self.flac_bit_depth.get()]
            level = self.flac_level.get()

            if not 0 <= level <= 8:
                raise ValueError(
                    "FLAC compression level must be between 0 and 8."
                )

            commands = [
                (
                    'SetPreference: '
                    'Name="FileFormats/FLACBitDepth" '
                    f'Value="{bit_depth}" Reload=1'
                ),
                (
                    'SetPreference: '
                    'Name="FileFormats/FLACLevel" '
                    f'Value="{level}" Reload=1'
                ),
            ]

            for command in commands:
                result = send_command(to_pipe, from_pipe, command)

                if "BatchCommand finished: Failed" in result:
                    raise RuntimeError(
                        f"Audacity rejected a FLAC setting: {command}"
                    )

        elif selected_format == "OGG":
            quality = self.ogg_quality.get()

            if not 0 <= quality <= 100:
                raise ValueError(
                    "OGG quality must be between 0 and 100."
                )

            command = (
                'SetPreference: '
                'Name="FileFormats/OggExportQuality" '
                f'Value="{quality}" Reload=1'
            )

            result = send_command(to_pipe, from_pipe, command)

            if "BatchCommand finished: Failed" in result:
                raise RuntimeError(
                    "Audacity rejected the OGG quality setting."
                )
        
        elif selected_format == "WMA":
            bitrate = self.wma_bitrate.get()

            if not 25 <= int(bitrate) <= 320:
                raise ValueError(
                    "WMA bitrate must be between 25 and 320 kbps."
                )

            value = int(bitrate) * 1000

            command = (
                'SetPreference: '
                'Name="FileFormats/WMABitRate" '
                f'Value="{value}" Reload=1'
            )

            result = send_command(to_pipe, from_pipe, command)

            if "BatchCommand finished: Failed" in result:
                raise RuntimeError(
                    "Audacity rejected the WMA bitrate setting."
                )
        
        elif selected_format == "M4A":
            bitrate = int(self.m4a_bitrate.get())

            if not 98 <= bitrate <= 320:
                raise ValueError(
                    "M4A bitrate must be between 98 and 320 kbps."
                )

            command = (
                'SetPreference: '
                'Name="FileFormats/AACQuality" '
                f'Value="{bitrate}" Reload=1'
            )

            result = send_command(to_pipe, from_pipe, command)

            if "BatchCommand finished: Failed" in result:
                raise RuntimeError(
                    "Audacity rejected the M4A bitrate setting."
                )
        
        else:
            # Other format-specific settings will be added later.
            pass

    def configure_sample_rate(self, sample_rate, to_pipe, from_pipe):
        """Set the Audacity project sample rate when a specific rate is selected."""

        selected_rate = sample_rate.get()

        if selected_rate == "Same as source":
            return

        rate = int(selected_rate.removesuffix(" Hz"))

        command = f"SetProject: Rate={rate}"
        result = send_command(to_pipe, from_pipe, command)

        if "BatchCommand finished: Failed" in result:
            raise RuntimeError(
                f"Audacity rejected the sample rate: {rate} Hz"
            )

    def export_audio_file(self, to_pipe, from_pipe, output_path):
        """Export the current Audacity project to the selected format."""
        selected_format = self.output_format.get()
                
        if selected_format not in OUTPUT_FORMATS:
            raise ValueError(
                f"Unsupported output format: {selected_format}"
            )

        expected_extension = OUTPUT_FORMATS[selected_format].lower()
        actual_extension = os.path.splitext(output_path)[1].lower()

        if actual_extension != expected_extension:
            raise ValueError(
                f"Expected a {expected_extension} output file, "
                f"but received: {output_path}"
            )

        command = (
            'Export2: Filename="'
            + quote_path(output_path)
            + f'" NumChannels={1 if self.export_channels.get() == "Mono" else 2}'
        )

        self.configure_export_settings(to_pipe, from_pipe)
        
        if selected_format == "WAV":
            self.configure_sample_rate(self.wav_sample_rate, to_pipe, from_pipe)
        elif selected_format == "AIFF":
            self.configure_sample_rate(self.aiff_sample_rate, to_pipe, from_pipe)

        return send_command(to_pipe, from_pipe, command)
    
    def reset_window(self):
        if self.is_exporting:
            messagebox.showwarning(
                "Export in Progress",
                "Wait until the current export finishes before resetting.",
                parent=self.root,
            )
            return

        self.input_folder.set("")
        self.output_folder.set("")
        self.output_format.set("MP3")

        self.include_subfolders.set(True)
        self.new_filenames.set(False)
        self.overwrite_files.set(True)
        self.skip_same_extension.set(True)

        self.clear_results()
        self.log("Settings reset. Select an input folder to begin.")
    
    def reset_output_folder(self):
        self.output_folder.set(self.input_folder.get())
    
    def cancel_batch(self):
        """Request cancellation after the current file is processed."""
        if not self.is_exporting:
            return

        self.cancel_requested = True
        self.cancel_button.configure(state="disabled")
        self.log("Cancellation requested. Stopping before the next file.")
    
    def close_application(self):
        if self.is_exporting:
            messagebox.showwarning(
                "Export in Progress",
                "Wait until the current export finishes before closing.",
                parent=self.root,
            )
            return

        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/IM", "Audacity.exe"],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except Exception as error:
            messagebox.showerror(
                "Close Error",
                f"Could not close Audacity:\n\n{error}",
                parent=self.root,
            )
            return

        self.root.destroy()
    
if __name__ == "__main__":
    root = tk.Tk()
    app = AudioConverterApp(root)
    root.mainloop()
