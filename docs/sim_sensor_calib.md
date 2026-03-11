# 仿真与传感器标定（仅 Taxim 光学 + FOTS Marker）

仿真 calib 目录使用**仿真文件格式与文件名**，可直接被 Taxim 光学仿真读取。Marker 参数在 `params.py` 与 `gsmini_taxim_fots.py` 中，无需单独标定文件。**所有标定脚本与数据统一在 Calib/ 与 Calib/data/。**

---

## 仿真用到的数据

| 数据 | 来源 |
|------|------|
| **触觉 RGB** | Taxim：calib 目录下 `dataPack.npz`（f0）、`polycalib.npz`、`shadowTable.npz`、`gelmap.npy`、`params.json`。 |
| **Marker** | FOTS：`gsmini_taxim_fots.py` 中 `marker_motion_sim_cfg`（num_markers_col/row, x0, y0, dx, dy），与 **params.py** 的 N, M, x0, y0, dx, dy 对应。 |

**marker_motion_sim_cfg 各参数来源：**

| 参数 | 来源 |
|------|------|
| **lamb** | 本仓库 **utils/marker_motion.py** 中 MarkerMotion 使用的形变权重（dilate/shear/twist），原 demos 中写死为 `[0.00125, 0.00021, 0.00038]`，仿真里与之一致即可。 |
| **pyramid_kernel_size**、**kernel_size** | 本仓库 **params.py**：`pyramid_kernel_size = [51, 21, 11, 5]`，`kernel_size = 5`。 |
| **marker_params**（num_markers_col/row, x0, y0, dx, dy） | 本仓库 **params.py** 的 **marker params**：`N=11` → num_markers_col，`M=9` → num_markers_row；`x0, y0, dx, dy` 为网格起点与步长（params 里 GelSight 为 x0=26, y0=15, dx=29, dy=26）。仿真里若坐标系不同（如先 col 后 row），可能对调为 x0=15, y0=26, dx=26, dy=29，需与触觉图宽高一致。 |

修改 Marker 网格时改 **params.py** 中 N, M, x0, y0, dx, dy，并同步改仿真配置中的 `marker_params`（注意行列/xy 约定是否与 params 一致）。

---

## 标定流程（输出为仿真 calib 目录）

**1. 准备数据**  
- 无接触背景图一张 → 作 f0（可用 `Calib/record.py` 采集，或使用合成测试的 bg.npy）。  
- 多张球体压痕图 + 每张标注（圆心、半径）→ CSV：`img_names`, `center_x`, `center_y`, `radius`。

**2. 标注**（无真机可用合成数据）  
- 合成测试数据：`python Calib/generate_calib_test_data.py`，输出到 **Calib/data/test_data/imgs/**、**Calib/data/test_data/bg.npy**、**Calib/data/csv/annotate_test.csv**。  
- 标注 GUI：`python Calib/label_data_qt.py --folder Calib/data/test_data/imgs --csv Calib/data/csv/annotate.csv`（左键圆心、再左键圆周一点）。

**3. 生成仿真 calib 目录（文件名与格式与仿真一致）**  

指定一个 calib 目录（如 `assets/simulations/GelSight_Mini/calibs/320x240`），在该目录下生成：

- `dataPack.npz`（含 `f0`, `imgs`, `touch_center`, `touch_radius`, `names`, `img_size`）
- `polycalib.npz`（`bins`, `grad_r`, `grad_g`, `grad_b`）
- `shadowTable.npz`（`shadowDirections`, `shadowTable`）
- `gelmap.npy`（凝胶高度 mm，平面可为全零）
- `params.json`（`sensor.pixmm`, `sensor.num_bins`, `sensor.w`, `sensor.h`）

命令（项目根目录执行）：

```bash
CALIB_DIR=<calib_dir>   # 如 assets/simulations/GelSight_Mini/calibs/320x240
python Calib/build_data_pack.py --image_dir Calib/data/test_data/imgs --annot_csv Calib/data/csv/annotate_test.csv --f0_path Calib/data/test_data/bg.npy --out_dir $CALIB_DIR
python Calib/poly_table_calib.py --data_path $CALIB_DIR
python Calib/generate_shadow_masks.py --data_path $CALIB_DIR
python Calib/write_sim_calib.py --calib_dir $CALIB_DIR
```

完成后 `$CALIB_DIR` 内即为仿真所需全部文件，`calib_folder_path` 指向该目录即可。

---

## 分辨率

- `params.py` 中 `sensor_h`, `sensor_w`（如 320×240）须与图像及 calib 一致。  
- 若仿真用 640×480，可对 `write_sim_calib.py` 加 `--resolution 640x480`（gelmap/params 为 640×480）。

---

## 脚本位置（均在 Calib/）

| 用途 | 脚本 |
|------|------|
| 生成 dataPack.npz | `Calib/build_data_pack.py` |
| 生成 polycalib.npz | `Calib/poly_table_calib.py` |
| 生成 shadowTable.npz | `Calib/generate_shadow_masks.py` |
| 写入 gelmap.npy、params.json | `Calib/write_sim_calib.py` |
| 合成测试图+CSV | `Calib/generate_calib_test_data.py`（输出到 Calib/data/） |
| 标注 GUI | `Calib/label_data_qt.py` |
| OpenCV 标注 | `Calib/label_data.py` |
| 采集背景帧 | `Calib/record.py` |

数据统一放在 **Calib/data/**（csv/、test_data/imgs、test_data/bg.npy 等）。
