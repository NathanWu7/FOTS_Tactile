"""
生成合成标定测试数据：仿触觉图 + CSV + bg.npy，输出到 Calib/data/test_data 与 Calib/data/csv。
"""
import os
import sys
import argparse
import csv

import numpy as np
import cv2

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
import params as pr

CALIB_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(CALIB_DIR, "data")

def make_background(h, w, rng=None):
    rng = rng or np.random.default_rng()
    base = np.array([120, 100, 90], dtype=np.float32)
    noise = rng.uniform(-15, 15, (h, w, 3)).astype(np.float32)
    return np.clip(base + noise, 0, 255).astype(np.uint8)

def draw_sphere_imprint(img, cx, cy, radius, intensity_drop=0.6, blur_sigma=2):
    h, w = img.shape[:2]
    overlay = img.astype(np.float32)
    y, x = np.ogrid[:h, :w]
    dist_sq = (x - cx) ** 2 + (y - cy) ** 2
    alpha = np.exp(-dist_sq / (2 * (radius * 0.6) ** 2))
    for ch in range(3):
        overlay[:, :, ch] *= (1 - alpha * intensity_drop)
    out = np.clip(overlay, 0, 255).astype(np.uint8)
    if blur_sigma > 0:
        out = cv2.GaussianBlur(out, (0, 0), blur_sigma)
    return out

def main():
    ap = argparse.ArgumentParser(description="Generate synthetic calib test data.")
    ap.add_argument("--out_dir", type=str, default=None, help="Output dir (default: Calib/data/test_data)")
    ap.add_argument("--num_imgs", type=int, default=24)
    ap.add_argument("--radius_min", type=int, default=25)
    ap.add_argument("--radius_max", type=int, default=45)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--save_bg", action="store_true", default=True)
    args = ap.parse_args()

    out_dir = args.out_dir or os.path.join(DATA_DIR, "test_data")
    img_dir = os.path.join(out_dir, "imgs")
    os.makedirs(img_dir, exist_ok=True)
    csv_dir = os.path.join(DATA_DIR, "csv")
    os.makedirs(csv_dir, exist_ok=True)

    h, w = pr.sensor_h, pr.sensor_w
    rng = np.random.default_rng(args.seed)
    bg = make_background(h, w, rng)
    if args.save_bg:
        np.save(os.path.join(out_dir, "bg.npy"), bg)
        print(f"Saved background: {out_dir}/bg.npy")

    margin = max(args.radius_max + 5, 40)
    csv_rows = [["img_names", "center_x", "center_y", "radius"]]
    for i in range(args.num_imgs):
        cx = rng.integers(margin, w - margin)
        cy = rng.integers(margin, h - margin)
        radius = int(rng.integers(args.radius_min, args.radius_max + 1))
        img = draw_sphere_imprint(bg.copy(), cx, cy, radius)
        fname = f"{i:04d}.png"
        cv2.imwrite(os.path.join(img_dir, fname), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        csv_rows.append([fname, cx, cy, radius])

    csv_path = os.path.join(csv_dir, "annotate_test.csv")
    with open(csv_path, "w", newline="") as f:
        csv.writer(f).writerows(csv_rows)
    print(f"Saved {args.num_imgs} images to {img_dir}")
    print(f"Saved CSV: {csv_path}")
    print("Next: python Calib/build_data_pack.py --image_dir {} --annot_csv {} --f0_path {} --out_dir <calib_dir>".format(
        img_dir, csv_path, os.path.join(out_dir, "bg.npy") if args.save_bg else "<f0_path>"))

if __name__ == "__main__":
    main()
