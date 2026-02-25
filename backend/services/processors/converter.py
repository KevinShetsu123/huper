"""
Module for converting PDF pages to images with page number markers
and base64 encoding.
"""

import logging
import base64
from io import BytesIO
from typing import List
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import fitz
import requests


logger = logging.getLogger(__name__)


class ImageConverter:
    """_summary_"""

    def __init__(self, dpi: int = 300):
        """_summary_

        Args:
            file_url (str): _description_

        Returns:
            _type_: _description_
        """
        self.dpi = dpi

    def get_file_bytes(self, file_url: str):
        """_summary_

        Args:
            file_url (str): _description_

        Returns:
            _type_: _description_
        """

        response = requests.get(file_url, timeout=60)
        if response.status_code == 200:
            return response.content
        else:
            logger.info("Failed to download file: %s", response.status_code)
            return None

    def images_converter(self, pdf_bytes, start_page, end_page):
        """Convert PDF bytes to list of PIL Images using PyMuPDF.

        Args:
            pdf_bytes (bytes): PDF file content as bytes
            start_page (int): First page to convert (1-indexed)
            end_page (int): Last page to convert (1-indexed)

        Returns:
            List[Image.Image]: List of PIL Image objects
        """
        images = []
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

        # Convert to 0-indexed for PyMuPDF
        start_idx = start_page - 1
        end_idx = min(end_page, pdf_document.page_count)

        # Calculate zoom factor from DPI (72 is default PDF DPI)
        zoom = self.dpi / 72
        mat = fitz.Matrix(zoom, zoom)

        for page_num in range(start_idx, end_idx):
            page = pdf_document[page_num]
            pix = page.get_pixmap(matrix=mat)

            # Convert to PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(BytesIO(img_data))
            images.append(img)

        pdf_document.close()
        return images

    def page_number_marker(
        self,
        images: List[Image.Image],
        current_page: int,
    ) -> List[Image.Image]:
        """_summary_

        Args:
            file_url (str): _description_
            current_page (int): _description_

        Returns:
            _type_: _description_
        """

        marked_images = []
        margin_left, margin_bottom = 75, 75
        padding = 20
        for idx, img in enumerate(images):
            actual_page = current_page + idx
            _, height = img.size

            draw = ImageDraw.Draw(img)
            text_tag = f"PAGE: {actual_page}"
            try:
                font = ImageFont.truetype("arial.ttf", 80)
            except (OSError, IOError):
                font = ImageFont.load_default()

            bbox = draw.textbbox((0, 0), text_tag, font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]

            rect_x0 = margin_left
            rect_y0 = height - margin_bottom - h - (padding * 2)
            rect_x1 = rect_x0 + w + (padding * 2)
            rect_y1 = height - margin_bottom

            draw.rectangle([rect_x0, rect_y0, rect_x1, rect_y1], fill="black")
            text_x = rect_x0 + padding
            text_y = rect_y0 + padding - bbox[1]
            draw.text((text_x, text_y), text_tag, fill="white", font=font)
            marked_images.append(img)

        return marked_images

    def image_enhance(
        self,
        images: List[Image.Image],
    ) -> List[Image.Image]:
        """_summary_

        Args:
            file_url (str): _description_

        Returns:
            _type_: _description_
        """

        enhanced_images = []
        for img in images:
            img = img.convert("L")
            img = ImageEnhance.Contrast(img).enhance(1.8)
            enhanced_images.append(img)
        return enhanced_images

    def images_concatenate(self, images: List[Image.Image]) -> Image.Image:
        """Concatenate multiple images vertically into one long image.

        Args:
            images (List[Image.Image]): List of PIL Image objects to
                concatenate

        Returns:
            Image.Image: A single concatenated image
        """
        if not images:
            raise ValueError("No images provided for concatenation")

        total_height = sum(img.height for img in images)
        max_width = max(img.width for img in images)

        concatenated_image = Image.new("L", (max_width, total_height), color=255)
        current_y = 0
        for img in images:
            x_offset = (max_width - img.width) // 2
            concatenated_image.paste(img, (x_offset, current_y))
            current_y += img.height

        return concatenated_image

    def base64_encode(self, images: List[Image.Image]) -> List[str]:
        """_summary_

        Args:
            file_url (str): _description_

        Returns:
            _type_: _description_
        """

        base64_images = []
        for img in images:
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=85)
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            base64_images.append(img_str)
            buffered.close()

        return base64_images
