# %% Imports
import roifile # pip install -U roifile tifffile
import numpy as np
# %% Load ROI csv
hms_roi = np.loadtxt('hitmis_roi.csv', dtype=float, delimiter=',').transpose()
names = np.asarray(hms_roi[1,:]*10, dtype=int)
x = l = np.asarray(hms_roi[2,:], dtype=int)
y = t = np.asarray(hms_roi[3,:], dtype=int)
w = np.asarray(hms_roi[4,:], dtype=int)
h = np.asarray(hms_roi[5,:], dtype=int)
r = l + w
b = t + h
# %%
for idx, wl in enumerate(names):
    roi = roifile.ImagejRoi(roitype=roifile.ROI_TYPE.RECT, left=l[idx], right=r[idx], top=t[idx], bottom=b[idx], name=str(wl))
    roi.tofile('%04d.roi'%(wl))
# %%
