# FOTS_Tactile（Isaac 分支 · 最小化）

本分支仅保留 **Taxim 光学仿真** 与 **FOTS Marker** 所需标定与数据获取，供仿真 calib 目录使用。**标定相关脚本与数据统一在 Calib/ 与 Calib/data/。**

## 依赖

```bash
pip install -r requirements-py311.txt
# 或 Isaac Lab 环境：pip install -r requirements-isaaclab23.txt
```

## 标定流程（输出为仿真 calib 目录）

标定结果**直接使用仿真文件格式与文件名**（`dataPack.npz`、`polycalib.npz`、`shadowTable.npz`、`gelmap.npy`、`params.json`）。完整步骤见：

- **[docs/sim_sensor_calib.md](docs/sim_sensor_calib.md)**

简要步骤：

1. 准备无接触图 f0 + 多张球体压痕图 + 标注 CSV（可用 `Calib/generate_calib_test_data.py` 生成测试数据到 **Calib/data/**，用 `Calib/label_data_qt.py` 标注）。
2. 运行 `Calib/build_data_pack.py` → `Calib/poly_table_calib.py` → `Calib/generate_shadow_masks.py` → `Calib/write_sim_calib.py`，`--out_dir`/`--data_path`/`--calib_dir` 指向仿真 calib 目录。

## 目录说明

| 目录/文件 | 说明 |
|-----------|------|
| **params.py** | 传感器与 Marker 参数（sensor_w, sensor_h, mm_to_pixel, N, M, x0, y0, dx, dy）。 |
| **Calib/** | 标定脚本：dataPack、polycalib、shadowTable、gelmap、params 生成；标注与测试数据脚本。 |
| **Calib/data/** | 统一数据目录：csv/、test_data/imgs、test_data/bg.npy 等。 |
| **utils/marker_motion.py** | FOTS Marker 形变模型（仿真侧 FOTSMarkerSimulatorCfg 对应）。 |
| **assets/simulations/GelSight_Mini/** | 仿真配置与 calib 目录。 |

## License

MIT. See LICENSE.
