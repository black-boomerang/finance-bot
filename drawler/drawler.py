# Класс отвечающий за создание изображений
import typing as tp

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


class Drawler:
    @staticmethod
    def _text_size(text, text_font) -> (int, int):
        """
        Вычисляет размер рамки с текстом
        """
        width = text_font.getmask(text).getbbox()[2]
        height = text_font.getmask(text).getbbox()[3]
        return height, width

    @staticmethod
    def draw_table(table: pd.DataFrame,
                   colors_dict: tp.Dict[str, tp.Tuple[int]],
                   height: int,
                   width: int) -> Image:
        """
        Создаёт изображение таблицы с возможностью задания цветов для
        каждой строки
        """
        image = Image.new('RGBA', (width - 1, height - 1), (255, 255, 255, 255))
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype("arial.ttf", 24)

        color_by_row = dict()
        for color, rows in colors_dict.items():
            for row in rows:
                color_by_row[row] = color

        rows_count, columns_count = table.shape
        cell_height = height / (rows_count + 1)
        cell_width = width / columns_count
        for row in range(rows_count + 1):
            font_color = '#ffffff' if row == 0 else '#000000'
            for column in range(columns_count):
                draw.rectangle((column * cell_width,
                                row * cell_height,
                                (column + 1) * cell_width - 2,
                                (row + 1) * cell_height - 2),
                               fill=color_by_row[row])

                if row == 0:
                    text = table.columns[column]
                else:
                    text = str(table.iloc[row - 1, column])
                text_height, text_width = Drawler._text_size(text, font)

                x = column * cell_width + 7
                y = row * cell_height + cell_height / 2 - text_height / 2 - 7
                draw.text((x, y), text, font=font, fill=font_color)

        return image
