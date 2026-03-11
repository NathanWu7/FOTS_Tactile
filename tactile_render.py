import sys
import cv2
import numpy as np
import torch
seed = 42
torch.seed = seed
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

from utils.fots_render import FOTSRender
from mlp_calib.src.train.mlp_model import MLP

def get_simapproach():
    import params as pr
    stype = pr.sensor_type
    # 路径按传感器类型拼接，便于扩展新传感器（如 xense）
    model_path = f'./assets/gel/{stype}_bg.npy'
    background_img = np.load(model_path)
    ini_bg_mlp = np.load(f'./utils/utils_data/ini_bg_fots_{stype}.npy')
    model = MLP().to(device)
    model.load_state_dict(torch.load(f"./mlp_calib/models/mlp_n2c_{stype}.pth"))
    model.to(device)
    simulation = FOTSRender(
        background_img      = background_img,
        bg_render           = ini_bg_mlp,
        model               = model,
    )
    return simulation
