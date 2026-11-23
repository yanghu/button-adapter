# 3D CAD Handoff Specification — Dedicated Modeling Agent Packet

> **Purpose**: This document is a self-contained mechanical specification intended for a dedicated **3D CAD Modeling Agent** using **`build123d`** (Python). Every constraint, verified part dimension, tolerance, coordinate convention, and verification gate is defined here so CAD generation can proceed deterministically without guesswork.

---

## 1. Deliverable Targets

The 3D CAD agent shall produce the following inside `cad/`:
1. **Parametric Source Script**: `cad/enclosure.py` built with **`build123d`** (Python) for native `.step` / `.stl` export and clean fillets/chamfers, with **all configurable dimensions in a single top-level config block/dict**.
2. **Exported Manufacturing Files** (`cad/export/`):
   - `bottom_tray.stl` & `bottom_tray.step`
   - `top_lid.stl` & `top_lid.step`
   - `assembly_preview.step` (complete closed assembly + simplified keep-out stand-ins for XIAO RP2040 and 3× 3.5mm jacks for interference inspection)
   - `snap_fit_test_coupon.stl` (optional small cut-out slice of the snap-fit/sliding joint so the user can print a 5-minute tolerance check on their printer before printing the full enclosure)
3. **Verification Report**: Programmatic checks confirming zero component-to-wall collisions, minimum wall thicknesses met, bounding box dimensions, and support-free printability.

---

## 2. Official Component Dimensions & Reference CAD Assets

