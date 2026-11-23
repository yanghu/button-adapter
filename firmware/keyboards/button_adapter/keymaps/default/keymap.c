// Copyright 2026 yanghu
// SPDX-License-Identifier: GPL-2.0-or-later

#include QMK_KEYBOARD_H

// Standard QMK (non-Vial) default keymap for build verification & minimal fallback.
// For daily use, flash the `vial` keymap instead (`button_adapter_vial.uf2`).
const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
    [0] = LAYOUT(
        KC_F17,     KC_F18, KC_F13,       KC_F15,     KC_F14,              KC_F16
    ),
    [1] = LAYOUT(
        LCTL(KC_M), KC_ENT, LGUI(KC_TAB), LGUI(KC_D), LCTL(LGUI(KC_LEFT)), LCTL(LGUI(KC_RGHT))
    ),
};
