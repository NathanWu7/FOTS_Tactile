"""
左键圆心、右键圆周，输出 CSV（img_names, center_x, center_y, radius）。默认图像目录 Calib/data/imgs，CSV Calib/data/csv/annotate.csv。
"""
import argparse
import csv
import glob
import math
import os
import cv2

CALIB_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(CALIB_DIR, "data")
base_path = DATA_DIR

def click_and_store(event, x, y, flags, param):
    global center_x, center_y
    if event == cv2.EVENT_LBUTTONDOWN:
        center_x, center_y = x, y
        cv2.circle(image, (x, y), 3, (0, 0, 255), -1)
        cv2.imshow("image", image)
    elif event == cv2.EVENT_RBUTTONDOWN:
        radius = math.sqrt((center_x - x) ** 2 + (center_y - y) ** 2)
        with open(filename, "a", newline="") as csvfile:
            csv.writer(csvfile).writerow([img_name, center_x, center_y, int(radius)])
        cv2.circle(image, (x, y), 3, (0, 0, 255), -1)
        cv2.imshow("image", image)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder", type=str, default="imgs", help="Subfolder under Calib/data or full path")
    ap.add_argument("--csv", type=str, default=os.path.join(DATA_DIR, "csv", "annotate.csv"))
    args = ap.parse_args()
    filename = args.csv
    img_folder = args.folder if os.path.isabs(args.folder) else os.path.join(DATA_DIR, args.folder)
    img_files = sorted(glob.glob(os.path.join(img_folder, "*.png")))
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    center_x = center_y = 0
    for img_path in img_files:
        image = cv2.imread(img_path)
        img_name = os.path.basename(img_path)
        cv2.imshow("image", image)
        cv2.setMouseCallback("image", click_and_store, image)
        cv2.waitKey(0)
    cv2.destroyAllWindows()
