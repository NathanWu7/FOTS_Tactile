"""
从 dataPack.npz 生成 polycalib.npz（仿真用）。
"""
import os
import sys
import argparse
import numpy as np
from scipy.ndimage import gaussian_filter
from scipy import interpolate
from scipy.linalg import lstsq

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(__file__))
import calib_params as rcp

def circle_center(cx, cy, r):
    return [cx, cy]

def process_initial_frame(f0, kscale, diff_threshold, frame_mixing_percentage):
    img_d = f0.astype("float")
    f0_out = f0.copy()
    for ch in range(img_d.shape[2]):
        f0_out[:, :, ch] = gaussian_filter(img_d[:, :, ch], kscale)
    dI = np.mean(f0_out - img_d, axis=2)
    idx = np.nonzero(dI < diff_threshold)
    for ch in range(f0_out.shape[2]):
        f0_out[:, :, ch][idx] = frame_mixing_percentage * f0_out[:, :, ch][idx] + (1 - frame_mixing_percentage) * img_d[:, :, ch][idx]
    return f0_out

def interpolate_holes(img):
    x, y = np.arange(img.shape[1]), np.arange(img.shape[0])
    array = np.ma.masked_where(img == 0, img)
    xx, yy = np.meshgrid(x, y)
    x1, y1, newarr = xx[~array.mask], yy[~array.mask], img[~array.mask]
    if newarr.size == 0:
        return img
    return interpolate.griddata((x1, y1), newarr.ravel(), (xx, yy), method="nearest", fill_value=0)

