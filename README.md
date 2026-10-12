# InvisiText
### Invisible Text Obfuscator

InvisiText is a lightweight desktop and command-line utility that injects invisible Zero-Width Space Unicode characters (`\u200B`) into text. The resulting text appears visually identical to human readers in standard rendering engines while breaking contiguous character sequences to disrupt automated tokenization, pattern matching, and plain-text parsers.

---

## Features

- **Zero-Width Space Obfuscation**: Injects standard Unicode Zero-Width Space characters (`\u200B`) exclusively after alphanumeric characters, preserving whitespace, punctuation, line endings, and emoji variation selectors.
- **Selectable Frequency Levels**:
  - **Minimum**: 20% injection probability for subtle modification.
  - **Normal** (Default): 45% injection probability for balanced coverage.
  - **Medium**: 70% injection probability for thorough disruption.
  - **Maximum**: 100% injection probability (injected after every alphanumeric character).
  - Custom float values between `0.0` and `1.0` supported via the CLI.
- **Compound Bloat Prevention**: Automatically strips existing invisible Unicode characters before applying new obfuscation passes to avoid character multiplication.
- **Inspection & Reveal Mode**: Toggles visual replacement of invisible characters with highlighted `[ZWSP]` markers in the GUI or CLI to verify exact injection points.
- **Sanitization & Stripping Tool**: One-click extraction and removal of hidden characters (`\u200B`, `\u200C`, `\u200D`, `\u2060`, `\uFEFF`) from pasted or imported text.
- **Real-Time Text Metrics**: Live counters displaying total characters, visible characters, hidden character count (with percentage increase), word count, line count, and UTF-8 byte size.
- **Modern Desktop GUI**:
  - Built with Python Tkinter and TTK using a dark slate theme.
  - High-DPI scaling enabled on Windows for sharp fonts.
  - Resilient layout with anchored action controls and responsive dual-pane editor.
  - Non-blocking asynchronous processing for large inputs exceeding 50,000 characters.
  - Clipboard integration with visual toast feedback.
  - Global keyboard shortcuts for rapid workflows.
- **Dual Interface**: Includes both the full desktop GUI and a command-line interface (CLI) for shell scripting and automation.
- **Comprehensive Test Suite**: 22 unit and integration tests covering edge cases, unicode scripts, emoji stability, and GUI state handlers.

---

## Obfuscation Mechanism

The core engine (`obfuscator.py`) operates through targeted insertion of the standard Unicode character `\u200B` (Zero-Width Space):

1. **Pre-Sanitization**:
   If `clean_existing=True` (default), the input text is first filtered through `strip_invisible_characters()`. This removes prior zero-width spaces (`\u200B`), non-joiners (`\u200C`), joiners (`\u200D`), word joiners (`\u2060`), and zero-width no-break spaces (`\uFEFF`) to prevent cumulative bloat across repeated runs.

2. **Alphanumeric Guard**:
   The engine iterates through the sanitized string character by character. An invisible space is eligible for insertion **only after alphanumeric characters** (`char.isalnum()`):
   - Standard whitespace (spaces, tabs) is never followed by an inserted zero-width space.
   - Line breaks (`\r`, `\n`) are preserved without trailing invisible characters.
   - Punctuation marks and symbols remain untouched.
   - Emoji variation selectors and composite sequences remain intact.

3. **Probabilistic Injection**:
   For each alphanumeric character, a pseudo-random check evaluates whether `random() < frequency`. When triggered, `\u200B` is appended immediately after that character. A deterministic seed can optionally be supplied for reproducible testing.

4. **Visual Result vs. Token Representation**:
   - **Rendered Output**: Rendered fonts assign zero advance width to `\u200B`, so the text looks completely unchanged on screen.
   - **Encoded Representation**: In UTF-8, each `\u200B` is encoded as the 3-byte sequence `0xE2 0x80 0x8B`. Subword tokenizers (e.g., BPE, WordPiece) treat the zero-width space as a distinct token or word boundary, altering token IDs without modifying human readability.

---

## Running the Standalone Executable (Windows)

A precompiled, standalone Windows executable is available:

1. Obtain `InvisibleTextObfuscator.exe` from the repository releases.
2. Double-click `InvisibleTextObfuscator.exe` to run.
3. No Python installation, runtime environment, or external dependencies are required.

---

## Running from Source

### Prerequisites
- Python 3.8 or higher.
- Standard Python installation including `tkinter` (included by default with official Windows Python installers).

### Setup
1. Clone or download this repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. (Optional) Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. Install optional and build dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: Core runtime and CLI require only the Python standard library. `Pillow` is optional for enhanced icon scaling in the GUI, and `pyinstaller` is required only for compiling the executable.*

### Launching the Desktop GUI
Run without arguments to start the desktop interface:
```bash
python main.py
```

### Running the Test Suite
Execute the test suite to verify installation and functionality:
```bash
python -m unittest discover -p "test_*.py"
```

---

## Usage Instructions

