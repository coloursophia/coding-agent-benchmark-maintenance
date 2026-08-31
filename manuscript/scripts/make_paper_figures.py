from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / "artifacts" / "formal-v3-local-r3"
OUTPUT = ROOT / "manuscript" / "figures"

INK = "#000000"
MUTED = "#000000"
GRID = "#D9DEE3"
LIGHT_GRID = "#EEF1F4"
WHITE = "#FFFFFF"
BLUE = "#1F5A94"
BLUE_LIGHT = "#AFC9DF"
ORANGE = "#C96A2B"
ORANGE_LIGHT = "#EBC5AC"
OLIVE = "#6F7D3E"
OLIVE_LIGHT = "#C9D0AF"
GOLD = "#C69A2B"
GRAY = "#5F6B76"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "arialbd.ttf" if bold else "arial.ttf"
    path = Path("C:/Windows/Fonts") / name
    return ImageFont.truetype(str(path), size=size)


F_TITLE = font(46, True)
F_SUBTITLE = font(24)
F_PANEL = font(27, True)
F_AXIS = font(20)
F_SMALL = font(17)
F_LABEL = font(20, True)
F_NOTE = font(18)


def read_csv(name: str) -> list[dict[str, str]]:
    with (ARTIFACT / name).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def line(draw: ImageDraw.ImageDraw, points, fill, width=3, dash=None):
    if not dash:
        draw.line(points, fill=fill, width=width, joint="curve")
        return
    on, off = dash
    for p1, p2 in zip(points, points[1:]):
        x1, y1 = p1
        x2, y2 = p2
        dx, dy = x2 - x1, y2 - y1
        length = max((dx * dx + dy * dy) ** 0.5, 1)
        ux, uy = dx / length, dy / length
        cursor = 0.0
        while cursor < length:
            end = min(cursor + on, length)
            draw.line(
                [(x1 + ux * cursor, y1 + uy * cursor),
                 (x1 + ux * end, y1 + uy * end)],
                fill=fill,
                width=width,
            )
            cursor += on + off


def marker(draw: ImageDraw.ImageDraw, x: float, y: float, shape: str, color: str, r=7):
    x, y = int(x), int(y)
    if shape == "circle":
        draw.ellipse((x-r, y-r, x+r, y+r), fill=WHITE, outline=color, width=3)
    elif shape == "square":
        draw.rectangle((x-r, y-r, x+r, y+r), fill=WHITE, outline=color, width=3)
    elif shape == "diamond":
        draw.polygon([(x, y-r-1), (x+r+1, y), (x, y+r+1), (x-r-1, y)], fill=WHITE, outline=color)
        draw.line([(x, y-r-1), (x+r+1, y), (x, y+r+1), (x-r-1, y), (x, y-r-1)], fill=color, width=3)
    else:
        draw.polygon([(x, y-r-2), (x-r-1, y+r), (x+r+1, y+r)], fill=WHITE, outline=color)
        draw.line([(x, y-r-2), (x-r-1, y+r), (x+r+1, y+r), (x, y-r-2)], fill=color, width=3)


def centered(draw, xy, text, fnt, fill=INK):
    box = draw.textbbox((0, 0), text, font=fnt)
    w = box[2] - box[0]
    h = box[3] - box[1]
    draw.text((xy[0] - w/2, xy[1] - h/2), text, font=fnt, fill=fill)


def save_high_resolution(img: Image.Image, path: Path, scale: int = 2):
    enlarged = img.resize((img.width * scale, img.height * scale), Image.Resampling.LANCZOS)
    enlarged.save(path, dpi=(600, 600), optimize=True)


