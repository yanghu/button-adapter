#!/usr/bin/env python3
"""
Parametric 3D-Printable Enclosure for the 8BitDo 3.5mm to USB-C HID Adapter.

Built with build123d (0.13.0) for 100% support-free FDM 3D printing
(0.4 mm nozzle, 0.2 mm layer height, PLA or PETG).

Coordinate Convention (Assembled Frame):
  - Origin (0, 0, 0) at bottom-center of the outer enclosure.
  - X: Width, Left (-X) to Right (+X), symmetric about X = 0.
  - Y: Length, Rear 3.5mm TRS jack wall (-Y) to Front USB-C wall (+Y).
  - Z: Height, Bottom outer face (Z = 0) to Top outer face (Z = outer_h).

Print Orientations:
  - bottom_tray.stl            : Right-side-up, bottom face flat on Z = 0.
  - bottom_tray_no_magnets.stl : Right-side-up, bottom face flat on Z = 0.
  - top_lid.stl                : Upside-down, outer top face flat on Z = 0.
  - snap_fit_test_coupon.stl   : Both test pieces flat on Z = 0.
  - *.step files               : Exported in assembled coordinates (Z = 0 bottom).

Usage:
  python3 cad/enclosure.py
  python3 cad/enclosure.py --preset switchcraft_35prm3
  python3 cad/enclosure.py --preset tensility_54_00081
"""

from __future__ import annotations

import argparse
import copy
import math
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from build123d import (
    Align,
    Axis,
    Box,
    BuildLine,
    BuildPart,
    BuildSketch,
    Circle,
    Color,
    Compound,
    Cylinder,
    FontStyle,
    GeomType,
    Line,
    Location,
    Locations,
    Mode,
    Part,
    Plane,
    Polyline,
    RadiusArc,
    Rectangle,
    RectangleRounded,
    Rotation,
    Text,
    chamfer,
    export_step,
    export_stl,
    extrude,
    fillet,
    import_step,
    make_face,
)

# =============================================================================
# 1. HARDWARE PRESETS & TOP-LEVEL USER PARAMETERS
# =============================================================================

JACK_PRESETS: dict[str, dict[str, Any]] = {
    # DEFAULT: Amazon Front-Mount M8 3.5mm Stereo TRS Panel Jack
    # (Ø10.2x3.3mm outer flange, Ø7.8mm M8x0.75 barrel, ~4.5mm thread,
    #  internal M8 hex nut Ø12.5x2.2mm, Ø7.0x10.3mm inner body + 4.5mm lugs)
    "amazon_m8_trs": {
        "jack_mount_style": "front_mount",
        "jack_hole_dia": 8.2,              # Ø7.8mm barrel + 0.4mm FDM clearance
        "jack_pitch_x": 16.5,              # >=4.0mm gap between internal M8 hex nuts
        "jack_behind_panel_depth": 16.5,   # 10.3mm body + 4.5mm lugs + 1.7mm solder margin
        "jack_wall_thickness": 2.4,        # Leaves ~2.1mm thread inside for M8 hex nut
        "jack_outer_flange_dia": 10.2,
        "jack_outer_flange_len": 3.3,
        "jack_inner_nut_dia": 12.5,        # Across corners of internal M8 hex nut
        "jack_inner_nut_thick": 2.2,
        "jack_body_od": 7.2,
        "jack_body_len_inside": 10.3,
        "jack_lug_envelope_dia": 7.6,
        "jack_lug_len": 4.5,
        "cavity_height": 15.0,             # >=1.25mm clearance above & below M8 hex nut
        "wiring_bay_depth": 16.9,          # Gives ~60x60mm compact square footprint
    },
    # Alternate: Switchcraft 35PRM3 All-Metal Brass Rear-Mount Jack (M6x0.75)
    "switchcraft_35prm3": {
        "jack_mount_style": "rear_mount",
        "jack_hole_dia": 6.35,             # M6 + 0.35mm FDM clearance
        "jack_pitch_x": 16.0,
        "jack_behind_panel_depth": 22.0,   # Body + solder lugs + heat-shrink keepout
        "jack_wall_thickness": 2.8,
        "jack_outer_flange_dia": 9.5,      # Knurled brass nut OD outside panel
        "jack_outer_flange_len": 2.2,
        "jack_inner_nut_dia": 10.0,        # Inner body/shoulder keepout
        "jack_inner_nut_thick": 0.0,
        "jack_body_od": 10.0,
        "jack_body_len_inside": 22.0,
        "jack_lug_envelope_dia": 10.0,
        "jack_lug_len": 0.0,
        "cavity_height": 14.0,
        "wiring_bay_depth": 15.0,
    },
    # Alternate: Tensility 54-00081 All-Metal Front-Mount Jack (M9x0.75)
    "tensility_54_00081": {
        "jack_mount_style": "front_mount",
        "jack_hole_dia": 9.6,              # M9 + 0.6mm FDM clearance
        "jack_pitch_x": 18.0,              # Wrench clearance for internal M9 hex nut
        "jack_behind_panel_depth": 18.5,
        "jack_wall_thickness": 2.4,
        "jack_outer_flange_dia": 11.5,
        "jack_outer_flange_len": 2.5,
        "jack_inner_nut_dia": 13.5,        # Internal M9 hex nut OD
        "jack_inner_nut_thick": 2.5,
        "jack_body_od": 9.5,
        "jack_body_len_inside": 13.0,
        "jack_lug_envelope_dia": 9.5,
        "jack_lug_len": 5.5,
        "cavity_height": 16.0,             # >=1.25mm clearance above & below M9 hex nut
        "wiring_bay_depth": 15.0,
    },
}

# Default official Seeed Studio XIAO RP2040 STEP path (used when present for
# assembly preview and B-Rep verification; falls back cleanly if absent).
DEFAULT_XIAO_STEP_PATH = Path(
    "/home/antigravity/.gemini/jetski/brain/v1/default/"
    "jetski_remote_agents_3p_devbox/8b4f0489-1c27-4cfd-b2c1-e2de311f8dde/"
    "scratch/ref/xiao_3d/Seeed Studio XIAO RP2040 v26.step"
)

