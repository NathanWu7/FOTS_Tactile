"""
向仿真 calib 目录写入 gelmap.npy 与 params.json（仿真文件格式、文件名一致）。
"""
import os
import sys
import argparse
import json
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
import params as pr

def main():
    ap = argparse.ArgumentParser(description="Write gelmap.npy and params.json to sim calib dir.")
    ap.add_argument("--calib_dir", type=str, required=True, help="Calib directory.")
    ap.add_argument("--resolution", type=str, default=None, help="e.g. 320x240 or 640x480; default from params.")
    args = ap.parse_args()
    calib_dir = os.path.abspath(args.calib_dir)
    os.makedirs(calib_dir, exist_ok=True)
    if args.resolution:
        w, h = [int(x) for x in args.resolution.lower().split("x")]
    else:
        h, w = pr.sensor_h, pr.sensor_w
    gelmap = np.zeros((h, w), dtype=np.float64)
    np.save(os.path.join(calib_dir, "gelmap.npy"), gelmap)
    pixmm = 1.0 / pr.mm_to_pixel
    num_bins = getattr(pr, "num_bins", 125)
    params = {"sensor": {"pixmm": pixmm, "num_bins": num_bins, "w": w, "h": h}}
    with open(os.path.join(calib_dir, "params.json"), "w", encoding="utf-8") as f:
        json.dump(params, f, indent=2)
    print(f"Wrote {calib_dir}/gelmap.npy ({h}x{w}), params.json.")

if __name__ == "__main__":
    main()
