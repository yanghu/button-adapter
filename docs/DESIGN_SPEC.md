# Finalized Design Specification — 8BitDo 3.5mm to USB-C HID Adapter

> **Status**: Finalized Design Baseline (v1.0)
> **Scope**: Hardware architecture, electrical topology, verified MCU/jack specs, and QMK/Vial firmware design for a compact 3-port inline USB-C HID adapter.

---

## 1. Problem Statement & Core Goals

8BitDo's **Dual Super Buttons** and **Super Stick** are passive mechanical switch peripherals terminated in 3.5mm TRS plugs intended to connect to the rear of an 8BitDo Retro Mechanical Keyboard. Plugging multiple stiff 3.5mm connectors behind a keyboard wastes desk depth and ties the accessories to a specific keyboard.

This adapter decouples both accessories into a standalone, compact, magnetically-anchored **3.5mm TRS to USB-C HID inline hub** built for **Vibe Coding** and daily cross-platform work:
- **Voice Input / Push-to-Talk (PTT)** (e.g., Superwhisper / Wispr Flow / IDE voice input)
- **Instant Mute / Unmute** (Zoom / Google Meet / Teams / OS mute)
- **4-Way Super Stick AI Coding Shortcuts** (Accept/Reject Diff, tab/window switching, scrolling, macros)
- **Small-Batch Build Strategy (1–2 units)**: Off-the-shelf MCU board + heavy-duty metal panel-mount 3.5mm TRS jacks + point-to-point silicone hookup wire + screwless 3D-printed enclosure (**no custom PCB fabrication required**).

---

## 2. Locked Design Decisions

| Decision Node | Final Choice | Key Rationale |
| :--- | :--- | :--- |
| **Port Count** | **3 × 3.5mm TRS jacks** (6 GPIOs + common GND) | Exact fit for 1× Dual Super Buttons (1 plug / 2 switches) + 1× Super Stick (2 plugs / 4 switches); minimizes enclosure width and soldering. |
| **MCU Board** | **Seeed Studio XIAO RP2040** | Standardized `21.0 × 17.8 mm` dimensions with official DXF/STEP files, flat single-sided PCB back, symmetrical 2×7 2.54 mm pads for clean L2 fan-out wiring, USB-C, onboard WS2812B RGB LED, and drop-in footprint compatibility with **XIAO nRF52840** for future wireless ZMK upgrades. |
| **3.5mm TRS Jack** | **Heavy-duty all-metal / long-thread panel-mount** (**Switchcraft `35PRM3`** primary; **Tensility `54-00081`** alternate) | 100% of plug insertion/withdrawal stress is absorbed by the 3D-printed wall + metal nut; solid `2.8–3.0 mm` FDM wall requires no fragile wall thinning; premium tactile durability. |
| **Sourcing Region** | **United States** (DigiKey / Mouser / Amazon / Tensility) | Parts locked to stocked US distributor SKUs with published mechanical drawings. |
| **Firmware** | **QMK / Vial** | Browser/desktop GUI remapping (`vial.rocks`) after one-time `.uf2` flash, instant cold boot, no unwanted USB flash drive popup on macOS/Windows, native Tap-Hold / Tap-Dance / Combos / Layers. |
| **Target OS** | **macOS + Windows Dual-Layer** | Layer 0 = macOS, Layer 1 = Windows; switched via button combo or Vial toggle, indicated by onboard WS2812B RGB LED color. |
| **Enclosure Layout** | **L2 Inline Pass-Through** | 3× 3.5mm jacks on rear wall, 1× USB-C centered on opposite front wall. Narrowest footprint (`~58 mm` wide) and straight fan-out internal wiring with zero sharp wire bends. |
| **Enclosure Fastening** | **Screwless Snap-Fit / Sliding Lid** | Zero screws or heat-set brass inserts; open-top bottom tray holds jacks & MCU for easy soldering before closing the lid. |
| **Enclosure Features** | `BOOT` & `RESET` pinholes, engraved `1 / 2 / 3` jack labels, WS2812B LED window, **4× bottom neodymium magnet recesses** | Compact wired-only volume (no unused LiPo battery bay; no rubber feet recesses since bottom magnets anchor the unit to a steel desk surface, monitor base, or adhesive strike plate). |

---

## 3. Peripheral Electrical Interface

Both 8BitDo peripherals use purely passive mechanical microswitches that short **Tip** or **Ring** to **Sleeve (GND)** when actuated (no active electronics, no power rails, no analog potentiometers):

| Peripheral | 3.5mm Plugs | Channels | Electrical Behavior |
| :--- | :--- | :--- | :--- |
| **8BitDo Dual Super Buttons** | 1 × 3.5mm TRS | 2 (Button A, Button B) | Tip ↔ Sleeve (Switch 1), Ring ↔ Sleeve (Switch 2) |
| **8BitDo Super Stick** | 2 × 3.5mm TRS (Y-split tail) | 4 (Up, Down, Left, Right; 8-way digital) | Each TRS plug carries 2 directional switches shorted to Sleeve |

