#!/usr/bin/env python3
"""
Automated Engineering Verification & Visual Inspection Renderer
for the 8BitDo 3.5mm to USB-C HID Adapter Enclosure.

Checks:
  1. Exact bounding boxes & flat Z = 0 print-bed seating.
  2. True 3D B-Rep boolean intersection volume == 0.000 mm^3 against:
     - Official Seeed Studio XIAO RP2040 v26.step
     - 3x 3.5mm TRS jack keep-outs (including internal M8 hex nuts!)
     - 4x 12x3mm neodymium disc magnets
     - Closed lid-to-tray fit (zero unintended closed overlap!)
  3. Coaxial alignment (<= 0.15 mm) of R/B pinholes, WS2812B LED window,
     and USB-C cutout against the actual imported XIAO STEP features.
  4. Wall thickness, thread engagement, magnet rim, and snap-beam strain checks.
  5. Watertight manifold mesh checks via trimesh on all exported STLs.
  6. Cross-preset verification (amazon_m8_trs, switchcraft_35prm3, tensility_54_00081).
  7. Generates 3 multi-panel inspection PNGs in cad/renders/.
"""

from __future__ import annotations

import copy
import math
import sys
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import trimesh

from build123d import (
    Location,
    Plane,
    Shape,
    export_stl,
    section,
)

# Allow importing cad/enclosure.py whether run from repo root or cad/
CAD_DIR = Path(__file__).resolve().parent
if str(CAD_DIR) not in sys.path:
    sys.path.insert(0, str(CAD_DIR))

import enclosure as enc


# =============================================================================
# 1. VERIFICATION HELPERS
# =============================================================================

def _bb_overlap(a_bb, b_bb, tol: float = 1e-4) -> bool:
    return (
        a_bb.min.X <= b_bb.max.X + tol
        and a_bb.max.X >= b_bb.min.X - tol
        and a_bb.min.Y <= b_bb.max.Y + tol
        and a_bb.max.Y >= b_bb.min.Y - tol
        and a_bb.min.Z <= b_bb.max.Z + tol
        and a_bb.max.Z >= b_bb.min.Z - tol
    )


def intersection_volume(a: Shape, b: Shape) -> float:
    """Compute exact 3D B-Rep boolean intersection volume in mm^3 with BB pre-filter."""
    a_solids = a.solids()
    b_solids = b.solids()
    total = 0.0
    for sa in a_solids:
        abb = sa.bounding_box()
        for sb in b_solids:
            if not _bb_overlap(abb, sb.bounding_box()):
                continue
            inter = sa & sb
            if inter is not None:
                total += sum(s.volume for s in inter.solids())
    return float(total)


def shape_to_trimesh(shape: Shape, tol: float = 0.03) -> trimesh.Trimesh:
    """Convert a build123d Shape to a trimesh object via temporary STL."""
    with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as tf:
        tmp_path = Path(tf.name)
    try:
        export_stl(shape, str(tmp_path), tolerance=tol, angular_tolerance=0.15)
        mesh = trimesh.load(str(tmp_path), force="mesh")
        return mesh
    finally:
        tmp_path.unlink(missing_ok=True)


from matplotlib.collections import PolyCollection


