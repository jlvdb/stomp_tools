import numpy as np
import stomp


def measure_region_area(mask_path, n_regions, region_idx):
    """
    Measure the area of the i-th region of a given STOMP mask.

    Parameters
    ----------
    mask_path : str
        File path of STOMP mask.
    n_regions : int
        Number of STOMP mask regions.
    region_idx : int
        i-th region index, must be in range [0, n_regions).

    Returns
    -------
    area : float
        Area of the i-th region in square degrees.
    """
    # initialize the region mask
    master_mask = stomp.Map(mask_path)
    master_mask.InitializeRegions(n_regions)
    region_mask = stomp.Map()
    master_mask.RegionOnlyMap(region_idx, region_mask)
    # get the region area
    area = region_mask.Area()
    del master_mask, region_mask
    return area


def regionize_data(mask_path, n_regions, RA, DEC):
    """
    Assign data objects to the regions of a given STOMP mask based on their
    right ascension / declination.

    Parameters
    ----------
    mask_path : str
        File path of STOMP mask.
    n_regions : int
        Number of STOMP mask regions.
    RA : array_like
        Right ascension in degrees.
    DEC : array_like
        Declination in degrees.

    Returns
    -------
    area : array
        List of N region indices in range [0, n_regions) indicating the region
        membership of the objects. If index == -1, the object falls outside the
        mask footprint.
    """
    # load mask
    stomp_mask = stomp.Map(mask_path)
    stomp_mask.InitializeRegions(n_regions)
    # check for every object in which stomp region it falls
    region_idx = np.empty(len(RA), dtype=np.int16)
    for i, (ra, dec) in enumerate(zip(RA, DEC)):
        ang = stomp.AngularCoordinate(
            ra, dec, stomp.AngularCoordinate.Equatorial)
        # first we must check whether the object falls into the mask at all,
        # since regions may extend over the mask bounds
        if stomp_mask.Contains(ang):
            region_idx[i] = stomp_mask.FindRegion(ang)
        else:
            region_idx[i] = -1
    del stomp_mask
    return region_idx
