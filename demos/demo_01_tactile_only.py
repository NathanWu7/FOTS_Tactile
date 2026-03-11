"""
Demo 01：仅触觉仿真（傻瓜式）
用程序生成的简单高度图（圆形凸起）调用 FOTS，得到触觉图并保存，不依赖 STL。
在项目根目录运行: python demos/demo_01_tactile_only.py
"""
import sys
import os
import numpy as np
import cv2

# 确保在项目根目录运行
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import params as pr


def make_bump_height_map(h, w, center_xy=None, radius_pix=40, bump_height_pix=15):
    """生成一个圆形凸起的高度图（像素单位），用于合成接触。"""
    if center_xy is None:
        center_xy = (w // 2, h // 2)
    yy, xx = np.ogrid[:h, :w]
    dist = np.sqrt((xx - center_xy[0]) ** 2 + (yy - center_xy[1]) ** 2)
    height = np.zeros((h, w), dtype=np.float64)
    mask_bump = dist < radius_pix
    height[mask_bump] = bump_height_pix * np.sqrt(np.maximum(1 - (dist[mask_bump] / radius_pix) ** 2, 0))
    return height, mask_bump


def main():
    print("Demo 01: 合成高度图 -> 触觉图像")
    psp_h, psp_w = pr.sensor_h, pr.sensor_w

    # 1. 合成高度图与接触 mask
    height_bump, contact_mask = make_bump_height_map(psp_h, psp_w, radius_pix=50, bump_height_pix=20)
    gel_pad = np.load(f"utils/utils_data/{pr.sensor_type}_pad.npy")
    height_map = height_bump + gel_pad * pr.mm_to_pixel
    gel_plane = np.ones((psp_h, psp_w)) * np.max(height_map) - 15.0
    zq = np.where(contact_mask, height_map, gel_plane) - gel_plane

    # 2. FOTS 生成触觉图
    from tactile_render import get_simapproach
    simulation = get_simapproach()
    tact_img = simulation.generate(zq, contact_mask, shadow=False)
    print("  触觉图像已生成:", tact_img.shape)

    # 3. 保存到 demos/out/
    out_dir = os.path.join(ROOT, "demos", "out")
    os.makedirs(out_dir, exist_ok=True)
    cv2.imwrite(os.path.join(out_dir, "demo01_tactile.png"), tact_img)
    cv2.imwrite(os.path.join(out_dir, "demo01_mask.png"), (contact_mask.astype(np.uint8) * 255))
    print("  已保存: demos/out/demo01_tactile.png, demo01_mask.png")

    # 4. 弹窗显示
    cv2.imshow("demo01_tactile", tact_img)
    cv2.imshow("demo01_mask", contact_mask.astype(np.uint8) * 255)
    print("  按任意键关闭窗口...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
