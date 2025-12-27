#!/usr/bin/python3
"""
Z13 LED GUI - A GTK tray application for controlling ASUS ROG Flow Z13 lighting.

This module provides a graphical interface for managing keyboard and lightbar
lighting on the ROG Flow Z13 laptop. It acts as a frontend to the 'z13-led'
utility, handling user interactions and state management while delegating
hardware control to the external binary.
"""

import json
import os
import subprocess
from dataclasses import dataclass
from typing import Dict, Tuple, Optional, Callable

import gi
gi.require_version("Gtk", "3.0")

import shutil
from pathlib import Path


HAVE_INDICATOR = True
try:
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import AppIndicator3  # type: ignore
except Exception:
    HAVE_INDICATOR = False

from gi.repository import Gtk, Gdk, GLib  # type: ignore


APP_ID = "local.z13_led_gui"

CONFIG_DIR = os.path.join(
    os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
    "z13-led",
)
STATE_PATH = os.path.join(CONFIG_DIR, "state.json")

FALLBACK_THEME_ICON = "keyboard-brightness-symbolic"


PRESETS: Dict[str, Dict[str, object]] = {
    "Off":    {"kb_on": False, "kb_rgb": (0, 0, 0),      "lb_on": False, "lb_rgb": (255, 255, 255)},
    "Red":    {"kb_on": True,  "kb_rgb": (255, 0, 0),    "lb_on": True,  "lb_rgb": (255, 0, 0)},
    "Blue":   {"kb_on": True,  "kb_rgb": (0, 102, 255),  "lb_on": True,  "lb_rgb": (0, 102, 255)},
    "Green":  {"kb_on": True,  "kb_rgb": (0, 255, 102),  "lb_on": True,  "lb_rgb": (0, 255, 102)},
    "Purple": {"kb_on": True,  "kb_rgb": (138, 43, 226), "lb_on": True,  "lb_rgb": (138, 43, 226)},
}


def clamp8(x: float) -> int:
    """Clamp a float value to 0-1 range and convert to 8-bit integer (0-255)."""
    v = int(round(max(0.0, min(1.0, x)) * 255.0))
    return max(0, min(255, v))


def rgba_to_rgb8(rgba: Gdk.RGBA) -> Tuple[int, int, int]:
    """Convert a Gdk.RGBA to an RGB tuple of 8-bit integers."""
    return (clamp8(rgba.red), clamp8(rgba.green), clamp8(rgba.blue))


def rgb8_to_rgba(r: int, g: int, b: int) -> Gdk.RGBA:
    """Convert RGB 8-bit integers to a Gdk.RGBA."""
    rgba = Gdk.RGBA()
    rgba.red = max(0, min(255, r)) / 255.0
    rgba.green = max(0, min(255, g)) / 255.0
    rgba.blue = max(0, min(255, b)) / 255.0
    rgba.alpha = 1.0
    return rgba


def run_cmd(args: list) -> None:
    """Run a subprocess command, raising an exception on failure."""
    subprocess.run(args, check=True)


def find_z13_led() -> Optional[str]:
    """
    Locate the z13-led binary in a way that works for GUI apps
    launched outside of a shell (GNOME, Wayland, etc).
    """
    # 1. Try PATH first
    path = shutil.which("z13-led")
    if path:
        return path

    # 2. Fallback to ~/.local/bin
    local = Path.home() / ".local" / "bin" / "z13-led"
    if local.exists() and local.is_file():
        return str(local)

    return None