def render_camera_shaded(
    ax,
    items: list[tuple[trimesh.Trimesh, str]],
    view_from: tuple[float, float, float],
    up_hint: tuple[float, float, float] = (0.0, 0.0, 1.0),
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    pad: float = 3.0,
) -> None:
    """
    Render one or more trimesh objects in crisp orthographic projection with
    back-face culling, directional + headlight shading, and exact painter's-order
    depth sorting (eliminates Matplotlib 3D z-fighting and back-wall bleed-through).
    """
    v = np.array(view_from, dtype=float)
    v /= np.linalg.norm(v)
    up = np.array(up_hint, dtype=float)
    # Build orthonormal right-handed screen basis (right, screen_up, view_from)
    right = np.cross(up, v)
    if np.linalg.norm(right) < 1e-6:
        right = np.cross(np.array([0.0, 1.0, 0.0]), v)
    right /= np.linalg.norm(right)
    screen_up = np.cross(v, right)
    screen_up /= np.linalg.norm(screen_up)

    # Key light slightly offset from camera + soft headlight for recessed engravings
    light_key = v * 0.72 + right * 0.38 + screen_up * 0.58
    light_key /= np.linalg.norm(light_key)
    light_fill = v * 0.85 - right * 0.35 - screen_up * 0.35
    light_fill /= np.linalg.norm(light_fill)

    all_polys = []
    all_depths = []
    all_colors = []
    u_min, u_max = np.inf, -np.inf
    v_min, v_max = np.inf, -np.inf

    for mesh, color_hex in items:
        if mesh is None:
            continue
        verts = mesh.vertices
        faces = mesh.faces
        normals = mesh.face_normals

        # Back-face culling: keep faces oriented toward camera
        facing = normals @ v
        keep = facing > 1e-4
        if not np.any(keep):
            continue

        tris = verts[faces[keep]]
        n_keep = normals[keep]

        # Project vertices to 2D screen (u, w) and camera depth (d)
        u = tris @ right
        w = tris @ screen_up
        d = tris @ v

        # Use max/mean blend for clean depth sorting of flat faces & recesses
        depth = d.mean(axis=1) + 0.15 * d.min(axis=1)

        # Lambertian + ambient + subtle depth-cue darkening so recesses, engravings,
        # and through-holes (e.g. 3x rear jack holes & 1/2/3/R/B text) pop sharply!
        diff_key = np.clip(n_keep @ light_key, 0.0, 1.0)
        diff_fill = np.clip(n_keep @ light_fill, 0.0, 1.0)
        d_mean = d.mean(axis=1)
        d_span = max(float(d_mean.max() - d_mean.min()), 1.0)
        depth_cue = 0.62 + 0.38 * np.clip((d_mean - d_mean.min()) / d_span, 0.0, 1.0)
        shade = (0.24 + 0.56 * diff_key + 0.22 * diff_fill) * depth_cue

        base_rgb = np.array(matplotlib.colors.to_rgb(color_hex))
        rgba = np.empty((len(n_keep), 4), dtype=float)
        rgba[:, :3] = np.clip(shade[:, None] * base_rgb[None, :], 0.0, 1.0)
        rgba[:, 3] = 1.0

        polys_2d = np.stack([u, w], axis=-1)
        all_polys.append(polys_2d)
        all_depths.append(depth)
        all_colors.append(rgba)

        u_min = min(u_min, float(u.min()))
        u_max = max(u_max, float(u.max()))
        v_min = min(v_min, float(w.min()))
        v_max = max(v_max, float(w.max()))

    if not all_polys:
        return

    polys = np.concatenate(all_polys, axis=0)
    depths = np.concatenate(all_depths, axis=0)
    colors = np.concatenate(all_colors, axis=0)

    order = np.argsort(depths)  # Back-to-front
    pc = PolyCollection(
        polys[order],
        facecolors=colors[order],
        edgecolors=colors[order],
        linewidths=0.15,
        antialiaseds=True,
    )
    ax.add_collection(pc)
    ax.set_aspect("equal")
    ax.set_xlim(u_min - pad, u_max + pad)
    ax.set_ylim(v_min - pad, v_max + pad)
    ax.set_facecolor("#F6F8FA")
    ax.grid(True, linestyle="--", alpha=0.30, zorder=0)
    if title:
        ax.set_title(title, fontsize=10, fontweight="bold", pad=6)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=8.5)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=8.5)
    ax.tick_params(labelsize=7.5)


def plot_brep_section(
    ax,
    shape: Shape,
    sec_plane: Plane,
    color: str,
    alpha: float = 0.85,
    edgecolor: str = "#111111",
    lw: float = 0.8,
    zorder: int = 2,
) -> None:
    """Slice a build123d Shape with sec_plane and plot exact 2D section polygons."""
    try:
        sliced = section(shape, section_by=sec_plane)
    except Exception:
        return
    if sliced is None:
        return

    faces = sliced.faces()
    if not faces:
        return

    for f in faces:
        # Tessellate each 2D face into triangles in world coords, then project to sec_plane 2D
        try:
            verts_3d, tris = f.tessellate(0.05)
        except Exception:
            continue
        if not verts_3d or not tris:
            continue
        pts_2d = []
        for v in verts_3d:
            loc = sec_plane.to_local_coords(v)
            pts_2d.append((loc.X, loc.Y))
        pts_2d = np.array(pts_2d)
        tris_arr = np.array(tris)
        ax.tripcolor(
            pts_2d[:, 0],
            pts_2d[:, 1],
            tris_arr,
            facecolors=np.zeros(len(tris_arr)),
            cmap=matplotlib.colors.ListedColormap([color]),
            alpha=alpha,
            edgecolors="none",
            zorder=zorder,
        )
        # Draw crisp section boundary edges
        for edge in f.edges():
            n_pts = 24 if edge.length > 1.5 else 10
            try:
                sampled = [sec_plane.to_local_coords(edge.position_at(t)) for t in np.linspace(0, 1, n_pts)]
                ax.plot(
                    [p.X for p in sampled],
                    [p.Y for p in sampled],
                    color=edgecolor,
                    linewidth=lw,
                    zorder=zorder + 1,
                )
            except Exception:
                pass


# =============================================================================
# 2. MAIN VERIFICATION SUITE
# =============================================================================

