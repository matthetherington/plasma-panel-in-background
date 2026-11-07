// SPDX-License-Identifier: MIT
// Test-only client for KWin's private fake-input protocol (version 4).
// Wire request order/signatures follow plasma-wayland-protocols/fake-input.xml.
// Never connect to the user's real Wayland socket.
#include <wayland-client.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static const struct wl_message requests[] = {
    {"authenticate", "ss", NULL}, {"pointer_motion", "ff", NULL},
    {"button", "uu", NULL}, {"axis", "uf", NULL},
    {"touch_down", "2uff", NULL}, {"touch_motion", "2uff", NULL},
    {"touch_up", "2u", NULL}, {"touch_cancel", "2", NULL},
    {"touch_frame", "2", NULL}, {"pointer_motion_absolute", "3ff", NULL},
    {"keyboard_key", "4uu", NULL}
};
static const struct wl_interface interface = {
    "org_kde_kwin_fake_input", 4, 11, requests, 0, NULL
};
static struct wl_proxy *input;
static void global(void *data, struct wl_registry *registry, uint32_t name,
                   const char *name_string, uint32_t version)
{
    (void)data;
    if (!strcmp(name_string, interface.name) && version >= 4)
        input = wl_registry_bind(registry, name, &interface, 4);
}
static void removed(void *data, struct wl_registry *registry, uint32_t name)
{ (void)data; (void)registry; (void)name; }
static const struct wl_registry_listener listener = {global, removed};

int main(int argc, char **argv)
{
    const char *runtime = getenv("XDG_RUNTIME_DIR");
    const char *socket = getenv("WAYLAND_DISPLAY");
    const char prefix[] = "/tmp/opencode/panel-in-background-nested-";
    if (!runtime || strncmp(runtime, prefix, sizeof(prefix) - 1)
            || !socket || strcmp(socket, "panel-in-background-test") || argc < 4) {
        fprintf(stderr, "Refusing input outside disposable Panel in Background session\n");
        return 2;
    }
    struct wl_display *display = wl_display_connect("panel-in-background-test");
    if (!display) return 3;
    struct wl_registry *registry = wl_display_get_registry(display);
    wl_registry_add_listener(registry, &listener, NULL);
    wl_display_roundtrip(display);
    if (!input) { fprintf(stderr, "Fake input unavailable\n"); return 4; }
    wl_proxy_marshal(input, 0, "Panel in Background integration test", "Test disposable session only");
    wl_display_roundtrip(display);
    // Allow other clients to bind the pointer after wl_seat gains capabilities.
    // This virtual compositor has no persistent physical input devices.
    usleep(700000);
    const int serve = !strcmp(argv[1], "serve");
    if (serve) { puts("READY"); fflush(stdout); }
    do {
        char action[16];
        double x, y;
        if (serve) {
            if (scanf("%15s %lf %lf", action, &x, &y) != 3) break;
        } else {
            snprintf(action, sizeof(action), "%s", argv[1]);
            x = atof(argv[2]); y = atof(argv[3]);
        }
        wl_proxy_marshal(input, 9, wl_fixed_from_double(x), wl_fixed_from_double(y));
        wl_display_roundtrip(display);
        usleep(200000);
        if (!strcmp(action, "click") || !strcmp(action, "rightclick")) {
            uint32_t button = !strcmp(action, "rightclick") ? 0x111u : 0x110u;
            wl_proxy_marshal(input, 2, button, 1u);
            wl_display_roundtrip(display);
            usleep(200000);
            wl_proxy_marshal(input, 2, button, 0u);
        } else if (!strcmp(action, "escape") || !strcmp(action, "home") || !strcmp(action, "enter")) {
            uint32_t key = !strcmp(action, "home") ? 102u : (!strcmp(action, "enter") ? 28u : 1u);
            wl_proxy_marshal(input, 10, key, 1u);
            wl_proxy_marshal(input, 10, key, 0u);
        }
        wl_display_roundtrip(display);
        if (serve) { puts("DONE"); fflush(stdout); }
    } while (serve);
    usleep(500000);
    wl_proxy_destroy(input);
    wl_registry_destroy(registry);
    wl_display_disconnect(display);
    return 0;
}
