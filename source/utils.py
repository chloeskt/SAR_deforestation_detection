#!/usr/bin/env python
# coding:utf-8
import os
import re
import shutil
from datetime import datetime
from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
from PIL import Image
from osgeo import gdal


def get_all_images_filepaths(workdir: str) -> List[str]:
    counter = 0
    all_filepaths = []
    for folder in os.listdir(workdir):
        if folder.endswith(".SAFE"):
            for sub_folder in os.listdir(os.path.join(workdir, folder)):
                if sub_folder == "measurement":
                    for file in os.listdir(os.path.join(workdir, folder, sub_folder)):
                        if file.endswith(".tiff"):
                            filepath = os.path.join(workdir, folder, sub_folder, file)
                            all_filepaths.append(filepath)
            counter += 1
    print("Number of folders downloaded: ", counter)
    print("Number of images downloaded: ", len(all_filepaths))
    return all_filepaths


def move_images_into_unique_folder(workdir: str, savedir: str) -> None:
    all_filepaths = get_all_images_filepaths(workdir)

    if not os.path.isdir(savedir):
        os.mkdir(savedir)

    counter = 0
    for image_filepath in all_filepaths:
        filename = image_filepath.split("/")[-1]
        new_filepath = os.path.join(savedir, filename)
        shutil.move(image_filepath, new_filepath)
        counter += 1
    print(f"Moved to {savedir} {counter} images")


def read_tiff(path):
    dataset = gdal.Open(path)
    for x in range(1, dataset.RasterCount + 1):
        band = dataset.GetRasterBand(x)
        array = band.ReadAsArray()
    return array.astype(np.float64)


def plot_sar(ima):
    plt.figure(figsize=(12, 12))
    t = np.mean(ima) + 3 * np.std(ima)
    plt.imshow(np.clip(ima, 0, t), cmap="gray")
    plt.show()


def save_tiff(img, dir, path):
    im = Image.fromarray(img)
    save_path = os.path.join(dir, path)
    print(f"Saving image at {save_path}")
    im.save(save_path)


def backscatter_signal_to_db(im: np.array, epsilon: float = 1e-7) -> np.array:
    return 10 * np.log10(im + epsilon)


def get_temporal_means_and_stds(
    image_paths: List[str],
    epsilon: Optional[float] = 0,
    image_type: Optional[str] = "rcr",
    cropped_coords: Optional[List[int]] = None,
) -> Tuple[List[float], List[float]]:
    temporal_means = []
    temporal_stds = []

    for img_path in image_paths:
        im = read_tiff(img_path)
        if image_type == "backscatter":
            im = backscatter_signal_to_db(im, epsilon)
        if cropped_coords:
            im = im[
                cropped_coords[0] : cropped_coords[1],
                cropped_coords[2] : cropped_coords[3],
            ]

        temporal_means.append(im.mean())
        temporal_stds.append(im.std())

    return temporal_means, temporal_stds


def generate_pixel_coord_with_offset(pixel_coords, offsets):
    tmp_pixel_coords = [x + offsets[0] for x in pixel_coords[:2]]
    tmp_pixel_coords.extend([x + offsets[1] for x in pixel_coords[2:]])
    return tmp_pixel_coords


def generate_graphs_from_pixel_coords(
    data_dir,
    title,
    x_title,
    y_title,
    gamma0: bool = True,
    epsilon: float = 1e-7,
    pixel_coords: Optional[List[int]] = None,
    offsets: Optional[List[int]] = None,
    return_results: bool = False
):
    image_paths = []
    for file in sorted(os.listdir(data_dir)):
        if file.endswith(".tif"):
            filepath = os.path.join(data_dir, file)
            image_paths.append(filepath)

    if pixel_coords:
        if offsets:
            pixel_coords = generate_pixel_coord_with_offset(pixel_coords, offsets)
        if gamma0:
            temporal_means, _ = get_temporal_means_and_stds(
                image_paths,
                epsilon,
                image_type="backscatter",
                cropped_coords=pixel_coords,
            )
        else:
            temporal_means, _ = get_temporal_means_and_stds(
                image_paths, cropped_coords=pixel_coords
            )
    else:
        if gamma0:
            temporal_means, _ = get_temporal_means_and_stds(
                image_paths, epsilon, image_type="backscatter"
            )
        else:
            temporal_means, _ = get_temporal_means_and_stds(image_paths)

    pattern = r"20[0-9]{6}"
    x = [re.findall(pattern, path)[0] for path in image_paths]
    x = [datetime.strptime(date, "%Y%m%d") for date in x]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=temporal_means, mode="lines+markers", name="mean"))
    fig.update_layout(title=title, xaxis_title=x_title, yaxis_title=y_title)
    fig.show()

    if return_results:
        return temporal_means


if __name__ == "__main__":
    workdir = "/mnt/hdd/ascending"
    savedir = "/mnt/hdd/data"
    move_images_into_unique_folder(workdir, savedir)