@dataclass
class State:
    """Application state for LED settings and preferences."""
    kb_on: bool = True
    kb_rgb: Tuple[int, int, int] = (255, 255, 255)
    lb_on: bool = True
    lb_rgb: Tuple[int, int, int] = (255, 255, 255)
    live_preview: bool = True

    @staticmethod
    def load() -> "State":
        """Load state from JSON file, with fallbacks for missing or corrupted data."""
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                raw = json.load(f)
            return State(
                kb_on=bool(raw.get("kb_on", True)),
                kb_rgb=tuple(raw.get("kb_rgb", [255, 255, 255]))[:3],  # type: ignore
                lb_on=bool(raw.get("lb_on", True)),
                lb_rgb=tuple(raw.get("lb_rgb", [255, 255, 255]))[:3],  # type: ignore
                live_preview=bool(raw.get("live_preview", True)),
            )
        except FileNotFoundError:
            return State()
        except Exception:
            # If corrupted, fall back safely.
            return State()

    def save(self) -> None:
        """Save current state to JSON file."""
        os.makedirs(CONFIG_DIR, exist_ok=True)
        payload = {
            "kb_on": self.kb_on,
            "kb_rgb": list(self.kb_rgb),
            "lb_on": self.lb_on,
            "lb_rgb": list(self.lb_rgb),
            "live_preview": self.live_preview,
        }
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)


