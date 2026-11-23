# Wiring & Assembly Guide

> **Hardware**: Seeed Studio XIAO RP2040 + 3× Switchcraft `35PRM3` (or Tensility `54-00081`) + L2 Inline Screwless Enclosure
> **Electrical Principle**: Passive Active-Low switching (`INPUT_PULLUP`). No resistors or diodes required.

---

## 1. Internal Wiring Topology (L2 Inline Top View)

Viewing the open **bottom tray** from **above** (XIAO RP2040 components facing UP, USB-C pointing North/`+Y`, 3.5mm jacks on the South/`-Y` wall):

```text
                        [ USB-C ]
                      ┌───────────┐
           (unused) D0│GP26     5V│(unused)
           (unused) D1│GP27    GND│◄───────────────────────────┐
           (unused) D2│GP28    3V3│(unused)                    │
           (unused) D3│GP29    D10│(unused)                    │
       ┌─────────── D4│GP6      D9│GP4 ──────────────┐         │
       │   ┌─────── D5│GP7      D8│GP2 ──────────┐   │         │
       │   │   ┌─── D6│GP0      D7│GP1 ──────┐   │   │         │
       │   │   │      └───────────┘          │   │   │         │
       │   │   │                             │   │   │         │
       │   │   │        Wiring Bay           │   │   │         │
       │   │   │       (~13 mm deep)         │   │   │         │
       │   │   │                             │   │   │         │
       ▼   ▼   │          ▼     ▼            │   ▼   ▼         │
      [T] [R]  │         [T]   [R]           │  [T] [R]        │
       │   │   └──────────┘     └────────────┘   │   │         │
      ┌─────┐            ┌─────┐                ┌─────┐        │
      │ J1  │            │ J2  │                │ J3  │        │
      │ [S] ┼────────────┼ [S] ┼────────────────┼ [S] ┼────────┘
      └─────┘            └─────┘                └─────┘
       Port 1             Port 2                 Port 3
    (Dual Super        (Super Stick           (Super Stick
      Buttons)            Plug A)                Plug B)
```

- **Signal Wires (6 total)**: Direct fan-out from the bottom 3 pads on each side of XIAO RP2040 (`D4, D5, D6` on left; `D7, D8, D9` on right) to the 3 jacks. Zero crossing bundles.
- **Ground Bus (1 daisy chain)**: Short black jumpers link `J1 Sleeve → J2 Sleeve → J3 Sleeve`, then a single black wire runs forward along the right side of the tray to XIAO **`GND`**.

---

## 2. Exact Pin-to-Jack Mapping Table

| Port Label | Intended Peripheral | Jack Contact | Wire Color (Suggested) | XIAO Pad | RP2040 GPIO | QMK Direct Pin |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: |
| **1** | Dual Super Buttons (Btn A) | **Tip** | Red | `D4` | `GPIO6` | `GP6` |
| **1** | Dual Super Buttons (Btn B) | **Ring** | Orange | `D5` | `GPIO7` | `GP7` |
| **2** | Super Stick — Plug A (Dir 1) | **Tip** | Yellow | `D6` | `GPIO0` | `GP0` |
| **2** | Super Stick — Plug A (Dir 2) | **Ring** | Green | `D7` | `GPIO1` | `GP1` |
| **3** | Super Stick — Plug B (Dir 3) | **Tip** | Blue | `D8` | `GPIO2` | `GP2` |
| **3** | Super Stick — Plug B (Dir 4) | **Ring** | Purple / White | `D9` | `GPIO4` | `GP4` |
| **1, 2, 3** | All 3 Peripherals (Common) | **Sleeve** | Black (daisy-chained) | `GND` | `GND` | `GND` |

> **Don't stress over Tip vs Ring swaps**: Every switch is an independent mechanical contact to `GND`, and **Vial** lets you remap all 6 inputs live in your browser. As long as **Sleeve** goes to `GND` (never Tip or Ring to `GND`!), swapping Tip and Ring on any jack is 100% harmless and fixed in 5 seconds inside Vial.

---

## 3. Identifying Terminals on the Amazon M8 3.5mm TRS Jack

Per the product dimensional drawing (`50V, 3-Pin Stereo TRS, Ø 7.8 mm M8 thread`):
- **Pin 4 — Sleeve (GND)**: Wide center tab (`2.0 mm` wide, `3.2 mm` long, offset `2.5 mm` off center, with solder hole).
- **Pin 2 — Tip**: Side tab that is **`1.3 mm` taller** (`4.5 mm` total length).
- **Pin 1 — Ring**: Opposite side tab (`3.2 mm` length).

*(If using the alternate Switchcraft `35PRM3`, Ground/Sleeve is continuous with the outer metal barrel, while Tip & Ring are the square-corner vs round-corner lugs.)*

### 30-Second Multimeter Sanity Check (Recommended Before Soldering)
1. Plug a bare 3.5mm TRS audio cable (or your Dual Super Buttons) into one jack.
2. Set your multimeter to **Continuity (beep)** mode.
3. Touch one probe to the gold-plated front bushing rim → verify **Pin 4** beeps (**Sleeve / GND**).
4. With Dual Super Buttons plugged in: keep one probe on **Pin 4 (GND)**, hold **Button A** → verify Tip/Ring beeps; hold **Button B** → verify the other side pin beeps.

