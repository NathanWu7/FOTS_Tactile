"""
从图像目录 + 标注 CSV 生成 Taxim 格式的 dataPack.npz（仿真用）。
"""
import os
import argparse
import numpy as np
import pandas as pd
import cv2

def load_image(path):
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(path)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

def main():
    ap = argparse.ArgumentParser(description="Build dataPack.npz from images + CSV.")
    ap.add_argument("--image_dir", type=str, required=True, help="Directory containing tactile images.")
    ap.add_argument("--annot_csv", type=str, required=True, help="CSV: img_names, center_x, center_y, radius.")
    ap.add_argument("--f0_path", type=str, required=True, help="Background image (no contact), .npy or image.")
    ap.add_argument("--out_dir", type=str, default=None, help="Output directory (default: image_dir).")
    args = ap.parse_args()

    out_dir = args.out_dir or args.image_dir
    os.makedirs(out_dir, exist_ok=True)

    if args.f0_path.lower().endswith(".npy"):
        f0 = np.load(args.f0_path)
        if f0.dtype in (np.float32, np.float64):
            f0 = (f0 * 255).astype(np.uint8) if f0.max() <= 1.0 else f0.astype(np.uint8)
    else:
        f0 = load_image(args.f0_path)

    df = pd.read_csv(args.annot_csv)
    for c in ["img_names", "center_x", "center_y", "radius"]:
        if c not in df.columns:
            raise SystemExit(f"CSV must have column: {c}")

    imgs, touch_center, touch_radius, names = [], [], [], []
    for _, row in df.iterrows():
        name = row["img_names"]
        if isinstance(name, str) and not name.strip():
            continue
        name_str = str(name).strip()
        path = os.path.join(args.image_dir, name_str)
        if not os.path.isfile(path):
            path = os.path.join(args.image_dir, os.path.basename(name_str))
        if not os.path.isfile(path):
            print(f"Skip (not found): {path}")
            continue
        img = load_image(path)
        if img.shape[:2] != f0.shape[:2]:
            img = cv2.resize(img, (f0.shape[1], f0.shape[0]))
        imgs.append(img)
        touch_center.append([int(round(float(row["center_x"]))), int(round(float(row["center_y"])))])
        touch_radius.append(int(round(float(row["radius"]))))
        names.append(os.path.basename(path))

    if len(imgs) == 0:
        raise SystemExit("No valid images found.")

    out_path = os.path.join(out_dir, "dataPack.npz")
    np.savez(out_path, f0=f0, imgs=np.array(imgs), touch_center=np.array(touch_center, dtype=np.float64),
             touch_radius=np.array(touch_radius, dtype=np.float64), names=np.array(names, dtype=object),
             img_size=np.array(f0.shape))
    print(f"Saved {out_path} with f0 shape {f0.shape}, {len(imgs)} images.")

if __name__ == "__main__":
    main()
