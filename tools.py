import os
import sys
from contextlib import contextmanager

import numpy as np
import pandas as pd
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


def regionize_data(mask_path, n_regions, data):
    """
    Assign data objects to the regions of a given STOMP mask based on their
    right ascension / declination.

    Parameters
    ----------
    mask_path : str
        File path of STOMP mask.
    n_regions : int
        Number of STOMP mask regions.
    data : array_like or pandas.DataFrame
        Must of array of shape (Nx2) with N entries of type (RA, DEC) or a
        pandas DataFrame with columns RA and DEC, angles given in degrees.

    Returns
    -------
    area : array
        List of N region indices in range [0, n_regions) indicating the region
        membership of the objects. If index == -1, the object falls outside the
        mask footprint.
    """
    try:  # if data is a pandas.DataFrame
        RA = data.RA
        DEC = data.DEC
    except AttributeError:  # if data is a Nx2 np.ndarray
        RA, DEC = data.T
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


def generate_randoms(mask_path, n_randoms):
    """
    Generate a sample of uniformly distributed objects on a STOMP mask.

    Parameters
    ----------
    mask_path : str
        File path of STOMP mask.
    n_randoms : int
        Number of random points to generate.

    Returns
    -------
    area : pandas.DataFrame
        Data frame with columns RA (right ascension, in degrees) and DEC
        (declination, in degrees) of the random objects.
    """
    # use the stomp methods to generate uniform random points
    stomp_map = stomp.Map(mask_path)
    random_vector = stomp.AngularVector()
    stomp_map.GenerateRandomPoints(random_vector, int(n_randoms))
    # convert to numpy array
    RA = np.asarray([rand.RA() for rand in random_vector.iterator()])
    DEC = np.asarray([rand.DEC() for rand in random_vector.iterator()])
    randoms = pd.DataFrame({"RA": RA, "DEC": DEC})
    del stomp_map, random_vector
    return randoms


def adapt_mask(RA, DEC, resolution):
    """
    Adapt a STOMP pixel mask from a vector of right ascensions and declinations
    at a given mask resolution. Creates new pixel for each position until
    all objects are covered.

    Parameters
    ----------
    RA : array_like
        List of right ascensions in degrees.
    DEC : array_like
        List of declinations in degrees.
    resolution : int
        Mask resolution (powers of 2 between 2 and 32768).

    Returns
    -------
    mask : stomp.Map
        STOMP pixel mask derived from the input data geometry.
    """
    assert(len(RA) == len(DEC))
    # create pixels for each object and convert them into a pixel map
    pix_vect = stomp.PixelVector()
    iterator = zip(
        np.asarray(RA, dtype=np.double),
        np.asarray(DEC, dtype=np.double))
    for RA, DEC in iterator:
        ang = stomp.AngularCoordinate(
            RA, DEC, stomp.AngularCoordinate.Equatorial)
        pix_vect.push_back(stomp.Pixel(ang, resolution, 1.0))
    # create the final map
    mask = stomp.Map()
    mask.IngestMap(pix_vect)
    return mask


def apply_mask(RA, DEC, map_path):
    """
    Adapt a STOMP pixel mask from a vector of right ascensions and declinations
    at a given mask resolution. Creates new pixel for each position until
    all objects are covered.

    Parameters
    ----------
    RA : array_like
        List of right ascensions in degrees.
    DEC : array_like
        List of declinations in degrees.
    map_path : string
        Stomp map file path to load from. The map cannot be parsed as object
        because objects wrapped with SWIG cannot be pickled, however this
        function must support multiprocessing.

    Returns
    -------
    mask : array_like of bools
        Boolean mask indicated whether an input object lies within the mask
        footprint.
    """
    assert(len(RA) == len(DEC))
    smap = stomp.Map(map_path)
    # check if objects fall within the mask
    mask = np.empty(len(RA), dtype="bool")
    iterator = zip(
        np.asarray(RA, dtype=np.double),
        np.asarray(DEC, dtype=np.double))
    for i, (ra, dec) in enumerate(iterator):
        new_obj = stomp.WeightedAngularCoordinate(
            ra, dec, 1.0, stomp.AngularCoordinate.Equatorial)
        mask[i] = smap.Contains(new_obj)
    return mask


@contextmanager
def stdout_redirected(dst=os.devnull):
    """
    Redirect all output from stdout temporarily to a file descriptor within the
    context manager.

    Parameters
    ----------
    dst : file descriptor
        File descriptor to which stdout is redirected (defaults to /dev/null).
    """

    term = sys.stdout.fileno()

    def redirect(dst):
        sys.stdout.close()
        os.dup2(dst.fileno(), term)  # redirects non-python output
        sys.stdout = os.fdopen(term, 'w')  # keep python on stdout

    with os.fdopen(os.dup(term), 'w') as term_restore:
        with open(dst, 'w') as file:
            redirect(file)
        try:
            yield
        finally:  # restore
            redirect(term_restore)


@contextmanager
def stderr_redirected(dst=os.devnull):
    """
    Redirect all output from stderr temporarily to a file descriptor within the
    context manager.

    Parameters
    ----------
    dst : file descriptor
        File descriptor to which stderr is redirected (defaults to /dev/null).
    """

    term = sys.stderr.fileno()

    def redirect(dst):
        sys.stderr.close()
        os.dup2(dst.fileno(), term)  # redirects non-python output
        sys.stderr = os.fdopen(term, 'w')  # keep python on stderr

    with os.fdopen(os.dup(term), 'w') as term_restore:
        with open(dst, 'w') as file:
            redirect(file)
        try:
            yield
        finally:  # restore
            redirect(term_restore)
