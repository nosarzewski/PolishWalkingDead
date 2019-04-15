# -*- coding: utf-8 -*-
# !/usr/bin/env python3

from pylab import *
from descartes import PolygonPatch
from itertools import product
import csv
import numpy as np
import shapefile


# functions
def set_color(p):
    x = int(((p - p_min) / p_max) * 245 + 5)
    return '#%02x%02x%02x' % (255, 255 - x, 255 - x)


def set_color_g(p):
    x = int(((p - p_min) / p_max) * 245 + 5)
    return x


def reverse_color(p, d):
    if p in d.keys():
        return d[p]
    else:
        return 0


# constants
shp_file = "powiaty"
people_file = "./pop_data.csv"

p_max = 1744351
p_min = 20606
p_max = p_max - p_min

# convert data about people to dictionary with index as GUS_ID
people_file = open(people_file, "r")
reader = csv.DictReader(people_file, delimiter=";")

county_pop_data = {}
people_to_color = {}

for row in reader:
    id = row['id']
    county_pop_data[id] = row['ludnosc']
    if 255 - set_color_g(int(row['ludnosc'])) in people_to_color.keys():
        people_to_color[255 - set_color_g(int(row['ludnosc']))] += int(row['ludnosc'])
    else:
        people_to_color[255 - set_color_g(int(row['ludnosc']))] = int(row['ludnosc'])

people_file.close()
sf = shapefile.Reader(shp_file)

fig = plt.figure(figsize=(9.6, 9.6))
ax = fig.gca()

# turn the polygons into colored-shapes
for polygon in sf.shapeRecords():
    color = set_color(int(county_pop_data[polygon.record[4]]))
    poly = polygon.shape.__geo_interface__
    ax.add_patch(PolygonPatch(poly, fc=color, ec=color, alpha=1, zorder=2))

ax.axis('scaled')
fig.canvas.draw()

# save the map
data = np.fromstring(fig.canvas.tostring_rgb(), dtype=np.uint8, sep='')
data = data.reshape(960, 960, 3)
plt.savefig("map.png", dpi=100)
fig.clear()

# crap unncessary data
data_crop = data.copy()
data_crop = np.delete(data_crop, range(801, 961), 0)
data_crop = np.delete(data_crop, range(841, 961), 1)
data_crop = np.delete(data_crop, range(0, 160), 0)
data_crop = np.delete(data_crop, range(0, 160), 1)

# remove data from outside Poland => turn it black
x, y, z = data_crop.shape
empty_space = np.array([0, 0, 0])
for pos in product(range(x - 1), range(y - 1)):
    if np.array_equal(data_crop[pos], [255, 255, 255]):
        # print("{} => {}".format(pos, data_crop[pos]))
        data_crop[pos] = empty_space.copy()

map_colored = data_crop.copy()
map_values = np.zeros([x, y], dtype=np.int)

# recalculate population per grid-point
population_counts = {}
for pos in product(range(x - 1), range(y - 1)):
    if not np.array_equal(map_colored[pos], [255, 255, 255]):
        if reverse_color(map_colored[pos][2], people_to_color) not in population_counts.keys():
            population_counts[reverse_color(map_colored[pos][2], people_to_color)] = 1
        else:
            population_counts[reverse_color(map_colored[pos][2], people_to_color)] += 1

for pos in product(range(x - 1), range(y - 1)):
    if not np.array_equal(map_colored[pos], [255, 255, 255]):
        map_values[pos] = int(reverse_color(map_colored[pos][2], people_to_color) / population_counts[
            reverse_color(map_colored[pos][2], people_to_color)])
    elif np.array_equal(map_colored[pos], [255, 255, 255]):
        map_values[pos] = 0
    else:
        print(int(reverse_color(map_colored[pos][2], people_to_color) / population_counts[
            reverse_color(map_colored[pos][2], people_to_color)]))
        map_values[pos] = 0

# save data for the simulation
with open('map_colored.out', 'wb') as mc, open('map_values.out', 'wb') as mv:
    np.save(mc, map_colored)
    np.save(mv, map_values)
