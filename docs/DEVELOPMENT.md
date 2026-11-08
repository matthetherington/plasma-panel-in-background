# Panel in Background: development

Run these commands from a source checkout. The `.plasmoid` archive doesn't include
build tools or tests.

## Build

Only Python 3 is needed:

```sh
python3 scripts/build_package.py
```

This creates `dist/plasma-panel-in-background-<version>.plasmoid` and a `.sha256` checksum, using the
version in `package/metadata.json`. The archive contains the widget, public docs
and MIT licence—not tests, local notes or backups.

Member order, timestamps and permissions are fixed. Builds are reproducible with
the same source and Python/zlib toolchain.

Verify the checksum from `dist/`:

```sh
sha256sum --check plasma-panel-in-background-0.4.0.plasmoid.sha256
```

## Packaging tests

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

These check archive contents, metadata, licence, checksum and reproducibility.
They don't start Plasma or install anything.

## Plasma integration tests

The harness currently uses Fedora's tool paths. It needs `kwin_wayland` with its
virtual backend, `plasmashell`, `dbus-run-session`, `qdbus-qt6`, `busctl`, Qt's `qml`
runner and `/usr/libexec/kactivitymanagerd`.

```sh
python3 tests/run-nested.py
python3 tests/run-nested.py --input
```

To test the built archive instead of the source widget:

```sh
python3 tests/run-nested.py --input --package dist/plasma-panel-in-background-0.4.0.plasmoid
```

Tests start a separate Plasma session with a private D-Bus bus and disposable XDG
directories under `/tmp/opencode` (create that directory first if needed). Your
desktop settings aren't changed, but this is **not a security sandbox**: test
processes still run as your user. Logs are kept in the printed directory.

`--input` needs a C compiler and Wayland development library for its test-only
input client. These aren't widget dependencies. Input is restricted to the private
test socket; global shortcuts and lockscreen integration are disabled.

To show the test desktop in a window and capture it with Spectacle:

```sh
python3 tests/run-nested.py --visible --diagnose
```

This is a short diagnostic, not the full test suite. Screenshots capture only the
nested desktop. Set `PIB_WIRE=1` or `PIB_QT_INPUT=1` for detailed input logs.

## Before publishing

1. Update `package/metadata.json` and `CHANGELOG.md`.
2. Run the packaging tests and build the archive.
3. Run integration tests with `--input --package` to check installation and behaviour.
4. Check the contents and checksum, then publish the archive and matching source.
5. Update the tested configurations in [COMPATIBILITY.md](COMPATIBILITY.md).
