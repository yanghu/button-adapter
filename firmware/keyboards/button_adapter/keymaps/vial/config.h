// Copyright 2026 yanghu
// SPDX-License-Identifier: GPL-2.0-or-later

#pragma once

// Unique 8-byte Vial Keyboard UID
#define VIAL_KEYBOARD_UID {0x11, 0x95, 0x9C, 0xDD, 0x70, 0x74, 0x35, 0x45}

// Unlock Vial security-sensitive ops by holding Button A (0,0) + Button B (0,1)
#define VIAL_UNLOCK_COMBO_ROWS { 0, 0 }
#define VIAL_UNLOCK_COMBO_COLS { 0, 1 }

// 4 dynamic layers: 0 = macOS, 1 = Windows, 2 = Meeting/Media, 3 = Custom
#define DYNAMIC_KEYMAP_LAYER_COUNT 4

// Generous dynamic slots (RP2040 has 2 MB Flash / emulated EEPROM)
#define VIAL_TAP_DANCE_ENTRIES 8
#define VIAL_COMBO_ENTRIES 8
#define VIAL_KEY_OVERRIDE_ENTRIES 8
#define DYNAMIC_KEYMAP_MACRO_COUNT 16

// Responsive timings for Push-to-Talk tap-dance and A+B OS-switch combo
#define TAPPING_TERM 200
#define COMBO_TERM 50
