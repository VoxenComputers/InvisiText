"""
Desktop GUI for Invisible Text Obfuscator
=========================================
A modern, lightweight desktop application built with Tkinter.
Features:
- Focused Zero-Width Space (\u200B) obfuscation workflow
- Selectable injection frequency: Minimum, Normal, Medium, Maximum
- Responsive windowed scaling with bottom action controls anchored
- Clean card layout with modern dark aesthetics
- Live character, word, invisible character, and byte statistics
- Copy to clipboard with visual confirmation
- Reveal/inspect mode to visually expose hidden characters
- Strip invisible characters tool
- Multi-threaded processing for heavy inputs to prevent UI lockup
- Full support for Unicode, emojis, multiline text, and keyboard shortcuts
"""

from __future__ import annotations
import os
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from obfuscator import (
    insert_zero_width_spaces,
    strip_invisible_characters,
    reveal_invisible_characters,
    get_text_statistics,
    ZW_SPACE,
    FREQUENCY_LEVELS,
)

# Color Theme: Modern Deep Slate & Indigo
THEME = {
    "bg": "#0F172A",          # Slate 900
    "card_bg": "#1E293B",     # Slate 800
    "card_border": "#334155", # Slate 700
    "input_bg": "#0B1120",    # Navy Dark
    "text": "#F8FAFC",        # Slate 50
    "text_muted": "#94A3B8",  # Slate 400
    "text_dim": "#64748B",    # Slate 500
    "primary": "#6366F1",     # Indigo 500
    "primary_hover": "#4F46E5",
    "primary_active": "#4338CA",
    "success": "#10B981",     # Emerald 500
    "success_hover": "#059669",
    "danger": "#EF4444",      # Rose / Red 500
    "danger_hover": "#DC2626",
    "secondary": "#334155",   # Slate 700
    "secondary_hover": "#475569",
    "accent_cyan": "#06B6D4", # Cyan 500
    "highlight_zwsp": "#F59E0B", # Amber for revealed markers
}

FONT_FAMILY = "Segoe UI"
FONT_MONO = "Consolas"

# Frequency option presets
FREQUENCY_OPTIONS = {
    "Minimum": FREQUENCY_LEVELS["minimum"],  # 0.20
    "Normal": FREQUENCY_LEVELS["normal"],    # 0.45
    "Medium": FREQUENCY_LEVELS["medium"],    # 0.70
    "Maximum": FREQUENCY_LEVELS["maximum"],  # 1.00
}


class ModernButton(tk.Button):
    """Custom styled flat button with hover and active states."""

    def __init__(
        self,
        master,
        text: str,
        bg: str,
        fg: str = "#FFFFFF",
        hover_bg: Optional[str] = None,
        active_bg: Optional[str] = None,
        font: tuple = (FONT_FAMILY, 10, "bold"),
        cursor: str = "hand2",
        command=None,
        padx: int = 14,
        pady: int = 7,
        **kwargs,
    ):
        self.normal_bg = bg
        self.hover_bg = hover_bg or bg
        self.active_bg = active_bg or hover_bg or bg

        super().__init__(
            master,
            text=text,
            bg=self.normal_bg,
            fg=fg,
            activebackground=self.active_bg,
            activeforeground=fg,
            font=font,
            bd=0,
            relief=tk.FLAT,
            cursor=cursor,
            command=command,
            padx=padx,
            pady=pady,
            **kwargs,
        )

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, event):
        if self["state"] != tk.DISABLED:
            self.configure(bg=self.hover_bg)

    def _on_leave(self, event):
        if self["state"] != tk.DISABLED:
            self.configure(bg=self.normal_bg)

    def set_normal_bg(self, new_bg: str, new_hover: Optional[str] = None):
        self.normal_bg = new_bg
        if new_hover:
            self.hover_bg = new_hover
        self.configure(bg=self.normal_bg)