def main():
    ap = argparse.ArgumentParser(description="Generate polycalib.npz from dataPack.npz.")
    ap.add_argument("--data_path", type=str, default=".", help="Folder containing dataPack.npz.")
    ap.add_argument(
        "--ball_radius_mm",
        type=float,
        default=None,
        help="Override sphere radius in mm for calibration (default from calib_params).",
    )
    ap.add_argument(
        "--mm_to_pixel",
        type=float,
        default=None,
        help="Override mm_to_pixel for calibration (default from params via calib_params).",
    )
    args = ap.parse_args()
    data_path = os.path.abspath(args.data_path)
    pack_path = os.path.join(data_path, "dataPack.npz")
    if not os.path.isfile(pack_path):
        raise SystemExit(f"Not found: {pack_path}")
    data = np.load(pack_path, allow_pickle=True)
    f0, imgs = data["f0"], data["imgs"]
    touch_center, touch_radius = data["touch_center"], data["touch_radius"]
    ball_radius_mm = args.ball_radius_mm if args.ball_radius_mm is not None else rcp.ball_radius_mm
    pixmm = (1.0 / args.mm_to_pixel) if args.mm_to_pixel is not None else rcp.pixmm
    ball_radius_pix = ball_radius_mm / pixmm
    if ball_radius_pix <= 1e-8:
        raise SystemExit("Invalid ball radius in pixels, please check --ball_radius_mm / --mm_to_pixel.")
    radius_max = float(np.max(touch_radius))
    if radius_max > ball_radius_pix * 1.05:
        print(
            "[WARN] touch_radius max=%.2f px is larger than ball_radius_pix=%.2f px. "
            "This can cause severe gradient clipping and unstable polycalib. "
            "Please check mm_to_pixel / ball_radius_mm (or pass --mm_to_pixel/--ball_radius_mm)."
            % (radius_max, ball_radius_pix)
        )
    num_bins = rcp.num_bins
    bg_proc = process_initial_frame(f0, rcp.kscale, rcp.diff_threshold, rcp.frame_mixing_percentage)

    sizey, sizex = f0.shape[:2]
    x_center = (sizex - 1) / 2.0
    y_center = (sizey - 1) / 2.0
    x_scale = max(x_center, 1.0)
    y_scale = max(y_center, 1.0)
    value_list, locx_list, locy_list = [], [], []
    for idx in range(len(imgs)):
        frame = imgs[idx]
        dI = frame.astype("float") - bg_proc
        cx, cy = int(touch_center[idx, 0]), int(touch_center[idx, 1])
        radius = int(touch_radius[idx])
        center = circle_center(cx, cy, radius)
        xqq, yqq = np.meshgrid(np.arange(sizex), np.arange(sizey))
        xq, yq = xqq - center[0], yqq - center[1]
        xqq_norm = (xqq - x_center) / x_scale
        yqq_norm = (yqq - y_center) / y_scale
        rsqcoord = xq * xq + yq * yq
        valid_rad = min(radius * radius, int(ball_radius_pix * ball_radius_pix))
        valid_mask = rsqcoord < valid_rad
        validId = np.nonzero(valid_mask)
        xvalid, yvalid = xq[validId], yq[validId]
        rvalid = np.sqrt(xvalid * xvalid + yvalid * yvalid)
        gradxseq = np.arcsin(np.clip(rvalid / ball_radius_pix, -1, 1))
        gradyseq = np.arctan2(-yvalid, -xvalid)
        binm = num_bins - 1
        idx_x = np.clip(np.floor(gradxseq / (0.5 * np.pi / binm)).astype("int"), 0, num_bins - 1)
        idx_y = np.clip(np.floor((gradyseq + np.pi) / (2 * np.pi / binm)).astype("int"), 0, num_bins - 1)
        value_map = np.zeros((num_bins, num_bins, 3))
        loc_x_map = np.zeros((num_bins, num_bins))
        loc_y_map = np.zeros((num_bins, num_bins))
        count_map = np.zeros((num_bins, num_bins))
        np.add.at(value_map[:, :, 0], (idx_x, idx_y), dI[:, :, 0][validId])
        np.add.at(value_map[:, :, 1], (idx_x, idx_y), dI[:, :, 1][validId])
        np.add.at(value_map[:, :, 2], (idx_x, idx_y), dI[:, :, 2][validId])
        np.add.at(loc_x_map, (idx_x, idx_y), xqq_norm[validId])
        np.add.at(loc_y_map, (idx_x, idx_y), yqq_norm[validId])
        np.add.at(count_map, (idx_x, idx_y), 1.0)
        nonzero_count = count_map > 0
        for i in range(3):
            value_map[:, :, i][nonzero_count] /= count_map[nonzero_count]
        loc_x_map[nonzero_count] /= count_map[nonzero_count]
        loc_y_map[nonzero_count] /= count_map[nonzero_count]
        for i in range(3):
            value_map[:, :, i] = interpolate_holes(value_map[:, :, i])
        loc_x_map = interpolate_holes(loc_x_map)
        loc_y_map = interpolate_holes(loc_y_map)
        value_list.append(value_map)
        locx_list.append(loc_x_map)
        locy_list.append(loc_y_map)

    table_v = np.array(value_list)
    table_x, table_y = np.array(locx_list), np.array(locy_list)
    grad_r = np.zeros((num_bins, num_bins, 6))
    grad_g = np.zeros((num_bins, num_bins, 6))
    grad_b = np.zeros((num_bins, num_bins, 6))
    for i in range(num_bins):
        for j in range(num_bins):
            xf, yf = table_x[:, i, j], table_y[:, i, j]
            A = np.stack([xf * xf, yf * yf, xf * yf, xf, yf, np.ones_like(xf)], axis=1)
            for params, vec in [(grad_r[i, j], table_v[:, i, j, 0]), (grad_g[i, j], table_v[:, i, j, 1]), (grad_b[i, j], table_v[:, i, j, 2])]:
                sol, *_ = lstsq(A, vec)
                params[:] = sol
    out_path = os.path.join(data_path, "polycalib.npz")
    np.savez(
        out_path,
        bins=num_bins,
        grad_r=grad_r,
        grad_g=grad_g,
        grad_b=grad_b,
        x_center=x_center,
        y_center=y_center,
        x_scale=x_scale,
        y_scale=y_scale,
    )
    print(
        "Saved %s (bins=%d, ball_radius_mm=%.4f, mm_to_pixel=%.4f, ball_radius_pix=%.2f)."
        % (out_path, num_bins, ball_radius_mm, 1.0 / pixmm, ball_radius_pix)
    )

if __name__ == "__main__":
    main()
