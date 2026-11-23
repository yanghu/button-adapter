# Wiring & Assembly Guide

> **Hardware**: Seeed Studio XIAO RP2040 + 3× `PJ-392A` M6 Rear-Mount 3.5mm TRS Stereo Jacks + L2 Inline Screwless Enclosure
> **Electrical Principle**: Passive Active-Low switching (`INPUT_PULLUP`). No resistors or diodes required.

---

## 1. Internal Wiring Topology (L2 Inline Top View)

Viewing the open **bottom tray** from **above** (XIAO RP2040 components facing UP, USB-C pointing North/`+Y`, 3.5mm jacks on the South/`-Y` wall; asymmetric rear spacing `J1–J2 = 15.5 mm`, `J2–J3 = 11.9 mm` for the 8BitDo Super Stick rigid dual-plug):

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
       │   │   │       (15.0 mm deep)        │   │   │         │
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
              ◄─ 15.5 mm ─►       ◄── 11.9 mm ──►
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

## 3. Identifying Terminals on the `PJ-392A` M6 Rear-Mount 3.5mm TRS Jack

Because third-party `PJ-392A` clones occasionally differ on whether the longest (`6.5 mm`) lug is **Sleeve (GND)** or **Tip**, **always run the 30-second multimeter continuity test below before soldering!**

### 30-Second Multimeter Sanity Check (Mandatory Before Soldering)
1. Set your multimeter to **Continuity (beep)** mode.
2. Touch one probe to the **silver metal M6 threaded barrel** on the front of the jack and probe each of the 3 rear lugs → whichever lug beeps is **Sleeve (GND)**! Mark it with a black Sharpie.
3. Plug your **8BitDo Dual Super Buttons** into the jack, keep one probe on the **Sleeve (GND)** lug you just found:
   - Hold **Button A** → whichever lug beeps is **Tip** (or Ring).
   - Hold **Button B** → verify the remaining 3rd lug beeps.

*(If using the alternate Amazon M8 front-mount jack: Pin 4 wide offset tab = Sleeve/GND, Pin 2 taller side tab = Tip, Pin 1 shorter side tab = Ring.)*

---

## 4. Recommended Soldering & Assembly Sequence

Follow this exact order to avoid fighting tight spaces or melting your 3D-printed enclosure:

### Step 1: Pre-Test the XIAO RP2040 Bare
1. Before soldering anything, plug the bare XIAO RP2040 into your computer via USB-C.
2. Hold **`B` (BOOT)** while plugging in (or tap `R` while holding `B`) → verify the `RPI-RP2` drive mounts.
3. Flash the compiled QMK/Vial `.uf2` firmware and verify it appears in [`vial.rocks`](https://vial.rocks) and the WS2812B LED lights up.

### Step 2: Dry-Fit & Self-Centering Alignment (Super Stick Dual-Plug Trick!)
1. Insert the 3× `PJ-392A` M6 jacks **from the inside** of the rear wall (`1, 2, 3`) and finger-thread the 3× `Ø 8.0 mm` knurled nuts onto the outside **loosely** (do not tighten yet).
2. **Self-Centering Trick for Ports `2` & `3`**: While the nuts on **Port 2** and **Port 3** are still finger-loose, **plug your actual 8BitDo Super Stick rigid dual-plug all the way into Ports 2 & 3**. Because the `Ø 6.45 mm` mounting holes allow `±0.2 mm` micro-alignment per jack, the dual-plug automatically centers both jacks to the exact millimeter pitch of your physical plug!
3. **While the Super Stick dual-plug is still inserted**, tighten the external knurled nuts on Ports 2 and 3 snug with fingers or rubber-jaw pliers, then unplug and verify smooth, binding-free re-insertion!
4. Test-fit the XIAO RP2040 into the front MCU cradle and insert your actual USB-C cable through the front wall cutout—confirm the plug seats all the way with a crisp click.
5. Test-fit the screwless top lid—verify the hold-down boss clears the buttons/LED and gently stabilizes the XIAO shield can, and verify a paperclip reaches both `R` (left) and `B` (right) buttons through the top pinholes.
6. *(If using magnets)* Glue the 4× `12 × 3 mm` neodymium magnets into the bottom recesses with a small drop of gel CA glue.

### Step 3: Solder Wire Pigtails Outside the Box, Then Mount Jacks
> **Rear-Mount Advantage**: Because `PJ-392A` mounts from the **inside** and the nut threads onto the **outside**, you can solder all wires cleanly on your silicone desk mat **completely outside the 3D-printed box**—zero risk of melting plastic!

1. Cut 6 signal wires (~`40 mm` each, 26–28 AWG silicone) and 3 black GND wires (`~22 mm`, `~18 mm`, `~48 mm`).
2. Strip ~`3 mm` of insulation, tin wire ends and jack solder lugs.
3. Slide a `~8 mm` piece of heat-shrink tubing onto every signal wire **before** soldering.
4. Solder **Tip**, **Ring**, and the **black GND daisy-chain** (`J1 GND → J2 GND → J3 GND → long tail`) cleanly to the 3 jacks on your desk mat and shrink all heat-shrink sleeves.
5. Insert the wired 3-jack harness from inside the rear wall (`Ports 1, 2, 3`), repeat the **Step 2 Super Stick plug-in self-centering trick** on Ports 2 & 3, and tighten all 3 external knurled nuts!

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
