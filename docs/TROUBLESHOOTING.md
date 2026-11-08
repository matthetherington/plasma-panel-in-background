# Troubleshooting and recovery

## Widget missing or showing an import error

Check that the package is installed:

```sh
kpackagetool6 --type Plasma/Applet --show io.github.matthetherington.plasma.panelinbackground
```

You need Plasma on Wayland and your distribution's LayerShellQt QML module
(`org.kde.layershell`). You don't need a compiler or development headers.
After an upgrade, log out and back in to reload the widget.

## The panel is covered

Move or minimise the covering application, or switch to an uncovered desktop.
Touching the screen edge won't raise the panel. Enter Edit Mode to reveal its
small **P↓** control, then right-click and choose **Disable behind windows**.

## The controller has disappeared

That's expected outside Edit Mode: it keeps running without taking panel space.
Enter Edit Mode to reveal it, whether enabled or disabled. Its right-click menu
has an **Enable behind windows** or **Disable behind windows** action.

## Disable from a terminal

This disables **all** Panel in Background widgets in your running Plasma session.
Each restores its panel's saved visibility mode; other widgets are left alone.

```sh
qdbus-qt6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript \
  'for (var p of panels()) { for (var w of p.widgets("io.github.matthetherington.plasma.panelinbackground")) { w.currentConfigGroup=["General"]; w.writeConfig("enabled",false); w.reloadConfig(); } }'
```

Run as your desktop user, not root. Your distribution may call this command
`qdbus6` or place it in Qt's `bin` directory.

If the widget itself can't load, automatic restoration won't work. Remove the
broken widget in Edit Mode and choose your preferred visibility mode in Plasma's
panel settings. Log out and back in to recreate the panel on its normal layer.
Keep the panel and its other widgets.

## Plasma won't start

Stop Plasma before editing its configuration, and back up the current files.
Restoring a whole old layout can discard unrelated changes; repair only the
affected widget settings where possible.

The usual files are `plasma-org.kde.plasma.desktop-appletsrc` and `plasmashellrc`
in `~/.config` (or `$XDG_CONFIG_HOME`, if set). Custom shells may use other filenames.

See the [uninstall instructions](../README.md#disable-or-uninstall) once you've
disabled or removed the widgets.
