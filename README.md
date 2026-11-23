# 8BitDo 3.5mm to USB-C HID Adapter (`button-adapter`)

Compact, screwless, 3D-printed inline USB-C HID adapter box for **8BitDo Dual Super Buttons** and **8BitDo Super Stick**, powered by a **Seeed Studio XIAO RP2040** running **QMK / Vial**.

## Finalized Architecture Summary

| Category | Finalized Decision |
| :--- | :--- |
| **3.5mm Ports** | **3 × 3.5mm TRS Stereo Panel-Mount Jacks** (6 digital GPIOs + shared GND) — 1× Dual Super Buttons + 1× Super Stick |
| **MCU Board** | **Seeed Studio XIAO RP2040** (`21.0 × 17.8 mm`, USB-C, flat back, future-compatible with XIAO nRF52840) |
| **3.5mm Jack (Primary)** | **Amazon Front-Mount M8 3.5mm TRS Stereo Jack** (`Ø 7.8 mm` M8×0.75 thread, front flange `Ø 10.2 × 3.3 mm`, internal M8 hex nut, `~19–20.5 mm` length) |
| **3.5mm Jack (Alternates)** | **Switchcraft `35PRM3`** (`switchcraft_35prm3`) & **Tensility `54-00081`** (`tensility_54_00081`) — both built into `cad/enclosure.py` presets |
| **Firmware** | **QMK / Vial** — instant browser remapping (`vial.rocks`), no USB mass-storage drive popup, dual-layer **macOS / Windows** switching with onboard WS2812B RGB LED indicator |
| **Enclosure Layout** | **L2 Inline Pass-Through** — 3× 3.5mm TRS jacks on one end, 1× USB-C on the opposite end (**`60.0 × 60.0 × 21.6 mm`** with `12×3 mm` magnets, or **`60.0 × 60.0 × 20.0 mm`** without magnets) |
| **Enclosure Fastening** | **Screwless Cantilever Snap-Fit Lid** (4× 45°-ramped support-free clips + 2× side pry notches + 5-min test coupon) |
| **Enclosure Features** | `BOOT` & `RESET` guided pinholes, engraved `1 / 2 / 3` + `R / B` labels, WS2812B LED light tunnel, toggleable 4× bottom `12 × 3 mm` neodymium magnet recesses |

## Documentation & CAD Map

- [`docs/DESIGN_SPEC.md`](docs/DESIGN_SPEC.md) — Finalized system architecture, electrical topology, pin map, and QMK/Vial dual-OS keymap spec.
- [`docs/BOM.md`](docs/BOM.md) — Verified US sourcing Bill of Materials with Amazon M8 TRS primary jack and DigiKey/Mouser alternates.
- [`docs/WIRING_AND_ASSEMBLY.md`](docs/WIRING_AND_ASSEMBLY.md) — Pin-to-jack wiring table, ASCII schematic, Pin 1/2/4 identification, soldering sequence, and bench verification steps.
- [`docs/CAD_HANDOFF_SPEC.md`](docs/CAD_HANDOFF_SPEC.md) — Mechanical & parametric specification for `build123d`.
- [`cad/enclosure.py`](cad/enclosure.py) — Parametric `build123d` source script (supports `amazon_m8_trs`, `switchcraft_35prm3`, `tensility_54_00081`, and `custom` presets).
- [`cad/verify_and_render.py`](cad/verify_and_render.py) — Automated 32-point B-Rep collision check, STL manifold verification, and cross-section blueprint renderer.
- `cad/export/` — Print-ready support-free `.stl` files (`bottom_tray.stl`, `bottom_tray_no_magnets.stl`, `top_lid.stl`, `snap_fit_test_coupon.stl`) and `.step` files (`assembly_preview.step`, etc.).
- `cad/renders/` — Orthographic, isometric, cross-section, and detail zoom engineering inspection sheets.
- [`firmware/README.md`](firmware/README.md) — QMK / Vial flashing, LED color legend, and `vial.rocks` setup guide.
- [`firmware/keyboards/button_adapter/`](firmware/keyboards/button_adapter/) — QMK / Vial keyboard definition for Seeed Studio XIAO RP2040 (`keyboard.json`, `button_adapter.c`, `keymaps/vial/`, `keymaps/default/`).
- [`.github/workflows/build-firmware.yml`](.github/workflows/build-firmware.yml) — Automated GitHub Actions workflow that builds and uploads `button_adapter_vial.uf2` and `button_adapter_default.uf2`.

## Project Roadmap

- [x] **Phase 1: Requirements & Hardware Spec Finalization** — Locked MCU, 3.5mm TRS jacks, QMK/Vial architecture, L2 inline screwless enclosure spec, US BOM, and wiring guide.
- [x] **Phase 2: Parametric 3D CAD Enclosure (`build123d`)** — Built `cad/enclosure.py`, verified `0.0000 mm³` collision against official Seeed XIAO RP2040 STEP + jack/magnet keep-outs, and exported print-ready `.stl`/`.step` files.
- [x] **Phase 3: QMK / Vial Firmware & CI** — Generated QMK/Vial keyboard definition for XIAO RP2040 (`direct_pins`), dual-OS macOS/Windows layers, WS2812B layer indicator, and GitHub Actions `.uf2` build workflow.
- [ ] **Phase 4: Bench Assembly & Validation** — Print enclosure, solder harness, flash `.uf2`, verify all 6 inputs via Vial Matrix Tester.