### Circuit Topology (Zero External Passive Components)
- Every jack's **Sleeve** terminal is tied together (daisy-chained) to XIAO **`GND`**.
- Every jack's **Tip** and **Ring** terminals connect directly to 6 dedicated 3.3V digital GPIOs on the XIAO RP2040.
- Firmware enables internal weak pull-ups (`INPUT_PULLUP` / QMK `DIRECT_PINS` active-low scanning). No external resistors or diodes are needed.

> **Electrical Safety Note**: XIAO RP2040 GPIOs are strictly **3.3V logic**. Only passive switch peripherals (short-to-GND) should be plugged into the 3.5mm jacks. Never plug an active audio source or powered device into these jacks.

---

## 4. Verified MCU Specification — Seeed Studio XIAO RP2040

Source: [Seeed Studio XIAO RP2040 Official Wiki](https://wiki.seeedstudio.com/XIAO-RP2040/) & [XIAO Series SoM Datasheet](https://files.seeedstudio.com/wiki/XIAO/Seeed-Studio-XIAO-Series-SOM-Datasheet.pdf).

### Key Hardware Parameters
- **SKU**: `102010428` (standard **un-soldered** version — do **not** buy the pre-soldered header version so wires can solder directly into the through-holes cleanly inside the low-profile case)
- **MCU**: Raspberry Pi RP2040 (Dual-core Cortex-M0+ up to 133 MHz, 264 KB SRAM, 2 MB Flash)
- **Form Factor**: **`21.0 × 17.8 mm`** PCB (`~3.5 mm` overall height including USB-C receptacle), **single-sided SMD** (completely flat backside)
- **Header Pitch**: 2 × 7 pins along the `21.0 mm` edges, `2.54 mm` pitch, `15.24 mm` (0.6") row spacing
- **Buttons**: Onboard tactile **`B` (BOOT)** and **`R` (RESET)** switches on the top surface
- **Onboard LEDs**:
  - **WS2812B NeoPixel RGB LED** (located between `B` and `R` buttons):
    - Data Pin: **`GPIO12`**
    - Power Enable Pin (`NEOPIXEL_POWER`): **`GPIO11`** (**CRITICAL**: Firmware MUST set `GPIO11` HIGH on boot to power the WS2812B!)
  - **Discrete 3-Color User LED** (located near USB-C port, **active-low**):
    - Red = `GPIO17`, Green = `GPIO16`, Blue = `GPIO25`

### Finalized GPIO Assignment (Optimized for L2 Inline Fan-Out)

Orientation: Viewing XIAO RP2040 from the **top** (components up) with **USB-C facing North (`+Y`)** and the **3 × 3.5mm jacks along South (`-Y`)**:

| Logical Input | Jack # | TRS Contact | XIAO Label | RP2040 GPIO | QMK Direct Pin | Physical Side on XIAO |
| :--- | :---: | :--- | :---: | :---: | :---: | :--- |
| **Switch 1 (Button A)** | Jack 1 (Left) | Tip | `D4` | `GPIO6` | `GP6` | Left edge, pin 5 from USB-C |
| **Switch 2 (Button B)** | Jack 1 (Left) | Ring | `D5` | `GPIO7` | `GP7` | Left edge, pin 6 from USB-C |
| **Switch 3 (Stick 1-A)** | Jack 2 (Center) | Tip | `D6` | `GPIO0` | `GP0` | Left edge, pin 7 (bottom-left) |
| **Switch 4 (Stick 1-B)** | Jack 2 (Center) | Ring | `D7` | `GPIO1` | `GP1` | Right edge, pin 7 (bottom-right) |
| **Switch 5 (Stick 2-A)** | Jack 3 (Right) | Tip | `D8` | `GPIO2` | `GP2` | Right edge, pin 6 from USB-C |
| **Switch 6 (Stick 2-B)** | Jack 3 (Right) | Ring | `D9` | `GPIO4` | `GP4` | Right edge, pin 5 from USB-C |
| **Common Ground** | Jacks 1, 2, 3 | Sleeve (all 3) | `GND` | `GND` | `GND` | Right edge, pin 2 from USB-C |

**Why `D4–D9`?**
1. **Zero wire crossovers** in the L2 Inline layout: the bottom 3 pins on each edge fan straight out to Jacks 1, 2, and 3.
2. **All 4 ADC pins (`D0–D3` / `GP26–GP29`) and `D10` (`GP3`) remain unused** for future expansion.
3. **Drop-in XIAO nRF52840 compatibility**: `D4–D9` are standard GPIOs across the entire XIAO family.
4. **No RP2040 boot-strap conflicts**: `GP0, GP1, GP2, GP4, GP6, GP7` are clean general-purpose inputs.

> **Note on Super Stick Plug Mapping**: The two 3.5mm plugs on the Super Stick are visually identical. Because Vial allows instant software remapping of all 6 switch slots in the browser without recompiling, the physical order of Tip/Ring or Jack 2 vs Jack 3 does not require rewiring if swapped.

---

## 5. Firmware Architecture — QMK / Vial (Phase 3 Spec)

### Core Configuration
- **MCU / Bootloader**: `RP2040`, UF2 bootloader (`BOOT` button + plug-in, plus QMK `QK_BOOT` combo for screwless/pinless future updates)
- **Matrix Mode**: `DIRECT_PINS` (`1 × 6` or `2 × 3` direct-pin matrix, no diodes):
  ```c
  // Logical order: [J1_Tip, J1_Ring, J2_Tip, J2_Ring, J3_Tip, J3_Ring]
  #define DIRECT_PINS { { GP6, GP7, GP0, GP1, GP2, GP4 } }
  ```
- **Debounce**: `sym_defer_pk` (or `sym_defer_g`), `DEBOUNCE 10` ms (cleanly eliminates microswitch contact bounce on arcade switches)
- **Vial Features Enabled**:
  - `VIAL_ENABLE = yes`
  - `TAP_DANCE_ENABLE = yes` (supports Hold = PTT, Double-Tap = Locked Voice Toggle)
  - `COMBO_ENABLE = yes` (e.g., **Button A + Button B simultaneously** switches between macOS and Windows layers, or triggers `QK_BOOT` on long-hold combo)
  - `DYNAMIC_KEYMAP_LAYER_COUNT = 4` (Layer 0: macOS, Layer 1: Windows, Layers 2–3: spare/Meeting/Custom)
  - `RGBLIGHT_ENABLE = yes` (`WS2812_DI_PIN GP12`, `RGBLIGHT_LED_COUNT 1`, `WS2812_DRIVER vendor` — with `gpio_set_pin_output(GP11); gpio_write_pin_high(GP11);` in `keyboard_pre_init_kb()` to power the NeoPixel!)

### Default Dual-OS Keymap Blueprint (All Editable Live in Vial)

| Physical Control | Layer 0: **macOS** (LED: Soft Blue) | Layer 1: **Windows** (LED: Soft Green) |
| :--- | :--- | :--- |
| **Button A (`J1 Tip`)** | **Voice / PTT** — e.g., `LOPT(KC_SPC)` (or Vial Tap-Dance: Hold = PTT, Double-Tap = Toggle) | **Voice / PTT** — e.g., `LWIN(KC_H)` or `LCTL(LALT(KC_SPC))` |
| **Button B (`J1 Ring`)** | **Mute Toggle** — `LGUI(LSFT(KC_A))` (Zoom/Meet) or `KC_MUTE` | **Mute Toggle** — `LCTL(LSFT(KC_M))` (Teams/Meet) or `KC_MUTE` |
| **Stick Up (`J2 Tip`)** | Page Up / Scroll Up / Previous AI Hunk | Page Up / Scroll Up / Previous AI Hunk |
| **Stick Down (`J2 Ring`)** | Page Down / Scroll Down / Next AI Hunk | Page Down / Scroll Down / Next AI Hunk |
| **Stick Left (`J3 Tip`)** | Reject Diff / Prev Tab (`LGUI(LSFT(KC_LBRC))`) | Reject Diff / Prev Tab (`LCTL(KC_PGUP)`) |
| **Stick Right (`J3 Ring`)** | Accept Diff / Next Tab (`LGUI(LSFT(KC_RBRC))`) | Accept Diff / Next Tab (`LCTL(KC_PGDN)`) |
| **Combo: A + B** | Toggle Layer 0 ↔ Layer 1 (`TG(1)`) | Toggle Layer 0 ↔ Layer 1 (`TG(1)`) |

### Onboard RGB LED Layer Indicator Rules
- **Layer 0 (macOS)**: Steady dim **Blue** (HSV ~ `170, 220, 40` — gentle desk brightness, not blinding)
- **Layer 1 (Windows)**: Steady dim **Green** (HSV ~ `85, 220, 40`)
- **Layer 2 (Optional Custom/Meeting)**: Steady dim **Amber/Orange**
- **Layer 3 (Optional Custom)**: Steady dim **Purple**
- **Discrete User LEDs (`GP16/17/25`)**: Driven HIGH (OFF) at boot so they don't bleed unwanted light through the window.

---

## 6. Mechanical & Enclosure Summary

Full mechanical tolerances, CAD parameter schema, and verification checklists are specified in [`docs/CAD_HANDOFF_SPEC.md`](CAD_HANDOFF_SPEC.md).

High-level enclosure envelope (L2 Inline with `Switchcraft 35PRM3` + `XIAO RP2040` + toggleable 4× `12×3 mm` bottom magnets):
- **Width (X)**: `~58.0 mm` (3× 3.5mm jacks at `16.0 mm` center-to-center pitch)
- **Length (Y)**: `~64.0 mm` (USB-C front wall + XIAO cradle + wiring bay + `35PRM3` rear depth + `2.8 mm` jack wall)
- **Height (Z)**: `~20.4 mm` with `12×3 mm` magnet recesses (or `~18.8 mm` with `enable_bottom_magnets = False`)
- **Support-Free FDM**: Two-piece **`build123d`** design (`bottom_tray` + `top_lid`) printable flat on bed with `0.4 mm` nozzle and `0.2 mm` layer height.
