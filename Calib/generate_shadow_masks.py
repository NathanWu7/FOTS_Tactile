"""
从 dataPack.npz 生成 shadowTable.npz（仿真用）。
"""
import os
import sys
import argparse
import numpy as np
from scipy.ndimage import gaussian_filter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(__file__))
import calib_params as rcp

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

def extract_patch(imgs, bg_proc, touch_center, touch_radius, i, c, max_rad):
    frame = imgs[i]
    cx, cy = int(touch_center[i, 0]), int(touch_center[i, 1])
    radius = int(touch_radius[i])
    dI_c = (frame.astype("float") - bg_proc)[:, :, c]
    h, w = dI_c.shape
    if cy - max_rad < 0 or cy + max_rad > h or cx - max_rad < 0 or cx + max_rad > w:
        return None
    xcoord, ycoord = np.meshgrid(np.arange(w), np.arange(h))
    xcoord, ycoord = xcoord - cx, ycoord - cy
    contact_mask = (xcoord * xcoord + ycoord * ycoord) < (radius * radius)
    patch = dI_c[cy - max_rad : cy + max_rad, cx - max_rad : cx + max_rad].copy()
    p_mask = contact_mask[cy - max_rad : cy + max_rad, cx - max_rad : cx + max_rad]
    patch = gaussian_filter(patch, sigma=3, order=0)
    patch[p_mask] = 0
    return patch

def extract_shadow_list(imgs, bg_proc, touch_center, touch_radius, max_rad):
    shadow_list = []
    for i in range(len(imgs)):
        shadow_mask = np.zeros((max_rad * 2, max_rad * 2, 3))
        valid = True
        for c in range(3):
            patch = extract_patch(imgs, bg_proc, touch_center, touch_radius, i, c, max_rad)
            if patch is None:
                valid = False
                break
            shadow_mask[:, :, c] = patch
        if valid:
            shadow_list.append(shadow_mask)
    return shadow_list

def generate_shadow_table(shadow_list, shadow_step, shadow_threshold, num_step, discritize_precision):
    if len(shadow_list) == 0:
        raise ValueError("shadow_list is empty")
    sh, sw = shadow_list[0].shape[0], shadow_list[0].shape[1]
    scx, scy = sw // 2, sh // 2
    thetas = np.arange(0, 2 * np.pi, discritize_precision)
    st, ct = np.sin(thetas), np.cos(thetas)
    direction = np.stack((ct, st))
    c_values = []
    for c in range(3):
        d_values = []
        for dd in range(direction.shape[1]):
            direct = direction[:, dd]
            s_values = []
            for shadow_mask in shadow_list:
                shadow_sample = shadow_mask[:, :, c]
                values = []
                for i in range(1, num_step):
                    cur_x = int(scx + shadow_step * i * direct[0])
                    cur_y = int(scy + shadow_step * i * direct[1])
                    if cur_x < 0 or cur_x >= sw or cur_y < 0 or cur_y >= sh:
                        break
                    val = shadow_sample[cur_y, cur_x]
                    if val != 0.0 and val > shadow_threshold:
                        break
                    if val != 0.0:
                        values.append(float(val))
                s_values.append(values)
            d_values.append(s_values)
        c_values.append(d_values)
    return thetas, np.array(c_values, dtype=object)

def main():
    ap = argparse.ArgumentParser(description="Generate shadowTable.npz from dataPack.npz.")
    ap.add_argument("--data_path", type=str, default=".", help="Folder containing dataPack.npz.")
    args = ap.parse_args()
    data_path = os.path.abspath(args.data_path)
    pack_path = os.path.join(data_path, "dataPack.npz")
    if not os.path.isfile(pack_path):
        raise SystemExit(f"Not found: {pack_path}")
    data = np.load(pack_path, allow_pickle=True)
    f0, imgs = data["f0"], data["imgs"]
    touch_center, touch_radius = data["touch_center"], data["touch_radius"]
    bg_proc = process_initial_frame(f0, rcp.kscale, rcp.diff_threshold, rcp.frame_mixing_percentage)
    shadow_list = extract_shadow_list(imgs, bg_proc, touch_center, touch_radius, rcp.max_rad)
    print(f"Extracted {len(shadow_list)} shadow masks.")
    thetas, shadow_table = generate_shadow_table(shadow_list, rcp.shadow_step, rcp.shadow_threshold, rcp.num_step, rcp.discritize_precision)
    out_path = os.path.join(data_path, "shadowTable.npz")
    np.savez(out_path, shadowDirections=thetas, shadowTable=shadow_table)
    print(f"Saved {out_path} (directions={len(thetas)}).")

if __name__ == "__main__":
    main()
