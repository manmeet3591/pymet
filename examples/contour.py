# coding:utf-8
import matplotlib.pyplot as plt
from pymet.metplt import MyBasemap
from pymet.io import GradsIO
from datetime import datetime

# read data from OpenDAP
io = GradsIO(Echo=False)
io.open('http://www.esrl.noaa.gov/psd/thredds/dodsC/Datasets/ncep.reanalysis.derived/pressure/hgt.mon.mean.nc')
io.setdim(lon=(0,357.5),lat=(-90,90),lev=500, time=datetime(2010,8,1))

# read data
data = io.get('hgt')
lon, lat = data.grid.latlon()

# close OpenDAP
io.close()

# plot
m = MyBasemap(lon=(0,360), lat=(-90,90), xlint=60, ylint=30)
m.contour(lon, lat, data, cint=100)
plt.title('NCEP-NCAR Reanalysis Z500 Aug2010')

plt.show()
