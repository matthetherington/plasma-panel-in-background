// SPDX-License-Identifier: MIT
import QtQuick
import QtQuick.Window

Window {
    id: cover
    title: "Panel in Background cover test"
    width: 480
    height: 760
    visible: true
    color: "#b03030"
    Timer {
        interval: 5000
        running: true
        onTriggered: cover.showMaximized()
    }
}
