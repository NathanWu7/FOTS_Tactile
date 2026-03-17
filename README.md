# FOTS_Tactile

用于生成 Taxim + FOTS 的标定结果文件，并对标定结果做可视化检查。  
标定脚本在 `Calib/`，数据在 `Calib/data/`。

## 环境配置

```bash
pip install -r requirements-py311.txt
# 或 Isaac Lab 环境
pip install -r requirements-isaaclab23.txt
```

## 标定参数需求

- `params.py`
  - `mm_to_pixel`、`ball_radius`：决定 `poly_table_calib.py` 的球几何映射。
  - `sensor_w/sensor_h`：基础分辨率参数（`write_sim_calib.py` 若检测到 `dataPack.npz`，会优先使用 `f0` 实际分辨率）。
  - `N/M/x0/y0/dx/dy`：Marker 网格参数（用于 FOTS marker 运动配置）。

## 标定流程

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

输出文件：
- `dataPack.npz`
- `polycalib.npz`
- `shadowTable.npz`
- `gelmap.npy`
- `params.json`

## 标定结果可视化

```bash
python Calib/visualize_calib.py \
  --calib_dir assets/xense \
  --sphere_cx 182 --sphere_cy 404 \
  --sphere_radius 56 --sphere_depth 14
```

常用可选参数：
- `--sphere_cx/--sphere_cy/--sphere_radius/--sphere_depth`：控制合成接触位置与几何。
- 默认保留 marker 纹理；若要旧行为可加 `--smooth_background`。
- 只看数据包可用 `--data_only`。

## 标定结果怎么接入仿真

- 仿真器读取 `calib_folder_path` 指向的目录（即上面 `$CALIB_DIR`）。
- Xense（TacManip）配置文件：`tac_manip/assets/sensors/xense/xense_taxim_fots.py`
  - `optical_sim_cfg.calib_folder_path` 指向 `.../Sensors/Xense/calibs`
  - `tactile_img_res` 从该目录 `params.json` 自动读取。

详见 `docs/sim_sensor_calib.md` 与 `Calib/README.md`。