---

## 4. Recommended Soldering & Assembly Sequence

Follow this exact order to avoid fighting tight spaces or melting your 3D-printed enclosure:

### Step 1: Pre-Test the XIAO RP2040 Bare
1. Before soldering anything, plug the bare XIAO RP2040 into your computer via USB-C.
2. Hold **`B` (BOOT)** while plugging in (or tap `R` while holding `B`) → verify the `RPI-RP2` drive mounts.
3. Flash the compiled QMK/Vial `.uf2` firmware and verify it appears in [`vial.rocks`](https://vial.rocks) and the WS2812B LED lights up.

### Step 2: Dry-Fit Mechanical Parts in the 3D-Printed Tray
1. Insert the 3× Amazon M8 jacks **from the outside** of the rear wall (`1, 2, 3`), orienting **Pin 4 (GND)** facing upward or toward the center for easy daisy-chaining, and thread the 3× M8 metal hex nuts on **from the inside**—confirm smooth fit and clearance between adjacent nuts.
2. Test-fit the XIAO RP2040 into the front MCU cradle and insert your actual USB-C cable through the front wall cutout—confirm the plug seats all the way with a crisp click.
3. Test-fit the screwless top lid—verify the hold-down boss clears the buttons/LED and gently stabilizes the XIAO shield can, and verify a paperclip reaches both `R` (left) and `B` (right) buttons through the top pinholes.
4. *(If using magnets)* Glue the 4× `12 × 3 mm` neodymium magnets into the bottom recesses with a small drop of gel CA glue.

### Step 3: Solder Wire Pigtails & Mount the 3.5mm Jacks
> **Front-Mount Assembly Tip**: Because the M8 hex nut slides onto the jack from the **inside**, you can either:
> - **(Easiest)** Solder pre-cut wires to each jack **outside the box**, pass the wire tails through the M8 hex nut *before* soldering them to the XIAO, insert the jack from the outside, and tighten the nut from inside; **OR**
> - Mount and lock all 3 jacks into the tray wall first, then solder cleanly to the protruding rear tabs (the insulated black housing keeps heat away from the 3D-printed wall—just keep iron contact to 2–3 seconds per lug).

1. Cut 6 signal wires (~`40 mm` each, 26–28 AWG silicone) and 3 black GND wires (`~22 mm`, `~22 mm`, `~48 mm`).
2. Strip ~`3 mm` of insulation, tin wire ends and jack solder tabs.
3. Slide a `~8 mm` piece of heat-shrink tubing onto every signal wire **before** soldering.
4. Solder **Tip (Pin 2)** and **Ring (Pin 1)** wires to each jack and shrink the heat-shrink sleeves.
5. Pass the wire tails through the M8 hex nuts, insert the 3 jacks from the outside of the rear wall (`Ports 1, 2, 3`), align all 3 **Pin 4 (GND)** tabs nicely, and tighten the M8 hex nuts inside the tray.
6. Solder the short black GND daisy-chain jumpers across `J1 Pin 4 → J2 Pin 4 → J3 Pin 4` and route the final black wire forward along the right inner wall toward XIAO `GND`.

### Step 4: Trim & Solder Wires to the XIAO RP2040
1. Seat the XIAO RP2040 temporarily in its cradle to gauge exact wire lengths (`~5–8 mm` slack for gentle curves, not taut).
2. Lift the XIAO slightly out of the cradle (rest on a silicone mat beside the tray), trim/strip wires, and solder `D4–D9` and `GND` from the **top or side through-hole** so the **bottom of the XIAO stays completely flat** (zero solder blobs protruding below the PCB!).
3. Visually inspect every joint—confirm no stray copper strands bridge adjacent pads (`3V3`, `5V`, or neighboring GPIOs).

### Step 5: Bench Electrical Test Before Closing Lid
1. Seat the XIAO RP2040 firmly into the cradle and route wires neatly into the wiring bay.
2. Plug in USB-C (without the lid on yet) → verify the LED turns on (no overheating, no USB overcurrent warning).
3. Plug Dual Super Buttons into **Port 1** and Super Stick into **Ports 2 & 3**.
4. Open **Vial → Matrix Tester** and actuate Button A, Button B, and all 4 stick directions (Up/Down/Left/Right) → confirm all 6 switch boxes light up cleanly with zero double-triggering.
5. Test the **A + B combo** → verify Layer 0 (Blue LED, macOS) toggles to Layer 1 (Green LED, Windows).

### Step 6: Final Closure
1. Tuck wires neatly into the central wiring bay (ensure no wire sits on top of the `B`/`R` switches or blocks the WS2812B LED).
2. Snap or slide the **top lid** closed until fully seated.
3. Re-test USB-C insertion/withdrawal (verify zero board movement) and verify a paperclip clicks `R` (Reset) cleanly through the pinhole.
