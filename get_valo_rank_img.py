import os


def get_valo_rank_img(rank_name):
    dir = os.path.dirname(__file__)
    file = os.path.join(dir, f'valoranks/{rank_name}.png')
    with open(file, "rb") as img:
        img_byte = img.read()
        return img_byte
