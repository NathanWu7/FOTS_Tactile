# FOTS 傻瓜式 Demo

在**项目根目录**（FOTS_Tactile/）下运行，例如：

```bash
cd /path/to/FOTS_Tactile
python demos/demo_00_check_env.py
python demos/demo_01_tactile_only.py
python demos/demo_02_full_pipeline.py
python demos/demo_03_multi_shapes.py
```

| 脚本 | 说明 |
|------|------|
| **demo_00_check_env.py** | 环境检查：Python、torch、open3d、资源文件、导入是否正常 |
| **demo_01_tactile_only.py** | 用合成圆形凸起高度图生成触觉图，保存到 `demos/out/`，无需 STL |
| **demo_02_full_pipeline.py** | 单 STL 完整流程：触觉图 + 标记图，可 `--stl path.stl`、`--no-show` |
| **demo_03_multi_shapes.py** | 对多个 STL（cylinder、sphere、cone 等）批量跑并保存到 `demos/out/multi_shapes/` |

详细使用说明见 [docs/FOTS_使用说明.md](../docs/FOTS_使用说明.md)。
