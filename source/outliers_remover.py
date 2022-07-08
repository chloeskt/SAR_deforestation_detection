import collections
from typing import Tuple, List, Dict, Union, Optional, Set

import numpy as np
from tqdm import tqdm

from utils import read_tiff, save_tiff


class OutliersRemover:
    def __init__(
        self,
        filepath: str,
        threshold: int,
        output_dir: str,
        output_filename: str,
        dark_value: int = -1,
        time_range: list = None,
    ):
        self.filepath = filepath
        self.threshold = threshold
        self.output_dir = output_dir
        self.dark_value = dark_value
        self.output_filename = output_filename
        self.time_range = time_range

    @staticmethod
    def create_mask_shadows(
        image: np.array, detected_coords_of_shadows: np.array
    ) -> np.array:
        mask = [
            True if (y, x) in detected_coords_of_shadows else False
            for y, x in np.ndindex(image.shape)
        ]
        mask = np.array(mask).reshape(image.shape)
        return mask

    def create_group_image(
        self,
        image: np.array,
        detected_groups_of_shadows: np.array,
        filename: Optional[str],
        save: bool = False,
    ) -> np.array:
        new_image = np.full_like(image, -1)

        for i, (_, coords) in tqdm(
            enumerate(
                sorted(detected_groups_of_shadows.items(), key=lambda x: len(x[1]))
            )
        ):
            for y, x in coords:
                new_image[y, x] = i

        if save:
            save_tiff(new_image, self.output_dir, filename)
        return new_image

    def get_shadow_image(self, image: np.array, mask: np.array) -> np.array:
        new_image = np.where(mask, image, -1.0)
        save_tiff(new_image, self.output_dir, self.output_filename)
        return new_image

    def main(
        self, return_all: bool = True
    ) -> Union[
        Tuple[
            np.array,
            Dict[Tuple[int, int], Tuple[int, float]],
            Dict[int, Set[Tuple[int, int]]],
        ],
        np.array,
    ]:
        # load image
        image = read_tiff(self.filepath)
        detected_coords_of_shadows, detected_groups_of_shadows = self.remove_outliers(
            image
        )
        mask = self.create_mask_shadows(image, detected_coords_of_shadows)
        new_image = self.get_shadow_image(image, mask)
        if return_all:
            return new_image, detected_coords_of_shadows, detected_groups_of_shadows
        else:
            return new_image

    def remove_outliers(
        self, image
    ) -> Tuple[
        Dict[Tuple[int, int], Tuple[int, float]], Dict[int, List[Tuple[int, int]]]
    ]:
        detected_coords_of_shadows = {}
        detected_groups_of_shadows = {}
        all_explored_pixels = set()

        for i, (original_y, original_x) in tqdm(enumerate(np.ndindex(image.shape))):
            to_explore = {(original_y, original_x)}

            # keep track of the values we got
            tmp_detected_coords_of_shadows = {}
            tmp_detected_groups_of_shadows = collections.defaultdict(set)

            while to_explore:
                y_being_explored, x_being_explored = to_explore.pop()

                # check if we already explored that pixel
                if (y_being_explored, x_being_explored) in all_explored_pixels:
                    continue

                if y_being_explored < 0 or x_being_explored < 0:
                    # edge case: -1 in python refers to the last pixel
                    continue

                # extract value at the pixel being explored (if any)
                try:
                    pixel_value = image[y_being_explored, x_being_explored]
                except IndexError:
                    continue

                all_explored_pixels.add((y_being_explored, x_being_explored))

                # dark pixel or not
                if self.time_range is not None:
                    if (
                        pixel_value == self.dark_value
                        or pixel_value < self.time_range[0]
                        or pixel_value > self.time_range[1]
                    ):
                        # there is nothing to do here
                        continue
                else:
                    if pixel_value == self.dark_value:
                        # there is nothing to do here
                        continue

                # now there is a value != self.dark_value, we need to explore nearby pixels
                # add nearby pixels in to_explore
                nearby_pixels = {
                    # (y_being_explored + 1, x_being_explored + 1),
                    (y_being_explored, x_being_explored + 1),
                    # (y_being_explored - 1, x_being_explored + 1),
                    (y_being_explored + 1, x_being_explored),
                    (y_being_explored - 1, x_being_explored),
                    # (y_being_explored + 1, x_being_explored - 1),
                    (y_being_explored, x_being_explored - 1),
                    # (y_being_explored - 1, x_being_explored - 1),
                }
                to_explore.update(nearby_pixels)

                # add to temporary detected groups of shadows
                tmp_detected_coords_of_shadows[(y_being_explored, x_being_explored)] = (
                    i,
                    pixel_value,
                )
                tmp_detected_groups_of_shadows[i].add(
                    (y_being_explored, x_being_explored)
                )

            # check if we have more than 4 nearby pixels in each group of shadows
            if len(tmp_detected_coords_of_shadows) >= self.threshold:
                detected_coords_of_shadows.update(tmp_detected_coords_of_shadows)
                detected_groups_of_shadows.update(tmp_detected_groups_of_shadows)

        return detected_coords_of_shadows, detected_groups_of_shadows


if __name__ == "__main__":
    threshold = 16

    outliers_remover = OutliersRemover(
        filepath="/mnt/SAR_images/processed/shadows/cropped/detected_shadows_image_indexes.tif",
        threshold=threshold,
        output_dir="/mnt/SAR_images/processed/shadows/cropped/",
        output_filename=f"filtered_shadow_image_threshold_{threshold}.tif",
        dark_value=-1,
    )
    (
        new_image,
        detected_coords_of_shadows,
        detected_groups_of_shadows,
    ) = outliers_remover.main()
