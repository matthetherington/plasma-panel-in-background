// SPDX-License-Identifier: MIT
// Isolated API probe: no visible window and no connection to the live desktop.
// Run with QT_QPA_PLATFORM=offscreen /usr/lib64/qt6/bin/qml this-file.qml
import QtQuick
import QtQuick.Window
import org.kde.layershell as LayerShell

Window {
    id: host
    visible: false

    Item {
        id: widget
        readonly property var hostWindow: widget.Window.window

        Component.onCompleted: {
            try {
                if (hostWindow !== host) {
                    throw new Error("Item cannot resolve its containing QQuickWindow");
                }
                const layerWindow = hostWindow.LayerShell.Window;
                if (!layerWindow) {
                    throw new Error("LayerShell attached object unavailable");
                }
                const original = layerWindow.layer;
                layerWindow.layer = LayerShell.Window.LayerBottom;
                if (layerWindow.layer !== LayerShell.Window.LayerBottom) {
                    throw new Error("Layer assignment failed");
                }
                layerWindow.layer = original;
                if (layerWindow.layer !== original) {
                    throw new Error("Layer restoration failed");
                }
                console.log("PASS: item -> host window -> LayerShell attached object; layer write/read/restore");
                console.log("requestUpdate callable:", typeof hostWindow.requestUpdate === "function");
                Qt.exit(0);
            } catch (error) {
                console.error("FAIL:", error);
                Qt.exit(1);
            }
        }
    }
}
