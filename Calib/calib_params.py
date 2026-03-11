"""
标定参数（Taxim 光学 + 仿真一致）。
传感器尺寸与 mm_to_pixel 与项目 params 一致。
"""
import sys
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
import params as pr

ball_radius_mm = getattr(pr, "ball_radius", 4.70 / 2)
pixmm = 1.0 / pr.mm_to_pixel
num_bins = 125
sensor_h = pr.sensor_h
sensor_w = pr.sensor_w

kscale = 50
diff_threshold = 5
frame_mixing_percentage = 0.15

max_rad = 100
shadow_step = 1.25
shadow_threshold = -10.0
num_step = 120
discritize_precision = 0.1