class TextObfuscatorApp:
    """Main application controller and view."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("InvisiText")

        # Responsive default dimensions for windowed mode and various display scales
        self.root.geometry("980x640")
        self.root.minsize(680, 420)
        self.root.configure(bg=THEME["bg"])

        # State
        self.is_processing = False
        self.reveal_mode = False
        self.raw_output_text = ""
        self._toast_timer: Optional[str] = None

        # Load favicon for window icon and header logo
        self._load_app_icons()

        # Frequency Selection State (Default: Normal)
        self.selected_freq_level = "Normal"
        self.freq_value = FREQUENCY_OPTIONS["Normal"]
        self.freq_buttons = {}

        # Build UI in resilient docking order so bottom controls can never be pushed off screen
        self._configure_styles()
        self._create_header()       # Top dock
        self._create_toolbar()      # Top dock below header
        self._create_status_bar()    # Bottom dock (lowest)
        self._create_action_bar()    # Bottom dock (above status bar)
        self._create_main_content()  # Middle expanding area (fills remaining space)

        # Keyboard shortcuts
        self._bind_shortcuts()

        # Initial stats
        self._update_input_stats()
        self._update_output_stats()

    def _load_app_icons(self):
        """Loads favicon.png for window titlebar/taskbar icon and header logo."""
        self.logo_image = None
        self.window_icon = None

        base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        candidates = [
            os.path.join(base_dir, "favicon.png"),
            os.path.join(base_dir, "Favicon.png"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "favicon.png"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "Favicon.png"),
        ]
        icon_path = next((p for p in candidates if os.path.isfile(p)), None)

        if not icon_path:
            return

        try:
            # Try high-quality PIL resizing if available
            from PIL import Image, ImageTk
            with Image.open(icon_path) as im:
                # 30x30 logo for header, 64x64 for window taskbar
                self.logo_image = ImageTk.PhotoImage(im.resize((30, 30), Image.Resampling.LANCZOS))
                self.window_icon = ImageTk.PhotoImage(im.resize((64, 64), Image.Resampling.LANCZOS))
        except Exception:
            try:
                # Fallback to standard Tk PhotoImage with integer subsampling
                raw_img = tk.PhotoImage(file=icon_path)
                factor_logo = max(1, raw_img.width() // 30)
                factor_win = max(1, raw_img.width() // 64)
                self.logo_image = raw_img.subsample(factor_logo, factor_logo)
                self.window_icon = raw_img.subsample(factor_win, factor_win)
            except Exception:
                self.logo_image = None
                self.window_icon = None

        if self.window_icon:
            try:
                self.root.iconphoto(True, self.window_icon)
            except Exception:
                pass

    def _configure_styles(self):
        """Configure ttk styles for widgets."""
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

    def _create_header(self):
        """Top banner with app title and description."""
        header_frame = tk.Frame(self.root, bg=THEME["bg"], padx=20, pady=8)
        header_frame.pack(side=tk.TOP, fill=tk.X)

        title_row = tk.Frame(header_frame, bg=THEME["bg"])
        title_row.pack(fill=tk.X)

        # Header Logo: use favicon.png if available, fallback to shield
        if self.logo_image:
            icon_label = tk.Label(
                title_row,
                image=self.logo_image,
                bg=THEME["bg"],
            )
            icon_label.pack(side=tk.LEFT, padx=(0, 10))
        else:
            icon_label = tk.Label(
                title_row,
                text="🛡️",
                font=(FONT_FAMILY, 18),
                bg=THEME["bg"],
                fg=THEME["text"],
            )
            icon_label.pack(side=tk.LEFT, padx=(0, 8))

        title_label = tk.Label(
            title_row,
            text="InvisiText",
            font=(FONT_FAMILY, 17, "bold"),
            bg=THEME["bg"],
            fg=THEME["text"],
        )
        title_label.pack(side=tk.LEFT)

        desc_label = tk.Label(
            header_frame,
            text="Injects zero-width space characters (\\u200B) between text tokens. Visually identical to humans, disruptive to automated tokenizers.",
            font=(FONT_FAMILY, 9),
            bg=THEME["bg"],
            fg=THEME["text_muted"],
        )
        desc_label.pack(anchor="w", pady=(2, 0))

    def _create_toolbar(self):
        """Settings card with selectable frequency levels (Minimum, Normal, Medium, Maximum)."""
        card = tk.Frame(
            self.root,
            bg=THEME["card_bg"],
            highlightbackground=THEME["card_border"],
            highlightthickness=1,
            padx=16,
            pady=8,
        )
        card.pack(side=tk.TOP, fill=tk.X, padx=20, pady=(0, 8))

        # Frequency label
        freq_lbl = tk.Label(
            card,
            text="Injection Frequency:",
            font=(FONT_FAMILY, 10, "bold"),
            bg=THEME["card_bg"],
            fg=THEME["text"],
        )
        freq_lbl.pack(side=tk.LEFT, padx=(0, 12))

        # Modern Segmented Pill Buttons
        pill_container = tk.Frame(
            card,
            bg=THEME["input_bg"],
            highlightbackground=THEME["card_border"],
            highlightthickness=1,
            padx=2,
            pady=2,
        )
        pill_container.pack(side=tk.LEFT)

        levels = ["Minimum", "Normal", "Medium", "Maximum"]
        for level in levels:
            is_active = (level == self.selected_freq_level)
            btn = tk.Button(
                pill_container,
                text=level,
                font=(FONT_FAMILY, 9, "bold" if is_active else "normal"),
                bg=THEME["primary"] if is_active else THEME["input_bg"],
                fg="#FFFFFF" if is_active else THEME["text_muted"],
                activebackground=THEME["primary_hover"],
                activeforeground="#FFFFFF",
                bd=0,
                padx=14,
                pady=4,
                cursor="hand2",
                relief=tk.FLAT,
                command=lambda lvl=level: self.set_frequency_level(lvl),
            )
            btn.pack(side=tk.LEFT, padx=1)
            self.freq_buttons[level] = btn

    def set_frequency_level(self, level: str):
        """Switch injection frequency between Minimum, Normal, Medium, and Maximum."""
        if level not in FREQUENCY_OPTIONS:
            return

        self.selected_freq_level = level
        self.freq_value = FREQUENCY_OPTIONS[level]

        # Update button visual styling
        for lvl, btn in self.freq_buttons.items():
            if lvl == level:
                btn.config(
                    bg=THEME["primary"],
                    fg="#FFFFFF",
                    font=(FONT_FAMILY, 9, "bold"),
                )
            else:
                btn.config(
                    bg=THEME["input_bg"],
                    fg=THEME["text_muted"],
                    font=(FONT_FAMILY, 9, "normal"),
                )

        pct = int(round(self.freq_value * 100))
        self.set_status(f"Injection frequency set to {level} ({pct}% obfuscation).", "normal")

    def get_frequency_value(self) -> float:
        """Returns the current numeric frequency value."""
        return self.freq_value

    def _create_status_bar(self):
        """Bottom status bar anchored to the bottom edge."""
        self.status_bar_frame = tk.Frame(self.root, bg="#080D1A", padx=20, pady=5)
        self.status_bar_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_icon = tk.Label(
            self.status_bar_frame,
            text="●",
            font=(FONT_FAMILY, 9),
            bg="#080D1A",
            fg=THEME["success"],
        )
        self.status_icon.pack(side=tk.LEFT, padx=(0, 6))

        self.status_label = tk.Label(
            self.status_bar_frame,
            text="Ready. Paste your text and click 'Obfuscate Text'.",
            font=(FONT_FAMILY, 9),
            bg="#080D1A",
            fg=THEME["text_muted"],
        )
        self.status_label.pack(side=tk.LEFT)

        shortcuts_label = tk.Label(
            self.status_bar_frame,
            text="Shortcuts: Ctrl+Enter (Obfuscate)  •  Ctrl+Shift+C (Copy)  •  Ctrl+L (Clear)",
            font=(FONT_FAMILY, 8),
            bg="#080D1A",
            fg=THEME["text_dim"],
        )
        shortcuts_label.pack(side=tk.RIGHT)

    def _create_action_bar(self):
        """Action row with main controls anchored above the status bar."""
        self.action_bar_frame = tk.Frame(self.root, bg=THEME["bg"], padx=20, pady=6)
        self.action_bar_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # Primary Obfuscate Button
        self.obfuscate_btn = ModernButton(
            self.action_bar_frame,
            text="⚡  Obfuscate Text  (Ctrl+Enter)",
            bg=THEME["primary"],
            hover_bg=THEME["primary_hover"],
            font=(FONT_FAMILY, 10, "bold"),
            padx=18,
            pady=7,
            command=self.obfuscate_text,
        )
        self.obfuscate_btn.pack(side=tk.LEFT, padx=(0, 8))

        # Secondary Copy Button
        self.main_copy_btn = ModernButton(
            self.action_bar_frame,
            text="📋  Copy Result",
            bg=THEME["success"],
            hover_bg=THEME["success_hover"],
            font=(FONT_FAMILY, 10, "bold"),
            padx=14,
            pady=7,
            command=self.copy_output,
        )
        self.main_copy_btn.pack(side=tk.LEFT, padx=(0, 8))

        # Strip / Clean Invisible Characters Button
        self.strip_btn = ModernButton(
            self.action_bar_frame,
            text="🧹  Strip Invisible Chars",
            bg=THEME["secondary"],
            hover_bg=THEME["secondary_hover"],
            font=(FONT_FAMILY, 9),
            padx=12,
            pady=7,
            command=self.strip_invisible_from_input,
        )
        self.strip_btn.pack(side=tk.LEFT, padx=(0, 8))

        # Clear All Button
        self.clear_all_btn = ModernButton(
            self.action_bar_frame,
            text="🗑️  Clear All",
            bg=THEME["danger"],
            hover_bg=THEME["danger_hover"],
            font=(FONT_FAMILY, 9, "bold"),
            padx=14,
            pady=7,
            command=self.clear_all,
        )
        self.clear_all_btn.pack(side=tk.RIGHT)

    def _create_main_content(self):
        """Split view with Input Text on left and Output Text on right, dynamically expanding."""
        self.content_paned = tk.PanedWindow(
            self.root,
            orient=tk.HORIZONTAL,
            bg=THEME["bg"],
            bd=0,
            sashwidth=6,
            sashrelief=tk.FLAT,
        )
        self.content_paned.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=20, pady=(0, 4))

        # --- LEFT PANE: INPUT ---
        input_container = tk.Frame(
            self.content_paned,
            bg=THEME["card_bg"],
            highlightbackground=THEME["card_border"],
            highlightthickness=1,
        )
        self.content_paned.add(input_container, stretch="always")

        # Input Header
        in_header = tk.Frame(input_container, bg=THEME["card_bg"], padx=12, pady=8)
        in_header.pack(fill=tk.X)

        in_title = tk.Label(
            in_header,
            text="ORIGINAL INPUT TEXT",
            font=(FONT_FAMILY, 9, "bold"),
            bg=THEME["card_bg"],
            fg=THEME["text_muted"],
        )
        in_title.pack(side=tk.LEFT)

        in_paste_btn = ModernButton(
            in_header,
            text="📋 Paste",
            bg=THEME["secondary"],
            hover_bg=THEME["secondary_hover"],
            font=(FONT_FAMILY, 9),
            padx=9,
            pady=3,
            command=self.paste_to_input,
        )
        in_paste_btn.pack(side=tk.RIGHT, padx=(6, 0))

        in_clear_btn = ModernButton(
            in_header,
            text="✕ Clear",
            bg=THEME["secondary"],
            hover_bg=THEME["secondary_hover"],
            font=(FONT_FAMILY, 9),
            padx=9,
            pady=3,
            command=self.clear_input,
        )
        in_clear_btn.pack(side=tk.RIGHT)

        # Input Text Area
        in_text_frame = tk.Frame(input_container, bg=THEME["input_bg"])
        in_text_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 4))

        in_scroll = ttk.Scrollbar(in_text_frame, orient=tk.VERTICAL)
        in_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.input_text = tk.Text(
            in_text_frame,
            bg=THEME["input_bg"],
            fg=THEME["text"],
            insertbackground=THEME["text"],
            selectbackground=THEME["primary"],
            selectforeground="#FFFFFF",
            font=(FONT_MONO, 11),
            wrap=tk.WORD,
            bd=0,
            padx=8,
            pady=8,
            height=6,
            width=20,
            yscrollcommand=in_scroll.set,
            undo=True,
        )
        self.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        in_scroll.config(command=self.input_text.yview)

        # Bind input text modifications to update stats
        self.input_text.bind("<<Modified>>", self._on_input_modified)
        self.input_text.bind("<KeyRelease>", lambda e: self._update_input_stats())

        # Input Footer / Stats
        self.in_stats_label = tk.Label(
            input_container,
            text="Chars: 0  |  Words: 0  |  Lines: 0  |  Bytes: 0 B",
            font=(FONT_FAMILY, 8),
            bg=THEME["card_bg"],
            fg=THEME["text_dim"],
            padx=12,
            pady=6,
            anchor="w",
        )
        self.in_stats_label.pack(fill=tk.X)

        # --- RIGHT PANE: OUTPUT ---
        output_container = tk.Frame(
            self.content_paned,
            bg=THEME["card_bg"],
            highlightbackground=THEME["card_border"],
            highlightthickness=1,
        )
        self.content_paned.add(output_container, stretch="always")

        # Output Header
        out_header = tk.Frame(output_container, bg=THEME["card_bg"], padx=12, pady=8)
        out_header.pack(fill=tk.X)

        out_title = tk.Label(
            out_header,
            text="OBFUSCATED OUTPUT",
            font=(FONT_FAMILY, 9, "bold"),
            bg=THEME["card_bg"],
            fg=THEME["text_muted"],
        )
        out_title.pack(side=tk.LEFT)

        self.copy_btn = ModernButton(
            out_header,
            text="📋 Copy Output",
            bg=THEME["success"],
            hover_bg=THEME["success_hover"],
            font=(FONT_FAMILY, 9, "bold"),
            padx=10,
            pady=3,
            command=self.copy_output,
        )
        self.copy_btn.pack(side=tk.RIGHT, padx=(6, 0))

        self.reveal_btn = ModernButton(
            out_header,
            text="👁️ Reveal Hidden",
            bg=THEME["secondary"],
            hover_bg=THEME["secondary_hover"],
            font=(FONT_FAMILY, 9),
            padx=9,
            pady=3,
            command=self.toggle_reveal_mode,
        )
        self.reveal_btn.pack(side=tk.RIGHT)

        # Output Text Area
        out_text_frame = tk.Frame(output_container, bg=THEME["input_bg"])
        out_text_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 4))

        out_scroll = ttk.Scrollbar(out_text_frame, orient=tk.VERTICAL)
        out_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.output_text = tk.Text(
            out_text_frame,
            bg=THEME["input_bg"],
            fg=THEME["text"],
            insertbackground=THEME["text"],
            selectbackground=THEME["primary"],
            selectforeground="#FFFFFF",
            font=(FONT_MONO, 11),
            wrap=tk.WORD,
            bd=0,
            padx=8,
            pady=8,
            height=6,
            width=20,
            yscrollcommand=out_scroll.set,
        )
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        out_scroll.config(command=self.output_text.yview)

        # Output highlights
        self.output_text.tag_configure("highlight_zw", foreground=THEME["highlight_zwsp"], font=(FONT_MONO, 11, "bold"))

        # Output Footer / Stats
        self.out_stats_label = tk.Label(
            output_container,
            text="Chars: 0  |  Hidden: 0  |  Words: 0  |  Bytes: 0 B",
            font=(FONT_FAMILY, 8),
            bg=THEME["card_bg"],
            fg=THEME["text_dim"],
            padx=12,
            pady=6,
            anchor="w",
        )
        self.out_stats_label.pack(fill=tk.X)

    def _bind_shortcuts(self):
        """Attach global keyboard shortcuts."""
        self.root.bind("<Control-Return>", lambda e: self.obfuscate_text())
        self.root.bind("<Control-KP_Enter>", lambda e: self.obfuscate_text())
        self.root.bind("<Control-Shift-C>", lambda e: self.copy_output())
        self.root.bind("<Control-Shift-c>", lambda e: self.copy_output())
        self.root.bind("<Control-l>", lambda e: self.clear_all())
        self.root.bind("<Control-L>", lambda e: self.clear_all())

    # --- UI Logic & Handlers ---

    def _on_input_modified(self, event=None):
        """Reset text widget modified flag and update stats."""
        if self.input_text.edit_modified():
            self._update_input_stats()
            self.input_text.edit_modified(False)

    def _update_input_stats(self):
        """Compute and display statistics for input text."""
        raw = self.input_text.get("1.0", "end-1c")
        stats = get_text_statistics(raw)
        self.in_stats_label.config(
            text=f"Chars: {stats['total_chars']:,}  |  Words: {stats['words']:,}  |  Lines: {stats['lines']:,}  |  Bytes: {stats['utf8_bytes']:,} B"
        )

    def _update_output_stats(self):
        """Compute and display statistics for output text."""
        stats = get_text_statistics(self.raw_output_text)
        pct_increase = 0
        if stats["visible_chars"] > 0:
            pct_increase = int(round((stats["invisible_chars"] / stats["visible_chars"]) * 100))

        hidden_desc = f"{stats['invisible_chars']:,} hidden (+{pct_increase}%)" if stats['invisible_chars'] else "0 hidden"
        self.out_stats_label.config(
            text=f"Chars: {stats['total_chars']:,} ({hidden_desc})  |  Words: {stats['words']:,}  |  Bytes: {stats['utf8_bytes']:,} B"
        )

    def set_status(self, text: str, state: str = "normal"):
        """Update status bar message with color indicator."""
        colors = {
            "normal": (THEME["success"], THEME["text_muted"]),
            "success": (THEME["success"], THEME["text"]),
            "warning": (THEME["highlight_zwsp"], THEME["highlight_zwsp"]),
            "error": (THEME["danger"], THEME["danger"]),
            "info": (THEME["accent_cyan"], THEME["text"]),
        }
        icon_color, text_color = colors.get(state, colors["normal"])
        self.status_icon.config(fg=icon_color)
        self.status_label.config(text=text, fg=text_color)

    def obfuscate_text(self):
        """Trigger obfuscation process."""
        if self.is_processing:
            return

        input_data = self.input_text.get("1.0", "end-1c")
        if not input_data:
            self.set_status("⚠️ Input text is empty. Paste or type text to obfuscate.", "warning")
            return

        frequency = self.freq_value

        # For large texts (> 50,000 chars), process in background thread to avoid UI stutter
        if len(input_data) > 50000:
            self._start_async_processing(input_data, frequency)
        else:
            self._perform_obfuscation(input_data, frequency)

    def _perform_obfuscation(self, text: str, freq: float):
        """Synchronously process and update UI with Zero-Width Space injection."""
        start_t = time.perf_counter()
        obfuscated = insert_zero_width_spaces(
            text=text,
            frequency=freq,
            clean_existing=True,
        )
        elapsed_ms = (time.perf_counter() - start_t) * 1000

        self.raw_output_text = obfuscated
        self.reveal_mode = False
        self.reveal_btn.configure(text="👁️ Reveal Hidden", bg=THEME["secondary"])

        # Display in output
        self._set_output_text(self.raw_output_text)
        self._update_output_stats()

        stats = get_text_statistics(obfuscated)
        self.set_status(
            f"✓ Obfuscated successfully! Injected {stats['invisible_chars']:,} hidden zero-width spaces ({elapsed_ms:.1f}ms).",
            "success",
        )

    def _start_async_processing(self, text: str, freq: float):
        """Asynchronously process large text in background thread."""
        self.is_processing = True
        self.obfuscate_btn.config(state=tk.DISABLED, text="⏳ Processing...")
        self.set_status("Processing large text in background...", "info")

        def worker():
            start_t = time.perf_counter()
            obfuscated = insert_zero_width_spaces(
                text=text,
                frequency=freq,
                clean_existing=True,
            )
            elapsed_ms = (time.perf_counter() - start_t) * 1000

            def on_done():
                self.is_processing = False
                self.obfuscate_btn.config(state=tk.NORMAL, text="⚡  Obfuscate Text  (Ctrl+Enter)")
                self.raw_output_text = obfuscated
                self.reveal_mode = False
                self.reveal_btn.configure(text="👁️ Reveal Hidden", bg=THEME["secondary"])
                self._set_output_text(self.raw_output_text)
                self._update_output_stats()
                stats = get_text_statistics(obfuscated)
                self.set_status(
                    f"✓ Obfuscated successfully! Injected {stats['invisible_chars']:,} hidden zero-width spaces ({elapsed_ms:.1f}ms).",
                    "success",
                )

            self.root.after(0, on_done)

        threading.Thread(target=worker, daemon=True).start()

    def _set_output_text(self, text: str, highlight_markers: bool = False):
        """Write text to output text widget."""
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", text)

        if highlight_markers:
            # Highlight revealed [ZWSP] markers in amber
            start_index = "1.0"
            tag = "[ZWSP]"
            while True:
                pos = self.output_text.search(tag, start_index, stopindex=tk.END)
                if not pos:
                    break
                end_pos = f"{pos}+{len(tag)}c"
                self.output_text.tag_add("highlight_zw", pos, end_pos)
                start_index = end_pos

    def toggle_reveal_mode(self):
        """Toggle visual inspection of invisible characters."""
        if not self.raw_output_text:
            self.set_status("⚠️ No output to inspect. Run obfuscation first.", "warning")
            return

        self.reveal_mode = not self.reveal_mode
        if self.reveal_mode:
            revealed = reveal_invisible_characters(self.raw_output_text, marker="[ZWSP]")
            self._set_output_text(revealed, highlight_markers=True)
            self.reveal_btn.configure(text="🔒 Hide Markers", bg=THEME["highlight_zwsp"])
            self.set_status("Revealing hidden zero-width space markers in orange.", "info")
        else:
            self._set_output_text(self.raw_output_text)
            self.reveal_btn.configure(text="👁️ Reveal Hidden", bg=THEME["secondary"])
            self.set_status("Showing clean identical visual representation.", "normal")

    def copy_output(self):
        """Copy obfuscated text to clipboard with toast notification."""
        if not self.raw_output_text:
            self.set_status("⚠️ Nothing to copy. Obfuscate some text first.", "warning")
            return

        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.raw_output_text)
            self.root.update()  # Finalize clipboard for Windows

            # Visual button feedback
            self.copy_btn.configure(text="✓ Copied!", bg="#059669")
            self.main_copy_btn.configure(text="✓ Copied to Clipboard!", bg="#059669")
            self.set_status(f"✓ Copied {len(self.raw_output_text):,} characters to clipboard!", "success")

            # Reset button appearance after 2 seconds
            if self._toast_timer:
                self.root.after_cancel(self._toast_timer)
            self._toast_timer = self.root.after(2000, self._reset_copy_buttons)
        except Exception as e:
            self.set_status(f"❌ Failed to copy to clipboard: {e}", "error")

    def _reset_copy_buttons(self):
        """Reset copy buttons to original labels."""
        self.copy_btn.configure(text="📋 Copy Output", bg=THEME["success"])
        self.main_copy_btn.configure(text="📋  Copy Result", bg=THEME["success"])

    def paste_to_input(self):
        """Paste clipboard content into input area."""
        try:
            clip_text = self.root.clipboard_get()
            if clip_text:
                self.input_text.insert(tk.INSERT, clip_text)
                self._update_input_stats()
                self.set_status("Pasted text from clipboard into input.", "normal")
        except Exception:
            self.set_status("⚠️ Clipboard is empty or contains non-text data.", "warning")

    def clear_input(self):
        """Clear only the input field."""
        self.input_text.delete("1.0", tk.END)
        self._update_input_stats()
        self.set_status("Input cleared.", "normal")

    def strip_invisible_from_input(self):
        """Strip all invisible characters from input field."""
        current = self.input_text.get("1.0", "end-1c")
        if not current:
            self.set_status("⚠️ Input is empty.", "warning")
            return

        cleaned = strip_invisible_characters(current)
        removed_count = len(current) - len(cleaned)
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert("1.0", cleaned)
        self._update_input_stats()

        if removed_count > 0:
            self.set_status(f"✓ Stripped {removed_count:,} invisible characters from input.", "success")
        else:
            self.set_status("Input did not contain any invisible characters.", "info")

    def clear_all(self):
        """Reset both input and output fields."""
        self.input_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)
        self.raw_output_text = ""
        self.reveal_mode = False
        self.reveal_btn.configure(text="👁️ Reveal Hidden", bg=THEME["secondary"])
        self._update_input_stats()
        self._update_output_stats()
        self.set_status("All fields reset. Ready.", "normal")
