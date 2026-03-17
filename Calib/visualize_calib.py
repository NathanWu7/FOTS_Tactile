"""
标定结果可视化：用 dataPack + polycalib（+ 可选 shadowTable）从合成高度图模拟触觉图并显示/保存；
或仅可视化某一环节结果（与 --data_only 平行的 --poly_only / --shadow_only / --sim_calib_only）。
用法（项目根目录）：
  # 仅可视化 dataPack（f0 + imgs 及 touch_center/radius 圆）：
  python Calib/visualize_calib.py --calib_dir <目录> --data_only [--max_imgs 24] [--no_show]
  # 仅可视化 poly_table_calib 结果（polycalib.npz）：
  python Calib/visualize_calib.py --calib_dir <目录> --poly_only [--no_show]
  # 仅可视化 shadow 结果（shadowTable.npz）：
  python Calib/visualize_calib.py --calib_dir <目录> --shadow_only [--no_show]
  # 仅可视化 write_sim_calib 结果（gelmap.npy + params.json）：
  python Calib/visualize_calib.py --calib_dir <目录> --sim_calib_only [--no_show]
  # 模拟触觉图（需 dataPack + polycalib）：
  python Calib/visualize_calib.py --calib_dir <目录> [--out_dir .] [--no_show]
"""
import os
import sys
import argparse
import numpy as np
import cv2
from scipy.ndimage import gaussian_filter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(__file__))
import params as pr
import calib_params as rcp


def process_initial_frame(f0, kscale, diff_threshold, frame_mixing_percentage):
    img_d = f0.astype("float")
    f0_out = f0.copy()
    for ch in range(img_d.shape[2]):
        f0_out[:, :, ch] = gaussian_filter(img_d[:, :, ch], kscale)
    dI = np.mean(f0_out - img_d, axis=2)
    idx = np.nonzero(dI < diff_threshold)
    for ch in range(f0_out.shape[2]):
        f0_out[:, :, ch][idx] = (
            frame_mixing_percentage * f0_out[:, :, ch][idx]
            + (1 - frame_mixing_percentage) * img_d[:, :, ch][idx]
        )
    return f0_out


def generate_normals(height_map):
    """从高度图得到梯度幅角与方向（与 Taxim generate_normals 一致）。"""
    h, w = height_map.shape
    top = height_map[0 : h - 2, 1 : w - 1]
    bot = height_map[2:h, 1 : w - 1]
    left = height_map[1 : h - 1, 0 : w - 2]
    right = height_map[1 : h - 1, 2:w]
    dzdx = (bot - top) / 2.0
    dzdy = (right - left) / 2.0
    mag_tan = np.sqrt(dzdx ** 2 + dzdy ** 2)
    grad_mag = np.arctan(np.clip(mag_tan, 1e-8, None))
    valid = mag_tan > 1e-8
    grad_dir = np.zeros((h - 2, w - 2))
    grad_dir[valid] = np.arctan2(
        dzdx[valid] / mag_tan[valid], dzdy[valid] / mag_tan[valid]
    )
    grad_mag = np.pad(grad_mag, ((1, 1), (1, 1)), mode="edge")
    grad_dir = np.pad(grad_dir, ((1, 1), (1, 1)), mode="edge")
    return grad_mag, grad_dir


def make_sphere_height_map(h, w, cx=None, cy=None, radius_pix=40, depth_pix=15):
    """生成中心球体压痕的简单高度图（像素单位）。球冠高度与 depth 成正比。"""
    cx = cx or w // 2
    cy = cy or h // 2
    yy, xx = np.ogrid[:h, :w]
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    height = np.zeros((h, w), dtype=np.float64)
    mask = dist <= radius_pix
    r_sq = np.clip(radius_pix ** 2 - dist[mask] ** 2, 0, None)
    height[mask] = depth_pix * np.sqrt(r_sq) / radius_pix
    return height