PARAMS: dict[str, Any] = {
    # --- Hardware presets ---
    "mcu_type": "xiao_rp2040",               # Seeed Studio XIAO RP2040 (21.1 x 17.8 mm)
    "jack_preset": "amazon_m8_trs",          # "amazon_m8_trs" | "switchcraft_35prm3" | "tensility_54_00081" | "custom"
    "num_jacks": 3,                          # 3 default (scales parametrically)
    "port_layout": "L2_inline",              # Opposite faces: 3x 3.5mm (-Y) vs USB-C (+Y)

    # --- MCU dimensions (verified from official XIAO RP2040 v26 STEP & v1.3 KiCad) ---
    "mcu_len_y": 21.10,                      # Fits both v26 STEP (21.00) and v1.3 KiCad (21.10)
    "mcu_wid_x": 17.80,                      # Fits both v26 STEP (17.50) and v1.3 KiCad (17.78)
    "mcu_pcb_t": 1.20,                       # Verified exact PCB thickness in v26 STEP
    "mcu_clearance_xy": 0.25,                # Per-side XY pocket clearance
    "mcu_usbc_center_z": 2.80,               # USB-C tongue & shell mouth center above PCB bottom
    "mcu_shield_top_z": 3.20,                # Flat metal RF shield top above PCB bottom (logo 3.21)
    "mcu_btn_top_z": 2.85,                   # R / B tactile switch cap top above PCB bottom
    "mcu_led_top_z": 2.30,                   # WS2812B NeoPixel top above PCB bottom
    # Midpoint between v26 STEP (-4.00, -8.95) & v1.3 KiCad (-4.06, -9.05) -> <=0.06mm error to both!
    "mcu_reset_xy": (-4.03, -9.00),          # Left (-X) RESET button relative to PCB center
    "mcu_boot_xy": (4.03, -9.00),            # Right (+X) BOOT button relative to PCB center
    "mcu_led_xy": (0.00, -9.00),             # Center WS2812B LED relative to PCB center

    # --- Custom jack overrides (used ONLY when jack_preset == "custom") ---
    "jack_mount_style": "front_mount",
    "jack_hole_dia": 8.2,
    "jack_pitch_x": 16.5,
    "jack_behind_panel_depth": 16.5,
    "jack_wall_thickness": 2.4,
    "jack_outer_flange_dia": 10.2,
    "jack_outer_flange_len": 3.3,
    "jack_inner_nut_dia": 12.5,
    "jack_inner_nut_thick": 2.2,
    "jack_body_od": 7.2,
    "jack_body_len_inside": 10.3,
    "jack_lug_envelope_dia": 7.6,
    "jack_lug_len": 4.5,
    "cavity_height": 15.0,
    "wiring_bay_depth": 16.9,

    # --- Enclosure geometry & FDM tolerances ---
    "wall_thickness": 2.8,                   # Side & front wall thickness
    "floor_thickness_base": 2.6,             # Used when enable_bottom_magnets = False
    "magnet_floor_backing": 1.05,            # Solid floor above magnet pocket (>=1.05 mm)
    "lid_thickness": 2.4,
    "outer_fillet_r": 3.0,                   # Outer vertical corner fillet
    "bottom_chamfer": 1.0,                   # Anti-elephant's foot 45-deg bottom chamfer
    "top_chamfer": 1.2,                      # Crisp 45-deg top lid chamfer (support-free upside-down)
    "inner_fillet_r": 1.0,                   # Inner cavity vertical corner fillet
    "lid_clearance_xy": 0.25,                # Per-side XY clearance for lid lip & snap beams
    "enable_teardrop_holes": True,           # Truncated 45-deg teardrop crown on holes > 6.8mm

    # --- Screwless cantilever snap-fit lid ---
    "fastening_style": "snap_fit",
    "snap_overhang": 0.55,                   # Tooth engagement into tray wall pocket
    "snap_beam_thick": 1.35,                 # 1.35mm @ 9.2mm length -> ~1.32% strain (safe in PLA/PETG)
    "snap_beam_width": 8.0,                  # Tab width along Y
    "snap_pocket_depth": 0.75,               # Leaves 2.05mm solid outer wall behind pocket
    "lid_lip_thick": 1.40,                   # Alignment lip thickness
    "lid_lip_height": 2.40,                  # Alignment lip descent into cavity

    # --- USB-C front cutout & thick-cable boot recess ---
    "usbc_inner_w": 10.4,                    # Inner pass-through slot width (shell is 8.94mm)
    "usbc_inner_h": 4.6,                     # Inner pass-through slot height (shell is 3.21mm)
    "usbc_inner_r": 1.8,                     # Corner radius of inner pass-through
    "usbc_shroud_w": 13.5,                   # Outer thick-cable boot recess width
    "usbc_shroud_h": 8.0,                    # Outer thick-cable boot recess height
    "usbc_shroud_r": 3.2,                    # Corner radius of outer boot recess
    "usbc_shroud_depth": 1.6,                # Leaves 1.2mm front wall around USB-C mouth

    # --- Top-lid pinholes, LED window, and engraved labels ---
    "enable_boot_reset_holes": True,
    "pinhole_dia": 2.2,
    "pinhole_chamfer": 0.6,                  # 45-deg countersink on top face
    "led_window_mode": "open_pipe",          # "open_pipe" (Ø2.6mm) | "thin_membrane" (0.4mm skin)
    "led_open_dia": 2.6,
    "led_membrane_dia": 3.4,
    "led_membrane_skin": 0.4,                # 2 layers at 0.2mm layer height
    "enable_port_labels": True,
    "port_labels": ["1", "2", "3"],
    "label_depth": 0.6,
    "label_font": "DejaVu Sans",

    # --- Bottom neodymium disc magnets (4 corners, 12x3mm default) ---
    "enable_bottom_magnets": True,
    "magnet_dia": 12.0,
    "magnet_height": 3.0,
    "magnet_clearance_xy": 0.25,             # -> Ø12.25mm press-fit + CA glue pocket
    "magnet_clearance_z": 0.15,              # -> 3.15mm pocket depth
}


# =============================================================================
# 2. DERIVED GEOMETRY RESOLVER (SINGLE SOURCE OF TRUTH)
# =============================================================================

