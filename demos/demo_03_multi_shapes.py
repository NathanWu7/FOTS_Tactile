"""
Demo 03：多形状批量测试（傻瓜式）
对 assets/daniel/ 下多个 STL 各跑一遍完整流程，保存触觉图与 marker 图到 demos/out/multi_shapes/。
在项目根目录运行: python demos/demo_03_multi_shapes.py
"""
import sys
import os
import numpy as np
import cv2
import open3d as o3d

# 确保在项目根目录运行
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import params as pr
from tactile_render import get_simapproach
from utils.marker_motion import MarkerMotion


def mesh_to_heightmap_and_contact(stl_path, trans=(0, 0, 0.1), rot=(0, 0, 0), num_points=500000):
    mm_to_pixel = pr.mm_to_pixel
    psp_w, psp_h = pr.sensor_w, pr.sensor_h
    s_type = pr.sensor_type
    mesh = o3d.io.read_triangle_mesh(stl_path)
    mesh.compute_vertex_normals()
    R = mesh.get_rotation_matrix_from_xyz(rot)
    mesh.rotate(R, center=[0, 0, 0])
    pcd = mesh.sample_points_uniformly(number_of_points=num_points)
    vertices = np.asarray(pcd.points)
    gel_pad = np.load(f"utils/utils_data/{s_type}_pad.npy")
    heightMap = np.zeros((psp_h, psp_w))
    cx, cy = 0.0, 0.0
    uu = ((vertices[:, 0] - cx + trans[0]) * mm_to_pixel + psp_w // 2).astype(int)
    vv = ((vertices[:, 1] - cy + trans[1]) * mm_to_pixel + psp_h // 2).astype(int)
    mask_u = np.logical_and(uu > 0, uu < psp_w)
    mask_v = np.logical_and(vv > 0, vv < psp_h)
    mask_z = vertices[:, 2] > 0.01
    mask_map = mask_u & mask_v & mask_z
    heightMap[vv[mask_map], uu[mask_map]] = vertices[mask_map][:, 2] * mm_to_pixel
    heightMap += gel_pad * mm_to_pixel
    max_o = np.max(heightMap)
    gel_map = np.ones((psp_h, psp_w)) * max_o
    pressing_height_pix = trans[2] * mm_to_pixel
    gel_map -= pressing_height_pix
    contact_mask = heightMap > gel_map
    zq = np.zeros((psp_h, psp_w))
    zq[contact_mask] = heightMap[contact_mask]
    zq[~contact_mask] = gel_map[~contact_mask]
    zq -= gel_map
    return zq, contact_mask


def main():
    assets_daniel = os.path.join(ROOT, "assets", "daniel")
    if not os.path.isdir(assets_daniel):
        print("错误: 找不到 assets/daniel/")
        return 1

    stl_files = [f for f in os.listdir(assets_daniel) if f.endswith(".stl")]
    if not stl_files:
        print("错误: assets/daniel/ 下没有 .stl 文件")
        return 1

    # 可选：只跑少量示例，避免太慢
    demo_list = ["cylinder.stl", "sphere.stl", "cone.stl", "flat_slab.stl", "hexagon.stl"]
    to_run = [f for f in demo_list if f in stl_files]
    if not to_run:
        to_run = stl_files[:5]
    to_run = [os.path.join(assets_daniel, f) for f in to_run]

    out_dir = os.path.join(ROOT, "demos", "out", "multi_shapes")
    os.makedirs(out_dir, exist_ok=True)
    print("Demo 03: 多形状批量测试")
    print("  输出目录:", out_dir)
    print("  共 %d 个 STL" % len(to_run))

    simulation = get_simapproach()
    trans = [0, 0, 0.1]
    rot = [0, 0, 0]
    relative_pos = [[0, 0, 0], [trans[0], trans[1], rot[2]]]
    mm_to_pixel = pr.mm_to_pixel

    for i, stl_path in enumerate(to_run):
        name = os.path.splitext(os.path.basename(stl_path))[0]
        print("  [%d/%d] %s" % (i + 1, len(to_run), name))
        try:
            zq, contact_mask = mesh_to_heightmap_and_contact(stl_path, trans=trans, rot=rot)
            tact_img = simulation.generate(zq, contact_mask, shadow=False)
            marker = MarkerMotion(
                frame0_blur=tact_img,
                depth=zq / mm_to_pixel,
                mask=contact_mask,
                traj=relative_pos,
                lamb=[0.00125, 0.00021, 0.00038],
            )
            marker_img = marker._marker_motion()
            cv2.imwrite(os.path.join(out_dir, f"{name}_tactile.png"), tact_img)
            cv2.imwrite(os.path.join(out_dir, f"{name}_marker.png"), marker_img)
        except Exception as e:
            print("    失败:", e)

    print("  完成。结果在 demos/out/multi_shapes/")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
