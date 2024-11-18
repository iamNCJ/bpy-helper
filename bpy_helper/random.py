import math
import random

import numpy as np


def gen_random_pts_around_origin(seed, N, min_dist_to_origin, max_dist_to_origin, min_theta_in_degree,
                                 max_theta_in_degree, z_up=True) -> list:
    """
    Generate random points around the origin

    :param seed: random seed
    :param N: number of points
    :param min_dist_to_origin: minimum distance to the origin
    :param max_dist_to_origin: maximum distance to the origin
    :param min_theta_in_degree: minimum theta in degree
    :param max_theta_in_degree: maximum theta in degree
    :param z_up: if True, z is up, otherwise y is up
    :return: list of point positions
    """

    if seed is not None:
        random.seed(seed)
    ret = []
    for i in range(N):
        phi = 2 * math.pi * random.random()
        theta = math.acos(2.0 * random.random() - 1.0)
        while theta < min_theta_in_degree * np.pi / 180.0 or theta > max_theta_in_degree * math.pi / 180.0:
            theta = math.acos(2.0 * random.random() - 1.0)
        dist = min_dist_to_origin + random.random() * (max_dist_to_origin - min_dist_to_origin)
        pt = [dist * math.sin(theta) * math.cos(phi), dist * math.sin(theta) * math.sin(phi),
              dist * math.cos(theta)]
        if not z_up:
            pt = [pt[0], pt[2], pt[1]]
        ret.append(pt)
    return ret
