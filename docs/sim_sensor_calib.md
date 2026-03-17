# 仿真传感器标定说明（Taxim + FOTS）

本流程输出的标定目录可被仿真器直接读取。  
固定输出文件：`dataPack.npz`、`polycalib.npz`、`shadowTable.npz`、`gelmap.npy`、`params.json`。

## 1) 环境与参数

- 安装依赖：见项目根 `README.md`
- 关键参数在 `params.py`：
  - `mm_to_pixel`、`ball_radius`
  - `sensor_w/sensor_h`
  - `N/M/x0/y0/dx/dy`（marker 网格）
- `poly_table_calib.py` 支持覆盖参数：
  - `--mm_to_pixel`
  - `--ball_radius_mm`

## 2) 标定输入数据

- 背景图（无接触）1 张：作为 `f0`
- 压痕图多张
- 标注 CSV（列名固定）：`img_names,center_x,center_y,radius`

## 3) 标定流程

```bash
CALIB_DIR=assets/xense
IMG_DIR=<你的触觉图目录>
ANNOT_CSV=<你的标注csv>
F0_PATH=<你的背景图.npy或png>

python Calib/build_data_pack.py --image_dir $IMG_DIR --annot_csv $ANNOT_CSV --f0_path $F0_PATH --out_dir $CALIB_DIR
python Calib/poly_table_calib.py --data_path $CALIB_DIR --mm_to_pixel 28 --ball_radius_mm 3.0
python Calib/generate_shadow_masks.py --data_path $CALIB_DIR
python Calib/write_sim_calib.py --calib_dir $CALIB_DIR
```

说明：
- `write_sim_calib.py` 默认会从 `$CALIB_DIR/dataPack.npz` 自动读取分辨率并写入 `params.json`。
- 若未检测到 `dataPack.npz`，才回退到 `params.py` 的分辨率。

## 4) 标定结果可视化

```bash
python Calib/visualize_calib.py \
  --calib_dir assets/xense \
  --sphere_cx 182 --sphere_cy 404 \
  --sphere_radius 56 --sphere_depth 14
```

常用参数：
- `--sphere_cx --sphere_cy --sphere_radius --sphere_depth`：控制合成接触
- 默认保留 marker；若需旧行为可加 `--smooth_background`
- 只检查数据包可用 `--data_only`

输出：
- `visualize_calib_sim.png`
- `visualize_calib_height.npy`

## 5) 在哪里设置和使用标定结果

- 仿真器通过 `calib_folder_path` 读取标定目录。
- TacManip Xense 配置：`tac_manip/assets/sensors/xense/xense_taxim_fots.py`
  - `optical_sim_cfg.calib_folder_path` 应指向 `.../Sensors/Xense/calibs`
  - `tactile_img_res` 可从该目录 `params.json` 自动读取。
