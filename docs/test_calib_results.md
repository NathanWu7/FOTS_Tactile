# FOTS 详细使用说明

FOTS（Fast Optical Tactile Simulator）用于从物体几何或高度图生成光学触觉传感器（如 GelSight、DIGIT）的仿真图像与标记运动图。本文档说明安装、资源、参数、流程及自带 Demo 用法。

---

## 1. 安装与环境

### 1.1 依赖安装

- **与 Isaac Lab 2.3 一致**（推荐）：  
  `pip install -r requirements-isaaclab23.txt`  
  或使用 conda：`conda env create -f environment-isaaclab23.yml` 后执行上述 pip。
- **仅 Python 3.11**：  
  `pip install -r requirements-py311.txt`
- **必须**：本仓库需安装 **open3d**（用于读 STL、点云采样）。  
  若缺失：`pip install "open3d>=0.18,<0.20"`

### 1.2 环境自检

在项目根目录执行：

```bash
python demos/demo_00_check_env.py
```

输出 “环境检查通过” 且无报错即表示依赖与资源就绪。

---

## 2. 资源文件说明

运行仿真前请确认以下路径存在且为当前使用的传感器类型。

### 2.1 传感器类型（`params.py`）

- `sensor_type = 'gelsight'`：使用 GelSight 相关资源。  
- 若改为 `'digit'`：需使用 DIGIT 对应的 `.npy` 与 `.pth`（见下）。

### 2.2 必需文件

| 路径 | 说明 |
|------|------|
| `assets/gel/gelsight_bg.npy` 或 `assets/gel/digit_bg.npy` | 传感器背景图（无接触时图像），用于叠加到仿真结果上 |
| `utils/utils_data/gelsight_pad.npy` 或 `digit_pad.npy` | 凝胶垫高度先验，与传感器类型一致 |
| `utils/utils_data/ini_bg_fots_gelsight.npy` 或 `ini_bg_fots_digit.npy` | FOTS 光学渲染用背景/参数 |
| `mlp_calib/models/mlp_n2c_gelsight.pth` 或 `mlp_n2c_digit.pth` | 法线→颜色 MLP 模型权重 |

**这四类数据如何得到、以及如何为新传感器（如 xense）标定**，见 **[docs/标定与四类数据说明.md](标定与四类数据说明.md)**。

### 2.3 可选：几何资源（用于从 mesh 生成高度图）

- **STL 模型**：放在 `assets/daniel/` 下，如 `cylinder.stl`、`sphere.stl` 等。  
- 主脚本与 Demo 默认使用 `assets/daniel/cylinder.stl`，也可通过参数换成其它 STL。

---

## 3. 核心参数（`params.py`）

| 参数 | 含义 | 典型值 |
|------|------|--------|
| `mm_to_pixel` | 毫米到像素比例 | 19.58 |
| `sensor_w`, `sensor_h` | 触觉图像宽、高（像素） | 240, 320 |
| `sensor_type` | 传感器类型 | `'gelsight'` 或 `'digit'` |
| `pyramid_kernel_size`, `kernel_size` | 高度图平滑核 | [51,21,11,5], 5 |
| `N`, `M`, `x0`, `y0`, `dx`, `dy` | 标记网格参数（GelSight/DIGIT 不同） | 见文件内注释 |

修改后无需重装，保存 `params.py` 即可生效。

---

## 4. 流程概览

### 4.1 从 STL 到触觉图像 + 标记运动（完整流程）

1. **读入 STL**：`open3d` 读取三角网格。  
2. **位姿**：对 mesh 做平移 `trans`（mm）、旋转 `rot`（rad）。  
3. **采样点云**：在 mesh 表面均匀或 Poisson 采样得到 3D 点。  
4. **投影到传感器平面**：按 `mm_to_pixel` 将 x,y 转到像素坐标，z 为高度，得到 `heightMap`（与凝胶垫 `gel_pad` 叠加）。  
5. **接触区域**：根据按压深度得到 `contact_mask` 与相对高度 `zq`。  
6. **触觉图像**：  
   `simulation = get_simapproach()` 得到 `FOTSRender`，  
   `tact_img = simulation.generate(zq, contact_mask)` 得到仿真触觉图（可选 `shadow=True` 带阴影）。  
7. **标记运动**：  
   `MarkerMotion(frame0_blur=tact_img, depth=zq/mm_to_pixel, mask=contact_mask, traj=relative_pos, lamb=...)`，  
   调用 `_marker_motion()` 得到 `marker_img`。

对应脚本：根目录 `fots_test.py`，或 **`demos/demo_02_full_pipeline.py`**（可改 STL、保存结果）。

### 4.2 仅从高度图生成触觉图像（无 STL）

若已有 `heightMap` 与 `contact_mask`（例如来自别处仿真或真实深度）：

1. 构造相对高度 `zq`（接触区用物体高度，非接触区用凝胶面，再减去凝胶面得到相对高度）。  
2. `simulation = get_simapproach()`，  
   `tact_img = simulation.generate(zq, contact_mask)`。

