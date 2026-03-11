"""
采集无接触背景：打开摄像头，按空格保存一帧为 gelsight_bg.npy（并可选保存到 Calib/data/）。
需将结果复制到仿真用 f0 或 --f0_path 指向的路径。
"""
import os
import cv2
import numpy as np

CALIB_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(CALIB_DIR, "data")

def takeimg(save_dir=None, num=1, camnum=0):
    """按空格采集 num+1 张，第一张同时存为 gelsight_bg.npy。save_dir 默认当前目录。"""
    if save_dir is None:
        save_dir = os.getcwd()
    os.makedirs(save_dir, exist_ok=True)
    cap = cv2.VideoCapture(camnum)
    cap.set(cv2.CAP_PROP_EXPOSURE, -10)
    i = 0
    while i < num + 1:
        ret, img = cap.read()
        if not ret:
            break
        image = cv2.resize(cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE), (240, 320))
        cv2.imshow("capture", image)
        key = cv2.waitKey(1)
        if key & 0xFF == 32:
            cv2.imwrite(os.path.join(save_dir, f"{i:04d}.png"), image)
            if i == 0:
                np.save(os.path.join(save_dir, "gelsight_bg.npy"), image)
                print("Saved gelsight_bg.npy")
            i += 1
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Capture background frame(s). SPACE to capture.")
    ap.add_argument("--dir", type=str, default=DATA_DIR, help="Save directory")
    ap.add_argument("--num", type=int, default=0, help="Extra frames after bg (0 = only bg)")
    ap.add_argument("--cam", type=int, default=0)
    args = ap.parse_args()
    takeimg(save_dir=args.dir, num=args.num, camnum=args.cam)
