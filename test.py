# radiocarbon_space_geomag.py
# ------------------------------------------------------------
# Create an illustration showing:
#   - Sun, solar energetic particles, and galactic cosmic rays
#   - Earth with dotted geomagnetic field rings
#   - Right-hand inset with carbon cycle and isotopes (14C, 10Be, 36Cl)
#
# Requirements:
#   pip install matplotlib
#
# Usage:
#   python radiocarbon_space_geomag.py
#   # or import and call draw_illustration(output_path="my_image.png", dpi=300)
# ------------------------------------------------------------

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Arc, Wedge, Rectangle

def draw_illustration(
    output_path="space_geomag_carboncycle.png",
    dpi=220,
    figsize=(18, 7),
    theme="dark",
    locale="en",
):
    """
    Render the illustration and save as an image.

    Parameters
    ----------
    output_path : str
        File path for the exported image (PNG/JPG).
    dpi : int
        Dots per inch for export resolution.
    figsize : tuple
        Figure size in inches (width, height).
    theme : str
        'dark' (default) or 'light' background.
    locale : str
        Language hint for labels ('en' default). If you want labels in German,
        set locale='de' (a few translations included); you can easily extend.
    """

    # --- Basic theme colors ---
    if theme.lower() == "light":
        bg = "#ffffff"
        fg = "#111111"
        dotted = (0, 0, 0, 0.7)
        sea = "#3da0d2"
        land = "#72c472"
        earth_blue = "#6ec0ff"
        geomag_color = (0, 0, 0, 0.8)
        label_iso = "#2e3a90"
    else:  # dark
        bg = "#0b0b0f"
        fg = "#ffffff"
        dotted = (1, 1, 1, 0.8)
        sea = "#3da0d2"
        land = "#72c472"
        earth_blue = "#6ec0ff"
        geomag_color = (1, 1, 1, 0.8)
        label_iso = "#2e3a90"

    # --- Labels (minimal i18n) ---
    labels = {
        "en": {
            "solar": "Solar energetic particles",
            "galactic": "Galactic cosmic rays",
            "geomag": "Geomagnetic field",
            "carbon_cycle": "Carbon cycle",
            "isotopes": "¹⁴C, ¹⁰Be, ³⁶Cl",
            "c14": "¹⁴C",
        },
        "de": {
            "solar": "Solare hochenergetische Partikel",
            "galactic": "Galaktische kosmische Strahlung",
            "geomag": "Geomagnetisches Feld",
            "carbon_cycle": "Kohlenstoffkreislauf",
            "isotopes": "¹⁴C, ¹⁰Be, ³⁶Cl",
            "c14": "¹⁴C",
        },
        # Extend here if you need more languages
    }
    L = labels.get(locale.lower(), labels["en"])

    # --- Canvas ---
    plt.rcParams.update({"figure.figsize": figsize, "font.size": 14})
    fig, ax = plt.subplots()
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 7)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)

    # --- SUN ---
    ax.add_patch(Circle((2.5, 3.5), 1.6, fc="#ffc300", ec="#ffb000", lw=2))
    # subtle glow rings
    for r, a in [(2.0, 0.08), (2.4, 0.05)]:
        ax.add_patch(Circle((2.5, 3.5), r, fc="none", ec=(1, 0.8, 0, a), lw=10))

    # --- EARTH ---
    ax.add_patch(Circle((9, 3.5), 1.3, fc=earth_blue, ec="#1b4f72", lw=2))
    # stylized continents (simple wedges just for impressionistic shapes)
    ax.add_patch(Wedge((9.2, 3.7), 1.05, 140, 210, width=0.5, fc=land, ec="none", alpha=0.9))
    ax.add_patch(Wedge((8.6, 3.4), 0.9, -40, 50, width=0.4, fc=land, ec="none", alpha=0.9))
    ax.add_patch(Wedge((9.2, 3.1), 0.8, 220, 320, width=0.35, fc=land, ec="none", alpha=0.9))

    # atmosphere / geomagnetic field (dotted rings)
    for r, a in [(1.55, 0.8), (1.8, 0.5), (2.05, 0.3)]:
        ax.add_patch(Circle((9, 3.5), r, fill=False, ec=(dotted[0], dotted[1], dotted[2], a), lw=1.2, ls=":"))

    ax.text(9, 5.9, L["geomag"], color=fg, ha="center", va="center", fontsize=14)

    # --- PARTICLE PATHS ---
    # Solar energetic particles (yellow) from Sun to Earth
    for yoff in [-0.3, 0.0, 0.3]:
        ax.add_patch(
            FancyArrowPatch(
                (4.2, 3.5 + yoff),
                (7.6, 3.5),
                connectionstyle=f"arc3,rad={-0.25 + yoff/1.2:.2f}",
                arrowstyle="-|>",
                mutation_scale=14,
                lw=3,
                color="#ffd54d",
            )
        )

    # Galactic cosmic rays (red) sweeping above and below
    for sign in [1, -1]:
        ax.add_patch(
            FancyArrowPatch(
                (0.5, 3.5 + 2.2 * sign),
                (8.0, 3.5),
                connectionstyle=f"arc3,rad={0.25 * sign}",
                arrowstyle="-|>",
                mutation_scale=14,
                lw=3,
                color="#ff3b3b",
            )
        )

    # Ray labels
    ax.text(2.8, 5.9, L["solar"], color=fg, ha="left", va="center")
    ax.text(1.0, 1.1, L["galactic"], color=fg, ha="left", va="center")

    # --- Connectors from Earth to the inset ---
    for y in (3.0, 4.0, 3.5):
        ax.plot([10.3, 13.0], [y, y + 0.8 * (y - 3.5)], color=fg, ls="--", lw=1)

    # --- RIGHT-HAND INSET: Carbon cycle & isotopes ---
    cx, cy, R = 15.0, 3.5, 2.2
    ax.add_patch(Circle((cx, cy), R, fc="#e9f4ff" if theme == "light" else "#e9f4ff", ec=fg, lw=2))

    # Ground and ocean bands
    ax.add_patch(Rectangle((cx - R, cy - R), 2 * R, R * 0.95, fc="#8a5a3b", ec="none"))  # soil
    ax.add_patch(Rectangle((cx - R, cy - 0.05), 2 * R, R * 0.55, fc=sea, ec="none"))      # water

    # Simple trees
    for tx in (cx - 1.5, cx + 1.5):
        ax.add_patch(Rectangle((tx - 0.12, cy + 0.6), 0.24, 0.6, fc="#7a4a2a", ec="none"))  # trunk
        ax.add_patch(Circle((tx, cy + 1.4), 0.5, fc=land, ec="none"))                       # canopy

    # Circular carbon-cycle arrows
    arc1 = Arc((cx, cy + 0.3), 2.3, 2.3, angle=0, theta1=35, theta2=180, lw=4, color="#2e3a46")
    arc2 = Arc((cx, cy + 0.3), 2.3, 2.3, angle=0, theta1=200, theta2=345, lw=4, color="#2e3a46")
    ax.add_patch(arc1)
    ax.add_patch(arc2)
    # arrowheads at the top of the arcs
    ax.add_patch(FancyArrowPatch((cx - 0.9, cy + 1.5), (cx - 0.88, cy + 1.5), arrowstyle="-|>", mutation_scale=18, color="#2e3a46"))
    ax.add_patch(FancyArrowPatch((cx + 0.9, cy + 1.5), (cx + 0.92, cy + 1.5), arrowstyle="-|>", mutation_scale=18, color="#2e3a46"))

    # Inset labels
    ax.text(cx, cy + 1.9, L["carbon_cycle"], ha="center", va="center", color=fg, fontsize=14)
    ax.text(cx, cy + 1.55, L["isotopes"], ha="center", va="center", color=label_iso, fontsize=12)
    ax.text(cx, cy + 0.95, L["c14"], ha="center", va="center", color="#1f2a35", fontsize=24, fontweight="bold")

    # Export
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"Saved: {output_path}")
    return fig


if __name__ == "__main__":
    # Example: dark theme, English labels, 220 dpi
    draw_illustration(output_path="space_geomag_carboncycle.png", dpi=220, theme="dark", locale="en")

    # Uncomment to export a light-theme version in higher resolution:
    # draw_illustration(output_path="space_geomag_carboncycle_light.png", dpi=300, theme="light", locale="de")