def simulate_tactile(calib_dir, height_map, use_shadow=False):
    """
    用标定结果从高度图模拟触觉图。
    calib_dir: 含 dataPack.npz, polycalib.npz[, shadowTable.npz] 的目录
    返回 (sim_img_no_shadow, sim_img_with_shadow 或 None)，均为 (H,W,3) float，未裁剪到 0~255
    """
    data = np.load(os.path.join(calib_dir, "dataPack.npz"), allow_pickle=True)
    f0 = data["f0"]
    poly = np.load(os.path.join(calib_dir, "polycalib.npz"))
    grad_r = poly["grad_r"]
    grad_g = poly["grad_g"]
    grad_b = poly["grad_b"]
    bins = int(poly["bins"])

    bg_proc = process_initial_frame(
        f0, rcp.kscale, rcp.diff_threshold, rcp.frame_mixing_percentage
    )
    H, W = f0.shape[0], f0.shape[1]
    if height_map.shape[0] != H or height_map.shape[1] != W:
        height_map = cv2.resize(
            height_map.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR
        )

    grad_mag, grad_dir = generate_normals(height_map)
    binm = bins - 1
    x_binr = 0.5 * np.pi / binm
    y_binr = 2 * np.pi / binm
    idx_x = np.floor(grad_mag / x_binr).astype(np.int32)
    idx_y = np.floor((grad_dir + np.pi) / y_binr).astype(np.int32)
    idx_x = np.clip(idx_x, 0, bins - 1)
    idx_y = np.clip(idx_y, 0, bins - 1)

    xx, yy = np.meshgrid(np.arange(W), np.arange(H))
    xf = xx.flatten().astype(np.float64)
    yf = yy.flatten().astype(np.float64)
    # 兼容两种 polycalib：若有坐标归一化参数则使用，避免高分辨率下回归病态
    if all(k in poly.files for k in ("x_center", "y_center", "x_scale", "y_scale")):
        x_center = float(poly["x_center"])
        y_center = float(poly["y_center"])
        x_scale = max(float(poly["x_scale"]), 1e-8)
        y_scale = max(float(poly["y_scale"]), 1e-8)
        xf = (xf - x_center) / x_scale
        yf = (yf - y_center) / y_scale
    A = np.stack([xf * xf, yf * yf, xf * yf, xf, yf, np.ones(H * W)], axis=1)

    params_r = grad_r[idx_x, idx_y, :].reshape(H * W, 6)
    params_g = grad_g[idx_x, idx_y, :].reshape(H * W, 6)
    params_b = grad_b[idx_x, idx_y, :].reshape(H * W, 6)
    est_r = np.sum(A * params_r, axis=1)
    est_g = np.sum(A * params_g, axis=1)
    est_b = np.sum(A * params_b, axis=1)

    contact_mask = height_map > 1e-8
    sim_img_r = np.zeros((H, W, 3))
    sim_img_r[:, :, 0] = est_r.reshape(H, W) * contact_mask
    sim_img_r[:, :, 1] = est_g.reshape(H, W) * contact_mask
    sim_img_r[:, :, 2] = est_b.reshape(H, W) * contact_mask
    sim_img = sim_img_r + bg_proc.astype(np.float64)
    # 诊断：若大量像素会被 0/255 裁剪，提示用户检查标定参数（常见是 mm_to_pixel 或球半径不匹配）
    sat_ratio = []
    for c in range(3):
        ch = sim_img[:, :, c]
        sat_ratio.append(float((ch <= 0).mean() + (ch >= 255).mean()))
    if max(sat_ratio) > 0.30:
        print(
            "[WARN] Simulated image is heavily saturated before clipping (R/G/B sat ratios: %.3f/%.3f/%.3f). "
            "Likely unstable polycalib. Check touch_radius vs ball_radius_pix and mm_to_pixel/ball_radius settings."
            % (sat_ratio[0], sat_ratio[1], sat_ratio[2])
        )

    if not use_shadow:
        return sim_img, None

    shadow_path = os.path.join(calib_dir, "shadowTable.npz")
    if not os.path.isfile(shadow_path):
        return sim_img, None
    shadow_data = np.load(shadow_path, allow_pickle=True)
    direction = shadow_data["shadowDirections"]
    shadow_table = shadow_data["shadowTable"]
    # 简化阴影：仅做示意（完整阴影需复刻 Taxim 的 contact_boundary + 方向/高度索引）
    shadow_sim = sim_img.copy()
    return sim_img, shadow_sim