### 2.1 MCU: Seeed Studio XIAO RP2040 (Un-soldered, SKU `102010428`)
- **Official Wiki & Mechanical Resources**: [`https://wiki.seeedstudio.com/XIAO-RP2040/#resources`](https://wiki.seeedstudio.com/XIAO-RP2040/) (includes official **2D DXF** and **3D STEP Model** — **MANDATORY: download/inspect the official STEP or DXF before locking exact button & LED `(X, Y)` coordinates!**)
- **Verified Baseline Dimensions**:
  - PCB Length (`Y`, USB-C axis): **`21.0 mm`**
  - PCB Width (`X`, across pin rows): **`17.8 mm`** (note: older docs say `17.5 mm`; use `17.8 mm` nominal so both revisions fit!)
  - PCB Thickness: **`~1.2 – 1.6 mm`** (verify exact PCB thickness + USB-C shell Z-height from official STEP; total module thickness is **`~3.5 mm`** per XIAO SoM Datasheet)
  - Backside Clearance: **Flat single-sided SMD** (no backside components; leave `0.4 mm` relief channel along the two side pin rows for flush-trimmed hand-soldered wire tails!)
  - Pin Header Rows: 2 × 7 pins along the `21.0 mm` edges, `2.54 mm` pitch, `15.24 mm` row center-to-center. Active soldered pads are **`D4–D6`** (left rear), **`D7–D9`** (right rear), and **`GND`** (right front, pin 2 from USB-C).
  - **Key Top-Face Features to Extract Precisely from Official STEP/DXF**:
    1. **USB-C Receptacle**: Exact front overhang past PCB `+Y` edge (typically `~1.0–1.5 mm`), shell width (`~9.0 mm`), shell height (`~3.2 mm`), and vertical centerline Z relative to PCB bottom face.
    2. **`B` (BOOT) & `R` (RESET) Tactile Switches**: Exact `(X, Y, Z)` actuator center coordinates for the lid pinholes.
    3. **WS2812B NeoPixel RGB LED** (located between `B` and `R` buttons): Exact `(X, Y)` center coordinate for the lid light window.

### 2.2 3.5mm TRS Panel-Mount Jacks (×3)

#### Primary Default: **`PJ-392A` M6×0.5 Rear-Mount 3.5mm TRS Stereo Jack** (`pj392a_m6_trs`)
- **Why Primary**: Matches the tight **`11.9–12.0 mm`** rigid dual-plug spacing of the **8BitDo Super Stick** with zero nut/body interference (`3.9 mm` clear gap between adjacent `Ø 8.0 mm` outer knurled nuts and inner bodies), rear-mount assembly allows clean external soldering before mounting, and low `2.2 mm` outer protrusion clears the dual-plug plastic shroud.
- **Verified Drawing Dimensions**:
  - Thread: **`M6 × 0.5`** × **`4.5 mm`** length → **FDM mounting hole = `Ø 6.45 mm`** (`+0.45 mm` clearance provides `±0.2 mm` self-centering play per jack so Ports 2 & 3 auto-align when tightening nuts with the Super Stick dual-plug inserted!)
  - External Knurled Nut: **`Ø 8.0 mm`** × **`1.8 mm`** thick (`2.3 mm` rear wall leaves `2.2 mm` exposed thread outside)
  - Body OD Behind Panel: **`Ø 8.0 ± 0.15 mm`** (`8.2 mm` keep-out) × **`11.8 mm`** long (`5.6 mm` metal collar + `6.2 mm` black sleeve)
  - Solder Lugs: 3-pin TRS stereo, longest lug **`6.5 mm`** (`18.3 mm` total behind panel → **`20.5 mm`** keep-out with solder/wire-bend margin)
  - **Asymmetric Rear Spacing**: **`J1–J2 = 15.5 mm`** (single Dual Super Buttons plug), **`J2–J3 = 11.9 mm`** (8BitDo Super Stick rigid dual-plug), centered on `X = 0` → `jack_xs = [-13.7, +1.8, +13.7] mm`.

#### Alternate Supported Presets (`cad/enclosure.py`)
- **`amazon_m8_trs`**: Front-mount M8×0.75 (`Ø 7.8 mm` barrel → `Ø 8.2 mm` hole, `Ø 10.2 × 3.3 mm` front collar, internal M8 hex nut `Ø 12.5 mm`, uniform `16.5 mm` pitch).
- **`switchcraft_35prm3`**: Rear-mount all-metal brass `M6 × 0.75` (`Ø 6.35 mm` hole, `Ø 9.5 × 2.2 mm` knurled nut, `22.0 mm` behind-panel keep-out, uniform `16.0 mm` pitch).
- **`tensility_54_00081`**: Front-mount all-metal brass `M9 × 0.75` (`Ø 9.6 mm` hole, internal M9 hex nut, `18.5 mm` behind-panel keep-out, uniform `18.0 mm` pitch).
- **Requirement**: The parametric script supports switching `jack_preset = "pj392a_m6_trs" | "amazon_m8_trs" | "switchcraft_35prm3" | "tensility_54_00081" | "custom"`!

### 2.3 Bottom Neodymium Magnets (×4, Toggleable)
- **Default Spec**: **`Ø 12.0 × 3.0 mm`** circular disc magnets (user-owned hardware; parameterized via `enable_bottom_magnets`, `magnet_dia`, and `magnet_height` so v1 can also be exported without magnets).
- **FDM Pocket Sizing**: `Ø 12.25 mm` × `3.15 mm` deep (flush press-fit + CA glue drop), with `≥ 1.05 mm` solid plastic floor thickness above the pocket (`floor_thickness = 4.2 mm` when magnets enabled; `2.6 mm` when disabled).

---

## 3. Coordinate System & L2 Inline Layout Envelope

Adopt a right-handed Cartesian frame with origin `(0, 0, 0)` at the **bottom-center of the outer enclosure**:
- **`X` axis (Width)**: Left (`-X`) to Right (`+X`). Symmetric about `X = 0`.
- **`Y` axis (Length)**: Rear 3.5mm jack wall (`-Y`) to Front USB-C wall (`+Y`).
- **`Z` axis (Height)**: Bottom outer face (`Z = 0`) to Top outer face (`Z = H`).

### Top-Down Layout Blueprint (Not to Scale)

```text
                        +Y (Front: USB-C)
          ┌──────────────────────────────────────────┐
          │ [Mag]     ┌──── USB-C Shroud ────┐ [Mag] │  <- Recessed USB-C boot pocket
          │           │   ┌──────────────┐   │       │
          │           │   │ XIAO RP2040  │   │       │  <- Retention cradle + lid boss
          │           │   │  (R) ● (B)   │   │       │     (● = WS2812B LED window)
          │           │   └──────────────┘   │       │
          │                                          │
          │           Open Wiring Bay (15.0 mm)      │  <- Fan-out 26-28 AWG silicone wires
          │                                          │
          │     ┌───┐          ┌───┐     ┌───┐       │
          │     │J1 │          │J2 │     │J3 │       │  <- 3x PJ-392A M6 (Asymmetric:
          │[Mag]│   │          │   │     │   │ [Mag] │     J1-J2=15.5mm, J2-J3=11.9mm)
          └─────┴───┴──────────┴───┴─────┴───┴───────┘
                  1              2         3
                        -Y (Rear: 3.5mm TRS)
```

### Finalized Outer Dimensional Budget (Default: `pj392a_m6_trs` + `12×3 mm` magnets)

| Axis | Breakdown | Final Outer Dimension |
| :--- | :--- | :---: |
| **Width (`X`)** | 3 jacks @ `15.5 / 11.9 mm` pitch (`27.4 mm` outer span, `X = -13.7 / +1.8 / +13.7 mm`) + `2 × 10.2 mm` side margin + `2 × 2.8 mm` walls | **`53.4 mm`** |
| **Length (`Y`)** | Front wall (`2.8 mm`) + XIAO pocket (`21.4 mm`) + wiring bay (`15.0 mm`) + `PJ-392A` behind-panel (`20.5 mm`) + rear jack wall (`2.3 mm`) | **`62.0 mm`** |
| **Height (`Z`)** | Bottom floor (`4.2 mm` incl. `3.15 mm` magnet recess + `1.05 mm` ceiling; or `2.6 mm` without magnets) + internal cavity (`15.0 mm`) + top lid (`2.4 mm`) | **`21.6 mm`** (or **`20.0 mm`** without magnets) |

> **4× Corner Magnet Collision Check (`12×3 mm`)**: At `53.4 × 62.0 mm`, placing the 4 bottom magnets (`Ø 12.25 mm`) with `10.5 mm` edge inset leaves `≥ 3.375 mm` solid perimeter rim on every outer edge even at the `Z = 0` chamfer. Because magnets reside strictly inside `Z ∈ [0, 3.15]` with solid floor up to `Z = 4.2 mm`, they have **zero vertical or horizontal interference** with the XIAO cradle or the 3.5mm jacks!

---

## 4. Mandatory Mechanical Features & Engineering Constraints

### 4.1 Screwless Lid Closure (FDM PLA & PETG Reliable!)
- **Requirement**: **Zero screws, zero heat-set inserts**. Must open cleanly for solder inspection or future swap to XIAO nRF52840 without breaking clips.
- **Recommended Mechanism (Pick the cleaner, stronger one in CAD)**:
  - **Option S1 (Preferred for PLA & PETG): Cantilever Snap-Fit Top Lid with Recessed Rim + Pry Notch**
    - Bottom tray is a continuous U-walled box (all 4 walls belong to the bottom tray so all 3 jacks + USB-C cutout stay anchored in one rigid piece!).
    - Top lid has an inner alignment lip (`0.25 mm` per-side XY clearance) and **4 long, flexible cantilever snap beams** (`length ≥ 9–10 mm`, `thickness 1.2–1.4 mm`, `0.5–0.6 mm` catch overhang with `30°` lead-in ramp and `45°` release ramp so it can be unclipped without snapping!).
    - Include **2 subtle chamfered pry notches** (`~6 × 1.5 mm`) along the left/right seam so a fingernail or guitar pick opens the lid cleanly.
  - **Option S2 (Alternative — Ultra-Robust in Brittle PLA): Dovetail Sliding Top Lid with Rear Detent Bump**
    - Top lid slides on from the `-Y` or `+Y` end along `45°` chamfered internal rails (100% support-free!) and clicks over a `0.4 mm` compliant detent bump at full closure.
    - **Caution if using S2**: Ensure the hold-down ribs pressing on the XIAO RP2040 don't snag on SMD components while sliding! (Tapered lead-in ramps on the hold-down rails strictly over the bare PCB edges solve this.)
- **Deliverable**: Include a small `snap_fit_test_coupon.stl` printing just one side clip/rail section so the user can verify fit on their exact printer/filament in 5 minutes.

### 4.2 MCU Retention Cradle & Anti-Push-Back Clamping
- Plugging in a stiff USB-C cable exerts `15–25 N` of axial push-back (`-Y`) force on the XIAO RP2040.
- **Bottom Tray Cradle**:
  - Raised flat pedestal elevating the XIAO PCB bottom face so the USB-C port centerline sits cleanly centered on the front wall (approx. `Z_pcb_bottom = floor_thickness + 3.0 mm`).
  - Surrounding retention rails (`+0.25 mm` XY clearance per side around `21.0 × 17.8 mm`) with a **solid rear backstop wall (`-Y` end)** behind the XIAO PCB (with cutouts/gaps where `D4–D9` wires exit!) so USB-C insertion force transfers directly into the tray structure—**zero reliance on glue**.
  - `0.5 mm` deep longitudinal relief channels directly under the two side through-hole pad strips (`X = ±7.62 mm`) so trimmed solder joints never rock the board.
- **Top Lid Hold-Down Ribs**:
  - Two narrow ribs descending from the underside of the top lid that contact the **unpopulated bare PCB perimeter** (or safe clear zones verified on the official XIAO STEP model!) with `0.15 mm` clearance/light contact, pinning the XIAO down in `+Z` when the lid is closed.
  - **Verify against XIAO STEP**: Hold-down ribs MUST NOT collide with the USB-C shield, `B`/`R` buttons, WS2812B LED, crystal, or `D4–D9` solder fillets!

### 4.3 USB-C Port Cutout & Thick-Cable Shroud Clearance
- **Inner Pass-Through Hole**: Matches XIAO USB-C metal shell + `0.5 mm` radial clearance (`~10.0 × 4.4 mm` pill/stadium slot).
- **Outer Recessed Boot Pocket / Chamfered Clearance**: **`≥ 13.5 mm wide × 8.0 mm tall`** (stadium/rounded-rect shape, `R = 3.5 mm`) recessed to within `1.0–1.2 mm` of the USB-C receptacle front face so bulky braided/molded USB-C cable overmolds seat completely without bottoming out against the outer enclosure wall.

### 4.4 Heavy-Duty 3.5mm Jack Wall & Engraved Port Labels
- **Wall Thickness**: Solid **`2.8 mm`** rear wall (parameterized; check `35PRM3_CD.pdf` max clamping thickness—if `< 2.8 mm`, add clean circular internal counterbore pockets of `Ø 11.0 mm` around each hole to hit the exact target wall thickness!).
- **Jack Pitch**: **`16.0 mm`** center-to-center (`X = -16.0, 0.0, +16.0 mm`) for `Switchcraft 35PRM3` (`Ø 9.5 mm` nut + comfortable finger clearance for 8BitDo's molded 3.5mm plug boots). Auto-adjusts to `18.0 mm` if `jack_preset = "tensility_54_00081"`.
- **Anti-Rotation Flat (Optional/If Applicable)**: Standard round `Ø 6.35 mm` hole for `35PRM3`.
- **Engraved Labels (`1`, `2`, `3`)**:
  - Recessed (`0.6 mm` deep, clean bold sans-serif font, stroke width `≥ 0.8 mm` for crisp `0.4 mm` FDM nozzle rendering) on the **top lid near the rear edge** directly aligned with `X = -16, 0, +16 mm` (and/or above each jack on the rear face if vertical height allows). Placing them on the **top lid face** (`Z = H`) guarantees razor-sharp legibility when printed face-down or face-up!

### 4.5 `BOOT` & `RESET` Pinhole Access
- Two vertical through-holes on the **top lid** directly coaxial with the `B` and `R` tactile switch actuators on the XIAO RP2040 (coordinates pulled from the official Seeed STEP/DXF!).
- **Hole Diameter**: **`Ø 2.2 mm`** with a `0.6 mm × 45°` top countersink/chamfer (easily admits a standard `0.9 mm` paperclip or SIM eject tool without catching).
- **Optional Engraving**: Tiny recessed `B` and `R` markings beside the two pinholes (`0.4 mm` deep).

### 4.6 WS2812B LED Status Window
- Directly above the XIAO RP2040 onboard **WS2812B NeoPixel** (between `B` and `R` buttons; coordinates pulled from official STEP/DXF).
- **Recommended Implementation (Parameterized)**:
  - **Mode A (`led_window_mode = "thin_membrane"`)**: Circular pocket from the underside of the lid (`Ø 4.0 mm`) leaving a **`0.4 mm` (2-layer) translucent top skin**—gives a super clean, diffused glowing dot with no dust hole (works great in white, gray, translucent, or light PLA/PETG; dim in opaque black).
  - **Mode B (Default — `led_window_mode = "open_pipe"`)**: Through-hole **`Ø 2.6 mm`** (accepts a short snippet of clear 1.75 mm filament as a DIY light pipe for opaque black enclosures, or works directly as a clean viewport!).
  - Expose `led_window_mode` as a top-level parameter!

---

## 5. Top-Level Parametric Configuration Schema

The `build123d` script MUST expose these clean parameters at the top of the file:

```python
PARAMS = {
    # Hardware presets
    "mcu_type": "xiao_rp2040",               # 21.0 x 17.8 mm
    "jack_preset": "switchcraft_35prm3",     # "switchcraft_35prm3" | "tensility_54_00081" | "custom"
    "num_jacks": 3,                          # 3 default (supports 4 if scaled)
    "port_layout": "L2_inline",              # Opposite faces: 3x 3.5mm (-Y) vs USB-C (+Y)

    # MCU dimensions (verify from official XIAO RP2040 STEP/DXF)
    "mcu_len_y": 21.0,
    "mcu_wid_x": 17.8,
    "mcu_pcb_t": 1.6,                        # Verify against STEP
    "mcu_clearance_xy": 0.25,

    # 3.5mm Jack dimensions (populated by jack_preset)
    "jack_hole_dia": 6.35,                   # M6 + 0.35mm FDM clearance (9.6 for Tensility 54-00081)
    "jack_pitch_x": 16.0,                    # 16.0 for 35PRM3, 18.0 for Tensility 54-00081
    "jack_behind_panel_depth": 22.0,         # Body + solder lugs + heat-shrink keepout
    "jack_nut_od": 9.5,
    "jack_wall_thickness": 2.8,              # Local wall thickness at jack face

    # Enclosure geometry & FDM tolerances
    "wall_thickness": 2.8,
    "floor_thickness_base": 2.6,             # Used when enable_bottom_magnets = False
    "magnet_floor_backing": 1.05,            # Solid plastic above magnet pocket when magnets enabled
    "lid_thickness": 2.4,
    "wiring_bay_depth": 13.0,                # Space between XIAO rear and jack lug tips
    "outer_fillet_r": 2.5,
    "lid_clearance_xy": 0.25,
    "snap_overhang": 0.55,
    "fastening_style": "snap_fit",           # "snap_fit" | "sliding_dovetail"

    # USB-C shroud clearance
    "usbc_shroud_w": 13.5,
    "usbc_shroud_h": 8.0,

    # Optional features
    "enable_boot_reset_holes": True,
    "pinhole_dia": 2.2,
    "led_window_mode": "open_pipe",          # "thin_membrane" (0.4mm) | "open_pipe" (Ø 2.6mm)
    "enable_port_labels": True,
    "port_labels": ["1", "2", "3"],

    # Bottom magnets (4 corners — user owns 12x3mm round disc magnets)
    "enable_bottom_magnets": True,
    "magnet_dia": 12.0,
    "magnet_height": 3.0,
    "magnet_clearance_xy": 0.25,
    "magnet_clearance_z": 0.15,
}
```

---

## 6. FDM Printability & Automated CAD Verification Checklist

Before declaring Phase 2 complete, the 3D CAD agent MUST verify:
- [ ] **Support-Free Orientation**:
  - `bottom_tray.stl` prints flat on `Z = 0` with **zero supports** (all horizontal holes ≤ `Ø 6.4 mm` or teardrop/chamfered top edge if > `8 mm`; USB-C slot bridges cleanly across `10–13.5 mm`).
  - `top_lid.stl` prints upside-down (outer top face flat on build plate) with **zero supports** and crisp recessed `1 / 2 / 3` engravings.
- [ ] **Official STEP Alignment**: XIAO RP2040 official STEP imported/overlayed in `assembly_preview.step` confirming exact alignment of USB-C shell, `BOOT` pinhole, `RESET` pinhole, and `WS2812B` LED window (`≤ 0.2 mm` centering error).
- [ ] **35PRM3 Panel Thickness Verified**: Confirm from `35PRM3_CD.pdf` that `jack_wall_thickness` allows at least `2.5–3` full thread turns on the knurled nut.
- [ ] **Zero-Interference Check**: Boolean intersection volume between `(bottom_tray ∪ top_lid)` and `(xiao_keepout ∪ 3× jack_keepout ∪ 4× magnet_keepout)` equals **`0.0 mm³`**.
- [ ] **Minimum Wall Integrity**: No thin walls `< 1.2 mm` anywhere except the intentional `0.4 mm` LED diffuser skin (if `thin_membrane` mode is active) and snap-fit flex beams (`≥ 1.2 mm`, i.e., 3 perimeters with `0.4 mm` nozzle).
- [ ] **Visual Render Inspection**: Generate orthographic + section-cut renders (top, rear jack face, front USB-C face, X-section through XIAO + jacks, Y-section through magnets + snap clips) and visually verify every detail.