class Z13LedGui(Gtk.Window):
    """Main GUI window for LED control settings."""

    def __init__(self, state: State, z13_led: Optional[str]):
        super().__init__(title="ROG Flow Z13 LED Control")
        self.set_border_width(14)
        self.set_default_size(540, -1)

        self.state = state
        
        self.z13_led = z13_led

        # Debounce handle for live preview applies
        self._apply_timeout_id: Optional[int] = None
        self._apply_debounce_ms = 150

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.add(outer)

        # ---------- Keyboard ----------
        kb_frame = Gtk.Frame(label="Keyboard")
        kb_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        kb_box.set_border_width(10)
        kb_frame.add(kb_box)

        kb_top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        kb_box.pack_start(kb_top, False, False, 0)

        self.kb_combo = Gtk.ComboBoxText()
        self.kb_combo.append_text("Off")
        self.kb_combo.append_text("On")
        self.kb_combo.set_active(1 if self.state.kb_on else 0)
        self.kb_combo.connect("changed", self.on_kb_state_changed)

        kb_top.pack_start(Gtk.Label(label="State:", xalign=0), True, True, 0)
        kb_top.pack_end(self.kb_combo, False, False, 0)

        self.kb_color = Gtk.ColorButton()
        self.kb_color.set_rgba(rgb8_to_rgba(*self.state.kb_rgb))
        self.kb_color.set_title("Keyboard Color")
        self.kb_color.set_use_alpha(False)
        self.kb_color.connect("color-set", self.on_kb_color_changed)

        kb_color_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        kb_color_row.pack_start(Gtk.Label(label="Color:", xalign=0), True, True, 0)
        kb_color_row.pack_end(self.kb_color, False, False, 0)
        kb_box.pack_start(kb_color_row, False, False, 0)

        outer.pack_start(kb_frame, False, False, 0)

        # ---------- Lightbar ----------
        lb_frame = Gtk.Frame(label="Lightbar")
        lb_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        lb_box.set_border_width(10)
        lb_frame.add(lb_box)

        lb_top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        lb_box.pack_start(lb_top, False, False, 0)

        self.lb_combo = Gtk.ComboBoxText()
        self.lb_combo.append_text("Off")
        self.lb_combo.append_text("On")
        self.lb_combo.set_active(1 if self.state.lb_on else 0)
        self.lb_combo.connect("changed", self.on_lb_state_changed)

        lb_top.pack_start(Gtk.Label(label="State:", xalign=0), True, True, 0)
        lb_top.pack_end(self.lb_combo, False, False, 0)

        self.lb_color = Gtk.ColorButton()
        self.lb_color.set_rgba(rgb8_to_rgba(*self.state.lb_rgb))
        self.lb_color.set_title("Lightbar Color")
        self.lb_color.set_use_alpha(False)
        self.lb_color.connect("color-set", self.on_lb_color_changed)

        lb_color_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        lb_color_row.pack_start(Gtk.Label(label="Color:", xalign=0), True, True, 0)
        lb_color_row.pack_end(self.lb_color, False, False, 0)
        lb_box.pack_start(lb_color_row, False, False, 0)

        outer.pack_start(lb_frame, False, False, 0)

        # ---------- Presets ----------
        preset_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        for name in ["Off", "Red", "Blue", "Green", "Purple"]:
            btn = Gtk.Button(label=name)
            btn.connect("clicked", self.on_preset_clicked, name)
            preset_box.pack_start(btn, True, True, 0)
        outer.pack_start(preset_box, False, False, 0)

        # ---------- Live preview + actions ----------
        bottom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.preview_check = Gtk.CheckButton(label="Live preview")
        self.preview_check.set_active(self.state.live_preview)
        self.preview_check.connect("toggled", self.on_preview_toggled)
        bottom.pack_start(self.preview_check, False, False, 0)

        self.apply_btn = Gtk.Button(label="Apply")
        self.apply_btn.connect("clicked", self.on_apply_clicked)
        close_btn = Gtk.Button(label="Close")
        close_btn.connect("clicked", lambda *_: self.hide())

        bottom.pack_end(close_btn, False, False, 0)
        bottom.pack_end(self.apply_btn, False, False, 0)

        outer.pack_start(bottom, False, False, 0)

        self.sync_controls_from_state()

    def sync_controls_from_state(self) -> None:
        """Update UI controls to reflect the current state."""
        self.kb_color.set_sensitive(self.state.kb_on)
        self.lb_color.set_sensitive(self.state.lb_on)

        self.kb_combo.set_active(1 if self.state.kb_on else 0)
        self.lb_combo.set_active(1 if self.state.lb_on else 0)
        self.kb_color.set_rgba(rgb8_to_rgba(*self.state.kb_rgb))
        self.lb_color.set_rgba(rgb8_to_rgba(*self.state.lb_rgb))
        self.preview_check.set_active(self.state.live_preview)

    def schedule_live_apply(self) -> None:
        """Schedule a debounced live preview apply if enabled."""
        if not self.state.live_preview:
            return

        if self._apply_timeout_id is not None:
            GLib.source_remove(self._apply_timeout_id)
            self._apply_timeout_id = None

        def _do_apply() -> bool:
            self._apply_timeout_id = None
            self.apply_state(save=False)  # preview doesn't persist
            return False

        self._apply_timeout_id = GLib.timeout_add(self._apply_debounce_ms, _do_apply)

    def on_preview_toggled(self, _check: Gtk.CheckButton) -> None:
        """Handle live preview checkbox toggle."""
        self.state.live_preview = bool(self.preview_check.get_active())
        # Persist this preference immediately.
        self.state.save()

    def on_kb_state_changed(self, _combo: Gtk.ComboBoxText) -> None:
        """Handle keyboard on/off state change."""
        self.state.kb_on = (self.kb_combo.get_active_text() == "On")
        self.kb_color.set_sensitive(self.state.kb_on)
        self.schedule_live_apply()

    def on_lb_state_changed(self, _combo: Gtk.ComboBoxText) -> None:
        """Handle lightbar on/off state change."""
        self.state.lb_on = (self.lb_combo.get_active_text() == "On")
        self.lb_color.set_sensitive(self.state.lb_on)
        self.schedule_live_apply()

    def on_kb_color_changed(self, _btn: Gtk.ColorButton) -> None:
        """Handle keyboard color change."""
        self.state.kb_rgb = rgba_to_rgb8(self.kb_color.get_rgba())
        self.schedule_live_apply()

    def on_lb_color_changed(self, _btn: Gtk.ColorButton) -> None:
        """Handle lightbar color change."""
        self.state.lb_rgb = rgba_to_rgb8(self.lb_color.get_rgba())
        self.schedule_live_apply()

    def on_preset_clicked(self, _btn: Gtk.Button, name: str) -> None:
        """Handle preset button click."""
        preset = PRESETS[name]
        self.state.kb_on = bool(preset["kb_on"])
        self.state.lb_on = bool(preset["lb_on"])
        self.state.kb_rgb = tuple(preset["kb_rgb"])  # type: ignore
        self.state.lb_rgb = tuple(preset["lb_rgb"])  # type: ignore
        self.sync_controls_from_state()

        # If live preview is on, apply immediately (debounced). Otherwise, wait for Apply.
        self.schedule_live_apply()

    def on_apply_clicked(self, _btn: Gtk.Button) -> None:
        """Handle apply button click."""
        ok = self.apply_state(save=True)
        if ok:
            self.hide()
            self.set_visible(False)  # extra nudge for some shells/compositors

    def apply_state(self, save: bool) -> bool:
        """Apply the current state to the hardware via z13-led commands."""
        if not self.z13_led:
            self.show_error(
                "Could not find 'z13-led'.\n\n"
                "Please install it and ensure it exists at:\n"
                "~/.local/bin/z13-led"
            )
            return False

        try:
            if self.state.kb_on:
                r, g, b = self.state.kb_rgb
                run_cmd([self.z13_led, "--keyboard", "--color", str(r), str(g), str(b)])
            else:
                run_cmd([self.z13_led, "--keyboard", "--color", "0", "0", "0"])

            if self.state.lb_on:
                r, g, b = self.state.lb_rgb
                run_cmd([self.z13_led, "--lightbar", "--color", str(r), str(g), str(b)])
            else:
                run_cmd([self.z13_led, "--lightbar", "--off"])

            if save:
                self.state.save()

            return True

        except subprocess.CalledProcessError as e:
            self.show_error(f"Command failed:\n{e}")
        except Exception as e:
            self.show_error(f"Unexpected error:\n{e}")

        return False


    def show_error(self, msg: str) -> None:
        """Show an error dialog with the given message."""
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE,
            text="Z13 LED Control Error",
        )
        dialog.format_secondary_text(msg)
        dialog.run()
        dialog.destroy()


