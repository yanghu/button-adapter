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

// Default keycodes (all live-editable in https://vial.rocks):
//   - Layer 0 (_MAC): emits raw F13-F18 for host-side Hammerspoon routing
//     (see hammerspoon/button_adapter.lua & docs/HOST_INTEGRATION.md)
//   - Layer 1 (_WIN): standalone Windows shortcuts (zero host software required)
#define MAC_BTN_A      KC_F17              // Hammerspoon: App-aware Voice (Antigravity / Claude / Gemini)
#define MAC_BTN_B      KC_F18              // Hammerspoon: Background Google Meet (Tap=Mute, Hold=Hand)
#define MAC_STICK_UP   KC_F13              // Hammerspoon: Mission Control
#define MAC_STICK_DN   KC_F15              // Hammerspoon: App Exposé
#define MAC_STICK_LFT  KC_F14              // Hammerspoon: Previous Space
#define MAC_STICK_RGT  KC_F16              // Hammerspoon: Next Space

#define WIN_BTN_A      LCTL(KC_M)          // Antigravity Voice Input Toggle (Ctrl+M)
#define WIN_BTN_B      KC_ENT              // Enter (send right after dictation)
#define WIN_STICK_UP   LGUI(KC_TAB)        // Task View (Win+Tab)
#define WIN_STICK_DN   LGUI(KC_D)          // Show / Toggle Desktop (Win+D)
#define WIN_STICK_LFT  LCTL(LGUI(KC_LEFT)) // Previous Virtual Desktop (Ctrl+Win+Left)
#define WIN_STICK_RGT  LCTL(LGUI(KC_RGHT)) // Next Virtual Desktop (Ctrl+Win+Right)

// LAYOUT order: (Btn A [GP6], Btn B [GP7], Stick Up [GP0], Stick Down [GP1], Stick Left [GP2], Stick Right [GP4])
const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
    [_MAC] = LAYOUT(
        MAC_BTN_A,    MAC_BTN_B,    MAC_STICK_UP, MAC_STICK_DN, MAC_STICK_LFT, MAC_STICK_RGT
    ),
    [_WIN] = LAYOUT(
        WIN_BTN_A,    WIN_BTN_B,    WIN_STICK_UP, WIN_STICK_DN, WIN_STICK_LFT, WIN_STICK_RGT
    ),
    [_MEETING] = LAYOUT(
        KC_MUTE,      KC_MPLY,      KC_VOLU,      KC_VOLD,      KC_MPRV,       KC_MNXT
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
            .input  = { MAC_BTN_A, MAC_BTN_B, KC_NO, KC_NO },
            .output = TG(_WIN),
        };
        // Combo 1: Press Button A + Button B on Windows layer -> toggle back to macOS layer (LED turns Blue)
        const vial_combo_entry_t win_to_mac = {
            .input  = { WIN_BTN_A, WIN_BTN_B, KC_NO, KC_NO },
            .output = TG(_WIN),
        };

        dynamic_keymap_set_combo(0, &mac_to_win);
        dynamic_keymap_set_combo(1, &win_to_mac);
        vial_init(); // Reload seeded combos into active RAM immediately

        eeconfig_update_user(USER_EECONFIG_SEED_MAGIC);
    }
}
#endif
