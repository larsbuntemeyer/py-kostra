from download import get_raw

get_raw()

import pykostra as pyk

ds = pyk.kostra_to_dataset()
ds.to_netcdf("kostra.nc")
