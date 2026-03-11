# FOTS: A Fast Optical Tactile Simulator for Sim2Real Learning of Tactile-motor Robot Manipulation Skills
This work has been accepted by IEEE Robotics and Automation Letters (RA-L).

FOTS is suitable for GelSight tactile sensors and its variations (like DIGIT sensors). 

In addition, FOTS does not rely on any simulation platform, you can integrate it to any platform (like [MuJoCo](https://github.com/google-deepmind/mujoco)). Here, we provide an example integrated into MuJoCo [FOTS-mujoco](https://github.com/Rancho-zhao/FOTS/tree/FOTS-mujoco).

## Installation

To install dependencies: `pip install -r requirements.txt`

### 环境与版本（Python 3.11 推荐）

- **Python**：原 `requirements.txt` 对应约 **Python 3.8–3.10**。若使用 **Python 3.11**，请用下面方式。
- **Conda 环境（推荐）**：
  ```bash
  conda env create -f environment.yml
  conda activate fots_tactile
  pip install -r requirements-py311.txt
  ```
- **仅 pip（已安装 Python 3.11 时）**：
  ```bash
  pip install -r requirements-py311.txt
  ```
- **版本兼容**：最高兼容 **Python 3.11**，PyTorch 2.x，NumPy 1.24–1.x。`requirements-py311.txt` 与 `environment.yml` 已按 Python 3.11 调整；代码中已移除对 `attrdict` 的依赖并修正 `mesh.compute_vertex_normals` 与脚本路径。

### 与 Isaac Lab 2.3 依赖一致

若需要在 **Isaac Lab 2.3**（Isaac Sim 5.1 + Python 3.11 + PyTorch 2.7） 下运行或与同一 conda 环境共用：

- **在已有 Isaac Lab 2.3 环境中安装 FOTS 依赖**：
  ```bash
  pip install -r requirements-isaaclab23.txt
  ```
- **单独建与 Isaac Lab 2.3 一致的 conda 环境**：
  ```bash
  conda env create -f environment-isaaclab23.yml
  conda activate fots_isaaclab23
  pip install -r requirements-isaaclab23.txt
  ```
- **版本对齐**：`requirements-isaaclab23.txt` 与 `environment-isaaclab23.yml` 使用 **torch==2.7.0**、**torchvision==0.22.0**、**Python 3.11**，与 [Isaac Lab 2.3 官方安装](https://isaac-sim.github.io/IsaacLab/release/2.3.0/source/setup/installation/pip_installation.html) 一致；其余科学栈版本与之兼容。

## Optical Calibration (optional)
1. MLP Calib: Connect a GelSight/DIGIT sensor, and collect ~50 tactile images of a sphere indenter on different locations.
2. Shadow Calib: Choose ~5 tactile images from last step.

*Note: Specific steps refers to respective readme file.*

## Marker Calibration (optional)
1. Collect ~45 tactile flow images of a sphere indenter on different locations (in order of dilate, shear, and twist, 15 images for each type).

*Note: Specific steps refers to respective readme file.*

## Usage Directly
We provide a set of calibration files and you can work with them directly. 

- `python fots_test.py`: you can obtain simulated tactile image, mask, and tactile flow image.

### 详细使用说明与傻瓜式 Demo

- **使用说明**：[docs/FOTS_使用说明.md](docs/FOTS_使用说明.md) — 安装、资源文件、参数、流程与 API 说明。
- **傻瓜式测试**：在项目根目录运行以下脚本（需先安装依赖并保证资源文件存在）：
  ```bash
  python demos/demo_00_check_env.py   # 环境检查
  python demos/demo_01_tactile_only.py   # 合成高度图 -> 触觉图
  python demos/demo_02_full_pipeline.py  # 单 STL -> 触觉图 + 标记图
  python demos/demo_03_multi_shapes.py  # 多 STL 批量测试
  ```
  详见 [demos/README.md](demos/README.md)。

## License
FOTS is licensed under [MIT license](LICENSE).

## Citing FOTS
If you use FOTS in your research, please cite:
```BibTeX
@article{zhao2024fots,
  title={FOTS: A Fast Optical Tactile Simulator for Sim2Real Learning of Tactile-motor Robot Manipulation Skills},
  author={Zhao, Yongqiang and Qian, Kun and Duan, Boyi and Luo, Shan},
  journal={IEEE Robotics and Automation Letters},
  year={2024}
}
```
[ArXiv Paper Link](https://arxiv.org/abs/2404.19217)
