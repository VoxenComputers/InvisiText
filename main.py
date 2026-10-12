"""
InvisiText - Main Entry Point
=============================
Launches the Desktop GUI application or provides command-line obfuscation.
"""

from __future__ import annotations
import argparse
import sys
import tkinter as tk

from obfuscator import (
    insert_zero_width_spaces,
    strip_invisible_characters,
    reveal_invisible_characters,
    get_text_statistics,
)


def enable_windows_dpi_awareness():
    """Enable high-DPI scaling on Windows so Tkinter renders razor-sharp fonts."""
    if sys.platform == "win32":
        try:
            import ctypes
            # Per-monitor DPI awareness (Windows 8.1+)
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                # System DPI awareness (Windows Vista+)
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


def run_gui():
    """Initialize and run the desktop GUI application."""
    enable_windows_dpi_awareness()

    from gui import TextObfuscatorApp

    root = tk.Tk()
    app = TextObfuscatorApp(root)
    root.mainloop()


def run_cli(args):
    """Handle command-line processing."""
    if args.input_file:
        try:
            with open(args.input_file, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            print(f"Error reading file '{args.input_file}': {e}", file=sys.stderr)
            sys.exit(1)
    elif args.text is not None:
        text = args.text
    else:
        text = sys.stdin.read()

    # Ensure stdout handles UTF-8 on Windows
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    if args.strip:
        result = strip_invisible_characters(text)
    else:
        # Resolve frequency: float or preset name
        try:
            freq_param = float(args.frequency)
        except ValueError:
            freq_param = args.frequency

        result = insert_zero_width_spaces(
            text=text,
            frequency=freq_param,
            clean_existing=not args.no_clean,
        )

    # Capture stats on actual obfuscated result before optional reveal transformation
    stats = get_text_statistics(result) if args.stats else None

    display_output = reveal_invisible_characters(result) if args.reveal else result

    if args.output_file:
        try:
            with open(args.output_file, "w", encoding="utf-8") as f:
                f.write(display_output)
        except Exception as e:
            print(f"Error writing file '{args.output_file}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        try:
            sys.stdout.write(display_output)
            sys.stdout.flush()
        except UnicodeEncodeError:
            # Fallback for legacy console encoding
            sys.stdout.buffer.write(display_output.encode("utf-8"))

    if stats:
        print("\n--- Text Statistics ---", file=sys.stderr)
        for k, v in stats.items():
            print(f"{k}: {v}", file=sys.stderr)


def main():
    """Main CLI / GUI dispatcher."""
    # If arguments are passed, run in CLI mode. If no args, launch desktop GUI.
    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser(
            description="InvisiText - Insert zero-width space characters (\\u200B) into text."
        )
        parser.add_argument(
            "-t", "--text", type=str, help="Input text string to obfuscate."
        )
        parser.add_argument(
            "-i", "--input-file", type=str, help="Input text file path."
        )
        parser.add_argument(
            "-o", "--output-file", type=str, help="Output file path (default stdout)."
        )
        parser.add_argument(
            "-f", "--frequency", type=str, default="normal",
            help="Insertion frequency: minimum, normal, medium, maximum, or a float 0.0-1.0 (default: normal)."
        )
        parser.add_argument(
            "--strip", action="store_true", help="Strip all invisible characters instead of inserting."
        )
        parser.add_argument(
            "--reveal", action="store_true", help="Reveal invisible characters with visual markers."
        )
        parser.add_argument(
            "--no-clean", action="store_true", help="Do not sanitize existing invisible characters first."
        )
        parser.add_argument(
            "--stats", action="store_true", help="Print text statistics to stderr."
        )
        parser.add_argument(
            "--gui", action="store_true", help="Explicitly launch the desktop GUI."
        )

        args = parser.parse_args()

        if args.gui:
            run_gui()
        else:
            run_cli(args)
    else:
        run_gui()


if __name__ == "__main__":
    main()
