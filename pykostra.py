import os
import glob
from pathlib import Path

import pandas as pd
import xarray as xr


__version__ = "0.2.0"


duration_name = "duration"
interval_name = "interval"
lat_vertices = "lat_vertices"
lon_vertices = "lon_vertices"
vertices_dim = "vertices"
lon = "lon"
lat = "lat"
x = "x"
y = "y"

data_vars = ["HN", "HN_KOG"]

xb_points = ["X2_SW_GEO", "X3_SE_GEO", "X4_NE_GEO", "X1_NW_GEO"]
yb_points = ["Y2_SW_GEO", "Y3_SE_GEO", "Y4_NE_GEO", "Y1_NW_GEO"]


def get_geoinfo():
    return pd.read_excel(
        "./raw/KOSTRA-DWD-2010R_geog_Bezug.xlsx",
        sheet_name="Raster_geog_Bezug",
        index_col="index_rc",
        engine="openpyxl",
    )


def parse_duration_level(f):
    """parse duration level from filename f"""
    stem = Path(f).stem
    return stem.split("_")[2]


def kog(f):
    """parse KOG from filename f"""
    stem = Path(f).stem
    try:
        return stem.split("_")[3] == "KOG"
    except:
        return False


def create_table(f, geoinfo):
    """read table and add meta data

    reads a single tables, adds duration level from filename
    and grid info from geoinfo table.

    """
    bounds_cols = xb_points + yb_points
    df = pd.read_csv(f, delimiter=";", index_col="INDEX_RC")
    df[duration_name] = parse_duration_level(f)
    df = df.join(geoinfo[["X_CENT_GEO", "Y_CENT_GEO", "Col", "Row"]])
    df = df.rename(columns={"Col": x, "Row": y, "X_CENT_GEO": lon, "Y_CENT_GEO": lat})
    return df


def add_bounds(ds, geoinfo):
    ds = ds.copy()
    bounds_cols = xb_points + yb_points
    df = geoinfo[["X_CENT_GEO", "Y_CENT_GEO", "Col", "Row"] + bounds_cols]
    df = df.rename(columns={"Col": x, "Row": y, "X_CENT_GEO": lon, "Y_CENT_GEO": lat})
    bnds = df.set_index([y, x]).to_xarray()
    v_lon = xr.concat([bnds[p].squeeze(drop=True) for p in xb_points], dim=vertices_dim)
    v_lat = xr.concat([bnds[p].squeeze(drop=True) for p in yb_points], dim=vertices_dim)
    v_lon.name = lon_vertices
    v_lat.name = lat_vertices
    v_lon.attrs["units"] = "degrees_east"
    v_lat.attrs["units"] = "degrees_north"
    ds[lon].attrs["bounds"] = lon_vertices
    ds[lat].attrs["bounds"] = lat_vertices
    ds[lon_vertices] = v_lon
    ds[lat_vertices] = v_lat
    return ds


def add_coord_attrs(ds):
    ds = ds.copy()
    ds[lon].attrs["long_name"] = "longitude"
    ds[lon].attrs["units"] = "degrees_east"
    ds[lat].attrs["long_name"] = "latitude"
    ds[lat].attrs["units"] = "degrees_north"
    return ds


def to_xarray(df):
    ds = df.set_index([duration_name, y, x]).to_xarray()  # convert to gridded data
    ds = ds.where(ds != -99.9)  # set nans
    ds = ds.assign_coords(
        lon=ds.lon.squeeze(drop=True), lat=ds.lat.squeeze(drop=True)
    )  # .drop(('x', 'y'))
    ds[duration_name] = [int(i[1:]) for i in ds[duration_name].values]
    ds[duration_name].attrs["units"] = "minutes"
    ds = add_coord_attrs(ds)
    return ds


def derive_varname(varname):
    if "KOG" in varname:
        return "HN_KOG"
    elif "HN" in varname:
        return "HN"
    else:
        return None


def interval_coord(data_vars):
    interval = xr.DataArray(
        [int(i[-4:-1]) for i in list(data_vars)], dims=interval_name
    )
    interval.attrs["units"] = "years"
    return interval


def duration_level(ds, numeric=True):
    return


def merge_variables(ds):
    """merge intervals allong interval coordinate"""
    ds = ds.copy()
    data_vars = [v for v in ds.data_vars if derive_varname(v) is not None]
    varname = derive_varname(data_vars[0])
    ds[varname] = xr.concat(
        [ds[var] for var in data_vars], dim=interval_coord(data_vars)
    )
    ds = ds.drop_vars(data_vars)
    ds[varname].attrs = {"long_name": "Bemessungsniederschlagswert", "units": "mm"}
    return ds.transpose(duration_name, interval_name, y, x)


def combine(dsets):
    HN_KOG = xr.concat([ds for ds in dsets if "HN_KOG" in ds], dim=duration_name)
    HN = xr.concat([ds for ds in dsets if "HN" in ds], dim=duration_name)
    # return HN.sortby(HN.duration_level), HN_KOG.sortby(HN_KOG.duration_level)
    return xr.merge([HN, HN_KOG]).sortby(HN[duration_name])


def unzip(f, targetdir):
    """unzip file f to targetdir"""
    import zipfile

    with zipfile.ZipFile(f, "r") as zip_ref:
        zip_ref.extractall(targetdir)


def get_csv_files(raw_dir="./raw", unzip_dir="./unzip"):
    url = os.path.join(raw_dir, "*.zip")
    zip_files = glob.glob(url)
    for f in zip_files:
        unzip(f, unzip_dir)
    return glob.glob(os.path.join(unzip_dir, "*.csv"))


def kostra_to_dataset(csv_files=None, path="raw", bounds=True, encode=True):
    """main function to convert kostra csf files to xarray dataset."""
    geoinfo = get_geoinfo()
    if csv_files is None:
        csv_files = get_csv_files(path)
    tables = [create_table(f, geoinfo) for f in csv_files]
    dsets = [to_xarray(df) for df in tables]
    dsets = [merge_variables(ds) for ds in dsets]
    ds = combine(dsets)
    if bounds is True:
        ds = add_bounds(ds, geoinfo)
    if encode is True:
        return nc_encode(ds)
    return ds


def nc_encode(ds):
    """encode meta data for netcdf"""
    for var in data_vars:
        ds[var].encoding["_FillValue"] = 1.0e20
        # ds[var].encoding["coordinates"] = "{} {}".format(lon, lat)
    for coord in ds.coords.values():
        coord.encoding["_FillValue"] = None
    for coord in [lon_vertices, lat_vertices]:
        ds[coord].encoding = {"_FillValue": None}
    return ds
