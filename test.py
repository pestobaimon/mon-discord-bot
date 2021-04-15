import os
from os.path import isfile, join
from valorant_ranks import Rank
onlyfiles = [f[:-4] for f in os.listdir('valoranks') if isfile(join('valoranks', f))]


def get_valo_rank_img(rank_name):
    dir = os.path.dirname(__file__)
    file = os.path.join(dir, f'valoranks/{rank_name}.png')
    with open(file, "rb") as img:
        img_byte = img.read()
        return img_byte

print(onlyfiles)

for rank_name in Rank.__members__.keys():

    print(rank_name)
