// Copyright 2026 yanghu
// SPDX-License-Identifier: GPL-2.0-or-later

#include QMK_KEYBOARD_H

// Standard QMK (non-Vial) default keymap for build verification & minimal fallback.
// For daily use, flash the `vial` keymap instead (`button_adapter_vial.uf2`).
const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
    [0] = LAYOUT(
        LOPT(KC_SPC), LGUI(LSFT(KC_A)), KC_PGUP, KC_PGDN, LGUI(LSFT(KC_LBRC)), LGUI(LSFT(KC_RBRC))
    ),
    [1] = LAYOUT(
        LWIN(KC_H),   LCTL(LSFT(KC_M)), KC_PGUP, KC_PGDN, LCTL(KC_PGUP),       LCTL(KC_PGDN)
    ),
};
