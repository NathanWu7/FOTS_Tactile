# 四类数据说明与标定流程

本文档说明 FOTS 仿真所需的四类资源数据分别是什么、如何用本仓库的标定脚本得到，以及**如何为新传感器（例如 xense）**准备这些数据。

---

## 1. 四类数据分别是什么

| 类型 | 文件名示例 | 含义 | 形状/格式 |
|------|------------|------|-----------|
| **① 背景图** | `assets/gel/gelsight_bg.npy` | 传感器**无接触**时拍到的单帧图像，作为仿真触觉图的底色 | `(320, 240, 3)` uint8，BGR |
| **② 凝胶垫高度** | `utils/utils_data/gelsight_pad.npy` | 凝胶垫**静止时的表面高度场**（单位：mm），与物体高度叠加后用于接触判断 | `(320, 240)` float，单位 mm |
| **③ FOTS 渲染背景** | `utils/utils_data/ini_bg_fots_gelsight.npy` | MLP 在**无接触/平面法线**下的输出（仿真“无接触”时的光学响应），用于从法线图还原颜色时减去 | `(320, 240, 3)` float |
| **④ 法线→颜色 MLP** | `mlp_calib/models/mlp_n2c_gelsight.pth` | 从**表面法线 (nx,ny,nz)** 映射到 **RGB 颜色** 的 MLP 权重，用于光学仿真 | PyTorch `state_dict` |

仿真时：高度图 → 法线图 → MLP → 得到“光学响应”，再减去 ③、乘 255、加上 ①，得到最终触觉图。② 用于构造带凝胶曲率的高度图。

---

## 2. 如何用本仓库脚本得到这四类数据

### 2.1 ① 背景图 `*_bg.npy`

**含义**：传感器在**无任何接触**时的一帧图像。

**本仓库做法**（`mlp_calib/scripts/record.py`）：

- 使用摄像头或传感器采集一帧，resize 到 `(240, 320)`（宽×高），保存为 `.npy`。
- 脚本里 `takeimg()` 会保存为 `gelsight_bg.npy`（当前工作目录），你需要**手动复制到** `assets/gel/` 并命名为 `传感器名_bg.npy`（如 `xense_bg.npy`）。

**步骤概要**：

1. 连接你的传感器（或摄像头），确保无接触、光照稳定。
2. 在 `mlp_calib/scripts/` 下运行 `record.py`（或改 `takeimg()` 的保存路径/文件名），按空格采集一帧。
3. 将得到的 `.npy` 放到 `assets/gel/`，命名为 `xense_bg.npy`。

若没有现成采集脚本，也可用 OpenCV 读一帧、resize 到 `(240, 320)`，再 `np.save("assets/gel/xense_bg.npy", img)`。

---

### 2.2 ② 凝胶垫高度 `*_pad.npy`

**含义**：凝胶表面在**未接触**时的高度场，形状 `(sensor_h, sensor_w)`，单位 **mm**。用于和物体高度叠加：`heightMap += gel_pad * mm_to_pixel`。

