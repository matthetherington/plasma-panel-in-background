# Changelog

## 0.4.2

- Update project metadata.
- Add CI/CD with GitHub Actions to test, build and release

## 0.4.1

- Show an animated demonstration in the README and refresh the static screenshot.
- Keep the animation under 5 MB using a reduced resolution and 8 fps playback.
- Bundle both images and verify them in packaging tests.
- Clarify that installation does not automatically add or enable the widget.
- Point development documentation to the maintained compatibility testing gaps.
- No widget behaviour changes.

## 0.4.0

- Use the window cover-switch icon suggested in issue #1.
- Add distribution-specific setup commands for Debian/Ubuntu/Kubuntu,
  Fedora/Asahi, Arch/EndeavourOS and openSUSE.
- Explain how to resolve a missing `org.kde.layershell` QML module.
- Remove migration guidance for unpublished development versions.

## 0.3.0

- First public release of **Panel in Background**.
- Keep Plasma Wayland panels behind application windows without reserving space.
- Per-panel toggle with saved settings, restart persistence and safe removal.
- Hide the controller during normal use without leaving a layout gap.
- Show a compact **P / P↓** control in Edit Mode, even when disabled.
- Add right-click actions to enable or disable behind-windows mode.
- MIT licence, reproducible `.plasmoid` package and installation/recovery docs.
- Packaging tests and isolated Plasma lifecycle/input tests.
