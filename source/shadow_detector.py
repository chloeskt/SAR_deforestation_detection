import os
from typing import List

import numpy as np
from PIL import Image
from tqdm import tqdm

from utils import read_tiff


class ShadowDetector:
    def __init__(
        self, image_paths: List[str], threshold: float = -4.5, VALUE: int = -1
    ) -> None:
        self.image_paths = image_paths
        self.threshold = threshold
        self.VALUE = VALUE

    def _get_min(self, write_dir: str) -> np.array:
        min_array = np.zeros_like(read_tiff(self.image_paths[0]))
        # first pass: get all the mins
        for i, img_path in enumerate(tqdm(self.image_paths)):
            img = read_tiff(img_path)
            if i == 0:
                min_array = img
            else:
                min_array = np.minimum(min_array, img)

        where = min_array < self.threshold
        min_array[~where] = np.inf

        im = Image.fromarray(min_array)
        save_path = f"{write_dir}/image_min.tif"
        print(f"Saving image at {save_path}")
        im.save(save_path)
        return min_array

    def _get_min_img_index(self, min_array: np.array) -> np.array:
        # second pass: get corresponding img path to the min value
        final_img = min_array.copy()
        for i, img_path in enumerate(tqdm(self.image_paths)):
            img = read_tiff(img_path)
            where_min = img == min_array
            final_img[where_min] = i

        where = final_img == np.inf
        final_img[where] = self.VALUE
        return final_img

    def detect_shadows_on_all_images(self, write_dir: str) -> None:
        if not os.path.isdir(write_dir):
            os.mkdir(write_dir)

        print(f"Start detecting shadows on {len(self.image_paths)} images")

        min_img = self._get_min(write_dir)
        final_img = self._get_min_img_index(min_img)

        im = Image.fromarray(final_img)
        save_path = f"{write_dir}/detected_shadows_image_indexes.tif"
        print(f"Saving image at {save_path}")
        im.save(save_path)

    def detect_shadow_single_image(self, img_indexes_path: str, write_dir: str) -> None:
        img_indexes = read_tiff(img_indexes_path)

        for i, img_path in enumerate(tqdm(sorted(self.image_paths))):
            where_index = img_indexes == i

            if not (where_index == False).all():
                print("Shadow detected on image", img_path.split("/")[-1])

            current_img = read_tiff(img_path)
            current_img[where_index] = 1
            current_img[~where_index] = 0
            im = Image.fromarray(current_img)
            img_name = img_path.split("/")[-1].split(".")[0][4:]
            save_path = f"{write_dir}/{img_name}.tif"
            print(f"Saving image at {save_path}")
            im.save(save_path)


if __name__ == "__main__":
    data_dir = "/mnt/SAR_images/processed/RCR/cropped/descending"

    image_paths = []
    for file in os.listdir(data_dir):
        if file.endswith(".tif"):
            filepath = os.path.join(data_dir, file)
            image_paths.append(filepath)

    image_paths = sorted(image_paths)
    shadow_detector = ShadowDetector(image_paths, threshold=-4.5, VALUE=-1)
    shadow_detector.detect_shadows_on_all_images(
        write_dir="/mnt/SAR_images/processed/shadows/cropped/descending"
    )
    shadow_detector.detect_shadow_single_image(
        img_indexes_path="/mnt/SAR_images/processed/shadows/cropped/detected_shadows_image_indexes.tif",
        write_dir="/mnt/SAR_images/processed/shadows/cropped/descending",
    )
