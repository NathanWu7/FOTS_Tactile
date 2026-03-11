"""
Demo 02：完整流程（傻瓜式）
从单个 STL 完成：读 mesh -> 高度图 -> 触觉图 -> 标记运动图，可选保存/显示。
在项目根目录运行:
  python demos/demo_02_full_pipeline.py
  python demos/demo_02_full_pipeline.py --stl assets/daniel/sphere.stl --no-show
"""
import sys
import os
import argparse
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
    """
    从 STL 生成 heightMap（含 gel_pad）、contact_mask、zq（相对高度）。
    trans: (tx, ty, tz) mm；rot: (rx, ry, rz) rad。
    """
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
    return zq, contact_mask, heightMap


def main():
    parser = argparse.ArgumentParser(description="Demo 02: STL -> 触觉图 + 标记图")
    parser.add_argument("--stl", default="assets/daniel/cylinder.stl", help="STL 模型路径")
    parser.add_argument("--out-dir", default=None, help="保存目录，默认 demos/out")
    parser.add_argument("--no-show", action="store_true", help="不弹窗显示，仅保存")
    parser.add_argument("--trans", type=float, nargs=3, default=[0, 0, 0.1], help="平移 tx ty tz (mm)")
    args = parser.parse_args()

    if not os.path.isfile(args.stl):
        print("错误: STL 不存在:", args.stl)
        return 1

    print("Demo 02: 完整流程 (STL -> 触觉图 + 标记图)")
    print("  STL:", args.stl)

    trans = args.trans
    rot = [0, 0, 0]
    zq, contact_mask, _ = mesh_to_heightmap_and_contact(args.stl, trans=trans, rot=rot)
    mm_to_pixel = pr.mm_to_pixel

    simulation = get_simapproach()
    tact_img = simulation.generate(zq, contact_mask, shadow=False)
    relative_pos = []
    if np.max(trans[2]) > 0.0:
        relative_pos.append([0, 0, 0])
        relative_pos.append([trans[0], trans[1], rot[2]])
    marker = MarkerMotion(
        frame0_blur=tact_img,
        depth=zq / mm_to_pixel,
        mask=contact_mask,
        traj=relative_pos,
        lamb=[0.00125, 0.00021, 0.00038],
    )
    marker_img = marker._marker_motion()

    out_dir = args.out_dir or os.path.join(ROOT, "demos", "out")
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(args.stl))[0]
    cv2.imwrite(os.path.join(out_dir, f"demo02_{base}_tactile.png"), tact_img)
    cv2.imwrite(os.path.join(out_dir, f"demo02_{base}_mask.png"), (contact_mask.astype(np.uint8) * 255))
    cv2.imwrite(os.path.join(out_dir, f"demo02_{base}_marker.png"), marker_img)
    print("  已保存: demos/out/demo02_%s_*.png" % base)

    if not args.no_show:
        cv2.imshow("tactile", tact_img)
        cv2.imshow("mask", contact_mask.astype(np.uint8) * 255)
        cv2.imshow("marker", marker_img)
        print("  按任意键关闭窗口...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
