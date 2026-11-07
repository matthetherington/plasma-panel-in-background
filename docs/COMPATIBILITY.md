# Compatibility and limitations

## Tested configuration

| Component | Tested |
| --- | --- |
| Desktop/session | KDE Plasma / Wayland |
| Plasma, KWin, LayerShellQt | 6.8.2 |
| Qt | 6.11.2 |
| Distribution | Fedora Asahi Remix 45 development |
| Architecture | aarch64 / ARM64 |

The widget works on both side panels of the development machine. It contains no
architecture-specific binaries or Asahi-specific code, but other distributions,
architectures and Plasma versions haven't been tested.

The minimum supported version is not yet known. The metadata's Plasma 6.0 API
baseline describes the applet format; it does **not** promise support for every
Plasma 6 release. The required LayerShellQt QML module must be available.

## Tested in isolated sessions

- Partial overlap and full-screen maximisation, with the panel below applications.
- Restoring visibility after disable, removal or a change in Plasma's panel settings.
- Duplicate rejection, moving panels between edges, and moving widgets between panels.
- Settings persistence after normal and forced desktop-shell restarts.
- Hidden controller with no layout gap; compact control and working right-click
  toggle in Edit Mode, both enabled and disabled.
- Hover and screen-edge contact without raising the panel.
- Opening the launcher above applications and dismissing it with Escape.
- Entering and leaving Edit Mode without raising or hiding the panel.

## Still to test

- Multiple displays, mixed scaling, hotplug and output rotation.
- Tray menus, other applet popups, global shortcuts and drag-and-drop.
- Lock/unlock, suspend/resume, activities, Show Desktop and overview effects.
- Interactions with other extensions that change panel layers or visibility.

## Intentional limits

- Plasma Wayland only; X11 and other desktops are unsupported.
- No hover-to-raise: move or minimise covering windows to reach the panel.
- The controller is hidden normally and uses a small amount of space only in Edit Mode.
- Menus and launcher popups can appear above application windows.
- Special windows and desktop effects may behave differently. In particular,
  application windows set to “Keep Below Others” can share the panel's layer.

When reporting a problem, include your software versions, distribution,
architecture, display layout/scaling, affected widgets and steps to reproduce it.
Review logs and configuration for private information before sharing them.
