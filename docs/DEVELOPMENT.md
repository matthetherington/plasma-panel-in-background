# Panel in Background: development

Run these commands from a source checkout. The `.plasmoid` archive doesn't include
build tools or tests.

## Current follow-up work

The QML widget is released; the prototype's input blocker and initial live-panel
trial are no longer pending. The maintained list of testing gaps is in
[COMPATIBILITY.md](COMPATIBILITY.md#still-to-test), including broader
distribution/version coverage and establishing a minimum supported Plasma version.

Local planning, investigation and trial notes are historical records, not an
active backlog. Native-extension, CMake/RPM and GPL packaging proposals in those
notes were superseded by the MIT-licensed QML-only package.

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
sha256sum --check plasma-panel-in-background-0.4.1.plasmoid.sha256
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
python3 tests/run-nested.py --input --package dist/plasma-panel-in-background-0.4.1.plasmoid
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

## GitHub Actions

The workflow in `.github/workflows/ci.yml` runs on pull requests, pushes to `main`,
version-tag pushes (`v*`), and manual runs from the Actions tab.

1. Run packaging and release-validation unit tests, build the `.plasmoid`, verify
   its SHA-256 checksum and save both files as the **plasmoid** workflow artifact.
2. Download that same artifact and run the full isolated Plasma lifecycle/input
   suite in a Fedora 44 container on an x86_64 GitHub-hosted runner. It uses
   software rendering, a virtual display, a private D-Bus session and disposable
   configuration. The job loads the runner's `udmabuf` kernel module and exposes
   only `/dev/udmabuf` to the unprivileged container for software-rendering buffers;
   recent KWin versions require this even without a physical GPU. No host desktop
   or GPU is needed. Diagnostics are saved as
   **plasma-logs**, including on failure when logs are available.
3. For a pushed version tag only, publish a GitHub Release after both jobs pass,
   attaching the exact tested package and checksum. Notes come from the matching
   section in `CHANGELOG.md`. Tags containing `-` produce prereleases.

The tag must exactly match `v` plus `KPlugin.Version` in `package/metadata.json`,
and its changelog section must exist and contain release notes. A mismatch fails
the workflow rather than publishing incorrectly named assets. Release publication
uses GitHub's automatic `GITHUB_TOKEN`; no personal token or KDE Store credentials
are needed. Only the release job has repository write permission. Fork pull
requests run tests without publishing or receiving release credentials.

Enable Actions in the repository settings if it is disabled, and ensure repository
or organisation policies allow the release job's `contents: write` permission.
No self-hosted runner is required. The workflow must be committed and pushed before
it can run; existing tags do not automatically trigger it retroactively.

The container pins the Fedora release, not individual package versions, so its
Plasma/Qt packages track that release's updates. Passing this job is not a promise
of compatibility with every distro or Plasma version. Keep manually verified
configurations and remaining gaps in [COMPATIBILITY.md](COMPATIBILITY.md).

### Publish a new version

1. Update `package/metadata.json`, add a matching `## <version>` section to
   `CHANGELOG.md`, and update versioned examples in this file and `README.md`.
2. Commit the changes and push `main`. Check that CI passes.
3. Create and push the matching annotated tag, for example for a future `0.4.2`:

   ```sh
   git tag -a v0.4.2 -m "Release 0.4.2"
   git push origin v0.4.2
   ```

4. Wait for the tag's workflow to pass and publish the GitHub Release. Download
   its `.plasmoid` and `.sha256` assets and verify the checksum before upload.
   Do not upload the outer ZIP downloaded from the Actions artifacts page as a
   widget; extract the `.plasmoid` first if using that download instead.
5. Upload the `.plasmoid` to the **KDE Store** manually and update the listing's
   version, release notes and screenshots as needed. Store publishing is not
   automated by this workflow; it does not require or store your Store password.

Do not manually create the GitHub Release before the tag workflow: publication
deliberately fails if a release with that tag already exists, rather than silently
overwriting published files. Rerun failed jobs after resolving a transient failure;
for content changes, prefer a new version/tag. Replacing an already-published tag
and its release assets requires a deliberate manual operation.

For local-only builds, continue using the build and test commands above. CI
artifacts live on GitHub, not in your local `dist/` directory.