def figure1_temporal_shift():
    rows = read_csv("longitudinal.csv")
    img = Image.new("RGB", (2200, 980), WHITE)
    d = ImageDraw.Draw(img)
    metrics = [
        ("Mean task solve-rate change", "solve_rate_change", "solve_rate_change_q025", "solve_rate_change_q975", BLUE, "circle"),
        ("Mean task entropy change", "entropy_change", "entropy_change_q025", "entropy_change_q975", ORANGE, "square"),
    ]
    panels = ["open-submission", "standardized-bash"]
    panel_labels = {"open-submission": "Open-submission: 2024 to 2025",
                    "standardized-bash": "Standardized Bash-only: 2025 to 2026"}
    x_min, x_max = -0.40, 0.40
    left, right = 490, 2070

    def xp(v):
        return left + (float(v)-x_min)/(x_max-x_min)*(right-left)

    for i, panel in enumerate(panels):
        top = 100 + i * 330
        d.text((95, top-15), panel_labels[panel], font=F_PANEL, fill=INK)
        for tick in [-0.4, -0.2, 0.0, 0.2, 0.4]:
            x = xp(tick)
            d.line((x, top+25, x, top+210), fill=GRID if tick else MUTED, width=2 if tick else 3)
            centered(d, (x, top+240), f"{tick:+.1f}", F_AXIS, MUTED)
        row = next(r for r in rows if r["panel"] == panel)
        for j, (label, key, lo_key, hi_key, color, shape) in enumerate(metrics):
            y = top + 75 + j*90
            d.text((120, y-14), label, font=F_AXIS, fill=INK)
            val, lo, hi = map(float, (row[key], row[lo_key], row[hi_key]))
            d.line((xp(lo), y, xp(hi), y), fill=color, width=7)
            d.line((xp(lo), y-11, xp(lo), y+11), fill=color, width=3)
            d.line((xp(hi), y-11, xp(hi), y+11), fill=color, width=3)
            marker(d, xp(val), y, shape, color, 9)
            label_text = f"{val:+.3f}  [{lo:+.3f}, {hi:+.3f}]"
            tx = min(xp(hi)+18, 1750)
            d.text((tx, y-16), label_text, font=F_LABEL, fill=INK)

    path = OUTPUT / "figure1_temporal_shift.png"
    save_high_resolution(img.crop((60, 50, 2150, 780)), path)
    return path


