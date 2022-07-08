import os
from typing import List, re

import numpy as np
from PIL import Image
from tqdm import tqdm

from utils import read_tiff


class RCR:
    def __init__(self, image_paths: List[str], xa: int = 3, xb: int = 5) -> None:
        self.image_paths = image_paths
        self.xa = xa
        self.xb = xb
        self.epsilon = 1e-7

    def _compute_mb(self, i: int) -> np.array:
        """
        Mb is the mean backscatter in Xb images before date di (included)

        :return:
            np.array
        """
        indices = range(i - self.xb + 1, i + 1)
        final_img = np.zeros_like(read_tiff(self.image_paths[0]))
        for k in indices:
            img_path = self.image_paths[k]
            img = read_tiff(img_path)
            final_img += img
        return final_img / self.xb

    def _compute_ma(self, i: int) -> np.array:
        """
        Ma is the mean backscatter in Xa images after date di+1 (included):

        :return:
            np.array
        """
        indices = range(i + 1, i + self.xa + 1)
        final_img = np.zeros_like(read_tiff(self.image_paths[0]))
        for k in indices:
            img_path = self.image_paths[k]
            img = read_tiff(img_path)
            final_img += img
        return final_img / self.xa

    def _compute_rcr(self, i: int) -> np.array:
        """
        RCR = Ma/Mb

        :return:
            np.array: each pixel contains the corresponding RCR for image i
        """
        return 10 * np.log10((self._compute_ma(i) / self._compute_mb(i)) + self.epsilon)

    def compute_rcr_for_all_images(self, write_dir: str) -> None:
        """
        Compute RCR for images i in [self.xb:N-self.xa] with N the total number
        of images.

        :param
            write_dir: str
                Directory to store the images

        :return:
            None
        """
        if not os.path.isdir(write_dir):
            os.mkdir(write_dir)

        print("Start computing RCR on all available images")
        N = len(self.image_paths)
        print(f"Number of available images: {N}")
        for i, img_path in enumerate(tqdm(self.image_paths[self.xb : N - self.xa])):
            i += self.xb
            rcr = self._compute_rcr(i)
            img_name = img_path.split("/")[-1].split(".")[0]
            im = Image.fromarray(rcr)
            save_path = f"{write_dir}/rcr_{img_name}.tif"
            print(f"Saving image at {save_path}")
            im.save(save_path)


if __name__ == "__main__":
    data_dir = "/mnt/SAR_images/processed/18MUU/cropped/descending"

    image_paths = []
    for file in os.listdir(data_dir):
        if file.endswith(".tif"):
            filepath = os.path.join(data_dir, file)
            image_paths.append(filepath)

    image_paths = sorted(image_paths)

    rcr_processor = RCR(image_paths, xa=3, xb=5)
    rcr_processor.compute_rcr_for_all_images(
        write_dir="/mnt/SAR_images/processed/RCR/cropped/descending"
    )