def visualize_datapack_only(calib_dir, out_dir, no_show, max_imgs=24):
    """只可视化 dataPack：f0 + 多张 imgs，每张图上画 touch_center/touch_radius 的圆。"""
    pack_path = os.path.join(calib_dir, "dataPack.npz")
    if not os.path.isfile(pack_path):
        raise SystemExit("Not found: %s" % pack_path)
    data = np.load(pack_path, allow_pickle=True)
    f0 = data["f0"]
    imgs = data["imgs"]
    touch_center = data["touch_center"]
    touch_radius = data["touch_radius"]
    n = min(imgs.shape[0], max_imgs)
    H, W = f0.shape[0], f0.shape[1]

    # 单张 f0 保存
    cv2.imwrite(
        os.path.join(out_dir, "visualize_datapack_f0.png"),
        cv2.cvtColor(f0, cv2.COLOR_RGB2BGR),
    )
    print("Saved: %s" % os.path.join(out_dir, "visualize_datapack_f0.png"))

    # 每张 img 画圆后拼成网格
    cols = min(6, n)
    rows = (n + cols - 1) // cols
    cell_h, cell_w = H, W
    grid = np.zeros((rows * cell_h, cols * cell_w, 3), dtype=np.uint8)
    grid[:] = 240  # 背景灰
    for i in range(n):
        r, c = i // cols, i % cols
        img = imgs[i].copy()
        cx = int(round(touch_center[i, 0]))
        cy = int(round(touch_center[i, 1]))
        rad = int(round(touch_radius[i]))
        cv2.circle(img, (cx, cy), rad, (0, 255, 0), 2)
        cv2.circle(img, (cx, cy), 3, (0, 0, 255), -1)
        grid[r * cell_h : (r + 1) * cell_h, c * cell_w : (c + 1) * cell_w] = img
    out_path = os.path.join(out_dir, "visualize_datapack_imgs.png")
    cv2.imwrite(out_path, cv2.cvtColor(grid, cv2.COLOR_RGB2BGR))
    print("Saved: %s (%d images with circles)" % (out_path, n))

    # f0 + 网格 拼一张
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(2, 1, figsize=(cols * 2, 4 + rows * 2))
        axes[0].imshow(f0)
        axes[0].set_title("f0 (background)")
        axes[0].axis("off")
        axes[1].imshow(grid)
        axes[1].set_title("imgs with touch_center/radius (%d frames)" % n)
        axes[1].axis("off")
        plt.tight_layout()
        all_path = os.path.join(out_dir, "visualize_datapack_all.png")
        plt.savefig(all_path, dpi=120)
        plt.close(fig)
        print("Saved: %s" % all_path)
    except Exception as e:
        print("Save all figure failed:", e)

    if not no_show and os.environ.get("DISPLAY"):
        try:
            import matplotlib
            matplotlib.use("TkAgg")
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(1, 1, figsize=(10, 8))
            ax.imshow(grid)
            ax.set_title("dataPack imgs (green circle = touch_center/radius)")
            ax.axis("off")
            plt.tight_layout()
            plt.show()
        except Exception as e:
            print("Display failed:", e)