def figure2_ranking_fidelity():
    all_rows = read_csv("formal_metrics.csv")
    rows = all_rows
    budgets = sorted({int(r["budget"]) for r in rows})
    panels = ["open-submission", "standardized-bash"]
    scopes = ["all_systems", "cluster_latest"]
    panel_labels = {"open-submission": "Open-submission", "standardized-bash": "Standardized Bash-only"}
    scope_labels = {"all_systems": "All systems", "cluster_latest": "Latest system per related cluster"}
    styles = {
        "random": ("Uniform random", GRAY, GRID, "diamond", (3, 7)),
        "repo_stratified_random": ("Repository-stratified random", BLUE, BLUE_LIGHT, "circle", None),
        "entropy": ("Training-period entropy", ORANGE, ORANGE_LIGHT, "square", (16, 9)),
        "temporal_coreset": ("Temporal core set", OLIVE, OLIVE_LIGHT, "triangle", (5, 7)),
    }
    img = Image.new("RGB", (2700, 1850), WHITE)
    d = ImageDraw.Draw(img)
    legend_y = 90
    lx = 120
    for method in styles:
        name, color, _, shape, dash = styles[method]
        line(d, [(lx, legend_y), (lx+105, legend_y)], color, 5, dash)
        marker(d, lx+52, legend_y, shape, color, 8)
        d.text((lx+122, legend_y-15), name, font=F_AXIS, fill=INK)
        lx += 625

    plot_w, plot_h = 1130, 560
    lefts = [145, 1450]
    tops = [220, 950]
    y_min, y_max = -0.2, 1.0

    for pi, panel in enumerate(panels):
        for si, scope in enumerate(scopes):
            left, top = lefts[si], tops[pi]
            right, bottom = left+plot_w, top+plot_h
            d.text((left, top-58), f"{panel_labels[panel]} - {scope_labels[scope]}", font=F_PANEL, fill=INK)
            for tick in [-0.2, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
                y = bottom - (tick-y_min)/(y_max-y_min)*plot_h
                d.line((left, y, right, y), fill=GRID if tick in (0.0, 1.0) else LIGHT_GRID, width=2)
                d.text((left-70, y-11), f"{tick:.1f}", font=F_SMALL, fill=MUTED)
            y_thr = bottom - (0.9-y_min)/(y_max-y_min)*plot_h
            line(d, [(left, y_thr), (right, y_thr)], MUTED, 3, (11, 8))
            d.line((left, top, left, bottom), fill=INK, width=2)
            d.line((left, bottom, right, bottom), fill=INK, width=2)

            def xp(budget):
                return left + budgets.index(int(budget))/(len(budgets)-1)*plot_w

            def yp(value):
                value = max(y_min, min(y_max, float(value)))
                return bottom - (value-y_min)/(y_max-y_min)*plot_h

            for idx, budget in enumerate(budgets):
                x = xp(budget)
                d.line((x, bottom, x, bottom+8), fill=INK, width=2)
                centered(d, (x, bottom+35), str(budget), F_SMALL, MUTED)

            for method in styles:
                name, color, light, shape, dash = styles[method]
                series = sorted(
                    [r for r in rows if r["panel"] == panel and r["scope"] == scope and r["method"] == method],
                    key=lambda r: int(r["budget"]),
                )
                pts = []
                for r in series:
                    x = xp(r["budget"])
                    y = yp(r["tau_b"])
                    y_lo, y_hi = yp(r["tau_b_q025"]), yp(r["tau_b_q975"])
                    d.line((x, y_hi, x, y_lo), fill=light, width=4)
                    d.line((x-5, y_hi, x+5, y_hi), fill=light, width=2)
                    d.line((x-5, y_lo, x+5, y_lo), fill=light, width=2)
                    pts.append((x, y))
                line(d, pts, color, 5, dash)
                for x, y in pts:
                    marker(d, x, y, shape, color, 6)

            centered(d, (left+plot_w/2, bottom+78), "Task budget", F_AXIS, INK)
            d.text((left-98, top-2), "τb", font=F_AXIS, fill=INK)

    def stacked_panel(filename: str, source_top: int):
        panel_img = Image.new("RGB", (1350, 1600), WHITE)
        panel_draw = ImageDraw.Draw(panel_img)
        legend_positions = [(25, 32), (690, 32), (25, 82), (690, 82)]
        for (method, (x, y)) in zip(styles, legend_positions):
            name, color, _, shape, dash = styles[method]
            line(panel_draw, [(x, y), (x + 85, y)], color, 4, dash)
            marker(panel_draw, x + 42, y, shape, color, 7)
            panel_draw.text((x + 102, y - 13), name, font=F_SMALL, fill=INK)
        first = img.crop((0, source_top, 1350, source_top + 740))
        second = img.crop((1325, source_top, 2675, source_top + 740))
        panel_img.paste(first, (0, 120))
        panel_img.paste(second, (0, 860))
        path = OUTPUT / filename
        save_high_resolution(panel_img, path, scale=3)
        return path

    return (
        stacked_panel("figure2a_open_ranking_fidelity.png", 150),
        stacked_panel("figure2b_standardized_ranking_fidelity.png", 880),
    )


def figure3_common_budget_matrix():
    rows = read_csv("formal_metrics.csv")
    methods = ["random", "repo_stratified_random", "entropy", "temporal_coreset"]
    method_labels = {
        "random": "Uniform random",
        "repo_stratified_random": "Repository-stratified random",
        "entropy": "Training-period entropy",
        "temporal_coreset": "Temporal core set",
    }
    budgets = sorted({int(r["budget"]) for r in rows})
    counts = {}
    first_all = {}
    for method in methods:
        for budget in budgets:
            cell_rows = [r for r in rows if r["method"] == method and int(r["budget"]) == budget]
            lower = 0.85 if method in {"random", "repo_stratified_random"} else 0.80
            count = sum(float(r["tau_b"]) >= 0.90 and float(r["tau_b_q025"]) >= lower for r in cell_rows)
            counts[(method, budget)] = count
        first_all[method] = next(b for b in budgets if counts[(method, b)] == 4)

    fills = {0: "#F2F4F6", 1: "#DCE8F1", 2: "#C9DBE8", 3: "#B4D0E3", 4: "#9EC2DC"}
    img = Image.new("RGB", (2500, 760), WHITE)
    d = ImageDraw.Draw(img)
    left, top = 500, 75
    cw, ch = 142, 145
    for j, budget in enumerate(budgets):
        centered(d, (left+j*cw+cw/2, top-42), str(budget), F_AXIS, INK)
    for i, method in enumerate(methods):
        y = top+i*ch
        d.text((95, y+52), method_labels[method], font=F_PANEL, fill=INK)
        for j, budget in enumerate(budgets):
            x = left+j*cw
            count = counts[(method, budget)]
            d.rectangle((x, y, x+cw-5, y+ch-8), fill=fills[count], outline=WHITE, width=3)
            centered(d, (x+(cw-5)/2, y+(ch-8)/2-8), f"{count}/4", F_PANEL, INK)
            if budget == first_all[method]:
                d.rectangle((x+4, y+4, x+cw-9, y+ch-12), outline=GOLD, width=7)
    path = OUTPUT / "figure3_common_budget_matrix.png"
    save_high_resolution(img.crop((60, 25, 2420, 700)), path)
    return path


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    figure2_paths = figure2_ranking_fidelity()
    for path in (figure1_temporal_shift(), *figure2_paths, figure3_common_budget_matrix()):
        print(path)


if __name__ == "__main__":
    main()