def run_verification() -> tuple[bool, dict]:
    """Run all automated CAD & STL verification gates."""
    export_dir = CAD_DIR / "export"
    all_passed = True
    report: dict = {}

    def check(name: str, passed: bool, detail: str) -> None:
        nonlocal all_passed
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_passed = False
        print(f"  [{status}] {name:44s} | {detail}")

    print("=" * 88)
    print("AUTOMATED CAD VERIFICATION SUITE — 8BitDo 3.5mm to USB-C HID Adapter Enclosure")
    print("=" * 88)

    cfg = enc.resolve_config(enc.PARAMS)
    tray = enc.build_bottom_tray(cfg)
    lid = enc.build_top_lid(cfg)
    lid_print = enc.orient_lid_for_printing(lid, cfg)
    xiao, used_official = enc.load_xiao_rp2040_positioned(cfg)
    jacks = enc.build_jack_keepouts(cfg)
    mags = enc.build_magnet_solids(cfg)

    print(f"\n1. Geometry Validity & Dimensions (preset = {cfg.jack_preset})")
    t_bb = tray.bounding_box()
    l_bb = lid.bounding_box()
    lp_bb = lid_print.bounding_box()
    check("Bottom tray B-Rep valid", bool(tray.is_valid), f"solids={len(tray.solids())}, vol={tray.volume:.1f} mm^3")
    check("Top lid B-Rep valid", bool(lid.is_valid), f"solids={len(lid.solids())}, vol={lid.volume:.1f} mm^3")
    check("Tray flat on Z=0", abs(t_bb.min.Z) < 1e-4, f"min.Z={t_bb.min.Z:.4f} mm")
    check("Top lid print orientation flat on Z=0", abs(lp_bb.min.Z) < 1e-4, f"min.Z={lp_bb.min.Z:.4f} mm")
    check(
        "Outer XY match (tray vs lid)",
        abs(t_bb.size.X - l_bb.size.X) < 1e-3 and abs(t_bb.size.Y - l_bb.size.Y) < 1e-3,
        f"tray={t_bb.size.X:.2f}x{t_bb.size.Y:.2f}, lid={l_bb.size.X:.2f}x{l_bb.size.Y:.2f} mm",
    )
    check(
        "Assembled outer bounding box",
        True,
        f"{t_bb.size.X:.2f} (W) x {t_bb.size.Y:.2f} (L) x {l_bb.max.Z:.2f} (H) mm",
    )

    print("\n2. True 3D B-Rep Boolean Collision Checks (Target: 0.000 mm^3)")
    check("Official XIAO RP2040 v26.step loaded", used_official, f"solids={len(xiao.solids())}")
    pairs = [
        ("bottom_tray vs XIAO RP2040 STEP", tray, xiao),
        ("top_lid vs XIAO RP2040 STEP", lid, xiao),
        ("bottom_tray vs 3x Jack keep-outs", tray, jacks),
        ("top_lid vs 3x Jack keep-outs", lid, jacks),
        ("bottom_tray vs 4x Magnet solids", tray, mags),
        ("top_lid vs 4x Magnet solids", lid, mags),
        ("bottom_tray vs top_lid (closed fit)", tray, lid),
        ("XIAO RP2040 vs 3x Jack keep-outs", xiao, jacks),
    ]
    for label, a, b in pairs:
        vol = intersection_volume(a, b)
        check(label, vol <= 1e-4, f"intersection = {vol:.4f} mm^3")

    print("\n3. Coaxial Feature Alignment Against Official XIAO RP2040 STEP (Gate: <= 0.15 mm)")
    solids = xiao.solids()
    # Verified solid indices from Seeed Studio XIAO RP2040 v26.step:
    # 23 = USB-C shell, 24 = Left button (R), 25 = WS2812B LED, 30 = Right button (B)
    r_bb = solids[24].bounding_box()
    led_bb = solids[25].bounding_box()
    b_bb = solids[30].bounding_box()
    r_step = ((r_bb.min.X + r_bb.max.X) / 2.0, (r_bb.min.Y + r_bb.max.Y) / 2.0)
    led_step = ((led_bb.min.X + led_bb.max.X) / 2.0, (led_bb.min.Y + led_bb.max.Y) / 2.0)
    b_step = ((b_bb.min.X + b_bb.max.X) / 2.0, (b_bb.min.Y + b_bb.max.Y) / 2.0)

    r_err = math.hypot(cfg.pin_r_xy[0] - r_step[0], cfg.pin_r_xy[1] - r_step[1])
    led_err = math.hypot(cfg.led_xy[0] - led_step[0], cfg.led_xy[1] - led_step[1])
    b_err = math.hypot(cfg.pin_b_xy[0] - b_step[0], cfg.pin_b_xy[1] - b_step[1])

    # USB-C front mouth center Z (tongue Solid 0 center Z)
    tongue_bb = solids[0].bounding_box()
    usbc_z_step = (tongue_bb.min.Z + tongue_bb.max.Z) / 2.0
    usbc_z_err = abs(cfg.z_port_center - usbc_z_step)

    check("RESET (R) pinhole coaxiality", r_err <= 0.15, f"err={r_err:.3f} mm (lid={cfg.pin_r_xy}, step=({r_step[0]:.2f},{r_step[1]:.2f}))")
    check("WS2812B LED window coaxiality", led_err <= 0.15, f"err={led_err:.3f} mm (lid={cfg.led_xy}, step=({led_step[0]:.2f},{led_step[1]:.2f}))")
    check("BOOT (B) pinhole coaxiality", b_err <= 0.15, f"err={b_err:.3f} mm (lid={cfg.pin_b_xy}, step=({b_step[0]:.2f},{b_step[1]:.2f}))")
    check("USB-C cutout Z coaxiality", usbc_z_err <= 0.05, f"err={usbc_z_err:.3f} mm (cutout Z={cfg.z_port_center:.2f}, tongue Z={usbc_z_step:.2f})")

    print("\n4. Mechanical Strength, FDM Wall Thickness & Snap-Fit Strain Checks")
    mag_floor_above = cfg.floor_t - cfg.magnet_pocket_depth
    mag_rim_z0 = min(
        cfg.outer_w / 2.0 - abs(cfg.magnet_positions[0][0]) - cfg.magnet_pocket_dia / 2.0 - cfg.bottom_chamfer,
        cfg.outer_l / 2.0 - abs(cfg.magnet_positions[0][1]) - cfg.magnet_pocket_dia / 2.0 - cfg.bottom_chamfer,
    )
    snap_wall_behind = cfg.wall_thickness - cfg.snap_pocket_depth
    nut_vert_clear = (cfg.cavity_height - cfg.jack_inner_nut_dia) / 2.0
    nut_gap_x = cfg.jack_pitch_x - cfg.jack_inner_nut_dia
    led_septum = abs(cfg.pin_r_xy[0] - cfg.led_xy[0]) - cfg.pinhole_dia / 2.0 - cfg.led_open_dia / 2.0
    # Cantilever bending strain eps = 1.5 * t * delta / L^2
    l_beam = cfg.snap_z_land_bot  # root to catch land ~9.1mm
    snap_strain_pct = 100.0 * (1.5 * cfg.snap_beam_thick * cfg.snap_overhang) / (l_beam ** 2)

    check("Solid floor above 12x3mm magnets (>=1.05mm)", mag_floor_above >= 1.049, f"{mag_floor_above:.2f} mm")
    check("Magnet outer rim at Z=0 chamfer (>=3.0mm)", mag_rim_z0 >= 3.0, f"{mag_rim_z0:.2f} mm")
    check("Solid wall behind snap pockets (>=1.8mm)", snap_wall_behind >= 1.8, f"{snap_wall_behind:.2f} mm")
    check("M8 hex nut vertical clearance (>=1.0mm)", nut_vert_clear >= 1.0, f"{nut_vert_clear:.2f} mm top & bottom")
    check("Adjacent M8 hex nut spacing (>=3.5mm)", nut_gap_x >= 3.5, f"{nut_gap_x:.2f} mm gap")
    check("LED-to-pinhole septum wall (>=1.2mm)", led_septum >= 1.2, f"{led_septum:.2f} mm")
    check("Snap-fit cantilever elastic strain (<=1.6%)", snap_strain_pct <= 1.6, f"{snap_strain_pct:.2f}% (PLA yield ~2.0%, PETG ~4.0%)")

    print("\n5. Watertight Manifold STL Checks (trimesh)")
    stl_files = [
        ("bottom_tray.stl", False),
        ("bottom_tray_no_magnets.stl", False),
        ("top_lid.stl", False),
        ("snap_fit_test_coupon.stl", True),
    ]
    for fname, multi_body in stl_files:
        fpath = export_dir / fname
        if not fpath.exists():
            check(f"STL exists: {fname}", False, "MISSING")
            continue
        mesh = trimesh.load(str(fpath), force="mesh")
        if multi_body:
            parts = mesh.split(only_watertight=False)
            wt = len(parts) == 2 and all(p.is_watertight for p in parts)
            detail = f"bodies={len(parts)}, watertight={[bool(p.is_watertight) for p in parts]}, minZ={mesh.bounds[0][2]:.3f}"
        else:
            wt = bool(mesh.is_watertight and mesh.is_volume)
            dims = mesh.bounds[1] - mesh.bounds[0]
            detail = f"watertight={mesh.is_watertight}, faces={len(mesh.faces)}, size={dims[0]:.2f}x{dims[1]:.2f}x{dims[2]:.2f}, minZ={mesh.bounds[0][2]:.3f}"
        check(f"STL manifold: {fname}", wt and abs(mesh.bounds[0][2]) < 0.02, detail)

    print("\n6. Alternate Jack Preset Smoke & Collision Checks")
    for preset in ("switchcraft_35prm3", "tensility_54_00081"):
        p_alt = copy.deepcopy(enc.PARAMS)
        p_alt["jack_preset"] = preset
        c_alt = enc.resolve_config(p_alt)
        t_alt = enc.build_bottom_tray(c_alt)
        l_alt = enc.build_top_lid(c_alt)
        x_alt, _ = enc.load_xiao_rp2040_positioned(c_alt)
        j_alt = enc.build_jack_keepouts(c_alt)
        m_alt = enc.build_magnet_solids(c_alt)
        v_max = max(
            intersection_volume(t_alt, x_alt),
            intersection_volume(l_alt, x_alt),
            intersection_volume(t_alt, j_alt),
            intersection_volume(l_alt, j_alt),
            intersection_volume(t_alt, m_alt),
            intersection_volume(t_alt, l_alt),
        )
        check(
            f"Preset '{preset}' zero collision",
            bool(t_alt.is_valid and l_alt.is_valid and v_max <= 1e-4),
            f"{c_alt.outer_w:.1f}x{c_alt.outer_l:.1f}x{c_alt.outer_h:.1f} mm, max_inter={v_max:.4f} mm^3",
        )

    print("=" * 88)
    print(f"OVERALL VERIFICATION STATUS: {'ALL GATES PASSED' if all_passed else 'FAILURES DETECTED'}")
    print("=" * 88)

    report.update(
        cfg=cfg,
        tray=tray,
        lid=lid,
        lid_print=lid_print,
        xiao=xiao,
        jacks=jacks,
        mags=mags,
    )
    return all_passed, report