def resolve_config(params: dict[str, Any] | None = None) -> SimpleNamespace:
    """Resolve preset overrides and derive all exact mechanical coordinates."""
    p = copy.deepcopy(PARAMS if params is None else params)

    preset_name = p["jack_preset"]
    if preset_name != "custom":
        if preset_name not in JACK_PRESETS:
            raise ValueError(
                f"Unknown jack_preset={preset_name!r}. "
                f"Choose from {list(JACK_PRESETS.keys()) + ['custom']}."
            )
        p.update(JACK_PRESETS[preset_name])

    cfg = SimpleNamespace(**p)

    # Vertical stack
    if cfg.enable_bottom_magnets:
        cfg.magnet_pocket_dia = cfg.magnet_dia + cfg.magnet_clearance_xy
        cfg.magnet_pocket_depth = cfg.magnet_height + cfg.magnet_clearance_z
        cfg.floor_t = round(cfg.magnet_pocket_depth + cfg.magnet_floor_backing, 4)
    else:
        cfg.magnet_pocket_dia = 0.0
        cfg.magnet_pocket_depth = 0.0
        cfg.floor_t = cfg.floor_thickness_base

    cfg.z_floor = cfg.floor_t
    cfg.z_lid_inner = round(cfg.z_floor + cfg.cavity_height, 4)
    cfg.outer_h = round(cfg.z_lid_inner + cfg.lid_thickness, 4)

    # Outer & inner width (X)
    jack_span_half = ((cfg.num_jacks - 1) / 2.0) * cfg.jack_pitch_x
    side_margin = max(cfg.jack_inner_nut_dia / 2.0 + 4.45, 10.2)
    cfg.inner_half_x = round(max(jack_span_half + side_margin, cfg.mcu_wid_x / 2.0 + 12.0), 4)
    cfg.inner_w = round(2.0 * cfg.inner_half_x, 4)
    cfg.outer_w = round(cfg.inner_w + 2.0 * cfg.wall_thickness, 4)

    # Outer & inner length (Y)
    # Front wall + front clearance + MCU + wiring bay + jack behind-panel + rear wall
    cfg.front_wall_t = cfg.wall_thickness
    cfg.rear_wall_t = cfg.jack_wall_thickness
    cfg.mcu_front_gap = cfg.mcu_clearance_xy + 0.05  # 0.30mm to v26 STEP, 0.25mm to v1.3 KiCad
    cfg.inner_l = round(
        cfg.mcu_front_gap
        + cfg.mcu_len_y
        + cfg.wiring_bay_depth
        + cfg.jack_behind_panel_depth,
        4,
    )
    cfg.outer_l = round(cfg.front_wall_t + cfg.inner_l + cfg.rear_wall_t, 4)

    cfg.y_front_outer = cfg.outer_l / 2.0
    cfg.y_front_inner = round(cfg.y_front_outer - cfg.front_wall_t, 4)
    cfg.y_rear_outer = -cfg.outer_l / 2.0
    cfg.y_rear_inner = round(cfg.y_rear_outer + cfg.rear_wall_t, 4)

    # Port vertical centerline (USB-C & 3.5mm TRS jacks coaxially aligned in Z)
    cfg.z_port_center = round(cfg.z_floor + cfg.cavity_height / 2.0, 4)
    cfg.z_pcb_bottom = round(cfg.z_port_center - cfg.mcu_usbc_center_z, 4)

    # XIAO RP2040 center Y coordinate
    cfg.y_mcu_center = round(cfg.y_front_inner - cfg.mcu_front_gap - cfg.mcu_len_y / 2.0, 4)
    cfg.mcu_pocket_half_x = round(cfg.mcu_wid_x / 2.0 + cfg.mcu_clearance_xy, 4)
    cfg.y_mcu_backstop_inner = round(cfg.y_mcu_center - cfg.mcu_len_y / 2.0 - cfg.mcu_clearance_xy, 4)

    # Exact world coordinates of RESET (R), WS2812B LED, and BOOT (B)
    cfg.pin_r_xy = (cfg.mcu_reset_xy[0], round(cfg.y_mcu_center + cfg.mcu_reset_xy[1], 4))
    cfg.pin_b_xy = (cfg.mcu_boot_xy[0], round(cfg.y_mcu_center + cfg.mcu_boot_xy[1], 4))
    cfg.led_xy = (cfg.mcu_led_xy[0], round(cfg.y_mcu_center + cfg.mcu_led_xy[1], 4))

    # 3.5mm jack X coordinates
    cfg.jack_xs = [
        round((i - (cfg.num_jacks - 1) / 2.0) * cfg.jack_pitch_x, 4)
        for i in range(cfg.num_jacks)
    ]

    # Snap-fit Y centers (2 per side, clear of rear hex nuts and central pry notch)
    snap_y_offset = min(13.5, cfg.inner_l / 2.0 - 11.5)
    cfg.snap_ys = (-round(snap_y_offset, 2), round(snap_y_offset, 2))

    # Snap-fit vertical profile parameters (measured downward from z_lid_inner)
    cfg.snap_z_ramp_top = 7.80
    cfg.snap_z_land_top = 8.60
    cfg.snap_z_land_bot = 9.10
    cfg.snap_z_tip = 10.50

    # Bottom corner magnet centers (leaves >= 3.37mm solid rim even at Z=0 chamfer)
    if cfg.enable_bottom_magnets:
        edge_inset = cfg.magnet_pocket_dia / 2.0 + cfg.bottom_chamfer + 3.375
        mx = round(cfg.outer_w / 2.0 - edge_inset, 3)
        my = round(cfg.outer_l / 2.0 - edge_inset, 3)
        cfg.magnet_positions = [(-mx, -my), (mx, -my), (-mx, my), (mx, my)]
    else:
        cfg.magnet_positions = []

    return cfg


# =============================================================================
# 3. HELPER GEOMETRY PRIMITIVES
# =============================================================================

def _add_jack_hole_2d(
    cx: float, cy: float, dia: float, use_teardrop: bool, flange_dia: float
) -> None:
    """
    Add a 2D jack-hole face centered at (cx, cy) inside the active BuildSketch
    (local X = horizontal, local Y = +Z up).
    For horizontal FDM holes > 6.8mm, applies a truncated 45-degree teardrop crown
    that eliminates top-crown sag while staying completely hidden behind the outer
    flange and inner hex nut.
    """
    r = dia / 2.0
    if not use_teardrop or dia <= 6.8:
        with Locations((cx, cy)):
            Circle(r)
        return

    # Truncated 45-degree teardrop: circle up to 45 deg above horizontal, then 45 deg
    # tangents rising to z_top = min(r + 0.38, flange_dia/2 - 0.55), joined by a short
    # horizontal bridge (~2.5-3.0mm wide, prints cleanly with zero supports).
    z_top = min(r + 0.38, flange_dia / 2.0 - 0.55)
    c45 = r / math.sqrt(2.0)
    dx_top = max(0.25, c45 - (z_top - c45))

    with BuildLine() as bl:
        RadiusArc((cx - c45, cy + c45), (cx + c45, cy + c45), radius=r, short_sagitta=False)
        Line((cx + c45, cy + c45), (cx + dx_top, cy + z_top))
        Line((cx + dx_top, cy + z_top), (cx - dx_top, cy + z_top))
        Line((cx - dx_top, cy + z_top), (cx - c45, cy + c45))
    make_face(bl.edges())


