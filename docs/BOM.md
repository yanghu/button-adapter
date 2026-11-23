# Bill of Materials (US Sourcing)

> **Target Build Quantity**: 1 unit (with spare recommendations for 2 units)
> **Sourcing Channels**: DigiKey, Mouser, Amazon US, Tensility Direct, Seeed Studio US
> **Prices**: Approximate US retail pricing as of verification; check live distributor pricing/shipping before ordering.

---

## 1. Core Electronic & Mechanical BOM (Per 1 Adapter Unit)

| Item | Part / Model | Spec & Selection Notes | Qty | Est. Unit Price | Est. Subtotal | Recommended US Sources |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **MCU Board** | **Seeed Studio XIAO RP2040** (SKU `102010428`, **un-soldered** headers) | `21.1 × 17.8 mm`, USB-C, RP2040, 2 MB Flash, WS2812B LED, flat backside. **Do not buy pre-soldered headers.** | 1 | \$5.40 – \$7.00 | ~\$6.00 | Amazon US (single or 3-pack ~\$16), Seeed Studio US, DigiKey (`1597-102010428-ND`) |
| **3.5mm TRS Jack (Primary)** | **Amazon Front-Mount M8 3.5mm TRS Stereo Jack** (5-pack) | 3-pin Stereo (TRS), front-mount black flange (`Ø 10.2 × 3.3 mm`) with gold insert + **internal M8 hex nut**, `Ø 7.8 mm` threaded shaft (`~4.5 mm` thread), `12.7 mm` body + `4.5 mm` max lug length (`~19–20.5 mm` total). | 3 (from 5-pack) | ~\$1.40 – \$2.00 | ~\$7–9 (5-pack) | **Amazon US** (free Prime shipping!) |
| **Neodymium Magnets** | **Disc Magnets, `12 × 3 mm`** *(already on hand)* | 4× recessed into bottom floor corners (`enable_bottom_magnets` toggleable; both with-magnet and no-magnet STLs exported). | 4 | — (owned) | \$0.00 | Already owned |
| **Hookup Wire** | **26–28 AWG Stranded Silicone Wire** *(already on hand)* | Flexible multi-strand wire prevents wire spring-back against the screwless lid. | ~0.5 m | — (owned) | \$0.00 | Already owned |
| **Heat-Shrink Tubing** | **1.5–2.5 mm Heat-Shrink Tubing** | Insulates exposed solder eyelets on rear of 3.5mm jacks. | 9 sleeves | — (owned) | \$0.00 | Already owned / bench stock |
| **USB-C Cable** | **USB-C Data Cable** *(already on hand)* | Must support USB data. Enclosure cutout fits oversized braided plug boots (`≥ 13.5 × 8.0 mm`). | 1 | — (owned) | \$0.00 | Already owned |
| **3D Printing Filament** | **PLA+ or PETG** (~30–35 g) *(already on hand)* | **PETG recommended** for snap-fit flexibility; PLA+ also supported with compliant clip geometry. | ~35 g | — (owned) | \$0.00 | Already owned |

**Actual Out-of-Pocket Order (Amazon US: XIAO RP2040 + 5-pack M8 3.5mm TRS Jacks)**: **~\$13 – \$16 USD** (Prime shipping, avoids DigiKey small-order shipping fee)

---

## 2. Supported 3.5mm Panel-Mount TRS Jack Presets (`cad/enclosure.py`)

All presets below are **3-conductor Stereo (TRS)**, **solder-lug termination**, and built into `cad/enclosure.py`:

| Preset / Model | Mount Style & Material | Thread & FDM Hole | Flange / Nut Clearance | Behind-Panel Depth (incl. lugs) | Target Wall Thickness | Verdict |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **`amazon_m8_trs`** *(Primary Default)* | **Front-mount** black insulated collar + gold brass insert + **internal M8 metal hex nut** | `Ø 7.8 mm` (`M8×0.75`) → **`Ø 8.2 mm`** hole | Outer collar `Ø 10.2 × 3.3 mm`; internal hex nut `~Ø 12.5 mm` (`16.5 mm` pitch) | **`14.8 mm`** inside cavity (`16.5 mm` keep-out) | **`2.4 mm`** | **Best Value & Compactness**: Cheap on Amazon Prime, shortest box length (`~58 mm`), clean flush front collar, clear 3-pin schematic. |
| **`switchcraft_35prm3`** *(Alternate)* | **Rear-mount** all-metal nickel-plated brass body & external knurled nut | `M6 × 0.75` → **`Ø 6.35 mm`** hole | External knurled nut `Ø 9.5 × 2.2 mm` (`16.0 mm` pitch) | `~20.5 mm` inside cavity (`22.0 mm` keep-out) | `2.8 mm` | Pro-audio all-metal build (`$3.51/ea` at DigiKey/Mouser, plus shipping). |
| **`tensility_54_00081`** *(Alternate)* | **Front-mount** all-metal nickel-plated brass body + internal M9 hex nut & lockwasher | `M9 × 0.75` → **`Ø 9.6 mm`** hole | Internal M9 hex nut (`18.0 mm` pitch) | `~18.5 mm` inside cavity | `2.6 mm` | Compact all-metal brass (`$2.07–2.23/ea` at Tensility/DigiKey). |

---

## 3. Optional Desk Anchoring & Bench Consumables

- **Adhesive Metal Strike Plate** (if your desk surface is wood/laminate rather than steel): Thin steel disc/plate stuck under the desk mat or monitor stand so the 4 bottom neodymium magnets snap the adapter right into place.
- **Superglue (Cyanoacrylate / Gel CA)** or **2-Part Epoxy**: A tiny drop inside each bottom magnet pocket locks the 4 magnets permanently flush.
- **Digital Calipers** (strongly recommended): Measure your actual delivered 3.5mm jacks, magnets, and USB-C cable boot before final STL export if you want zero-iteration perfection.
- **Multimeter (Continuity / Beep Mode)**: Quick sanity check for Tip/Ring/Sleeve polarity and verifying zero shorts before plugging in USB-C.

---

## 4. Pre-Order Verification Checklist

Before clicking checkout:
1. Confirm XIAO RP2040 is the **un-soldered** variant (`102010428`), NOT the pre-soldered pin-header variant.
2. Confirm 3.5mm jacks are **3-conductor Stereo (TRS)** (`35PRM3` or `54-00081`), NOT 2-conductor Mono (`35PM2A` / `54-00080`).
3. Confirm you have **26–28 AWG flexible silicone wire** (avoid stiff solid-core 22 AWG jumper wire, which makes closing a screwless snap-fit lid frustrating).
4. Confirm magnet dimensions (`10 × 2 mm` default in CAD spec) match what you order—if you already own `6 × 2 mm` or `8 × 3 mm` magnets, simply update `magnet_dia` and `magnet_thickness` in the CAD parameters before printing.
