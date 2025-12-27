# Z13 LED GUI - AI Agent Instructions

## Project Overview
This is a lightweight GTK tray application providing a graphical interface for controlling ASUS ROG Flow Z13 keyboard and lightbar lighting via the `z13-led` utility. The GUI acts as a frontend only - all hardware interaction is handled by the separate `z13-led` binary.

**Architecture**: Single Python script (`gui.py`) using GTK3 and AppIndicator for system tray integration. No complex components or services - just a tray icon that opens a GUI window on click.

## Key Dependencies
- **z13-led**: External utility (GPL-3.0) - must be installed separately, handles all LED control
- **Python 3** with GTK3 bindings
- **AppIndicator**: For system tray support (works on Wayland/X11)
- **Optional**: Desktop environment with tray support

## Development Workflow
1. **Setup**: Install `z13-led` first, then Python dependencies (GTK3, AppIndicator)
2. **Install GUI**: Run `./install.sh` - installs `gui.py` as `z13-led-gui` in `~/.local/bin`, copies icon and desktop entry
3. **Run**: Execute `z13-led-gui` or launch from desktop menu
4. **Debug**: Check system tray for icon; click to open GUI. No build step - pure Python.

## Code Patterns
- **Tray Integration**: Use `AppIndicator3.Indicator` for tray icon with symbolic SVG that adapts to themes
- **GUI Framework**: GTK3 with `Gtk.Application` and `Gtk.ApplicationWindow`
- **Installation**: Bash script creates launcher script, installs icon to `~/.local/share/icons/hicolor/symbolic/apps`, desktop file to `~/.local/share/applications`
- **No Root Required**: GUI runs as user, delegates hardware control to `z13-led`

## File Structure
- `gui.py`: Main application code (GTK tray + GUI window)
- `icons/rog-symbolic.svg`: Symbolic icon for tray and desktop
- `z13-led-gui.desktop`: Desktop entry for menu integration
- `install.sh`: Installation script (creates dirs, copies files, updates icon cache)

## Important Notes
- **Immutable Systems**: Compatible with Bazzite/Silverblue via distrobox or system-wide installs
- **No Bundling**: Never bundle or modify `z13-led` - it's a separate project
- **Testing**: Requires physical ROG Flow Z13 hardware or compatible device
- **Dependencies**: GTK/AppIndicator packages vary by distro (pacman, dnf, apt)

## Common Tasks
- **Add Preset**: Extend GUI with preset buttons calling `z13-led` with specific args
- **Live Preview**: Implement color picker widgets that update LEDs in real-time
- **Theme Adaptation**: Icon automatically adapts via symbolic SVG - no code changes needed