def _make_snap_pocket_solid(cfg: SimpleNamespace, side_sign: int, y_center: float) -> Part:
    """
    Create the tray wall snap-fit pocket solid to subtract from the left (-1) or
    right (+1) tray inner wall. Both roof and floor slope at 45 degrees so the
    pocket prints 100% support-free right-side-up on Z = 0.
    """
    x_in = cfg.inner_half_x
    depth = cfg.snap_pocket_depth
    # 0.15mm clearance above tooth upper 45-deg ramp (no unintended closed overlap)
    z_roof_in = cfg.z_lid_inner - (cfg.snap_z_ramp_top + 0.10)   # z_d = 7.90
    z_roof_out = z_roof_in - depth                                # z_d = 8.65
    z_floor_out = cfg.z_lid_inner - 9.70
    z_floor_in = z_floor_out - depth                              # z_d = 10.45

    pocket_w_y = cfg.snap_beam_width + 0.60  # +0.30mm clearance per side along Y
    # Extend 0.5mm into cavity so boolean subtraction cleanly pierces the inner wall
    x_ov = x_in - 0.50
    x_out = x_in + depth

    pts = [
        (side_sign * x_ov, z_roof_in),
        (side_sign * x_in, z_roof_in),
        (side_sign * x_out, z_roof_out),
        (side_sign * x_out, z_floor_out),
        (side_sign * x_in, z_floor_in),
        (side_sign * x_ov, z_floor_in),
    ]
    if side_sign < 0:
        pts.reverse()

    with BuildPart() as bp:
        with BuildSketch(Plane.XZ.offset(-y_center)):
            with BuildLine():
                Polyline(*pts, close=True)
            make_face()
        extrude(amount=pocket_w_y / 2.0, both=True)
    return bp.part


def _make_snap_tab_solid(cfg: SimpleNamespace, side_sign: int, y_center: float) -> Part:
    """
    Create one cantilever snap-fit beam descending from z_lid_inner.
    Upper catch ramp is 45 deg (support-free when lid prints upside-down!);
    lower lead-in ramp is ~30 deg for smooth low-force lid closure.
    """
    x_outer = cfg.inner_half_x - cfg.lid_clearance_xy
    x_inner = x_outer - cfg.snap_beam_thick
    x_tooth = cfg.inner_half_x + cfg.snap_overhang

    z0 = cfg.z_lid_inner + 0.50  # Overlap 0.5mm into lid plate for clean boolean fuse
    z1 = cfg.z_lid_inner - cfg.snap_z_ramp_top
    z2 = cfg.z_lid_inner - cfg.snap_z_land_top
    z3 = cfg.z_lid_inner - cfg.snap_z_land_bot
    z4 = cfg.z_lid_inner - cfg.snap_z_tip
    # Gentle inner chamfer at the free tip
    z_tip_in = z4 + 0.45
    x_tip_in = x_inner + 0.45

    pts = [
        (side_sign * x_inner, z0),
        (side_sign * x_outer, z0),
        (side_sign * x_outer, z1),
        (side_sign * x_tooth, z2),
        (side_sign * x_tooth, z3),
        (side_sign * x_outer, z4),
        (side_sign * x_tip_in, z4),
        (side_sign * x_inner, z_tip_in),
    ]
    if side_sign < 0:
        pts.reverse()

    with BuildPart() as bp:
        with BuildSketch(Plane.XZ.offset(-y_center)):
            with BuildLine():
                Polyline(*pts, close=True)
            make_face()
        extrude(amount=cfg.snap_beam_width / 2.0, both=True)
    return bp.part


def _make_side_pry_notch(cfg: SimpleNamespace, side_sign: int) -> Part:
    """
    Subtle chamfered fingernail/pick pry notch at the left/right seam (Y = 0).
    45-degree sloped bottom makes it 100% support-free on the bottom tray.
    """
    x_out = cfg.outer_w / 2.0
    depth = 1.00
    height = 1.40
    width_y = 7.0
    z_top = cfg.z_lid_inner
    z_bot = z_top - height

    pts = [
        (side_sign * (x_out + 0.5), z_top + 0.2),
        (side_sign * (x_out - depth), z_top + 0.2),
        (side_sign * (x_out - depth), z_top - (height - depth)),
        (side_sign * x_out, z_bot),
        (side_sign * (x_out + 0.5), z_bot),
    ]
    if side_sign < 0:
        pts.reverse()

    with BuildPart() as bp:
        with BuildSketch(Plane.XZ):
            with BuildLine():
                Polyline(*pts, close=True)
            make_face()
        extrude(amount=width_y / 2.0, both=True)
    return bp.part


# =============================================================================
# 4. MAIN ENCLOSURE BUILDERS
# =============================================================================