class App:
    """Main application class managing the GUI window and system tray indicator."""

    def __init__(self):
        self.state = State.load()
        self.z13_led = find_z13_led()
        
        self.win = Z13LedGui(self.state, self.z13_led)
        self.win.connect("delete-event", self.on_delete)


        self.indicator = None
        if HAVE_INDICATOR:
            self.setup_indicator()


    def setup_indicator(self) -> None:
        """Set up the system tray indicator with menu."""
        icon_name = "rog-symbolic"

        # Fallback if icon is not installed
        if not Gtk.IconTheme.get_default().has_icon(icon_name):
            icon_name = "keyboard-brightness-symbolic"

        self.indicator = AppIndicator3.Indicator.new(
            "z13-led-gui",
            icon_name,
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
        )

        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        menu = Gtk.Menu()

        open_item = Gtk.MenuItem(label="Open")
        open_item.connect("activate", lambda *_: self.show_window())
        menu.append(open_item)

        menu.append(Gtk.SeparatorMenuItem())

        for name in ["Off", "Red", "Blue", "Green", "Purple"]:
            item = Gtk.MenuItem(label=f"Preset: {name}")
            item.connect("activate", self.on_preset_menu, name)
            menu.append(item)

        menu.append(Gtk.SeparatorMenuItem())

        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", lambda *_: Gtk.main_quit())
        menu.append(quit_item)

        menu.show_all()
        self.indicator.set_menu(menu)

    def on_preset_menu(self, _item: Gtk.MenuItem, name: str) -> None:
        """Handle preset selection from tray menu."""
        preset = PRESETS[name]
        self.state.kb_on = bool(preset["kb_on"])
        self.state.lb_on = bool(preset["lb_on"])
        self.state.kb_rgb = tuple(preset["kb_rgb"])  # type: ignore
        self.state.lb_rgb = tuple(preset["lb_rgb"])  # type: ignore
        self.win.sync_controls_from_state()

        # Tray preset should feel immediate.
        self.win.apply_state(save=True)

    def show_window(self) -> None:
        """Show and present the main GUI window."""
        self.win.show_all()
        self.win.present()

    def on_delete(self, *_args) -> bool:
        """Handle window close event - hide instead of quit to keep tray alive."""
        # Hide instead of exiting so tray stays alive.
        self.win.hide()
        return True


def main() -> int:
    """Main entry point for the application."""
    app = App()
    app.show_window()
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
