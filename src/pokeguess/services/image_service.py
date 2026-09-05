import logging
import os
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

import aiofiles
import numpy as np
from PIL import Image

log = logging.getLogger(__name__.removesuffix("_service"))


BACKGROUND_SIZE = (260, 260)
POKEMON_SIZE = (215, 215)
MAIN_COLOR = (16, 88, 178, 255)
OUTLINE_COLOR = (20, 62, 135, 255)
OUTLINE_OFFSET = (-1, -1)
SHADOW_COLOR = (0, 0, 0, 135)
SHADOW_OFFSET = (-6, 8)


class ImageService:
    def __init__(self, background_file: Path) -> None:
        self.background_file = background_file

        self.background_image = Image.open(background_file).resize(BACKGROUND_SIZE)

    def make_silhouette(
        self,
        img: Image.Image,
        color: tuple[int, int, int, int],
        offset: tuple[int, int],
    ) -> Image.Image:
        img = img.convert("RGBA")
        arr = np.array(img)  # shape (H, W, 4)
        alpha = arr[:, :, 3].astype(np.float32)
        opacity = (alpha * (color[3] / 255)).astype(np.uint8)

        out = np.zeros_like(arr)
        out[:, :, 0] = color[0]
        out[:, :, 1] = color[1]
        out[:, :, 2] = color[2]
        out[:, :, 3] = opacity

        shifted = np.zeros_like(out)
        dx, dy = offset
        h, w = arr.shape[:2]
        src_x0, src_x1 = max(0, -dx), min(w, w - dx)
        dst_x0, dst_x1 = max(0, dx), min(w, w + dx)
        src_y0, src_y1 = max(0, -dy), min(h, h - dy)
        dst_y0, dst_y1 = max(0, dy), min(h, h + dy)

        shifted[dst_y0:dst_y1, dst_x0:dst_x1] = out[src_y0:src_y1, src_x0:src_x1]
        return Image.fromarray(shifted, mode="RGBA")

    def layer_images(self, imgs: list[Image.Image]) -> Image.Image:
        first = imgs[0]
        mode = first.mode
        size = first.size

        result = Image.new(mode, size, (0, 0, 0, 0))

        center = (int(size[0] / 2), int(size[1] / 2))

        for img in imgs:
            img_center = (int(img.size[0] / 2), int(img.size[1] / 2))

            offset = (center[0] - img_center[0], center[1] - img_center[1])

            result.alpha_composite(img, dest=offset)

        return result

    def scale(self, img: Image.Image, scale: tuple[int, int]):
        """Scales while preserving the image ratio"""
        new_size = img.size

        if img.size[0] > img.size[1]:
            difference = scale[0] / img.size[0]
            new_size = (scale[0], int(difference * img.size[1]))
        else:
            difference = scale[1] / img.size[1]
            new_size = (int(difference * img.size[0]), scale[1])

        return img.resize(new_size)

    async def process_image(
        self, original_path: Path, hidden_path: Path, revealed_path: Path
    ):
        log.debug(f"Starting to process {original_path}")
        start_time = datetime.now(UTC)

        # Creating output directories
        os.makedirs(hidden_path.parent, exist_ok=True)
        os.makedirs(revealed_path.parent, exist_ok=True)

        original_img = Image.open(original_path, "r")
        original_img.verify()  # verify closes the file
        original_img = Image.open(original_path, "r")

        original_img = self.scale(original_img, POKEMON_SIZE)

        # Convert the image to RGBA
        if original_img.mode == "P":
            original_img = original_img.convert(mode="RGBA")

        # Create original image and scaling the canvas to the background
        original_img = self.layer_images(
            [
                Image.new("RGBA", BACKGROUND_SIZE, (0, 0, 0, 0)),
                original_img,
            ]
        )

        shadow_img = self.make_silhouette(original_img, SHADOW_COLOR, SHADOW_OFFSET)

        silhouette_img = self.layer_images(
            [
                shadow_img,
                self.make_silhouette(original_img, OUTLINE_COLOR, OUTLINE_OFFSET),
                self.make_silhouette(original_img, MAIN_COLOR, (0, 0)),
            ]
        )

        # scale down and up to create some compression/blur effect
        silhouette_img = silhouette_img.resize((150, 150)).resize(silhouette_img.size)

        pokemon_img = self.layer_images(
            [
                shadow_img,
                original_img,
            ]
        )

        pokemon_img = pokemon_img.resize((150, 150)).resize(pokemon_img.size)

        hidden_img = self.layer_images(
            [
                self.background_image,
                silhouette_img,
            ]
        )

        revealed_img = self.layer_images(
            [
                self.background_image,
                pokemon_img,
            ]
        )

        await save_image(hidden_img, hidden_path)
        await save_image(revealed_img, revealed_path)

        log.info(f"Done processing {original_path} [{datetime.now(UTC) - start_time}]")


async def save_image(image: Image.Image, path: Path) -> None:
    # https://stackoverflow.com/a/70308690/10101321

    log.debug(f"Saving {path}")

    extension = path.name.split(".")
    if len(extension) > 1:
        extension = extension[1]
    else:
        extension = None

    buffer = BytesIO()
    image.save(buffer, format=extension)

    async with aiofiles.open(path, "wb") as file:
        await file.write(buffer.getbuffer())
