import numpy as np

arr = np.array([3, 4, 5, 6, 7,10])

is_consecutive = np.all(np.diff(arr) == 1)

print(is_consecutive)