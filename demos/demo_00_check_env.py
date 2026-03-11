"""
Demo 00：环境检查（傻瓜式）
检查 Python、torch、open3d、cv2 以及本仓库所需资源文件是否就绪。
在项目根目录运行: python demos/demo_00_check_env.py
"""
import sys
import os

# 确保在项目根目录运行
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def main():
    errors = []
    print("===== FOTS 环境检查 =====\n")

    # 1. Python 版本
    print(f"Python: {sys.version.split()[0]}")
    if sys.version_info < (3, 9):
        errors.append("需要 Python 3.9+")

    # 2. 关键包
    packages = [
        ("cv2", "opencv-python"),
        ("numpy", "numpy"),
        ("torch", "torch"),
        ("open3d", "open3d"),
    ]
    for mod, name in packages:
        try:
            m = __import__(mod)
            v = getattr(m, "__version__", "?")
            print(f"  {name}: {v}")
        except ImportError:
            print(f"  {name}: 未安装")
            errors.append(f"请安装 {name}: pip install {name}")

    # 3. 资源文件（与 params.sensor_type 一致）
    import params as pr
    stype = pr.sensor_type
    files = [
        "assets/gel/gelsight_bg.npy" if stype == "gelsight" else "assets/gel/digit_bg.npy",
        f"utils/utils_data/{stype}_pad.npy",
        f"utils/utils_data/ini_bg_fots_{stype}.npy",
        f"mlp_calib/models/mlp_n2c_{stype}.pth",
    ]
    print("\n资源文件 (sensor_type=%s):" % stype)
    for f in files:
        if os.path.isfile(f):
            print(f"  [OK] {f}")
        else:
            print(f"  [缺失] {f}")
            errors.append(f"缺少文件: {f}")

    # 4. 可选：STL 示例
    stl = "assets/daniel/cylinder.stl"
    if os.path.isfile(stl):
        print(f"  [OK] {stl} (示例 STL)")
    else:
        print(f"  [可选] {stl} 不存在，demo_02/03 需要 STL")

    # 5. 导入本仓库模块
    print("\n导入本仓库模块:")
    try:
        from tactile_render import get_simapproach
        print("  tactile_render.get_simapproach: OK")
    except Exception as e:
        errors.append("tactile_render 导入失败: " + str(e))
        print("  tactile_render: 失败 -", e)
    try:
        from utils.marker_motion import MarkerMotion
        print("  utils.marker_motion: OK")
    except Exception as e:
        errors.append("marker_motion 导入失败: " + str(e))
        print("  utils.marker_motion: 失败 -", e)

    print("\n===== 结果 =====")
    if errors:
        print("环境检查未通过，请处理以下问题：")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print("环境检查通过，可以运行 demo_01 / demo_02 / demo_03。")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
