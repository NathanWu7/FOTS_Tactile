# Calib

Taxim + FOTS 标定脚本。输出目录为仿真器可直接读取的 calib 目录。

## 脚本

- `build_data_pack.py`：图像 + 标注 CSV -> `dataPack.npz`
- `poly_table_calib.py`：`dataPack.npz` -> `polycalib.npz`
  - 可选：`--mm_to_pixel`、`--ball_radius_mm`
- `generate_shadow_masks.py`：生成 `shadowTable.npz`
- `write_sim_calib.py`：生成 `gelmap.npy`、`params.json`
  - 默认从 `dataPack.npz` 自动推断分辨率
- `visualize_calib.py`：标定结果可视化
  - 默认保留 marker；`--smooth_background` 可切换旧行为
  - 支持 `--sphere_cx/--sphere_cy/--sphere_radius/--sphere_depth`

## 数据目录

- `Calib/data/csv/`：标注 CSV（`img_names, center_x, center_y, radius`）
- `Calib/data/test_data/`：测试图与背景
- `Calib/data/imgs/`：可选真实图像目录

## 快速流程

```bash
CALIB_DIR=assets/xense
IMG_DIR=<你的触觉图目录>
ANNOT_CSV=<你的标注csv>
F0_PATH=<你的背景图.npy或png>

python Calib/build_data_pack.py --image_dir $IMG_DIR --annot_csv $ANNOT_CSV --f0_path $F0_PATH --out_dir $CALIB_DIR
python Calib/poly_table_calib.py --data_path $CALIB_DIR --mm_to_pixel 28 --ball_radius_mm 3.0
python Calib/generate_shadow_masks.py --data_path $CALIB_DIR
python Calib/write_sim_calib.py --calib_dir $CALIB_DIR
python Calib/visualize_calib.py \
  --calib_dir assets/xense \
  --sphere_cx 182 --sphere_cy 404 \
  --sphere_radius 56 --sphere_depth 14
```

输出文件固定为：
`dataPack.npz`、`polycalib.npz`、`shadowTable.npz`、`gelmap.npy`、`params.json`。

详见 `docs/sim_sensor_calib.md`。
