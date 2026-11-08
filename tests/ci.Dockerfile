# SPDX-License-Identifier: MIT
# Fedora paths match the existing isolated-session test harness.
FROM registry.fedoraproject.org/fedora:44

RUN dnf install -y --setopt=install_weak_deps=False \
        python3 gcc glibc-devel wayland-devel dbus-daemon systemd \
        kwin plasma-workspace plasma-desktop kactivitymanagerd \
        layer-shell-qt kf6-kwindowsystem kf6-kpackage \
        qt6-qtdeclarative-devel qt6-qttools qt6-qtwayland \
        mesa-dri-drivers breeze-icon-theme google-noto-sans-fonts \
        shadow-utils \
    && dnf clean all \
    && useradd --uid 1000 --create-home ci \
    && mkdir -p /tmp/panel-in-background-tests \
    && chmod 1777 /tmp/panel-in-background-tests

# KWin's scheduling capability prevents exec when all container capabilities are
# dropped. The virtual/software-rendered test session does not need it.
RUN setcap -r /usr/bin/kwin_wayland

USER ci
ENV HOME=/home/ci
ENV KWIN_COMPOSE=O2 QT_QUICK_BACKEND=software
ENV XDG_CURRENT_DESKTOP=KDE XDG_SESSION_DESKTOP=KDE XDG_SESSION_TYPE=wayland
ENV KDE_FULL_SESSION=true KDE_SESSION_VERSION=6
WORKDIR /workspace
CMD ["python3", "tests/run-ci.py"]