def visualize_poly_only(calib_dir, out_dir, no_show):
    """只可视化 poly_table_calib 结果：polycalib.npz 的 grad_r/grad_g/grad_b 表。"""
    poly_path = os.path.join(calib_dir, "polycalib.npz")
    if not os.path.isfile(poly_path):
        raise SystemExit("Not found: %s" % poly_path)
    poly = np.load(poly_path)
    bins = int(poly["bins"])
    grad_r = poly["grad_r"]   # (bins, bins, 6)
    grad_g = poly["grad_g"]
    grad_b = poly["grad_b"]
    # 每个 bin 取 6 个系数的 L2 范数作为该通道的“强度”热力图
    def norm_map(g):
        return np.sqrt(np.sum(g * g, axis=2))
    r_map = norm_map(grad_r)
    g_map = norm_map(grad_g)
    b_map = norm_map(grad_b)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 3, figsize=(12, 4))
        for ax, arr, name in zip(axes, [r_map, g_map, b_map], ["grad_r", "grad_g", "grad_b"]):
            im = ax.imshow(arr, aspect="auto")
            ax.set_title("%s (bins=%d, L2 of 6 coeffs)" % (name, bins))
            ax.set_xlabel("grad_dir bin")
            ax.set_ylabel("grad_mag bin")
            plt.colorbar(im, ax=ax)
        plt.tight_layout()
        out_path = os.path.join(out_dir, "visualize_poly_only.png")
        plt.savefig(out_path, dpi=120)
        plt.close(fig)
        print("Saved: %s" % out_path)
    except Exception as e:
        print("Save poly figure failed:", e)
        return
    if not no_show and os.environ.get("DISPLAY"):
        try:
            import matplotlib
            matplotlib.use("TkAgg")
            import matplotlib.pyplot as plt
            fig, axes = plt.subplots(1, 3, figsize=(12, 4))
            for ax, arr, name in zip(axes, [r_map, g_map, b_map], ["grad_r", "grad_g", "grad_b"]):
                ax.imshow(arr, aspect="auto")
                ax.set_title(name)
                ax.set_xlabel("grad_dir bin")
                ax.set_ylabel("grad_mag bin")
            plt.tight_layout()
            plt.show()
        except Exception as e:
            print("Display failed:", e)


def visualize_shadow_only(calib_dir, out_dir, no_show):
    """只可视化 shadow 结果：shadowTable.npz 的方向与表结构。"""
    shadow_path = os.path.join(calib_dir, "shadowTable.npz")
    if not os.path.isfile(shadow_path):
        raise SystemExit("Not found: %s" % shadow_path)
    data = np.load(shadow_path, allow_pickle=True)
    thetas = data["shadowDirections"]
    shadow_table = data["shadowTable"]  # (3, num_directions) object array, each cell list of lists
    num_dirs = len(thetas)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(2, 1, figsize=(10, 6))
        axes[0].plot(np.degrees(thetas), np.ones_like(thetas), ".")
        axes[0].set_title("shadowDirections (deg), count=%d" % num_dirs)
        axes[0].set_xlabel("angle (deg)")
        axes[0].set_ylabel("placeholder")
        # 每个方向、channel 0 取“第一帧”的 value 序列长度作为示意（shadow_table 形状 (3,) 每元素为 list of num_dirs）
        lens = []
        for d in range(num_dirs):
            try:
                lst = shadow_table[0][d] if shadow_table.ndim == 1 else shadow_table[0, d]
            except Exception:
                lst = []
            if hasattr(lst, "__len__") and len(lst) > 0 and hasattr(lst[0], "__len__"):
                lens.append(len(lst[0]))
            else:
                lens.append(0)
        axes[1].bar(np.arange(num_dirs), lens, color="steelblue", alpha=0.8)
        axes[1].set_title("Channel 0: length of first-frame value list per direction")
        axes[1].set_xlabel("direction index")
        axes[1].set_ylabel("length")
        plt.tight_layout()
        out_path = os.path.join(out_dir, "visualize_shadow_only.png")
        plt.savefig(out_path, dpi=120)
        plt.close(fig)
        print("Saved: %s" % out_path)
    except Exception as e:
        print("Save shadow figure failed:", e)
        return
    if not no_show and os.environ.get("DISPLAY"):
        try:
            import matplotlib
            matplotlib.use("TkAgg")
            import matplotlib.pyplot as plt
            plt.figure(figsize=(10, 4))
            plt.bar(np.arange(num_dirs), lens, color="steelblue", alpha=0.8)
            plt.title("Shadow: value list length per direction (ch0)")
            plt.xlabel("direction index")
            plt.ylabel("length")
            plt.tight_layout()
            plt.show()
        except Exception as e:
            print("Display failed:", e)


