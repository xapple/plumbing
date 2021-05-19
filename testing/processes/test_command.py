# Built-in module #

# Internal modules #
from plumbing.processes import prll_map

def add(xy):
    x,y = xy
    return x+y

inputs = [(5,5), (2,2), (20,30)]

results = prll_map(add, inputs)

print(results)