import os
import numpy as np

from PIL import Image
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator

dir_path = os.path.dirname(os.path.realpath(__file__))
with open(f'{dir_path}/words.txt') as f:
    text = ''.join(c if c.isalnum() else ' ' for c in f.read())

stopwords = set(STOPWORDS) | {'may', 'use', 'using', 'takes', 'following'}

wc = WordCloud(
    width=1920,
    height=1080,
    random_state=5,
    stopwords=stopwords,
    collocations=True,
    mode='RGBA',
    prefer_horizontal=0.8,
    max_words=2000,
    background_color='rgba(0, 0, 0, 1)',
    color_func=lambda *args, **kwargs: 'rgba(255, 255, 255, 0)',
    # mask=np.array(Image.open(f'{dir_path}/img/base/logo-fat-mask.png')),
    # colormap='inferno',
    font_path='fonts/Roboto/Roboto-Bold.ttf',
    font_step=2,
    min_font_size=4,
).generate(text)

directory = f'{dir_path}/img/{wc.width}x{wc.height}/'
if not os.path.exists(directory):
    os.makedirs(directory)

if wc.colormap is not None:
    wc.to_file(f'{directory}/{wc.colormap}-wordcloud-colormap.png')

else:
    arr = wc.to_array()
    arr = [
        [
            [0, 0, 0, 255] if tuple(rgba) == (0, 0, 0, 1) else
            [255, 255, 255, 0] if tuple(rgba) == (255, 255, 255, 0) else
            [0, 0, 0, 127]
            for rgba in row
        ] for row in arr
    ]
    arr = np.array([np.array([np.array(rgba) for rgba in row]) for row in arr])

    Image.fromarray(arr.astype(np.uint8))\
        .save(f'{directory}/wordcloud-transparent-raw.png')

# colors = np.array(Image.open(f'{dir_path}/img/base/coloring.png'))
# image_colors = ImageColorGenerator(colors)
# wc.recolor(color_func=image_colors)
# wc.to_file(f'{directory}/wordcloud-mask-coloring.png')