def visualize_sim_calib_only(calib_dir, out_dir, no_show):
    """只可视化 write_sim_calib 结果：gelmap.npy + params.json。"""
    gel_path = os.path.join(calib_dir, "gelmap.npy")
    params_path = os.path.join(calib_dir, "params.json")
    if not os.path.isfile(gel_path):
        raise SystemExit("Not found: %s" % gel_path)
    gel = np.load(gel_path)
    params_str = ""
    if os.path.isfile(params_path):
        with open(params_path, "r", encoding="utf-8") as f:
            params_str = f.read()
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        axes[0].imshow(gel, cmap="viridis")
        axes[0].set_title("gelmap.npy shape=%s" % str(gel.shape))
        axes[0].axis("off")
        axes[1].text(0.1, 0.5, params_str or "(no params.json)", transform=axes[1].transAxes,
                     fontsize=9, verticalalignment="center", family="monospace", wrap=True)
        axes[1].set_title("params.json")
        axes[1].axis("off")
        plt.tight_layout()
        out_path = os.path.join(out_dir, "visualize_sim_calib_only.png")
        plt.savefig(out_path, dpi=120)
        plt.close(fig)
        print("Saved: %s" % out_path)
    except Exception as e:
        print("Save sim_calib figure failed:", e)
        return
    if not no_show and os.environ.get("DISPLAY"):
        try:
            import matplotlib
            matplotlib.use("TkAgg")
            import matplotlib.pyplot as plt
            plt.figure(figsize=(6, 5))
            plt.imshow(gel, cmap="viridis")
            plt.title("gelmap.npy")
            plt.axis("off")
            plt.tight_layout()
            plt.show()
        except Exception as e:
            print("Display failed:", e)


