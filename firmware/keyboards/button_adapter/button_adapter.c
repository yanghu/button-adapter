// Copyright 2026 yanghu
// SPDX-License-Identifier: GPL-2.0-or-later

#include "quantum.h"

// Seeed Studio XIAO RP2040 onboard LED pins:
//   - WS2812B NeoPixel: Data = GP12, Power Enable = GP11 (active-high)
//   - Discrete User RGB LED (active-low): R = GP17, G = GP16, B = GP25
#define XIAO_NEOPIXEL_POWER_PIN GP11
#define XIAO_USER_LED_G_PIN     GP16
#define XIAO_USER_LED_R_PIN     GP17
#define XIAO_USER_LED_B_PIN     GP25

// Gentle desk brightness (0..100, capped by rgblight.max_brightness in keyboard.json)
#define LAYER_LED_VAL 45

static void update_layer_led(layer_state_t state) {
#ifdef RGBLIGHT_ENABLE
    switch (get_highest_layer(state)) {
        case 0: // Layer 0: macOS — Calm Blue
            rgblight_sethsv_noeeprom(170, 220, LAYER_LED_VAL);
            break;
        case 1: // Layer 1: Windows — Calm Green
            rgblight_sethsv_noeeprom(85, 220, LAYER_LED_VAL);
            break;
        case 2: // Layer 2: Meeting / Media — Warm Amber
            rgblight_sethsv_noeeprom(25, 240, LAYER_LED_VAL);
            break;
        case 3: // Layer 3: Extra / Custom — Soft Purple
            rgblight_sethsv_noeeprom(200, 220, LAYER_LED_VAL);
            break;
        default:
            rgblight_sethsv_noeeprom(0, 0, LAYER_LED_VAL);
            break;
    }
#endif
}

void keyboard_pre_init_kb(void) {
    // Power on XIAO RP2040 onboard WS2812B NeoPixel
    gpio_set_pin_output(XIAO_NEOPIXEL_POWER_PIN);
    gpio_write_pin_high(XIAO_NEOPIXEL_POWER_PIN);

    // Keep discrete active-low user LEDs off so only the WS2812B glows through the top light pipe
    gpio_set_pin_output(XIAO_USER_LED_R_PIN);
    gpio_write_pin_high(XIAO_USER_LED_R_PIN);
    gpio_set_pin_output(XIAO_USER_LED_G_PIN);
    gpio_write_pin_high(XIAO_USER_LED_G_PIN);
    gpio_set_pin_output(XIAO_USER_LED_B_PIN);
    gpio_write_pin_high(XIAO_USER_LED_B_PIN);

    keyboard_pre_init_user();
}

void keyboard_post_init_kb(void) {
#ifdef RGBLIGHT_ENABLE
    rgblight_enable_noeeprom();
    rgblight_mode_noeeprom(RGBLIGHT_MODE_STATIC_LIGHT);
    update_layer_led(layer_state | default_layer_state);
#endif
    keyboard_post_init_user();
}

layer_state_t layer_state_set_kb(layer_state_t state) {
    state = layer_state_set_user(state);
    update_layer_led(state | default_layer_state);
    return state;
}

layer_state_t default_layer_state_set_kb(layer_state_t state) {
    state = default_layer_state_set_user(state);
    update_layer_led(layer_state | state);
    return state;
}