**本仓库**：未提供自动生成脚本，现有 `gelsight_pad.npy` / `digit_pad.npy` 来自 [digit-depth](https://github.com/vocdex/digit-depth) 或其它标定。

**对新传感器（如 xense）的可行做法**：

- **方案 A**：若凝胶可视为平面，用**全零**即可：  
  `np.save("utils/utils_data/xense_pad.npy", np.zeros((320, 240), dtype=np.float64))`
- **方案 B**：若有曲面/曲率标定或从 3D 模型导出的高度图，保存为 `(320, 240)` float，单位 mm，再放到 `utils/utils_data/xense_pad.npy`。

---

### 2.3 ③ FOTS 渲染背景 `ini_bg_fots_*.npy`

**含义**：在**无接触**（或平面接触）时，由当前 MLP 对“平面法线”渲染出的 RGB 响应；仿真时用 `sim_img - ini_bg_fots` 再叠加真实背景。

**本仓库**：`utils/fots_render.py` 里有注释可保存该量（`np.save("ini_bg_fots_gelsight3.npy", sim_img)`）。即：用**已训练好的 MLP**，输入**全平面法线**（例如 (0,0,1)），得到 `sim_img`（reshape 成 (320,240,3)），保存为 `ini_bg_fots_传感器名.npy`。

**步骤**（需先有 ④ MLP）：

1. 在项目根目录，用“平面法线”跑一遍 FOTS 的 MLP 前向，得到 `sim_img_r` reshape 后的 (320,240,3)。
2. 将该数组保存到 `utils/utils_data/ini_bg_fots_xense.npy`。

我们在下文「新传感器 xense 步骤」里会给出一个**一键生成脚本**，在你有 MLP 后直接生成 ③。

---

### 2.4 ④ 法线→颜色 MLP `mlp_n2c_*.pth`

**含义**：把每个像素的**法线 (nx, ny, nz)** 映射成 **RGB** 的 MLP 权重。训练数据来自：**已知几何的球体压痕**在传感器上的图像 + 对应的法线图。

**本仓库标定流程**（`mlp_calib/`）：

1. **record**：用球体（已知半径）在传感器上**多位置**滚动，采集多张触觉图（约 50 张），保存到某文件夹（如 `gelsight/`）。
2. **label_data**：对每张图用鼠标标定**球心 + 圆周**，得到 `center_x, center_y, radius`，写入 CSV。
3. **create_image_dataset**：根据标注生成「颜色–法线」数据集（从球体几何算 GT 法线），写入 `datasets/A`（颜色）、`datasets/B`（法线）和 `train_test_split`。
4. **train_mlp**：用 CSV 训练 MLP，保存为 `mlp_calib/models/mlp_n2c_传感器名.pth`。

**涉及脚本与配置**：

- `mlp_calib/scripts/record.py`：采集图像（或改用你自己的传感器接口）。
- `mlp_calib/scripts/label_data.py`：`--folder gelsight`、`--csv .../csv/annotate.csv`，标定球心与半径。
- `mlp_calib/scripts/create_image_dataset.py`：依赖 `mlp_calib/config/normal_to_rgb.yaml`（需改 `base_path`、`annot_file`、`dataloader` 的路径和 `mm_to_pixel` 等）。
- `mlp_calib/scripts/train_mlp.py`：`--train_path` / `--test_path` 指向上面生成的 CSV，`--mode train`，保存时改名为 `mlp_n2c_xense.pth`。

**注意**：`normal_to_rgb.yaml` 里目前有绝对路径（如 `/home/r404/...`），新传感器需改成你自己的路径（图像目录、annotate.csv、mm_to_pixel 等）。

---

## 3. 为新传感器「xense」准备数据的步骤汇总

假设新传感器名为 **xense**，图像尺寸与 GelSight 一致（320×240）。若尺寸不同，需在 `params.py` 中改 `sensor_w` / `sensor_h`，并保证所有数据与之一致。

### 步骤 1：参数与目录

- 在 **`params.py`** 中设置：
  - `sensor_type = 'xense'`
  - 若分辨率不同：改 `sensor_w`, `sensor_h`，以及 `mm_to_pixel`（若已知）
- 在 **`mlp_calib/config/normal_to_rgb.yaml`** 中：
  - 将 `base_path`、`annot_file`、`dataloader` 相关路径改为你本机的 `mlp_calib` 路径；
  - `mm_to_pixel` 与 `params.py` 一致；
  - `dataloader.annot_file` 指向即将生成的标注 CSV（如 `mlp_calib/csv/annotate_xense.csv`）。

### 步骤 2：① 背景图

- 用传感器在**无接触**下采一帧，resize 到 (240, 320)，保存为：
  - **`assets/gel/xense_bg.npy`**

（若用 `record.py` 的 `takeimg()`，先改保存路径和文件名，再复制到 `assets/gel/`。）

### 步骤 3：② 凝胶垫高度

- 平面凝胶：在项目根目录运行：
  ```bash
  python -c "
  import numpy as np
  import params as pr
  h, w = pr.sensor_h, pr.sensor_w
  np.save('utils/utils_data/xense_pad.npy', np.zeros((h, w), dtype=np.float64))
  print('Saved utils/utils_data/xense_pad.npy (zeros)')
  "
  ```
- 若有曲面标定，替换为你的 `(sensor_h, sensor_w)` 高度图（单位 mm），再保存为 `utils/utils_data/xense_pad.npy`。

### 步骤 4：④ 训练 MLP（得到 .pth）

1. **采集**：用已知半径的球体在 xense 上滚动，保存约 50 张图像到例如 `mlp_calib/xense/`。
2. **标注**：
   ```bash
   cd mlp_calib/scripts
   python label_data.py --folder xense --csv ../csv/annotate_xense.csv
   ```
   每张图：左键球心，右键圆周，ESC 下一张。
3. **改配置**：在 `normal_to_rgb.yaml` 中把 `dataloader.annot_file` 设为 `annotate_xense.csv` 的路径，`dir_dataset`（在 create_image_dataset 里用）改为 `xense` 图像目录。
4. **生成数据集**：
   ```bash
   cd mlp_calib/scripts
   python create_image_dataset.py
   ```
   （若报错，检查 yaml 中路径和 base_path。）
5. **训练**：
   ```bash
   python train_mlp.py --mode train --epochs 200
   ```
   训练结束后把生成的 `.pth` **重命名**为 `mlp_n2c_xense.pth` 并放到 **`mlp_calib/models/`**。

### 步骤 5：③ 生成 ini_bg_fots_xense.npy

在已有 **xense_bg.npy、xense_pad.npy、mlp_n2c_xense.pth** 的前提下，用下面的一键脚本生成 ③（需在**项目根目录**运行）：

```bash
python scripts/generate_ini_bg_fots.py --sensor xense
```

（该脚本见下一节「附录：生成 ini_bg_fots 的脚本」。）

### 步骤 6：让 FOTS 使用 xense

- **`params.py`** 已设为 `sensor_type = 'xense'`。
- **`tactile_render.py`** 里 `get_simapproach()` 是按 `params.sensor_type` 拼路径的；若你严格按上面命名（`xense_bg.npy`、`xense_pad.npy`、`ini_bg_fots_xense.npy`、`mlp_n2c_xense.pth`），则无需改 `tactile_render.py`。  
  若未按 `sensor_type` 拼路径，需在 `tactile_render.py` 中把 `gelsight` 改为从 `params.sensor_type` 读取（与当前 demo_00 / 文档一致即可）。

完成后运行 `python demos/demo_00_check_env.py` 会检查 `xense` 的四个文件是否都存在；再运行 `demo_01` / `demo_02` 即可用 xense 做仿真。

---

## 4. 标定脚本与配置文件速查

| 目的 | 脚本/配置 | 说明 |
|------|-----------|------|
| 采集无接触背景 | `mlp_calib/scripts/record.py` | 按空格保存一帧；需自行把结果放到 `assets/gel/xense_bg.npy` |
| 采集球体压痕图 | 同上或自定义 | 约 50 张，保存到如 `mlp_calib/xense/*.png` |
| 标定球心与半径 | `mlp_calib/scripts/label_data.py` | `--folder xense --csv ../csv/annotate_xense.csv` |
| 生成颜色–法线数据集 | `mlp_calib/scripts/create_image_dataset.py` | 依赖 `config/normal_to_rgb.yaml` 路径与 mm_to_pixel |
| 训练法线→颜色 MLP | `mlp_calib/scripts/train_mlp.py` | 保存为 `models/mlp_n2c_xense.pth` |
| 凝胶垫高度 | 无现成脚本 | 平面用全零；曲面用外部标定或几何导出 |
| FOTS 渲染背景 ③ | 见下文脚本 | 用已训练 MLP + 平面法线生成 |

---

## 5. 附录：生成 ini_bg_fots 的脚本

脚本已放在 **`scripts/generate_ini_bg_fots.py`**。在项目根目录、且已有该传感器的 MLP 权重（如 `mlp_n2c_xense.pth`）时运行：

```bash
python scripts/generate_ini_bg_fots.py --sensor xense
```

不写 `--sensor` 时使用 `params.sensor_type`。会生成 `utils/utils_data/ini_bg_fots_<sensor>.npy`，供 FOTS 渲染时减去无接触响应使用。