### Desktop GUI
1. **Input Text**: Paste or type text into the left pane (**ORIGINAL INPUT TEXT**), or use the **Paste** button.
2. **Select Frequency**: Click on **Minimum** (20%), **Normal** (45%), **Medium** (70%), or **Maximum** (100%) in the top toolbar.
3. **Obfuscate**: Click **Obfuscate Text** or press `Ctrl + Enter`.
4. **Copy Output**: Click **Copy Result** or press `Ctrl + Shift + C` to copy the obfuscated text to your clipboard.
5. **Inspect Hidden Characters**: Click **Reveal Hidden** to replace invisible spaces with visible `[ZWSP]` markers highlighted in orange.
6. **Strip Invisible Characters**: Click **Strip Invisible Chars** to sanitize input text by removing existing hidden characters.
7. **Clear**: Click **Clear All** or press `Ctrl + L` to reset both editors.

#### GUI Keyboard Shortcuts
| Shortcut | Action |
| --- | --- |
| `Ctrl + Enter` | Obfuscate input text |
| `Ctrl + Shift + C` | Copy obfuscated output to clipboard |
| `Ctrl + L` | Clear all fields |

### Command-Line Interface (CLI)
`main.py` provides command-line flags when arguments are supplied:

```bash
# Obfuscate inline text
python main.py -t "Sample confidential text"

# Set frequency level (minimum, normal, medium, maximum, or float 0.0-1.0)
python main.py -t "Sample text" -f maximum

# Process text from a file and write to an output file
python main.py -i input.txt -o obfuscated.txt -f medium

# Inspect injection points with visible [ZWSP] markers and output metrics
python main.py -t "Inspect this text" --reveal --stats

# Strip all invisible characters from a file
python main.py -i obfuscated.txt -o cleaned.txt --strip

# Pipe text through stdin
echo "Streamed input text" | python main.py -f normal
```

#### CLI Options Reference
| Flag | Description |
| --- | --- |
| `-t`, `--text` | Input text string to process |
| `-i`, `--input-file` | Path to input text file |
| `-o`, `--output-file` | Path to destination file (default: stdout) |
| `-f`, `--frequency` | Injection frequency (`minimum`, `normal`, `medium`, `maximum`, or float `0.0`-`1.0`) |
| `--strip` | Strip invisible characters instead of inserting |
| `--reveal` | Replace invisible characters with `[ZWSP]` markers |
| `--no-clean` | Do not sanitize existing invisible characters before inserting |
| `--stats` | Print text metrics to stderr |
| `--gui` | Force launch desktop GUI even if arguments are present |

---

## Known Limitations

- **Platform Normalization**: Many platforms, web forms, CMS systems, social media networks, and word processors automatically normalize or strip non-printable Unicode characters upon submission or pasting. If a platform strips zero-width spaces, the text reverts to its plain original form.
- **No Guaranteed AI Detector Bypass**: While zero-width spaces alter tokenizer sequences, modern AI detection tools and language model pipelines evolve continuously. Simple preprocessing pipelines can strip zero-width characters prior to evaluation. InvisiText does not guarantee bypass of any specific AI detector or automated filter.
- **Payload Size Increase**: Each zero-width space character (`\u200B`) requires 3 bytes in UTF-8 encoding. At maximum frequency, byte size can roughly double relative to visible character count.
- **Terminal and Editor Artifacts**: Some legacy terminal emulators, basic text editors, or fonts that lack proper zero-width Unicode handling may render zero-width characters as question marks, empty square boxes, or cause cursor positioning misalignment.

---

## Building the Windows Executable

The standalone Windows executable is built using PyInstaller and a compliant multi-layer Windows ICO icon.

### Build Steps
1. Ensure dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the build script:
   ```cmd
   build.bat
   ```

### What `build.bat` Does:
- Verifies Python and PyInstaller availability.
- Executes `create_ico.py` to convert `favicon.png` into a multi-resolution `favicon.ico` (16x16, 24x24, 32x32, 48x48, 64x64, 128x128 DIB + 256x256 PNG).
- Invokes PyInstaller with:
  - `--onefile --windowed` for a standalone single executable without a background console window.
  - `--icon favicon.ico` and `--add-data "favicon.png;."` for embedded app branding.
  - Module exclusions for heavy third-party packages (e.g., `matplotlib`, `numpy`, `pandas`, `scipy`) to minimize file size.
- Generates the final output binary at `dist\InvisibleTextObfuscator.exe`.

---

## Project Structure

```
.
├── .gitignore                    # Git exclusion rules for builds, caches, and environments
├── build.bat                     # Windows batch script to compile the standalone executable
├── CHANGELOG.md                  # Release version history and notable changes
├── create_ico.py                 # Multi-layer Windows ICO generator
├── favicon.ico                   # Application icon for Windows executable
├── Favicon.png                   # High-resolution source icon
├── gui.py                        # Tkinter desktop GUI implementation
├── InvisibleTextObfuscator.spec   # PyInstaller build specification
├── main.py                       # Application entry point (GUI launcher and CLI dispatcher)
├── obfuscator.py                 # Core text obfuscation, sanitization, and metrics engine
├── README.md                     # Project documentation
├── requirements.txt              # Optional runtime and build dependencies
├── test_gui.py                   # GUI component and callback integration tests
└── test_obfuscator.py            # Obfuscation engine unit tests
```

---

## License

No license has been selected yet. All rights are currently reserved pending author selection.
