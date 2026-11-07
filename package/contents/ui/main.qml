// SPDX-License-Identifier: MIT
import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.shell as Shell
import org.kde.layershell as LayerShell
import org.kde.kwindowsystem as WindowSystem
import "owners.js" as Owners

PlasmoidItem {
    id: root
    preferredRepresentation: fullRepresentation
    // Plasma removes hidden applets from the layout but shows them in Edit Mode.
    // The applet and its panel controller remain alive in both cases.
    Plasmoid.status: PlasmaCore.Types.HiddenStatus
    Plasmoid.contextualActions: [
        PlasmaCore.Action {
            text: Plasmoid.configuration.enabled ? "Disable behind windows" : "Enable behind windows"
            onTriggered: root.toggle()
        }
    ]
    readonly property var host: root.Window.window
    property var controlledHost: null
    property int originalLayer: LayerShell.Window.LayerTop
    property bool changing: false
    property bool ready: false
    property string statusText: "Disabled"

    function toggle() {
        console.log("PIB toggle clicked");
        Plasmoid.configuration.enabled = !Plasmoid.configuration.enabled;
    }

    function supported(window) {
        return WindowSystem.KWindowSystem.isPlatformWayland
            && window && typeof window.visibilityMode !== "undefined"
            && (Plasmoid.formFactor === PlasmaCore.Types.Horizontal
                || Plasmoid.formFactor === PlasmaCore.Types.Vertical);
    }

    function report(action, window) {
        console.log("PIB", action, "mode=" + window.visibilityMode,
                    "layer=" + window.LayerShell.Window.layer,
                    "zone=" + window.LayerShell.Window.exclusionZone);
    }

    function restore(restoreVisibility) {
        const window = controlledHost;
        controlledHost = null;
        if (window) {
            changing = true;
            window.LayerShell.Window.layer = originalLayer;
            if (restoreVisibility && Plasmoid.configuration.savedVisibility >= 0)
                window.visibilityMode = Plasmoid.configuration.savedVisibility;
            window.requestUpdate();
            report("restored", window);
            changing = false;
        }
        Owners.release(root);
    }

    function reconcile() {
        if (!ready)
            return;
        if (controlledHost && (controlledHost !== host || !Plasmoid.configuration.enabled)) {
            restore(true);
            Plasmoid.configuration.savedVisibility = -1;
        }
        if (!Plasmoid.configuration.enabled) {
            Plasmoid.configuration.savedVisibility = -1;
            statusText = "Disabled";
            return;
        }
        if (!supported(host)) {
            statusText = "Requires a supported Plasma Wayland panel";
            return;
        }
        if (controlledHost)
            return;
        if (!Owners.claim(host, root)) {
            statusText = "Another controller already owns this panel";
            console.warn("PIB duplicate controller rejected");
            Plasmoid.configuration.enabled = false;
            return;
        }
        changing = true;
        originalLayer = host.LayerShell.Window.layer;
        if (Plasmoid.configuration.savedVisibility < 0)
            Plasmoid.configuration.savedVisibility = host.visibilityMode;
        controlledHost = host;
        host.visibilityMode = Shell.Panel.WindowsGoBelow;
        host.LayerShell.Window.layer = LayerShell.Window.LayerBottom;
        host.requestUpdate();
        statusText = "Behind windows";
        report("enabled", host);
        changing = false;
    }

    onHostChanged: Qt.callLater(reconcile)
    Connections {
        target: Plasmoid.configuration
        function onEnabledChanged() { Qt.callLater(root.reconcile); }
    }
    Connections {
        target: root.controlledHost
        ignoreUnknownSignals: true
        function onVisibilityModeChanged() {
            if (!root.changing && root.controlledHost
                    && root.controlledHost.visibilityMode !== Shell.Panel.WindowsGoBelow) {
                // Preserve the native visibility choice the user just made.
                root.restore(false);
                Plasmoid.configuration.savedVisibility = -1;
                Plasmoid.configuration.enabled = false;
            }
        }
    }
    Component.onCompleted: {
        ready = true;
        Qt.callLater(reconcile);
    }
    Component.onDestruction: restore(true)

    fullRepresentation: Item {
        implicitWidth: 28
        implicitHeight: 28
        Layout.minimumWidth: 28
        Layout.preferredWidth: 28
        Layout.maximumWidth: 28
        Layout.minimumHeight: 28
        Layout.preferredHeight: 28
        Layout.maximumHeight: 28

        Controls.Button {
            anchors.centerIn: parent
            width: 28
            height: 28
            padding: 0
            text: Plasmoid.configuration.enabled ? "P↓" : "P"
            Accessible.name: "Behind windows: " + root.statusText
            onClicked: root.toggle()
        }
    }
}
