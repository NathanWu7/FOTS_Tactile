# Calib

统一标定脚本与数据目录：Taxim 光学标定（dataPack、polycalib、shadowTable、gelmap、params.json）及标注、测试数据生成。数据统一放在 **Calib/data/**。

## 脚本（均在项目根目录运行）

| 脚本 | 说明 |
|------|------|
| **build_data_pack.py** | 从图像目录 + CSV 生成 dataPack.npz |
| **poly_table_calib.py** | 从 dataPack 生成 polycalib.npz |
| **generate_shadow_masks.py** | 从 dataPack 生成 shadowTable.npz |
| **write_sim_calib.py** | 向 calib 目录写入 gelmap.npy、params.json（仿真格式） |
| **generate_calib_test_data.py** | 合成测试图 + CSV + bg.npy，输出到 data/test_data、data/csv |
| **label_data_qt.py** | PyQt5 标注 GUI（圆心+半径） |
| **label_data.py** | OpenCV 标注（左键圆心、右键圆周） |
| **record.py** | 采集无接触背景帧 |

## 数据目录 Calib/data/

- **data/csv/**：标注 CSV（如 annotate.csv、annotate_test.csv）
- **data/test_data/**：合成测试数据（imgs/、bg.npy）
- **data/imgs/**：可选，放置真实采集图像

## 标定流程

```bash
# 1) 合成测试数据（可选）
python Calib/generate_calib_test_data.py

# 2) 或标注：python Calib/label_data_qt.py --folder Calib/data/test_data/imgs --csv Calib/data/csv/annotate.csv

# 3) 生成仿真 calib 目录（<calib_dir> 如 assets/simulations/GelSight_Mini/calibs/320x240）
CALIB_DIR=<calib_dir>
python Calib/build_data_pack.py --image_dir Calib/data/test_data/imgs --annot_csv Calib/data/csv/annotate_test.csv --f0_path Calib/data/test_data/bg.npy --out_dir $CALIB_DIR
python Calib/poly_table_calib.py --data_path $CALIB_DIR
python Calib/generate_shadow_masks.py --data_path $CALIB_DIR
python Calib/write_sim_calib.py --calib_dir $CALIB_DIR
```

详见 [docs/sim_sensor_calib.md](../docs/sim_sensor_calib.md)。
