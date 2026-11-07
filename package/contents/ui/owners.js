// SPDX-License-Identifier: MIT
.pragma library

// Shared by controller instances in this QML engine; never mutate the host QObject.
const owners = [];

function claim(window, owner) {
    for (const entry of owners) {
        if (entry.window === window)
            return entry.owner === owner;
    }
    owners.push({window: window, owner: owner});
    return true;
}

function release(owner) {
    for (let i = owners.length - 1; i >= 0; --i) {
        if (owners[i].owner === owner)
            owners.splice(i, 1);
    }
}
