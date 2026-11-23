// Copyright 2026 yanghu
// SPDX-License-Identifier: GPL-2.0-or-later

#include QMK_KEYBOARD_H

#ifdef VIAL_ENABLE
#    include "vial.h"
#    include "dynamic_keymap.h"
#    include "eeconfig.h"
#endif

// Layer definitions (indicated by XIAO RP2040 onboard WS2812B LED in button_adapter.c):
//   _MAC     (0) -> Calm Blue
//   _WIN     (1) -> Calm Green
//   _MEETING (2) -> Warm Amber
//   _EXTRA   (3) -> Soft Purple
enum adapter_layers {
    _MAC = 0,
    _WIN,
    _MEETING,
    _EXTRA,
};

// Default Vibe Coding keycodes (all live-editable in https://vial.rocks)
#define MAC_VOICE     LOPT(KC_SPC)         // Superwhisper / Wispr Flow Push-to-Talk
#define MAC_MUTE      LGUI(LSFT(KC_A))     // macOS Zoom / Meet Mute Toggle (or remap to KC_MUTE)
#define MAC_PREV_TAB  LGUI(LSFT(KC_LBRC))  // Previous Tab / Reject Diff
#define MAC_NEXT_TAB  LGUI(LSFT(KC_RBRC))  // Next Tab / Accept Diff

#define WIN_VOICE     LWIN(KC_H)           // Windows Voice Typing / PTT
#define WIN_MUTE      LCTL(LSFT(KC_M))     // Windows Teams / Meet Mute Toggle
#define WIN_PREV_TAB  LCTL(KC_PGUP)        // Previous Tab
#define WIN_NEXT_TAB  LCTL(KC_PGDN)        // Next Tab

// LAYOUT order: (Btn A [GP6], Btn B [GP7], Stick Up [GP0], Stick Down [GP1], Stick Left [GP2], Stick Right [GP4])
const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
    [_MAC] = LAYOUT(
        MAC_VOICE,    MAC_MUTE,     KC_PGUP,      KC_PGDN,      MAC_PREV_TAB, MAC_NEXT_TAB
    ),
    [_WIN] = LAYOUT(
        WIN_VOICE,    WIN_MUTE,     KC_PGUP,      KC_PGDN,      WIN_PREV_TAB, WIN_NEXT_TAB
    ),
    [_MEETING] = LAYOUT(
        KC_MUTE,      KC_MPLY,      KC_VOLU,      KC_VOLD,      KC_MPRV,      KC_MNXT
    ),
    [_EXTRA] = LAYOUT(
        KC_TRNS,      KC_TRNS,      KC_TRNS,      KC_TRNS,      KC_TRNS,      KC_TRNS
    ),
};

#if defined(VIAL_ENABLE) && defined(VIAL_COMBO_ENABLE)
// Non-zero sentinel stored in user EEPROM after factory combos are seeded once.
// Preserves any custom combo edits made later in Vial, and cleanly re-seeds on EEPROM reset.
#define USER_EECONFIG_SEED_MAGIC 0x5649414CU

void keyboard_post_init_user(void) {
    if (eeconfig_read_user() != USER_EECONFIG_SEED_MAGIC) {
        // Combo 0: Press Button A + Button B on macOS layer -> toggle Windows layer (LED turns Green)
        const vial_combo_entry_t mac_to_win = {
            .input  = { MAC_VOICE, MAC_MUTE, KC_NO, KC_NO },
            .output = TG(_WIN),
        };
        // Combo 1: Press Button A + Button B on Windows layer -> toggle back to macOS layer (LED turns Blue)
        const vial_combo_entry_t win_to_mac = {
            .input  = { WIN_VOICE, WIN_MUTE, KC_NO, KC_NO },
            .output = TG(_WIN),
        };

        dynamic_keymap_set_combo(0, &mac_to_win);
        dynamic_keymap_set_combo(1, &win_to_mac);
        vial_init(); // Reload seeded combos into active RAM immediately

        eeconfig_update_user(USER_EECONFIG_SEED_MAGIC);
    }
}
#endif
