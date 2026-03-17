"""
向仿真 calib 目录写入 gelmap.npy 与 params.json（仿真文件格式、文件名一致）。
params.json 包含 sensor 与 simulator 段；simulator 根据 calib_params 生成
（触觉仿真器用的背景模糊、阴影步长、变形金字塔等，均为相对分辨率 _rel，与 GelSight_Mini 格式一致）。
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

def build_simulator_params(w, h):
    """根据 calib_params 生成 simulator 段（与 GelSight_Mini/params.json 结构一致）。"""
    sys.path.insert(0, os.path.dirname(__file__))
    import calib_params as rcp
    # 相对分辨率的 sigma/步长：像素值 / (w 或 h)
    kscale = getattr(rcp, "kscale", 50)
    shadow_step = getattr(rcp, "shadow_step", 1.25)
    pyramid = getattr(pr, "pyramid_kernel_size", [51, 21, 11, 5])
    if len(pyramid) < 6:
        pyramid = (pyramid + [5, 3, 2])[:6]
    kernel_size = getattr(pr, "kernel_size", 5)
    return {
        "simulator": {
            "initial_frame_sigma_rel": [kscale / w, kscale / h],
            "diff_threshold": rcp.diff_threshold,
            "frame_mixing_percentage": rcp.frame_mixing_percentage,
            "shadow_step_rel": [shadow_step / w, shadow_step / h],
            "discretize_precision": getattr(rcp, "discritize_precision", 0.1),
            "height_precision": 0.1,
            "fan_angle": 0.1,
            "fan_precision": 0.05,
            "contact_scale": 0.4,
            "deform_pyramid_sigma_rel": [
                [s / w for s in pyramid],
                [s / h for s in pyramid],
            ],
            "deform_final_sigma_rel": [kernel_size / w, kernel_size / h],
            "shadow_blur_sigma_rel": [kernel_size / w * 0.35, kernel_size / h * 0.35],
            "shadow_attachment_kernel_size_rel": [kernel_size / w, kernel_size / h],
        }
    }


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
    params.update(build_simulator_params(w, h))
    with open(os.path.join(calib_dir, "params.json"), "w", encoding="utf-8") as f:
        json.dump(params, f, indent=2)
    print(f"Wrote {calib_dir}/gelmap.npy ({h}x{w}), params.json (sensor + simulator).")

if __name__ == "__main__":
    main()