def main():
    ap = argparse.ArgumentParser(description="Visualize calib: dataPack / poly / shadow / sim_calib only, or simulate tactile from height map.")
    ap.add_argument("--calib_dir", type=str, required=True, help="Directory with dataPack.npz (and polycalib.npz / shadowTable.npz / gelmap.npy as needed)")
    ap.add_argument("--out_dir", type=str, default=None, help="Save images here (default: calib_dir)")
    ap.add_argument("--no_show", action="store_true", help="Do not show window, only save")
    ap.add_argument("--data_only", action="store_true", help="Only visualize dataPack (f0 + imgs with circles)")
    ap.add_argument("--poly_only", action="store_true", help="Only visualize poly_table_calib result (polycalib.npz)")
    ap.add_argument("--shadow_only", action="store_true", help="Only visualize shadow result (shadowTable.npz)")
    ap.add_argument("--sim_calib_only", action="store_true", help="Only visualize write_sim_calib result (gelmap.npy + params.json)")
    ap.add_argument("--max_imgs", type=int, default=24, help="Max number of imgs to show in grid (default 24, --data_only)")
    ap.add_argument("--sphere_radius", type=float, default=40, help="Sphere radius in pixels for synthetic height (sim only)")
    ap.add_argument("--sphere_depth", type=float, default=12, help="Sphere depth in pixels (sim only)")
    ap.add_argument("--sphere_cx", type=float, default=None, help="Sphere center x in pixels (default image center)")
    ap.add_argument("--sphere_cy", type=float, default=None, help="Sphere center y in pixels (default image center)")
    args = ap.parse_args()

    calib_dir = os.path.abspath(args.calib_dir)
    out_dir = args.out_dir or calib_dir
    os.makedirs(out_dir, exist_ok=True)

    modes = [args.data_only, args.poly_only, args.shadow_only, args.sim_calib_only]
    if sum(modes) > 1:
        raise SystemExit("Only one of --data_only, --poly_only, --shadow_only, --sim_calib_only may be set.")
    if args.data_only:
        visualize_datapack_only(calib_dir, out_dir, args.no_show, max_imgs=args.max_imgs)
        return
    if args.poly_only:
        visualize_poly_only(calib_dir, out_dir, args.no_show)
        return
    if args.shadow_only:
        visualize_shadow_only(calib_dir, out_dir, args.no_show)
        return
    if args.sim_calib_only:
        visualize_sim_calib_only(calib_dir, out_dir, args.no_show)
        return

    data = np.load(os.path.join(calib_dir, "dataPack.npz"), allow_pickle=True)
    f0 = data["f0"]
    touch_center = data["touch_center"] if "touch_center" in data.files else None
    H, W = f0.shape[0], f0.shape[1]

    sphere_cx = int(round(args.sphere_cx)) if args.sphere_cx is not None else (W // 2)
    sphere_cy = int(round(args.sphere_cy)) if args.sphere_cy is not None else (H // 2)
    if touch_center is not None and args.sphere_cx is None and args.sphere_cy is None:
        tcx_min, tcx_max = float(np.min(touch_center[:, 0])), float(np.max(touch_center[:, 0]))
        tcy_min, tcy_max = float(np.min(touch_center[:, 1])), float(np.max(touch_center[:, 1]))
        if not (tcx_min <= sphere_cx <= tcx_max and tcy_min <= sphere_cy <= tcy_max):
            print(
                "[WARN] Synthetic sphere center (%d,%d) is outside touch_center range x:[%.1f, %.1f], y:[%.1f, %.1f]. "
                "This may cause spatial extrapolation and unrealistic colors. "
                "Consider --sphere_cx/--sphere_cy near data mean center."
                % (sphere_cx, sphere_cy, tcx_min, tcx_max, tcy_min, tcy_max)
            )

    height_map = make_sphere_height_map(
        H, W,
        cx=sphere_cx,
        cy=sphere_cy,
        radius_pix=int(args.sphere_radius),
        depth_pix=float(args.sphere_depth),
    )
    sim_img, _ = simulate_tactile(calib_dir, height_map, use_shadow=False)

    out_img = np.clip(sim_img, 0, 255).astype(np.uint8)
    out_path = os.path.join(out_dir, "visualize_calib_sim.png")
    cv2.imwrite(out_path, cv2.cvtColor(out_img, cv2.COLOR_RGB2BGR))
    print(f"Saved: {out_path}")

    height_path = os.path.join(out_dir, "visualize_calib_height.npy")
    np.save(height_path, height_map)
    print(f"Saved height map: {height_path}")

    if not args.no_show:
        try:
            import matplotlib
            matplotlib.use("Agg")  # 无显示时先保存，再尝试弹窗
            import matplotlib.pyplot as plt
            fig, axes = plt.subplots(1, 3, figsize=(12, 4))
            axes[0].imshow(f0)
            axes[0].set_title("f0 (background)")
            axes[0].axis("off")
            axes[1].imshow(height_map, cmap="gray")
            axes[1].set_title("Height map (synthetic)")
            axes[1].axis("off")
            axes[2].imshow(out_img)
            axes[2].set_title("Simulated tactile")
            axes[2].axis("off")
            plt.tight_layout()
            plt.savefig(os.path.join(out_dir, "visualize_calib_all.png"), dpi=120)
            print("Saved: %s" % os.path.join(out_dir, "visualize_calib_all.png"))
            plt.close(fig)
            # 仅在存在 DISPLAY 时尝试弹窗，避免无头环境崩溃
            if os.environ.get("DISPLAY"):
                matplotlib.use("TkAgg")
                plt.figure()
                plt.imshow(out_img)
                plt.title("Simulated tactile")
                plt.axis("off")
                plt.show()
            else:
                print("No DISPLAY: skip window. Use --no_show to suppress this.")
        except Exception as e:
            print("Display failed (use --no_show to only save files):", e)


if __name__ == "__main__":
    main()
