"""
生成 FOTS 渲染用背景 ini_bg_fots_<sensor>.npy。
在无接触（平面法线）时，用已训练好的 MLP 前向得到输出，保存供 simulation.generate() 中减去使用。
在项目根目录运行: python scripts/generate_ini_bg_fots.py [--sensor xense]
"""
import sys
import os
import argparse
import numpy as np
import torch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import params as pr
from utils.prepost_mlp import preproc_mlp
from mlp_calib.src.train.mlp_model import MLP


def main():
    parser = argparse.ArgumentParser(description="Generate ini_bg_fots_<sensor>.npy")
    parser.add_argument("--sensor", type=str, default=None, help="传感器名，默认使用 params.sensor_type")
    args = parser.parse_args()
    stype = args.sensor or pr.sensor_type
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    h, w = pr.sensor_h, pr.sensor_w

    # 平面法线 (0,0,1) -> 在 generate_normals 后的取值范围里为 (0.5, 0.5, 1.0)
    normal_flat = np.ones((h, w, 3), dtype=np.float64) * np.array([0.5, 0.5, 1.0])
    img_n = preproc_mlp(normal_flat)
    model = MLP().to(device)
    pth_path = f"./mlp_calib/models/mlp_n2c_{stype}.pth"
    if not os.path.isfile(pth_path):
        print("错误: 未找到", pth_path)
        return 1
    model.load_state_dict(torch.load(pth_path, map_location=device))
    model.eval()
    with torch.no_grad():
        sim_img_r = model(img_n).cpu().numpy()
    ini_bg = sim_img_r.reshape(h, w, 3)
    out_path = f"utils/utils_data/ini_bg_fots_{stype}.npy"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    np.save(out_path, ini_bg)
    print("已保存:", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
