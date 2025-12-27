# Z13 LED GUI

A lightweight GTK tray application with a graphical interface for controlling ASUS ROG Flow Z13 lighting via `z13-led`.

This project provides a system tray interface for managing keyboard and lightbar lighting on the ROG Flow Z13. It acts as a frontend for the upstream [`z13-led`](https://github.com/rpheuts/z13) utility and does **not** bundle or replace it.

---

## Features

- GTK-based GUI with system tray integration
- Controls keyboard and lightbar lighting
- Preset support and live preview
- Symbolic tray icon (adapts automatically to light/dark themes)
- Works on Wayland and X11
- No root privileges required for the GUI
- Compatible with immutable systems (Bazzite / Silverblue)

---

## Requirements

### Required
- `z13-led` (installed separately)
- Python 3
- GTK 3
- AppIndicator support 

### Optional
- Desktop environment with system tray support (See [AppIndicator and KStatusNotifierItem Support](https://extensions.gnome.org/extension/615/appindicator-support/) extension for gnome)

---

## Installation

### 1. Install `z13-led`

This project depends on the separate  [z13-led](https://github.com/rpheuts/z13) utility. Install it first, then return here to continue setup.

### Install Python dependencies

**Testers needed for Fedora Workstation and Ubuntu based distros**

#### Arch and Arch Based Distros

```bash
sudo pacman -S python python-gobject gtk3 libappindicator
```

#### Fedora (Workstation)
```bash
sudo dnf install python3 python3-gobject gtk3 libappindicator-gtk3
```

#### Bazzite / Fedora Atomic

Bazzite does not include GTK or AppIndicator development libraries in the base image.

**Option 1: Install dependencies system-wide**

```shell
sudo rpm-ostree install python3-gobject gtk3 libappindicator-gtk3
```

This modifies the system image and requires a reboot after running.

**Option 2: Use Distrobox (no system modification)**

If you prefer not to modify the host system, you can install dependencies inside a Distrobox container and run the application from there.

**TODO: Add distrobox instructions**

#### Ubuntu
```bash
sudo apt install python3 python3-gi python3-gi-cairo gir1.2-gtk-3.0 libappindicator3-1
```

---

## Installing the GUI

```bash
git clone https://github.com/ngencokamin/z13-led-gui
cd z13-led-gui
chmod +x install.sh
./install.sh
```

This installs:
- the launcher to `~/.local/bin`
- the symbolic icon to `~/.local/share/icons`
- a desktop entry for menu access

---

## Usage

You can start the application with:

```bash
z13-led-gui
```

Or by launching **Z13 LED GUI** from your desktop menu.

The application runs in the system tray and opens a full GUI when clicked.

---

## Notes

- This project does **not** bundle or modify `z13-led`
- All hardware interaction is handled by `z13-led`
- The GUI itself does not require root privileges

---

## License

MIT License.

This project is independent from `z13-led`, which is licensed separately under GPL-3.0.
