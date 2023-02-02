import numpy as np
import glob
import scipy
from scipy.io import savemat
import os

npyfile = glob.glob('*.npy')
for f in npyfile:
	fm = os.path.splitext(f)[0] + '.mat'
	d = np.load(f)
	# savemat(fm, {"data": d})
	print('generated', fm, 'from', f)
