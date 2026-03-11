# 可选：DIGIT 硬件支持；无硬件时可不安装，不影响 fots_test / 触觉仿真
try:
    from .digit import *
except ImportError:
    pass  # digit_interface 未安装时跳过，仅使用触觉仿真时无需安装
from .third_party import *
from .train import *
from .dataio import *