def build_bottom_tray(cfg: SimpleNamespace) -> Part:
    """Build the rigid 4-walled bottom tray with XIAO cradle, ports, magnets & snap pockets."""
    with BuildPart() as tray:
        # 1. Outer rounded-rectangle block from Z = 0 to Z = z_lid_inner
        with BuildSketch(Plane.XY):
            RectangleRounded(cfg.outer_w, cfg.outer_l, radius=cfg.outer_fillet_r)
        extrude(amount=cfg.z_lid_inner)

        # 2. Anti-elephant's-foot 45-degree bottom perimeter chamfer
        bottom_edges = tray.edges().filter_by_position(Axis.Z, -0.01, 0.01)
        chamfer(bottom_edges, length=cfg.bottom_chamfer)

        # 3. Hollow out internal cavity from z_floor up through z_lid_inner
        cavity_center_y = (cfg.y_front_inner + cfg.y_rear_inner) / 2.0
        with BuildSketch(Plane.XY.offset(cfg.z_floor)):
            with Locations((0, cavity_center_y)):
                RectangleRounded(cfg.inner_w, cfg.inner_l, radius=cfg.inner_fillet_r)
        extrude(amount=cfg.cavity_height + 1.0, mode=Mode.SUBTRACT)

        # 4. XIAO RP2040 Central Pedestal, Side Retention Rails & Solid Rear Backstop
        # Pedestal top stops 0.05mm below nominal Z_pcb_bottom for crisp B-Rep clearance
        # while supporting the full flat SMD backside center (X in [-5.8, +5.8]).
        # Side through-hole pin rows (X = +/-7.62mm) hang over 4.65mm open relief channels!
        ped_top_z = cfg.z_pcb_bottom - 0.05
        ped_h = ped_top_z - cfg.z_floor
        ped_w_x = 11.6  # Leaves X in [5.8, 9.15] completely open under solder pads!
        ped_y_min = cfg.y_mcu_backstop_inner - 2.0
        ped_y_max = cfg.y_front_inner + 0.5  # Fuses monolithically into front wall
        ped_y_len = ped_y_max - ped_y_min
        ped_y_mid = (ped_y_max + ped_y_min) / 2.0

        with BuildSketch(Plane.XY.offset(cfg.z_floor - 0.2)):
            with Locations((0, ped_y_mid)):
                Rectangle(ped_w_x, ped_y_len)
        extrude(amount=ped_h + 0.2)

        # Solid rear PCB backstop wall (absorbs 25N USB-C insertion push-back force directly
        # into the pedestal & floor; X in [-5.8, +5.8] leaves D4-D9 wire paths 100% open!)
        backstop_t = 2.0
        backstop_h = (cfg.z_pcb_bottom + 1.80) - cfg.z_floor
        backstop_y_mid = cfg.y_mcu_backstop_inner - backstop_t / 2.0
        with BuildSketch(Plane.XY.offset(cfg.z_floor - 0.2)):
            with Locations((0, backstop_y_mid)):
                Rectangle(ped_w_x, backstop_t)
        extrude(amount=backstop_h + 0.2)

        # Side retention guide posts (front corners + rear corners, leaving the middle
        # X = +/-7.62mm pin-row span open so D4-D9 and GND wires exit smoothly!)
        rail_t = 2.0
        rail_x_center = cfg.mcu_pocket_half_x + rail_t / 2.0  # Inner face at +/-9.15mm
        rail_h = (cfg.z_pcb_bottom + 2.30) - cfg.z_floor

        # Front pair (Y_rel in [+6.8, +10.8] -> fuses into front inner wall)
        front_rail_y0 = cfg.y_mcu_center + 6.8
        front_rail_y1 = cfg.y_front_inner + 0.5
        front_rail_len = front_rail_y1 - front_rail_y0
        front_rail_ymid = (front_rail_y0 + front_rail_y1) / 2.0

        # Rear pair (Y_rel in [-12.6, -8.5] -> frames rear PCB corners without blocking D4-D9)
        rear_rail_y0 = cfg.y_mcu_backstop_inner - 1.8
        rear_rail_y1 = cfg.y_mcu_center - 8.5
        rear_rail_len = rear_rail_y1 - rear_rail_y0
        rear_rail_ymid = (rear_rail_y0 + rear_rail_y1) / 2.0

        with BuildSketch(Plane.XY.offset(cfg.z_floor - 0.2)):
            for sx in (-1, 1):
                with Locations((sx * rail_x_center, front_rail_ymid)):
                    Rectangle(rail_t, front_rail_len)
                with Locations((sx * rail_x_center, rear_rail_ymid)):
                    Rectangle(rail_t, rear_rail_len)
        extrude(amount=rail_h + 0.2)

        # 5. Front Wall (+Y) USB-C Cutout + Recessed Thick-Cable Boot Pocket
        # Note: x_dir=(-1,0,0), z_dir=(0,1,0) -> right-handed y_dir = z x x = (0,0,+1) (+Z up!).
        front_plane = Plane(origin=(0, cfg.y_front_outer, 0), x_dir=(-1, 0, 0), z_dir=(0, 1, 0))
        with BuildSketch(front_plane.offset(0.2)):
            with Locations((0, cfg.z_port_center)):
                RectangleRounded(cfg.usbc_inner_w, cfg.usbc_inner_h, radius=cfg.usbc_inner_r)
        extrude(amount=-(cfg.front_wall_t + 1.5), mode=Mode.SUBTRACT)

        with BuildSketch(front_plane.offset(0.2)):
            with Locations((0, cfg.z_port_center)):
                RectangleRounded(cfg.usbc_shroud_w, cfg.usbc_shroud_h, radius=cfg.usbc_shroud_r)
        extrude(amount=-(cfg.usbc_shroud_depth + 0.2), mode=Mode.SUBTRACT)

        # 6. Rear Wall (-Y) 3x 3.5mm TRS Jack Holes (with truncated teardrop if > 6.8mm)
        # x_dir=(1,0,0), z_dir=(0,-1,0) -> right-handed y_dir = z x x = (0,0,+1) (+Z up!).
        rear_plane = Plane(origin=(0, cfg.y_rear_outer, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
        with BuildSketch(rear_plane.offset(0.2)):
            for jx in cfg.jack_xs:
                _add_jack_hole_2d(
                    jx,
                    cfg.z_port_center,
                    cfg.jack_hole_dia,
                    cfg.enable_teardrop_holes,
                    cfg.jack_outer_flange_dia,
                )
        extrude(amount=-(cfg.rear_wall_t + 1.5), mode=Mode.SUBTRACT)

        # 7. Bottom 4x Corner Magnet Pockets (12x3mm disc magnets, toggleable)
        if cfg.enable_bottom_magnets:
            with BuildSketch(Plane.XY.offset(-0.1)):
                with Locations(*cfg.magnet_positions):
                    Circle(cfg.magnet_pocket_dia / 2.0)
            extrude(amount=cfg.magnet_pocket_depth + 0.1, mode=Mode.SUBTRACT)

    tray_part = tray.part

    # 8. Subtract Snap-Fit Pockets & Side Pry Notches in clean algebra mode (outside BuildPart!)
    for side_sign in (-1, 1):
        for sy in cfg.snap_ys:
            tray_part -= _make_snap_pocket_solid(cfg, side_sign, sy)
        tray_part -= _make_side_pry_notch(cfg, side_sign)

    return tray_part


def build_top_lid(cfg: SimpleNamespace) -> Part:
    """
    Build the screwless snap-fit top lid in assembled coordinates
    (bottom of lid plate at z_lid_inner, top outer face at outer_h).
    """
    with BuildPart() as lid:
        # 1. Main top lid plate with matching outer vertical corner fillets
        with BuildSketch(Plane.XY.offset(cfg.z_lid_inner)):
            RectangleRounded(cfg.outer_w, cfg.outer_l, radius=cfg.outer_fillet_r)
        extrude(amount=cfg.lid_thickness)

        # 2. Crisp 45-degree top outer chamfer (support-free when printed upside-down!)
        top_edges = lid.edges().filter_by_position(Axis.Z, cfg.outer_h - 0.01, cfg.outer_h + 0.01)
        chamfer(top_edges, length=cfg.top_chamfer)

        # 3. Inner Alignment Lips (Front + 6 Side segments; rear jack nut zone left open!)
        lip_t = cfg.lid_lip_thick
        lip_h = cfg.lid_lip_height
        x_lip_out = cfg.inner_half_x - cfg.lid_clearance_xy
        x_lip_mid = x_lip_out - lip_t / 2.0
        y_front_lip_out = cfg.y_front_inner - cfg.lid_clearance_xy
        y_front_lip_mid = y_front_lip_out - lip_t / 2.0

        # Front alignment lip (stops well clear of inner corner fillets)
        front_lip_w = cfg.inner_w - 10.0
        with BuildSketch(Plane.XY.offset(cfg.z_lid_inner + 0.3)):
            with Locations((0, y_front_lip_mid)):
                Rectangle(front_lip_w, lip_t)
        extrude(amount=-(lip_h + 0.3))

        # Side alignment lip segments with 1.5mm flex-relief slots beside every snap tab
        half_tab_relief = cfg.snap_beam_width / 2.0 + 1.5
        sy_neg, sy_pos = cfg.snap_ys
        side_segments = [
            (sy_neg + half_tab_relief, sy_pos - half_tab_relief),              # Center (Y=0)
            (sy_pos + half_tab_relief, cfg.y_front_inner - 2.6),               # Front corner
            (cfg.y_rear_inner + max(cfg.jack_inner_nut_thick + 0.8, 2.6), sy_neg - half_tab_relief),  # Rear
        ]
        with BuildSketch(Plane.XY.offset(cfg.z_lid_inner + 0.3)):
            for y0, y1 in side_segments:
                seg_len = y1 - y0
                if seg_len >= 2.5:
                    ymid = (y0 + y1) / 2.0
                    for sx in (-1, 1):
                        with Locations((sx * x_lip_mid, ymid)):
                            Rectangle(lip_t, seg_len)
        extrude(amount=-(lip_h + 0.3))

        # 4. XIAO RP2040 Anti-Lift Hold-Down Boss (over flat metal RF shield can)
        # Stops 0.15mm above RF shield top (Z_pcb + 3.35mm) -> zero collision with shield/logo!
        boss_bottom_z = cfg.z_pcb_bottom + cfg.mcu_shield_top_z + 0.15
        boss_len_z = cfg.z_lid_inner - boss_bottom_z
        if boss_len_z > 0.5:
            boss_y_mid = cfg.y_mcu_center - 2.0  # Shield spans Y_rel in [-7.5, +3.5]
            with BuildSketch(Plane.XY.offset(cfg.z_lid_inner + 0.3)):
                with Locations((0, boss_y_mid)):
                    RectangleRounded(9.0, 7.0, radius=1.2)
            extrude(amount=-(boss_len_z + 0.3))

        # 5. Guide Chimney for RESET (R), WS2812B LED, and BOOT (B)
        # Descends to 1.0mm above R/B button tops (keeps paperclip centered & blocks LED bleed)
        chimney_bottom_z = cfg.z_pcb_bottom + cfg.mcu_btn_top_z + 1.00
        chimney_len_z = cfg.z_lid_inner - chimney_bottom_z
        chimney_y_mid = cfg.led_xy[1]
        if cfg.enable_boot_reset_holes and chimney_len_z > 0.5:
            with BuildSketch(Plane.XY.offset(cfg.z_lid_inner + 0.3)):
                with Locations((0, chimney_y_mid)):
                    RectangleRounded(12.8, 5.0, radius=1.5)
            extrude(amount=-(chimney_len_z + 0.3))

        # 6. Engraved Top-Lid Labels ("1", "2", "3" above jacks + subtle "R" & "B" beside pinholes)
        if cfg.enable_port_labels:
            label_y = cfg.y_rear_outer + 7.5
            labels = list(cfg.port_labels)[: cfg.num_jacks]
            with BuildSketch(Plane.XY.offset(cfg.outer_h)):
                for jx, txt in zip(cfg.jack_xs, labels):
                    with Locations((jx, label_y)):
                        Text(
                            str(txt),
                            font_size=6.2,
                            font=cfg.label_font,
                            font_style=FontStyle.BOLD,
                            align=(Align.CENTER, Align.CENTER),
                        )
            extrude(amount=-cfg.label_depth, mode=Mode.SUBTRACT)

            if cfg.enable_boot_reset_holes:
                with BuildSketch(Plane.XY.offset(cfg.outer_h)):
                    with Locations((cfg.pin_r_xy[0] - 4.6, cfg.pin_r_xy[1])):
                        Text(
                            "R",
                            font_size=4.2,
                            font=cfg.label_font,
                            font_style=FontStyle.BOLD,
                            align=(Align.CENTER, Align.CENTER),
                        )
                    with Locations((cfg.pin_b_xy[0] + 4.6, cfg.pin_b_xy[1])):
                        Text(
                            "B",
                            font_size=4.2,
                            font=cfg.label_font,
                            font_style=FontStyle.BOLD,
                            align=(Align.CENTER, Align.CENTER),
                        )
                extrude(amount=-0.50, mode=Mode.SUBTRACT)

    lid_part = lid.part

    # 7. Fuse Four Flexible Cantilever Snap-Fit Tabs (outside BuildPart -> zero stray solids!)
    for side_sign in (-1, 1):
        for sy in cfg.snap_ys:
            lid_part += _make_snap_tab_solid(cfg, side_sign, sy)

    # 8. Subtract RESET (R) & BOOT (B) Coaxial Pinholes + 45-deg Top Countersinks
    from build123d import loft

    if cfg.enable_boot_reset_holes:
        cut_h = cfg.outer_h - chimney_bottom_z + 2.0
        for px, py in (cfg.pin_r_xy, cfg.pin_b_xy):
            hole = Cylinder(
                radius=cfg.pinhole_dia / 2.0,
                height=cut_h,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            ).moved(Location((px, py, chimney_bottom_z - 1.0)))
            lid_part -= hole

            # 45-degree top countersink cone (prints support-free upside-down on build plate!)
            r_inner = cfg.pinhole_dia / 2.0
            r_outer = r_inner + cfg.pinhole_chamfer
            with BuildPart() as csk:
                with BuildSketch(Plane.XY.offset(cfg.outer_h - cfg.pinhole_chamfer)):
                    with Locations((px, py)):
                        Circle(r_inner)
                with BuildSketch(Plane.XY.offset(cfg.outer_h + 0.2)):
                    with Locations((px, py)):
                        Circle(r_outer + 0.2)
                loft()
            lid_part -= csk.part

    # 9. Subtract WS2812B NeoPixel LED Status Window
    lx, ly = cfg.led_xy
    if cfg.led_window_mode == "open_pipe":
        cut_h = cfg.outer_h - chimney_bottom_z + 2.0
        led_hole = Cylinder(
            radius=cfg.led_open_dia / 2.0,
            height=cut_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        ).moved(Location((lx, ly, chimney_bottom_z - 1.0)))
        lid_part -= led_hole

        # Crisp 0.4mm x 45-deg top chamfer
        c_ch = 0.40
        with BuildPart() as led_csk:
            with BuildSketch(Plane.XY.offset(cfg.outer_h - c_ch)):
                with Locations((lx, ly)):
                    Circle(cfg.led_open_dia / 2.0)
            with BuildSketch(Plane.XY.offset(cfg.outer_h + 0.2)):
                with Locations((lx, ly)):
                    Circle(cfg.led_open_dia / 2.0 + c_ch + 0.2)
            loft()
        lid_part -= led_csk.part
    elif cfg.led_window_mode == "thin_membrane":
        blind_top_z = cfg.outer_h - cfg.led_membrane_skin
        blind_h = blind_top_z - (chimney_bottom_z - 1.0)
        led_pocket = Cylinder(
            radius=cfg.led_membrane_dia / 2.0,
            height=blind_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        ).moved(Location((lx, ly, chimney_bottom_z - 1.0)))
        lid_part -= led_pocket
    else:
        raise ValueError(f"Unknown led_window_mode={cfg.led_window_mode!r}")

    return lid_part


def orient_lid_for_printing(lid: Part, cfg: SimpleNamespace) -> Part:
    """Flip top lid upside-down so its flat outer top face rests directly on Z = 0."""
    flipped = lid.moved(Location((0, 0, cfg.outer_h), (180, 0, 0)))
    # Snap min.Z to exact 0.0 to eliminate floating-point drift
    z_min = flipped.bounding_box().min.Z
    if abs(z_min) > 1e-6:
        flipped = flipped.moved(Location((0, 0, -z_min)))
    return flipped


def build_snap_fit_test_coupon(cfg: SimpleNamespace) -> Compound:
    """
    Build a compact ~5-minute FDM tolerance test coupon consisting of:
      1) A 16mm-long section of the right tray side wall + floor stub containing 1 real
         snap-fit pocket (flat on Z = 0).
      2) Side-by-side (+16mm in X), a matching 16mm-long section of the top lid containing
         1 real cantilever snap tab + adjacent alignment lip stubs (upside-down on Z = 0).
    """
    sy = cfg.snap_ys[1]
    slice_len_y = 16.0
    slice_x_min = cfg.inner_half_x - 7.5
    slice_x_max = cfg.outer_w / 2.0 + 1.0
    slice_w_x = slice_x_max - slice_x_min

    # Build full parts and slice cleanly around the (+X, +snap_y) joint
    tray = build_bottom_tray(cfg)
    lid = build_top_lid(cfg)

    clip_box = Box(
        slice_w_x,
        slice_len_y,
        cfg.outer_h + 2.0,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    ).moved(Location((slice_x_min, sy, -1.0)))

    tray_coupon = tray & clip_box
    lid_coupon = lid & clip_box

    # Orient both coupons flat on Z = 0, spaced neatly side-by-side
    tb = tray_coupon.bounding_box()
    tray_coupon = tray_coupon.moved(Location((-tb.min.X - tb.size.X - 4.0, -sy, -tb.min.Z)))

    lid_coupon = lid_coupon.moved(Location((0, 0, cfg.outer_h), (180, 0, 0)))
    lb = lid_coupon.bounding_box()
    lid_coupon = lid_coupon.moved(Location((-lb.min.X + 4.0, -lb.center().Y, -lb.min.Z)))

    return Compound(children=[tray_coupon, lid_coupon], label="snap_fit_test_coupon")


# =============================================================================
# 5. REFERENCE HARDWARE KEEP-OUTS & ASSEMBLY PREVIEW
# =============================================================================

def build_jack_keepouts(cfg: SimpleNamespace) -> Compound:
    """
    Build accurate 3D keep-out solids for all 3.5mm TRS panel-mount jacks,
    including outer flange/nut, threaded barrel, internal hex nut (for front-mount),
    inner body, and solder lug + heat-shrink envelope.
    """
    jacks = []
    # Orientation: local +Z points inward (+Y world), starting at outer rear face (y_rear_outer)
    y_out = cfg.y_rear_outer
    y_in = cfg.y_rear_inner
    z_c = cfg.z_port_center

    for i, jx in enumerate(cfg.jack_xs):
        parts = []
        # 1. Outer flange / external nut (protruding OUTWARD in -Y from outer rear face)
        # Rotation (90, 0, 0) maps local +Z -> world -Y, so align=MIN puts cylinder in [-L, 0] + y_out.
        outer_flange = Cylinder(
            radius=cfg.jack_outer_flange_dia / 2.0,
            height=cfg.jack_outer_flange_len,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        ).moved(Location((jx, y_out - 0.05, z_c), (90, 0, 0)))
        parts.append(outer_flange)

        # 2. Threaded barrel passing through rear wall (nominal OD = hole_dia - 0.4mm)
        barrel_dia = max(5.8, cfg.jack_hole_dia - 0.40)
        barrel = Cylinder(
            radius=barrel_dia / 2.0,
            height=cfg.rear_wall_t + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        ).moved(Location((jx, y_out - 0.1, z_c), (-90, 0, 0)))
        parts.append(barrel)

        # 3. Internal M8/M9 hex nut keep-out (flush against inner rear wall +0.05mm gap)
        if cfg.jack_inner_nut_thick > 0.0:
            inner_nut = Cylinder(
                radius=cfg.jack_inner_nut_dia / 2.0,
                height=cfg.jack_inner_nut_thick,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            ).moved(Location((jx, y_in + 0.05, z_c), (-90, 0, 0)))
            parts.append(inner_nut)

        # 4. Inner body behind rear wall
        body_len = max(1.0, cfg.jack_body_len_inside)
        inner_body = Cylinder(
            radius=cfg.jack_body_od / 2.0,
            height=body_len,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        ).moved(Location((jx, y_in + 0.05, z_c), (-90, 0, 0)))
        parts.append(inner_body)

        # 5. Solder lug + heat-shrink envelope behind plastic body
        rem_len = cfg.jack_behind_panel_depth - body_len - 0.05
        if rem_len > 0.2:
            lugs = Cylinder(
                radius=cfg.jack_lug_envelope_dia / 2.0,
                height=rem_len,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            ).moved(Location((jx, y_in + 0.05 + body_len, z_c), (-90, 0, 0)))
            parts.append(lugs)

        jack_solid = parts[0]
        for extra in parts[1:]:
            jack_solid = jack_solid + extra
        jack_solid.label = f"jack_{i + 1}_{cfg.jack_preset}"
        jack_solid.color = Color(0.82, 0.68, 0.28)
        jacks.append(jack_solid)

    return Compound(children=jacks, label="jacks_3x")


def build_magnet_solids(cfg: SimpleNamespace) -> Compound | None:
    """Build 4x bottom neodymium disc magnet solids positioned inside their pockets."""
    if not cfg.enable_bottom_magnets:
        return None
    mags = []
    for i, (mx, my) in enumerate(cfg.magnet_positions):
        m = Cylinder(
            radius=cfg.magnet_dia / 2.0,
            height=cfg.magnet_height,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        ).moved(Location((mx, my, 0.05)))  # 0.05mm recessed from Z=0, 0.10mm below pocket roof
        m.label = f"magnet_{i + 1}"
        m.color = Color(0.72, 0.75, 0.78)
        mags.append(m)
    return Compound(children=mags, label="magnets_4x")


def load_xiao_rp2040_positioned(
    cfg: SimpleNamespace, step_path: Path = DEFAULT_XIAO_STEP_PATH
) -> tuple[Compound | Part, bool]:
    """
    Load the official Seeed Studio XIAO RP2040 STEP positioned inside the enclosure.
    Returns (shape, used_official_step).
    """
    if step_path.exists():
        raw = import_step(str(step_path))
        # Bake translation into every child solid so Compound.location remains identity
        # (prevents double-translation during B-Rep boolean '&' and section() in build123d).
        delta = (0.0, cfg.y_mcu_center, cfg.z_pcb_bottom)
        baked_solids = [s.translate(delta) for s in raw.solids()]
        positioned = Compound(children=baked_solids, label="xiao_rp2040_official_step")
        return positioned, True

    # Fallback faithful keep-out if official STEP isn't present on a user's machine
    with BuildPart() as mcu:
        Box(
            cfg.mcu_wid_x,
            cfg.mcu_len_y,
            cfg.mcu_pcb_t,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        with Locations((0, 7.85, cfg.mcu_pcb_t)):
            Box(8.94, 7.30, 3.20, align=(Align.CENTER, Align.CENTER, Align.MIN))
        with Locations((0, -2.0, cfg.mcu_pcb_t)):
            Box(12.0, 11.0, 2.00, align=(Align.CENTER, Align.CENTER, Align.MIN))
    fallback = mcu.part.moved(Location((0, cfg.y_mcu_center, cfg.z_pcb_bottom)))
    fallback.label = "xiao_rp2040_keepout"
    fallback.color = Color(0.12, 0.14, 0.16)
    return fallback, False


def build_assembly_preview(
    cfg: SimpleNamespace,
    tray: Part | None = None,
    lid: Part | None = None,
    step_path: Path = DEFAULT_XIAO_STEP_PATH,
) -> Compound:
    """Assemble closed enclosure + XIAO RP2040 + 3x jacks + 4x magnets for inspection."""
    tray_p = copy.deepcopy(build_bottom_tray(cfg) if tray is None else tray)
    lid_p = copy.deepcopy(build_top_lid(cfg) if lid is None else lid)
    tray_p.label = "bottom_tray"
    tray_p.color = Color(0.22, 0.26, 0.32)
    lid_p.label = "top_lid"
    lid_p.color = Color(0.32, 0.38, 0.46, 0.85)

    xiao, _ = load_xiao_rp2040_positioned(cfg, step_path=step_path)
    jacks = build_jack_keepouts(cfg)
    children = [tray_p, lid_p, xiao, jacks]

    mags = build_magnet_solids(cfg)
    if mags is not None:
        children.append(mags)

    return Compound(children=children, label="button_adapter_assembly")


# =============================================================================
# 6. CLI EXPORT PIPELINE
# =============================================================================

def export_all(
    preset: str | None = None,
    out_dir: Path | None = None,
    xiao_step_path: Path = DEFAULT_XIAO_STEP_PATH,
) -> dict[str, Path]:
    """Generate and export all manufacturing STL/STEP artifacts."""
    params = copy.deepcopy(PARAMS)
    if preset is not None:
        params["jack_preset"] = preset

    export_dir = Path(__file__).resolve().parent / "export" if out_dir is None else out_dir
    export_dir.mkdir(parents=True, exist_ok=True)

    # 1. Default variant (with 4x 12x3mm bottom magnets)
    cfg = resolve_config(params)
    print(f"Building enclosure [preset={cfg.jack_preset}, magnets={cfg.enable_bottom_magnets}]...")
    print(
        f"  Outer dimensions : {cfg.outer_w:.2f} x {cfg.outer_l:.2f} x {cfg.outer_h:.2f} mm "
        f"(floor={cfg.floor_t:.2f}, cavity={cfg.cavity_height:.2f}, lid={cfg.lid_thickness:.2f})"
    )
    print(
        f"  Port center Z    : {cfg.z_port_center:.2f} mm | XIAO PCB bottom Z: {cfg.z_pcb_bottom:.2f} mm"
    )
    print(
        f"  XIAO center Y    : {cfg.y_mcu_center:.2f} mm | R={cfg.pin_r_xy}, LED={cfg.led_xy}, B={cfg.pin_b_xy}"
    )

    tray = build_bottom_tray(cfg)
    lid = build_top_lid(cfg)
    lid_print = orient_lid_for_printing(lid, cfg)

    paths: dict[str, Path] = {}
    paths["bottom_tray_stl"] = export_dir / "bottom_tray.stl"
    paths["bottom_tray_step"] = export_dir / "bottom_tray.step"
    paths["top_lid_stl"] = export_dir / "top_lid.stl"
    paths["top_lid_step"] = export_dir / "top_lid.step"
    paths["assembly_step"] = export_dir / "assembly_preview.step"
    paths["coupon_stl"] = export_dir / "snap_fit_test_coupon.stl"

    export_stl(tray, str(paths["bottom_tray_stl"]), tolerance=0.01, angular_tolerance=0.1)
    export_step(tray, str(paths["bottom_tray_step"]))
    export_stl(lid_print, str(paths["top_lid_stl"]), tolerance=0.01, angular_tolerance=0.1)
    export_step(lid, str(paths["top_lid_step"]))

    assembly = build_assembly_preview(cfg, tray=tray, lid=lid, step_path=xiao_step_path)
    export_step(assembly, str(paths["assembly_step"]))

    coupon = build_snap_fit_test_coupon(cfg)
    export_stl(coupon, str(paths["coupon_stl"]), tolerance=0.01, angular_tolerance=0.1)

    # 2. Slim no-magnet variant
    params_nomag = copy.deepcopy(params)
    params_nomag["enable_bottom_magnets"] = False
    cfg_nomag = resolve_config(params_nomag)
    print(f"Building slim no-magnet tray [height={cfg_nomag.outer_h:.2f} mm]...")
    tray_nomag = build_bottom_tray(cfg_nomag)

    paths["bottom_tray_no_magnets_stl"] = export_dir / "bottom_tray_no_magnets.stl"
    paths["bottom_tray_no_magnets_step"] = export_dir / "bottom_tray_no_magnets.step"
    export_stl(
        tray_nomag,
        str(paths["bottom_tray_no_magnets_stl"]),
        tolerance=0.01,
        angular_tolerance=0.1,
    )
    export_step(tray_nomag, str(paths["bottom_tray_no_magnets_step"]))

    print("\nExported files:")
    for key, path in paths.items():
        size_kb = path.stat().st_size / 1024.0
        print(f"  - {path.relative_to(export_dir.parent.parent)} ({size_kb:.1f} KB)")
    print("Note: top_lid.stl is oriented upside-down on Z=0 for instant support-free slicing;")
    print("      top_lid.step is in assembled coordinates matching bottom_tray.step.")
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate parametric build123d enclosure for 8BitDo 3.5mm to USB-C HID Adapter."
    )
    parser.add_argument(
        "--preset",
        choices=list(JACK_PRESETS.keys()) + ["custom"],
        default=None,
        help="Override jack_preset from PARAMS (default: amazon_m8_trs).",
    )
    args = parser.parse_args()
    export_all(preset=args.preset)


if __name__ == "__main__":
    main()
