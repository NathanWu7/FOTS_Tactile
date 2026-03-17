# ========== 参数说明 ==========
# 标定与仿真共用；Calib 标定、write_sim_calib、仿真 marker_motion_sim_cfg 均会读取此处。

# ---- 实验/标定 ----
# ball_radius: 标定用球体半径 (mm)，如 4.70mm 直径则 4.70/2
ball_radius = 4.70 / 2
# mm_to_pixel: 每毫米对应像素数，用于物理尺寸与像素换算；仿真里 sensor.pixmm = 1/mm_to_pixel
mm_to_pixel = 19.58

# ---- 传感器 ----
# sensor_h, sensor_w: 触觉图高、宽（像素），与图像、calib、仿真分辨率一致
sensor_h = 320
sensor_w = 240
# sensor_type: 传感器类型，用于拼路径（如 gelsight_bg.npy）
sensor_type = "gelsight"

# ---- 光学/高度图处理（FOTS Marker 与仿真中用） ----
# pyramid_kernel_size: 多尺度高斯模糊核尺寸列表，用于高度图平滑
pyramid_kernel_size = [51, 21, 11, 5]
# kernel_size: 单次高斯模糊核尺寸
kernel_size = 5

# ---- Marker 网格（凝胶表面标记点布局） ----
# 在 utils/marker_motion.py 中：网格为均匀矩形，共 N 列 × M 行。
# N: 列方向标记点个数 (num_markers_col)
# M: 行方向标记点个数 (num_markers_row)
# x0: 第一列标记点的列坐标（像素，横轴）。第一个标记点 = 网格左上角 = 像素 (x0, y0)，即 (列, 行)。
# y0: 第一行标记点的行坐标（像素，纵轴）
# dx: 列方向间距（像素），即相邻两列之间的像素差
# dy: 行方向间距（像素），即相邻两行之间的像素差
# 如何确定“第一个”标记点：在传感器图像上找到标记点网格，取左上角（列最小、行最小）的那颗为 (x0, y0)；
#   然后沿列方向量到下一颗得到 dx，沿行方向量到下一颗得到 dy。
# 若间距不恒定：当前实现假定均匀网格；非均匀时需改代码传入各点坐标列表，或用平均 dx/dy 近似。
# 仿真 FOTSMarkerSimulatorCfg 的 marker_params 与此对应（若坐标系约定不同可能 x0/y0、dx/dy 对调）
## DIGIT 示例（注释）
# N = 9
# M = 8
# x0 = 40
# y0 = 27
# dx = 27
# dy = 27
## GelSight Mini
N = 11
M = 9
x0 = 26
y0 = 15
dx = 29
dy = 26