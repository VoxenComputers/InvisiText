"""
Automated GUI Tests for TextObfuscatorApp
========================================
Tests all GUI interactions, button actions, callbacks, and edge cases.
"""

import unittest
import tkinter as tk
from gui import TextObfuscatorApp
from obfuscator import count_invisible_characters, strip_invisible_characters


class TestTextObfuscatorGUI(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        # Withdraw window so it doesn't pop up and steal focus during tests
        self.root.withdraw()
        self.app = TextObfuscatorApp(self.root)
        self.root.update()

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_initial_state(self):
        """Test initial UI fields and stats."""
        self.assertEqual(self.root.title(), "InvisiText")
        self.assertIsNotNone(self.app.logo_image)
        self.assertEqual(self.app.input_text.get("1.0", "end-1c"), "")
        self.assertEqual(self.app.output_text.get("1.0", "end-1c"), "")
        self.assertEqual(self.app.raw_output_text, "")
        self.assertIn("Chars: 0", self.app.in_stats_label.cget("text"))
        self.assertIn("Chars: 0", self.app.out_stats_label.cget("text"))

    def test_obfuscate_workflow(self):
        """Test typing input, clicking obfuscate, and inspecting output."""
        sample = "Clean up my Bill Splitter project and ensure ZeroCode rules."
        self.app.input_text.insert("1.0", sample)
        self.app._update_input_stats()

        # Check input stats updated
        self.assertIn(f"Chars: {len(sample)}", self.app.in_stats_label.cget("text"))

        # Trigger obfuscation
        self.app.obfuscate_text()
        self.root.update()

        output = self.app.output_text.get("1.0", "end-1c")
        self.assertGreater(len(output), len(sample))
        self.assertGreater(count_invisible_characters(output), 0)
        self.assertEqual(strip_invisible_characters(output), sample)
        self.assertEqual(self.app.raw_output_text, output)

        # Check output stats
        out_stats_str = self.app.out_stats_label.cget("text")
        self.assertIn("hidden", out_stats_str)
        self.assertIn("✓ Obfuscated successfully!", self.app.status_label.cget("text"))

    def test_copy_functionality(self):
        """Test copy button copies output to clipboard."""
        sample = "Short test text for clipboard"
        self.app.input_text.insert("1.0", sample)
        self.app.obfuscate_text()
        self.root.update()

        self.app.copy_output()
        self.root.update()

        clipboard_text = self.root.clipboard_get()
        self.assertEqual(clipboard_text, self.app.raw_output_text)
        self.assertIn("✓ Copied", self.app.status_label.cget("text"))

    def test_reveal_hidden_toggle(self):
        """Test reveal hidden markers toggle."""
        sample = "Secret message"
        self.app.input_text.insert("1.0", sample)
        self.app.obfuscate_text()
        self.root.update()

        # Toggle Reveal ON
        self.app.toggle_reveal_mode()
        self.root.update()
        revealed_text = self.app.output_text.get("1.0", "end-1c")
        self.assertIn("[ZWSP]", revealed_text)
        self.assertEqual(self.app.reveal_btn.cget("text"), "🔒 Hide Markers")

        # Toggle Reveal OFF
        self.app.toggle_reveal_mode()
        self.root.update()
        hidden_text = self.app.output_text.get("1.0", "end-1c")
        self.assertNotIn("[ZWSP]", hidden_text)
        self.assertEqual(hidden_text, self.app.raw_output_text)

    def test_strip_from_input(self):
        """Test strip invisible characters button on input field."""
        sample_with_zwsp = "H\u200be\u200bl\u200bl\u200bo"
        self.app.input_text.insert("1.0", sample_with_zwsp)
        self.app.strip_invisible_from_input()
        self.root.update()

        cleaned = self.app.input_text.get("1.0", "end-1c")
        self.assertEqual(cleaned, "Hello")
        self.assertIn("Stripped 4 invisible characters", self.app.status_label.cget("text"))

    def test_empty_input_handling(self):
        """Test clicking obfuscate with empty input shows warning without crashing."""
        self.app.input_text.delete("1.0", tk.END)
        self.app.obfuscate_text()
        self.root.update()

        self.assertEqual(self.app.output_text.get("1.0", "end-1c"), "")
        self.assertIn("⚠️ Input text is empty", self.app.status_label.cget("text"))

    def test_clear_all(self):
        """Test clear all resets input, output, stats and state."""
        self.app.input_text.insert("1.0", "Some text")
        self.app.obfuscate_text()
        self.root.update()

        self.app.clear_all()
        self.root.update()

        self.assertEqual(self.app.input_text.get("1.0", "end-1c"), "")
        self.assertEqual(self.app.output_text.get("1.0", "end-1c"), "")
        self.assertEqual(self.app.raw_output_text, "")
        self.assertIn("Chars: 0", self.app.in_stats_label.cget("text"))
        self.assertIn("Chars: 0", self.app.out_stats_label.cget("text"))
        self.assertIn("All fields reset", self.app.status_label.cget("text"))

    def test_unicode_and_emojis(self):
        """Test unicode characters and emojis through GUI."""
        unicode_sample = "Привет мир! 🌍🚀 Déjà vu café 123"
        self.app.input_text.insert("1.0", unicode_sample)
        self.app.obfuscate_text()
        self.root.update()

        output = self.app.output_text.get("1.0", "end-1c")
        self.assertIn("🌍🚀", output)
        self.assertEqual(strip_invisible_characters(output), unicode_sample)

    def test_frequency_selection(self):
        """Test switching selectable frequency levels."""
        self.assertEqual(self.app.selected_freq_level, "Normal")
        self.assertEqual(self.app.get_frequency_value(), 0.45)

        self.app.set_frequency_level("Minimum")
        self.assertEqual(self.app.selected_freq_level, "Minimum")
        self.assertEqual(self.app.get_frequency_value(), 0.20)

        self.app.set_frequency_level("Maximum")
        self.assertEqual(self.app.selected_freq_level, "Maximum")
        self.assertEqual(self.app.get_frequency_value(), 1.00)

        self.app.set_frequency_level("Medium")
        self.assertEqual(self.app.selected_freq_level, "Medium")
        self.assertEqual(self.app.get_frequency_value(), 0.70)

    def test_window_scaling(self):
        """Test that bottom controls remain visible across various window sizes."""
        self.root.deiconify()
        for width, height in [(700, 450), (980, 640), (1200, 800)]:
            self.root.geometry(f"{width}x{height}")
            self.root.update()

            # Verify action bar and status bar are positioned inside the window
            action_y = self.app.action_bar_frame.winfo_y()
            status_y = self.app.status_bar_frame.winfo_y()

            # Status bar is at the bottom, action bar is immediately above it
            self.assertGreater(action_y, 0)
            self.assertGreater(status_y, action_y)
            self.assertLess(status_y, height)
        self.root.withdraw()


if __name__ == "__main__":
    unittest.main()
