# Panel in Background

Keep KDE Plasma panels **above the wallpaper but behind application windows**.
Windows cover only the parts they overlap; the rest of the panel stays visible
and usable. Panels don't hide, reserve screen space, or rise at the screen edge.

Add one small QML widget to each panel you want to control. No native plugin,
root access or Plasma rebuild is needed.

![A terminal window partially covering a monitoring panel, with the uncovered widgets still visible.](docs/images/panel-in-background.png)

*Windows cover only the parts of the panel they overlap.*

## Motivation

Plasma 5 had a similar **Windows Can Cover** mode. It was removed in Plasma 6
and replaced with **Dodge Windows**; KDE's developers have
[said there are no plans to bring the old mode back](https://bugs.kde.org/show_bug.cgi?id=486701#c1).

Plasma 6's built-in visibility modes are:

- **Always visible:** stays above windows and reserves screen space.
- **Auto hide:** hides until you move the pointer to the screen edge.
- **Dodge windows:** hides the whole panel when a window overlaps it.
- **Windows go below:** stays above windows without reserving screen space.

None keeps the panel permanently behind application windows while leaving its
uncovered parts visible. This widget adds that behaviour. Unlike the old
Windows Can Cover mode, it doesn't raise the panel when you touch the screen edge.

## Requirements

- KDE Plasma on **Wayland**.
- LayerShellQt's `org.kde.layershell` QML module, `org.kde.kwindowsystem`,
  and Plasma's shell QML APIs, supplied by your distribution.
- `kpackagetool6` to install from a terminal.

Tested on Plasma **6.8.2** with Fedora Asahi Remix 45 development on ARM64.
Other configurations are unverified. See [compatibility](docs/COMPATIBILITY.md).

## Install

Install a downloaded `.plasmoid` file, adjusting the path as needed:

```sh
kpackagetool6 --type Plasma/Applet --install ./plasma-panel-in-background-0.3.0.plasmoid
```

Run this as your desktop user, without `sudo`. To build from source, see
[development instructions](docs/DEVELOPMENT.md).

1. Right-click your panel and enter **Edit Mode**.
2. Choose **Add Widgets**, search for **Panel in Background**, and add it to that panel.
3. Right-click its small **P** control and choose **Enable behind windows**.
4. Leave Edit Mode. The control disappears and takes no panel space.

Repeat for other panels as needed. The widget starts disabled and preserves your
existing panel layout.

## Behaviour

- To configure it, enter Edit Mode and right-click the small **P↓** control. Choose
  **Disable behind windows** to restore the previous visibility setting.
- The control appears in Edit Mode even when disabled, so you can always re-enable it.
- Settings survive logouts and desktop-shell restarts.
- Launcher and menu popups can open above applications without raising the panel.
- Choosing a different visibility mode in Plasma's panel settings disables the widget.
- Removing the widget restores the previous mode. Duplicate controllers are rejected.
- Plasma may temporarily reserve space for panel controls in Edit Mode.

## Upgrade

```sh
kpackagetool6 --type Plasma/Applet --upgrade ./plasma-panel-in-background-0.3.0.plasmoid
```

Use the new version's filename, then log out and back in to load the updated widget.

### Migrating from 0.2.0 or earlier

The rename changes the package ID from `org.kde.zzero` to
`io.github.matthetherington.plasma.panelinbackground`. Plasma treats these as
different widgets, so `--upgrade` cannot migrate the old one.

1. In Edit Mode, disable and remove the old controller from each panel. Keep the
   panels and their other widgets.
2. Remove the old package: `kpackagetool6 --type Plasma/Applet --remove org.kde.zzero`.
3. Install the new archive with `--install`, add **Panel in Background** to those
   panels, and enable it again.

Don't enable both versions on the same panel. Your existing installation is
unchanged until you choose to migrate.

## Disable or uninstall

Enter Edit Mode and use the control's right-click menu to disable it. To uninstall,
remove **Panel in Background** from every panel before removing the package:

```sh
kpackagetool6 --type Plasma/Applet --remove io.github.matthetherington.plasma.panelinbackground
```

Can't reach the widget? See [troubleshooting and recovery](docs/TROUBLESHOOTING.md).

## Licence and acknowledgements

Licensed under [MIT](LICENSE). KDE/Qt dependencies retain their own licences
and aren't bundled.

Inspired by
[plasma-panel-windows-can-cover](https://github.com/benjiman/plasma-panel-windows-can-cover)
and KDE's APIs. This is an independent QML implementation and includes none of that
project's code. It is not an official KDE add-on.