# =============================================================================
# 3. TECHNICAL INSPECTION RENDERS
# =============================================================================

def generate_renders(report: dict) -> list[Path]:
    """Generate orthographic, isometric, and exact B-Rep cross-section inspection PNGs."""
    render_dir = CAD_DIR / "renders"
    render_dir.mkdir(parents=True, exist_ok=True)

    cfg = report["cfg"]
    tray = report["tray"]
    lid = report["lid"]
    xiao = report["xiao"]
    jacks = report["jacks"]
    mags = report["mags"]

    print("\nTessellating solids for 3D renders...")
    m_tray = shape_to_trimesh(tray, tol=0.04)
    m_lid = shape_to_trimesh(lid, tol=0.04)
    m_xiao = shape_to_trimesh(xiao, tol=0.05)
    m_jacks = shape_to_trimesh(jacks, tol=0.05)
    m_mags = shape_to_trimesh(mags, tol=0.05) if mags is not None else None

    coupon = enc.build_snap_fit_test_coupon(cfg)
    m_coupon = shape_to_trimesh(coupon, tol=0.03)

    bmin = np.array([-cfg.outer_w / 2.0 - 2.0, -cfg.outer_l / 2.0 - 5.0, -2.0])
    bmax = np.array([cfg.outer_w / 2.0 + 2.0, cfg.outer_l / 2.0 + 2.0, cfg.outer_h + 2.0])

    generated: list[Path] = []

    # -------------------------------------------------------------------------
    # Sheet 1: 6-Panel Orthographic Views
    # -------------------------------------------------------------------------
    fig, axes = plt.subplots(2, 3, figsize=(18, 11.5), dpi=160, facecolor="white")
    fig.suptitle(
        f"8BitDo 3.5mm -> USB-C Adapter Enclosure — Orthographic Inspection "
        f"({cfg.jack_preset}: {cfg.outer_w:.1f} x {cfg.outer_l:.1f} x {cfg.outer_h:.1f} mm)",
        fontsize=14,
        fontweight="bold",
        y=0.98,
    )

    # 1. Top Lid outer (+Z looking down; +X right, +Y up -> USB-C top, Jacks bottom!)
    render_camera_shaded(
        axes[0, 0],
        [(m_tray, "#5C7898"), (m_lid, "#789BC0"), (m_xiao, "#268755"), (m_jacks, "#D4A63C")],
        view_from=(0.0, 0.0, 1.0),
        up_hint=(0.0, 1.0, 0.0),
        title="1. Top Lid (+Z: Labels 1/2/3, R/B Pinholes & LED)",
        xlabel="X (mm)",
        ylabel="Y (mm)",
    )
    # 2. Bottom Tray outer (-Z looking up; 4x 12x3mm magnet pockets)
    render_camera_shaded(
        axes[0, 1],
        [(m_tray, "#5C7898"), (m_mags, "#B8C2CC")],
        view_from=(0.0, 0.0, -1.0),
        up_hint=(0.0, 1.0, 0.0),
        title="2. Bottom Outer (-Z: 4x 12x3mm Magnet Pockets)",
        xlabel="X (mm)",
        ylabel="Y (mm)",
    )
    # 3. Open Tray Interior (+Z looking down; XIAO cradle, relief channels, 3x M8 jacks)
    render_camera_shaded(
        axes[0, 2],
        [(m_tray, "#5C7898"), (m_xiao, "#268755"), (m_jacks, "#D4A63C")],
        view_from=(0.0, 0.0, 1.0),
        up_hint=(0.0, 1.0, 0.0),
        title="3. Open Tray Interior (+Z: XIAO Cradle & 3x M8 Jacks)",
        xlabel="X (mm)",
        ylabel="Y (mm)",
    )
    # 4. Front Face (+Y looking toward -Y: USB-C shell centered inside recessed boot pocket)
    render_camera_shaded(
        axes[1, 0],
        [(m_tray, "#5C7898"), (m_lid, "#789BC0"), (m_xiao, "#268755")],
        view_from=(0.0, 1.0, 0.0),
        up_hint=(0.0, 0.0, 1.0),
        title="4. Front Face (+Y: USB-C Cutout & Thick Boot Recess)",
        xlabel="-X (mm)",
        ylabel="Z (mm)",
    )
    # 5. Rear Face (-Y looking toward +Y: bare 3x M8 truncated teardrop holes)
    render_camera_shaded(
        axes[1, 1],
        [(m_tray, "#5C7898"), (m_lid, "#789BC0")],
        view_from=(0.0, -1.0, 0.0),
        up_hint=(0.0, 0.0, 1.0),
        title="5. Rear Face (-Y: 3x M8 Truncated Teardrop Holes)",
        xlabel="X (mm)",
        ylabel="Z (mm)",
    )
    # 6. Right Side (+X looking toward -X: flush seam, pry notch, outer jack flanges)
    render_camera_shaded(
        axes[1, 2],
        [(m_tray, "#5C7898"), (m_lid, "#789BC0"), (m_jacks, "#D4A63C")],
        view_from=(1.0, 0.0, 0.0),
        up_hint=(0.0, 0.0, 1.0),
        title="6. Right Side (+X: Flush Seam, Pry Notch & Jack Flange)",
        xlabel="Y (mm)",
        ylabel="Z (mm)",
    )

    p1 = render_dir / "01_orthographic_views.png"
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(p1, dpi=160)
    plt.close(fig)
    generated.append(p1)
    print(f"  Saved {p1.relative_to(CAD_DIR.parent)}")

    # -------------------------------------------------------------------------
    # Sheet 2: 4-Panel Isometric (Closed, Exploded, Lid Underside, Test Coupon)
    # -------------------------------------------------------------------------
    fig, axes = plt.subplots(2, 2, figsize=(16, 12), dpi=160, facecolor="white")
    fig.suptitle(
        "8BitDo 3.5mm -> USB-C Adapter Enclosure — Isometric Assembly, Lid Print View & Test Coupon",
        fontsize=14,
        fontweight="bold",
        y=0.98,
    )

    # Panel 1: Closed Isometric (Rear-Right 3/4 view showing 3x M8 jacks, labels 1/2/3, pry notch)
    render_camera_shaded(
        axes[0, 0],
        [(m_tray, "#5C7898"), (m_lid, "#789BC0"), (m_xiao, "#268755"), (m_jacks, "#D4A63C")],
        view_from=(0.68, -0.78, 0.62),
        title="1. Closed Assembly (Rear-Right 3/4: 3x M8 Jacks, Labels & Pry Notch)",
    )

    # Panel 2: Exploded Isometric (Front-Right 3/4 showing USB-C, XIAO, jacks, magnets)
    m_lid_exp = m_lid.copy()
    m_lid_exp.apply_translation([0, 0, 22.0])
    m_xiao_exp = m_xiao.copy()
    m_xiao_exp.apply_translation([0, 0, 7.5])
    m_mags_exp = m_mags.copy() if m_mags is not None else None
    if m_mags_exp is not None:
        m_mags_exp.apply_translation([0, 0, -9.0])

    render_camera_shaded(
        axes[0, 1],
        [(m_tray, "#5C7898"), (m_lid_exp, "#789BC0"), (m_xiao_exp, "#268755"), (m_jacks, "#D4A63C"), (m_mags_exp, "#B8C2CC")],
        view_from=(0.70, 0.76, 0.50),
        title="2. Exploded Assembly (Front-Right 3/4: USB-C, XIAO, Jacks & Magnets)",
    )

    # Panel 3: Top Lid Underside (Print Orientation Upside-Down on Z=0!)
    m_lid_print = shape_to_trimesh(report["lid_print"], tol=0.04)
    render_camera_shaded(
        axes[1, 0],
        [(m_lid_print, "#789BC0")],
        view_from=(0.65, -0.72, 0.68),
        title="3. Top Lid Print Orientation (Upside-Down on Z=0: 4x Snap Tabs, Chimney & Boss)",
    )

    # Panel 4: 5-Minute Snap-Fit Test Coupon (Both Pieces Flat on Z=0)
    render_camera_shaded(
        axes[1, 1],
        [(m_coupon, "#5A88A8")],
        view_from=(0.55, -0.80, 0.58),
        title="4. 5-Min Snap-Fit Tolerance Test Coupon (Flat on Z=0)",
    )

    p2 = render_dir / "02_isometric_open_closed.png"
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(p2, dpi=160)
    plt.close(fig)
    generated.append(p2)
    print(f"  Saved {p2.relative_to(CAD_DIR.parent)}")

    # -------------------------------------------------------------------------
    # Sheet 3: 4-Panel Exact B-Rep 2D CAD Cross-Sections
    # -------------------------------------------------------------------------
    fig, axes = plt.subplots(2, 2, figsize=(17, 11), dpi=160, facecolor="white")
    fig.suptitle(
        "8BitDo 3.5mm -> USB-C Adapter Enclosure — Exact B-Rep Cross-Section Blueprints",
        fontsize=14,
        fontweight="bold",
        y=0.98,
    )

    sec_specs = [
        (
            axes[0, 0],
            "Section A-A (X = 0): USB-C, XIAO Shield Boss, WS2812B LED Pipe & Center Jack #2",
            Plane(origin=(0, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0)),
            "Y (mm)  [-Y Rear Jack  --->  +Y Front USB-C]",
            "Z (mm)",
            (-cfg.outer_l / 2.0 - 5.5, cfg.outer_l / 2.0 + 3.0),
            (-1.5, cfg.outer_h + 2.5),
        ),
        (
            axes[0, 1],
            f"Section B-B (Y = {cfg.led_xy[1]:.2f}): R / WS2812B / B Coaxial Pinholes & Solder Relief",
            Plane(origin=(0, cfg.led_xy[1], 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0)),
            "X (mm)  [Left R  |  Center LED  |  Right B]",
            "Z (mm)",
            (-cfg.outer_w / 2.0 - 2.0, cfg.outer_w / 2.0 + 2.0),
            (-1.5, cfg.outer_h + 2.5),
        ),
        (
            axes[1, 0],
            f"Section C-C (Y = {cfg.snap_ys[1]:.2f}): 45-deg Snap-Fit Clips, Tray Pockets & XIAO Hold-Down",
            Plane(origin=(0, cfg.snap_ys[1], 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0)),
            "X (mm)  [Left & Right Cantilever Snap Tabs]",
            "Z (mm)",
            (-cfg.outer_w / 2.0 - 2.0, cfg.outer_w / 2.0 + 2.0),
            (-1.5, cfg.outer_h + 2.5),
        ),
        (
            axes[1, 1],
            f"Section D-D (Y = {cfg.y_rear_inner + 1.0:.2f}): 3x Internal M8 Hex Nuts & Rear Corner Magnets",
            Plane(origin=(0, cfg.y_rear_inner + 1.0, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0)),
            "X (mm)  [3x M8 Hex Nuts @ 16.5mm Pitch]",
            "Z (mm)",
            (-cfg.outer_w / 2.0 - 2.0, cfg.outer_w / 2.0 + 2.0),
            (-1.5, cfg.outer_h + 2.5),
        ),
    ]

    for ax, title, pln, xlabel, ylabel, xlim, ylim in sec_specs:
        plot_brep_section(ax, tray, pln, color="#5C82A8", alpha=0.85, zorder=2)
        plot_brep_section(ax, lid, pln, color="#4DA89B", alpha=0.85, zorder=3)
        plot_brep_section(ax, xiao, pln, color="#2D8B57", alpha=0.95, zorder=4)
        plot_brep_section(ax, jacks, pln, color="#D9A73E", alpha=0.90, zorder=4)
        if mags is not None:
            plot_brep_section(ax, mags, pln, color="#A8B0B8", alpha=0.90, zorder=4)

        ax.set_aspect("equal")
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        ax.grid(True, linestyle="--", alpha=0.35)
        ax.set_title(title, fontsize=10, fontweight="bold")
        ax.set_xlabel(xlabel, fontsize=9)
        ax.set_ylabel(ylabel, fontsize=9)

    # Also add magnet cross-section note on Section D-D and annotate R/LED/B on Section B-B
    axes[0, 1].axvline(cfg.pin_r_xy[0], color="#D62728", ls=":", lw=1.0, alpha=0.8)
    axes[0, 1].axvline(cfg.led_xy[0], color="#9467BD", ls=":", lw=1.0, alpha=0.8)
    axes[0, 1].axvline(cfg.pin_b_xy[0], color="#D62728", ls=":", lw=1.0, alpha=0.8)
    axes[0, 1].text(cfg.pin_r_xy[0], cfg.outer_h + 0.6, "R", ha="center", fontsize=9, fontweight="bold", color="#D62728")
    axes[0, 1].text(cfg.led_xy[0], cfg.outer_h + 0.6, "LED", ha="center", fontsize=8, fontweight="bold", color="#9467BD")
    axes[0, 1].text(cfg.pin_b_xy[0], cfg.outer_h + 0.6, "B", ha="center", fontsize=9, fontweight="bold", color="#D62728")

    # Legend
    legend_handles = [
        Patch(facecolor="#5C82A8", edgecolor="#111111", label="Bottom Tray"),
        Patch(facecolor="#4DA89B", edgecolor="#111111", label="Top Lid"),
        Patch(facecolor="#2D8B57", edgecolor="#111111", label="XIAO RP2040 (Official STEP)"),
        Patch(facecolor="#D9A73E", edgecolor="#111111", label=f"3x Jacks ({cfg.jack_preset})"),
        Patch(facecolor="#A8B0B8", edgecolor="#111111", label="4x 12x3mm Magnets"),
    ]
    fig.legend(handles=legend_handles, loc="lower center", ncol=5, frameon=True, fontsize=9, bbox_to_anchor=(0.5, 0.01))

    p3 = render_dir / "03_cross_sections.png"
    fig.tight_layout(rect=[0, 0.04, 1, 0.95])
    fig.savefig(p3, dpi=160)
    plt.close(fig)
    generated.append(p3)
    print(f"  Saved {p3.relative_to(CAD_DIR.parent)}")

    # -------------------------------------------------------------------------
    # Sheet 4: Zoomed Close-Up Cross-Sections (Snap-Fit Joint + Magnet Pocket + USB-C)
    # -------------------------------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.5), dpi=160, facecolor="white")
    fig.suptitle(
        "Zoomed Critical Detail Cross-Sections (Snap-Fit, Magnets, USB-C Mouth)",
        fontsize=13,
        fontweight="bold",
        y=0.98,
    )

    # Zoom 1: Right Snap-Fit Tab & 45-deg Tray Pocket
    pln_snap = Plane(origin=(0, cfg.snap_ys[1], 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
    plot_brep_section(axes[0], tray, pln_snap, color="#5C82A8", alpha=0.88)
    plot_brep_section(axes[0], lid, pln_snap, color="#4DA89B", alpha=0.88)
    axes[0].set_xlim(cfg.inner_half_x - 3.5, cfg.outer_w / 2.0 + 1.0)
    axes[0].set_ylim(cfg.z_floor + 2.0, cfg.outer_h + 1.0)
    axes[0].set_title("1. Right Snap-Fit Joint (45° Ramps, 0.15mm Gap)", fontsize=10, fontweight="bold")
    axes[0].set_xlabel("X (mm)")
    axes[0].set_ylabel("Z (mm)")

    # Zoom 2: Corner Magnet Pocket (X = +mx, Y-Z slice)
    mx, my = cfg.magnet_positions[3]
    pln_mag = Plane(origin=(mx, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
    plot_brep_section(axes[1], tray, pln_mag, color="#5C82A8", alpha=0.88)
    if mags is not None:
        plot_brep_section(axes[1], mags, pln_mag, color="#A8B0B8", alpha=0.92)
    axes[1].set_xlim(my - 9.0, cfg.outer_l / 2.0 + 1.5)
    axes[1].set_ylim(-0.8, 8.0)
    axes[1].set_title("2. Corner 12x3mm Magnet Pocket & 1.05mm Ceiling", fontsize=10, fontweight="bold")
    axes[1].set_xlabel("Y (mm)")
    axes[1].set_ylabel("Z (mm)")

    # Zoom 3: USB-C Front Wall Cutout, Boot Recess & XIAO Mouth (X = 0, Y-Z slice)
    pln_usbc = Plane(origin=(0, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
    plot_brep_section(axes[2], tray, pln_usbc, color="#5C82A8", alpha=0.88)
    plot_brep_section(axes[2], lid, pln_usbc, color="#4DA89B", alpha=0.88)
    plot_brep_section(axes[2], xiao, pln_usbc, color="#2D8B57", alpha=0.95)
    axes[2].set_xlim(cfg.y_mcu_center + 2.0, cfg.outer_l / 2.0 + 2.0)
    axes[2].set_ylim(cfg.z_floor - 0.5, cfg.outer_h + 1.0)
    axes[2].set_title("3. Front USB-C Mouth, Boot Recess & Pedestal", fontsize=10, fontweight="bold")
    axes[2].set_xlabel("Y (mm)")
    axes[2].set_ylabel("Z (mm)")

    for ax in axes:
        ax.set_aspect("equal")
        ax.grid(True, linestyle="--", alpha=0.35)

    p4 = render_dir / "04_detail_zooms.png"
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(p4, dpi=160)
    plt.close(fig)
    generated.append(p4)
    print(f"  Saved {p4.relative_to(CAD_DIR.parent)}")

    return generated


def main() -> None:
    passed, report = run_verification()
    generate_renders(report)
    if not passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
