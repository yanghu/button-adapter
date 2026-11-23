# QMK / Vial Firmware — 8BitDo Button Adapter (Seeed Studio XIAO RP2040)

This directory contains the complete **QMK / Vial** firmware definition for the **Seeed Studio XIAO RP2040** (`RP2040`, `direct_pins`, onboard WS2812B layer indicator, dual-OS macOS/Windows defaults).

---

## 1. Getting the Ready-to-Flash `.uf2` File

GitHub Actions automatically compiles the firmware on every push to `firmware/` (or via manual run in the **Actions → Build QMK / Vial Firmware** tab):

1. Open the latest green **Build QMK / Vial Firmware** workflow run in GitHub Actions.
2. Download the **`button-adapter-firmware-uf2`** artifact zip and unzip it.
3. Use **`button_adapter_vial.uf2`** (recommended — enables live browser remapping at [vial.rocks](https://vial.rocks)).

---

## 2. Flashing the Seeed Studio XIAO RP2040

1. Hold down the **`B` (BOOT)** button on the XIAO RP2040 (accessible through the right top-lid pinhole once assembled) while plugging the USB-C cable into your computer — or hold `B` and tap `R` (left pinhole) while plugged in.
2. A removable USB drive named **`RPI-RP2`** appears.
3. Drag and drop **`button_adapter_vial.uf2`** onto `RPI-RP2`.
4. The board reboots automatically in ~1 second (macOS may show a harmless "Disk Not Ejected Properly" notification) and enumerates as **`8BitDo Button Adapter`** — with **no** persistent USB flash drive!

---

## 3. Onboard WS2812B LED Color Legend

The XIAO RP2040's central WS2812B NeoPixel (`GP12`, powered by `GP11`) glows gently through the top lid's light pipe to show the active layer:

| Layer | Name | LED Color | Out-of-the-Box Function |
| :---: | :--- | :--- | :--- |
| **0** | **macOS** *(Default)* | **Calm Blue** | Raw HID `F17` / `F18` / `F13`–`F16` for [Hammerspoon](../hammerspoon/button_adapter.lua) (Btn A: App-aware Voice · Btn B: Background Google Meet · Stick: Spaces/Mission Control) |
| **1** | **Windows** | **Calm Green** | Standalone direct shortcuts: Btn A: `Ctrl+M` (Antigravity Voice) · Btn B: `Enter` (Send) · Stick: `Win+Tab` / `Win+D` / `Ctrl+Win+←/→` |
| **2** | **Meeting / Media** | **Warm Amber** | Btn A: `KC_MUTE` · Btn B: Play/Pause · Stick: Vol+/Vol-/Prev/Next |
| **3** | **Custom** | **Soft Purple** | Transparent (`KC_TRNS`) — ready for your own Vial macros |

- **Switching macOS ↔ Windows**: Press **Button A + Button B simultaneously** (seeded into Vial Combo slots 0 & 1 on first boot; fully editable or removable in Vial!).
- **macOS Host Setup**: See [`docs/HOST_INTEGRATION.md`](../docs/HOST_INTEGRATION.md) for loading [`hammerspoon/button_adapter.lua`](../hammerspoon/button_adapter.lua).

---

## 4. Bench Testing & Live Remapping in Vial (`vial.rocks`)

Open [https://vial.rocks](https://vial.rocks) in Chrome/Edge (or the desktop Vial app) and click **Start Vial** → select **`8BitDo Button Adapter`**:

1. **Verify All 6 Soldered Pins (No Debug Firmware Needed!)**:
   - Click the **Matrix Tester** tab in Vial and toggle **Unlock** (hold **Button A + Button B** when prompted).
   - Press **Button A**, **Button B**, and all 4 **Super Stick** directions. Each of the 6 switches lights up immediately so you can confirm wiring and identify which Super Stick TRS plug is Up/Down vs Left/Right.
   - If any two directions are swapped (e.g., Up/Down or Port 2 vs Port 3), simply drag/assign the desired keycode in Vial's **Keymap** tab — no resoldering required!
2. **Optional Hold-for-PTT / Double-Tap-to-Toggle Voice Input**:
   - Open the **Tap Dance** tab in Vial → configure `TD(0)`:
     - **On Hold**: your Push-to-Talk shortcut (e.g., `Option + Space`)
     - **On Double Tap**: your hands-free Voice Toggle shortcut
   - Assign `TD(0)` to **Button A** on Layer 0.

---

## 5. Hardware Pinout Reference

| Matrix Position | Signal | XIAO Pad | RP2040 GPIO |
| :---: | :--- | :---: | :---: |
| `(0, 0)` | Port 1 Tip (Button A) | `D4` | `GP6` |
| `(0, 1)` | Port 1 Ring (Button B) | `D5` | `GP7` |
| `(0, 2)` | Port 2 Tip (Stick 1-A) | `D6` | `GP0` |
| `(0, 3)` | Port 2 Ring (Stick 1-B) | `D7` | `GP1` |
| `(0, 4)` | Port 3 Tip (Stick 2-A) | `D8` | `GP2` |
| `(0, 5)` | Port 3 Ring (Stick 2-B) | `D9` | `GP4` |
| — | WS2812B Power Enable | Onboard | `GP11` (HIGH) |
| — | WS2812B Data | Onboard | `GP12` (PIO vendor driver) |

---

## 6. Local Docker Build (Optional)

If you prefer compiling locally instead of using GitHub Actions:

```bash
git clone --depth=1 --branch vial --recurse-submodules https://github.com/vial-kb/vial-qmk.git /tmp/vial-qmk
cp -r firmware/keyboards/button_adapter /tmp/vial-qmk/keyboards/button_adapter
docker run --rm -v /tmp/vial-qmk:/qmk_firmware -w /qmk_firmware ghcr.io/qmk/qmk_cli \
  bash -lc "git config --global --add safe.directory '*' && qmk compile -kb button_adapter -km vial"
# Output: /tmp/vial-qmk/button_adapter_vial.uf2
```
