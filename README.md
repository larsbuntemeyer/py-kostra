# py-kostra

Convert [DWD-KOSTRA](https://www.dwd.de/DE/leistungen/kostra_dwd_rasterwerte/kostra_dwd_rasterwerte.html) data to `xarray` (including download).

The original DWD-KOSTRA dataset contains of a number of csv tables and additional grid definitions in excel tables.
This repository contains the python module `pykostra` which let's you easily convert thos csv tables of the DWD-KOSTRA dataset to xarray.
It supposed to create an analysis ready dataset for easy exploration of the KOSTRA dataset. 
For further scientific information, please consult the official documentation.

To see how it works, just click the binder button!

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/larsbuntemeyer/py-kostra/master?urlpath=lab%2Ftree%2Fkostra-to-xarray.ipynb)


## Requirements

There is an conda environmnet file in the `.binder` subdirectory, which you can use to create an environment. However, the requirements are quite basic. You only need:

* xarray
* pandas
* openpyxl (for letting pandas read excel)
* bs4 (for download)
* matplotlib (for plotting) 
