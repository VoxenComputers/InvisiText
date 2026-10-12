# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - Initial Release

### Added
- **Core Obfuscation Engine (`obfuscator.py`)**:
  - Deterministic and randomized injection of Zero-Width Space characters (`\u200B`).
  - Strict injection after alphanumeric characters only, preserving whitespaces, newlines, punctuation, and emoji sequences.
  - Frequency presets: `Minimum` (20%), `Normal` (45%), `Medium` (70%), and `Maximum` (100%), with support for custom float ratios (0.0–1.0).
  - Sanitization function (`strip_invisible_characters`) targeting zero-width spaces, joiners, non-joiners, word joiners, and zero-width no-break spaces (`\uFEFF`).
  - Pre-cleaning mechanism to prevent compound bloat across successive obfuscation runs.
  - Inspection utility (`reveal_invisible_characters`) with configurable visual markers (default `[ZWSP]`).
  - Comprehensive text metrics calculation: total characters, visible characters, invisible count, word count, line count, and UTF-8 byte size.
- **Desktop GUI Application (`gui.py`)**:
  - Built with Python `tkinter` and `ttk` using a modern dark slate palette.
  - Windows High-DPI scaling support via `ctypes` per-monitor awareness.
  - Resilient layout architecture anchoring top controls and bottom action bars to avoid window clipping.
  - Dual-pane layout featuring independent scrollbars, word wrapping, and responsive sizing.
  - Interactive frequency selection via segmented pill buttons.
  - Real-time text statistics for both input and output panes.
  - One-click actions: Obfuscate, Copy Result (with clipboard toast), Strip Invisible Characters, Clear All, and Reveal Hidden (highlighted markers).
  - Multi-threaded background processing for inputs exceeding 50,000 characters to keep the UI responsive.
  - Global keyboard shortcuts: `Ctrl+Enter` (Obfuscate), `Ctrl+Shift+C` (Copy), and `Ctrl+L` (Clear All).
- **Command-Line Interface (`main.py`)**:
  - CLI arguments for text strings (`-t`), input files (`-i`), output files (`-o`), frequency levels (`-f`), character stripping (`--strip`), inspection mode (`--reveal`), and metadata output (`--stats`).
  - Support for `stdin` piping and UTF-8 console output.
- **Executable & Build Tooling**:
  - `create_ico.py`: Generator for multi-resolution Windows ICO icons (16x16 up to 256x256).
  - `build.bat`: Automated Windows single-file standalone executable builder via PyInstaller with optimized module exclusion.
- **Automated Test Suite**:
  - 22 unit and integration tests covering edge cases, character integrity, foreign scripts, performance, and GUI controls.