参见 **`demos/demo_01_tactile_only.py`**（用简单合成高度图演示）。

---

## 5. API 简要说明

### 5.1 获取仿真器

```python
from tactile_render import get_simapproach
simulation = get_simapproach()
```

- 会加载当前 `params.sensor_type` 对应的背景、pad、ini_bg、MLP 权重。  
- 返回 `FOTSRender` 实例。

### 5.2 生成触觉图像

```python
# zq: (H, W) 相对高度图（像素单位）；contact_mask: (H, W) bool
tact_img = simulation.generate(zq, contact_mask, shadow=False)
# tact_img: (320, 240, 3) uint8，BGR
```

- `shadow=True` 会叠加平面光源阴影，更真实但更慢。

### 5.3 生成标记运动图

```python
from utils.marker_motion import MarkerMotion
import params as pr
marker = MarkerMotion(
    frame0_blur=tact_img,
    depth=zq / pr.mm_to_pixel,  # 转回 mm
    mask=contact_mask,
    traj=relative_pos,  # 物体相对位姿列表，如 [[0,0,0], [tx, ty, rot_z]]
    lamb=[0.00125, 0.00021, 0.00038],
)
marker_img = marker._marker_motion()
```

---

## 6. 自带 Demo 使用（傻瓜式测试）

所有 Demo 均在 **项目根目录** 下执行（即 `FOTS_Tactile/` 为当前目录）：

```bash
cd /path/to/FOTS_Tactile
python demos/demo_00_check_env.py   # 环境检查
python demos/demo_01_tactile_only.py   # 合成高度图 → 触觉图
python demos/demo_02_full_pipeline.py  # STL → 触觉图 + 标记图
python demos/demo_03_multi_shapes.py   # 多 STL 批量跑并保存
```

### 6.1 demo_00_check_env.py — 环境检查

- **作用**：检查 Python、torch、open3d、cv2 及本仓库所需资源文件是否存在。  
- **用法**：`python demos/demo_00_check_env.py`  
- **无需** STL 或其它输入，适合首次运行前自检。

### 6.2 demo_01_tactile_only.py — 仅触觉仿真（合成高度图）

- **作用**：用程序生成的简单高度图（如圆形凸起）调用 FOTS，得到触觉图并保存，不依赖 STL。  
- **用法**：`python demos/demo_01_tactile_only.py`  
- **输出**：默认在 `demos/out/` 下保存 `tactile_only_tact.png`、`tactile_only_mask.png` 等。  
- **可改**：脚本内可调凸起半径、高度、保存路径。

### 6.3 demo_02_full_pipeline.py — 完整流程（单 STL）

- **作用**：从单个 STL 完成“读 mesh → 高度图 → 触觉图 → 标记运动图”，并可选显示/保存。  
- **用法**：  
  `python demos/demo_02_full_pipeline.py`  
  或指定 STL：  
  `python demos/demo_02_full_pipeline.py --stl assets/daniel/sphere.stl`  
- **输出**：可选保存触觉图、mask、marker 图到 `demos/out/`，或弹窗显示。

### 6.4 demo_03_multi_shapes.py — 多形状批量测试

- **作用**：对 `assets/daniel/` 下多个 STL（如 cylinder、sphere、cone 等）各跑一遍完整流程，保存每种的触觉图与 marker 图，便于对比。  
- **用法**：`python demos/demo_03_multi_shapes.py`  
- **输出**：在 `demos/out/multi_shapes/` 下按文件名生成多组图像。

---

## 7. 常见问题

- **ModuleNotFoundError: No module named 'open3d'**  
  安装：`pip install "open3d>=0.18,<0.20"`。

- **FileNotFoundError: assets/gel/gelsight_bg.npy（或其它 .npy/.pth）**  
  确认在项目根目录运行，且未删除 `assets/`、`utils/utils_data/`、`mlp_calib/models/` 中对应文件；若使用 DIGIT，需在 `params.py` 中设 `sensor_type='digit'` 并确保存在 digit 所用资源。

- **触觉图全黑或异常**  
  检查 `contact_mask` 是否合理（有 True）、`zq` 单位是否为像素高度；若从 STL 来，可适当增大 `trans[2]`（按压深度）或检查 mesh 是否在视野内。

- **与 Isaac Lab 共用环境**  
  使用 `requirements-isaaclab23.txt` 安装依赖即可；FOTS 不依赖 Isaac Sim，仅需 Python 3.11 + PyTorch 2.7 + open3d 等。

---

## 8. 参考文献

若在研究中使用了 FOTS，请引用：

```bibtex
@article{zhao2024fots,
  title={FOTS: A Fast Optical Tactile Simulator for Sim2Real Learning of Tactile-motor Robot Manipulation Skills},
  author={Zhao, Yongqiang and Qian, Kun and Duan, Boyi and Luo, Shan},
  journal={IEEE Robotics and Automation Letters},
  year={2024}
}
```

[ArXiv](https://arxiv.org/abs/2404.19217)
