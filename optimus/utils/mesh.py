"""Get mesh statistics and scale mesh elements."""

import bempp.api as _bempp
from ..geometry.common import Geometry as _Geometry
from .conversions import convert_to_float as _convert_to_float
import numpy as _np


def _get_mesh_stats(grid, verbose=False):
    """Compute the minimum, maximum, median, mean and standard deviation of
    mesh elements for a grid object.

    Parameters
    ----------
    grid : bempp.api.Grid
        The surface grid.
    verbose: boolean
        Print the results.

    Returns
    -------
    stats : dict
        The mesh statistics.
    """

    elements = list(grid.leaf_view.entity_iterator(0))
    element_size = [
        _np.sqrt(
            (
                (
                    element.geometry.corners
                    - _np.roll(element.geometry.corners, 1, axis=1)
                )
                ** 2
            ).sum(axis=0)
        )
        for element in elements
    ]
    elements_min = _np.min(element_size)
    elements_max = _np.max(element_size)
    elements_avg = _np.mean(element_size)
    elements_med = _np.median(element_size)
    elements_std = _np.std(element_size)
    number_of_nodes = grid.leaf_view.entity_count(2)

    if verbose:
        print("\n", 70 * "*")
        print("Number of nodes: {0}.\n".format(number_of_nodes))
        print(
            "Statistics about the element size in the triangular surface grid:\n"
            " Min: {0:.2e}\n Max: {1:.2e}\n AVG: {2:.2e}\n"
            " MED: {3:.2e}\n STD: {4:.2e}\n".format(
                elements_min, elements_max, elements_avg, elements_med, elements_std
            )
        )
        print("\n", 70 * "*")

    return {
        "elements_min": elements_min,
        "elements_max": elements_max,
        "elements_avg": elements_avg,
        "elements_med": elements_med,
        "elements_std": elements_std,
        "number_of_nodes": number_of_nodes,
    }


def get_geometries_stats(geometries, verbose=False):
    """Compute the minimum, maximum, median, mean and standard deviation of
    mesh elements for optimus Geometries.

    Parameters
    ----------
    geometries : optimus.geometry.common.Geometry, tuple[optimus.geometry.common.Geometry]
        The Optimus geometry object(s).
    verbose: boolean
        Print the results.

    Returns
    -------
    stats : dict
        The mesh statistics.
    """

    if isinstance(geometries, (list, tuple)):
        labels = []
        elements_min = []
        elements_max = []
        elements_avg = []
        elements_med = []
        elements_std = []
        number_of_nodes = []

        for geometry in geometries:
            labels.append(geometry.label)
            stats = _get_mesh_stats(geometry.grid, verbose=False)
            elements_min.append(stats["elements_min"])
            elements_max.append(stats["elements_max"])
            elements_avg.append(stats["elements_avg"])
            elements_med.append(stats["elements_med"])
            elements_std.append(stats["elements_std"])
            number_of_nodes.append(stats["number_of_nodes"])
        total_number_of_nodes = _np.sum(number_of_nodes)

        stats_total = {
            "label": labels,
            "elements_min": elements_min,
            "elements_max": elements_max,
            "elements_avg": elements_avg,
            "elements_med": elements_med,
            "elements_std": elements_std,
            "number_of_nodes": number_of_nodes,
        }

        if verbose:
            print("\n", 70 * "*")
            for i, geometry in enumerate(geometries):
                print(
                    "Number of nodes in geometry '{0}' is {1}.\n".format(
                        labels[i], number_of_nodes[i]
                    )
                )
                print(
                    (
                        "Statistics about the element size in the triangular surface "
                        "grid of geometry '{0}':\n"
                        " Min: {1:.2e}\n Max: {2:.2e}\n AVG: {3:.2e}\n"
                        " MED: {4:.2e}\n STD: {5:.2e}\n"
                    ).format(
                        labels[i],
                        elements_min[i],
                        elements_max[i],
                        elements_avg[i],
                        elements_med[i],
                        elements_std[i],
                    )
                )
            print(
                "The total number of nodes in all geometries is {0}.".format(
                    total_number_of_nodes
                )
            )
            print("\n", 70 * "*")
    else:
        stats_total = _get_mesh_stats(geometries.grid, verbose=verbose)

    return stats_total


def scale_mesh(geometry, scaling_factor):
    """Scale the entire geometry with a multiplicative factor.

    The connectivity of the mesh remains intact and the scaling is with respect
    to the global origin as defined in the mesh.

    Parameters
    ----------
    geometry: optimus.geometry.common.Geometry
        The geometry to scale.
    scaling_factor : float
        Scaling factor for the grid.

    Returns
    -------
    geometry: optimus.geometry.common.Geometry
        A new, scaled geometry.
    """

    scaling = _convert_to_float(scaling_factor, "mesh scaling factor")
    new_vertices = geometry.grid.leaf_view.vertices * scaling
    new_grid = _bempp.grid_from_element_data(
        new_vertices,
        geometry.grid.leaf_view.elements,
        geometry.grid.leaf_view.domain_indices,
    )
    return _Geometry(new_grid, label=geometry.label + "_scaled")


def translate_mesh(geometry, translation_vector):
    """
    Translate the entire geometry with an additive vector.

    The connectivity of the mesh remains intact.

    Parameters
    ----------
    geometry: optimus.geometry.common.Geometry
        The geometry to translate.
    translation_vector : numpy.ndarray
        A 3D vector to translate the grid.

    Returns
    -------
    geometry: optimus.geometry.common.Geometry
        A new, translated geometry.
    """
    from ..utils.conversions import convert_to_array

    translation = convert_to_array(translation_vector, (3, 1), "translation vector")
    new_vertices = geometry.grid.leaf_view.vertices + translation
    new_grid = _bempp.grid.grid_from_element_data(
        new_vertices,
        geometry.grid.leaf_view.elements,
        geometry.grid.leaf_view.domain_indices,
    )
    return _Geometry(new_grid, label=geometry.label + "_translated")


def rotate_mesh(geometry, rotation_angles):
    """
    Rotate the entire geometry by the rotation angles.

    The connectivity of the mesh remains intact.

    Parameters
    ----------
    geometry: optimus.geometry.common.Geometry
        The geometry to rotate.
    rotation_angles : list[float]
        The three rotation angles (x, y, z).

    Returns
    -------
    geometry: optimus.geometry.common.Geometry
        A new, rotated geometry.
    """

    if len(rotation_angles) != 3:
        raise ValueError(
            "The input angles must be a list of three floats, "
            "the three rotation angles (x,y,z)"
        )

    alpha, beta, gamma = rotation_angles
    rotation_matrix_x = _np.array(
        [
            [1, 0, 0],
            [0, _np.cos(alpha), -_np.sin(alpha)],
            [0, _np.sin(alpha), _np.cos(alpha)],
        ]
    )
    rotation_matrix_y = _np.array(
        [
            [_np.cos(beta), 0, _np.sin(beta)],
            [0, 1, 0],
            [-_np.sin(beta), 0, _np.cos(beta)],
        ]
    )
    rotation_matrix_z = _np.array(
        [
            [_np.cos(gamma), -_np.sin(gamma), 0],
            [_np.sin(gamma), _np.cos(gamma), 0],
            [0, 0, 1],
        ]
    )

    old_vertices = geometry.grid.leaf_view.vertices
    new_vertices = (
        rotation_matrix_z @ rotation_matrix_y @ rotation_matrix_x @ old_vertices
    )

    new_grid = _bempp.grid.grid_from_element_data(
        new_vertices,
        geometry.grid.leaf_view.elements,
        geometry.grid.leaf_view.domain_indices,
    )
    return _Geometry(new_grid, label=geometry.label + "_rotated")


def rotate_mesh_around_center(geometry, rotation_angles):
    """
    Rotate the entire geometry by the rotation angles around its center.

    The connectivity of the mesh remains intact.

    Parameters
    ----------
    geometry: optimus.geometry.common.Geometry
        The geometry to rotate.
    rotation_angles : list[float]
        The three rotation angles (x, y, z).

    Returns
    -------
    geometry: optimus.geometry.common.Geometry
        A new, rotated geometry.
    """
    origin = [
        (geometry.grid.bounding_box[0][0] + geometry.grid.bounding_box[1][0]) / 2,
        (geometry.grid.bounding_box[0][1] + geometry.grid.bounding_box[1][1]) / 2,
        (geometry.grid.bounding_box[0][2] + geometry.grid.bounding_box[1][2]) / 2,
    ]
    first_translation = translate_mesh(geometry, [-x for x in origin])
    rotation = rotate_mesh(first_translation, rotation_angles)
    new_geometry = translate_mesh(rotation, origin)
    new_geometry.label = new_geometry.label[:-29] + "rotated_around_center"

    return new_geometry


def msh_from_string(geo_string):
    """Create a mesh from a string."""

    import os
    import subprocess

    gmsh_command = _bempp.GMSH_PATH
    if gmsh_command is None:
        raise RuntimeError("Gmsh is not found. Cannot generate mesh")

    import tempfile

    geo, geo_name = tempfile.mkstemp(suffix=".geo", dir=_bempp.TMP_PATH, text=True)
    geo_file = os.fdopen(geo, "w")
    msh_name = os.path.splitext(geo_name)[0] + ".msh"

    geo_file.write(geo_string)
    geo_file.close()

    fnull = open(os.devnull, "w")
    cmd = gmsh_command + " -2 " + geo_name
    try:
        subprocess.check_call(cmd, shell=True, stdout=fnull, stderr=fnull)
    except:
        print("The following command failed: " + cmd)
        fnull.close()
        raise
    os.remove(geo_name)
    fnull.close()
    return msh_name


def generate_grid_from_geo_string(geo_string):
    """Helper routine that implements the grid generation"""

    import os

    msh_name = msh_from_string(geo_string)
    grid = _bempp.import_grid(msh_name)
    os.remove(msh_name)
    return grid


def plane_grid(x_axis_lims, y_axis_lims, rotation_axis, rotation_angle, element_size):
    """Return a 2D square shaped plane.

    Parameters
    ----------
    x_axis_lims : tuple[float], list[float]
        A list of length two for the bounding values along the x-axis of plane.
    y_axis_lims : tuple[float], list[float]
        A list of length two for the bounding values along the y-axis of plane.
    rotation_axis : tuple[int], list[int]
        A list of length three populated with 0 or 1.
        It defines the axis of rotation so to construct the desired plane
        from an x-y plane.
    rotation_angle : str
        The angle of rotation.
    element_size : float
        Element size.

    Returns
    -------
    grid : bempp.api.Grid
        The triangular mesh on the plane.
    """

    stub = """
    Point(1) = {ax1_lim1, ax2_lim1, 0, cl};
    Point(2) = {ax1_lim2, ax2_lim1, 0, cl};
    Point(3) = {ax1_lim2, ax2_lim2, 0, cl};
    Point(4) = {ax1_lim1, ax2_lim2, 0, cl};
    Line(1) = {1, 2};
    Line(2) = {2, 3};
    Line(3) = {3, 4};
    Line(4) = {4, 1};
    Line Loop(1) = {1, 2, 3, 4};
    Plane Surface(2) = {1};
    Rotate {{rot_ax1, rot_ax2, rot_ax3}, {0, 0, 0}, rot_ang_rad} { Surface{2}; }
    Mesh.Algorithm = 2;
    """
    import sys

    if sys.version_info.major >= 3 and sys.version_info.minor >= 6:
        return
    else:
        geometry = (
            "ax1_lim1 = "
            + str(x_axis_lims[0])
            + ";\n"
            + "ax1_lim2 = "
            + str(x_axis_lims[1])
            + ";\n"
            + "ax2_lim1 = "
            + str(y_axis_lims[0])
            + ";\n"
            + "ax2_lim2 = "
            + str(y_axis_lims[1])
            + ";\n"
            + "rot_ax1 = "
            + str(rotation_axis[0])
            + ";\n"
            + "rot_ax2 = "
            + str(rotation_axis[1])
            + ";\n"
            + "rot_ax3 = "
            + str(rotation_axis[2])
            + ";\n"
            + "rot_ang_rad = "
            + rotation_angle
            + ";\n"
            + "cl = "
            + str(element_size)
            + ";\n"
            + stub
        )
        return generate_grid_from_geo_string(geometry)


def create_grid_points(resolution, plane_axes, plane_offset, bounding_box, mode):
    """Create a grid on a plane, either with Numpy or Gmsh.

    Parameters
    ----------
    resolution : list[int], tuple[int]
        The number of visualisation points along the plane axes.
    plane_axes : list[int], tuple[int]
        The labels of the plane axes (0,1,2).
    plane_offset : float
        The offset of the plane in perpendicular direction.
    bounding_box : list[float], tuple[float]
        Restricting the plane to the bounding box.
    mode : str
        The algorithm to create a visualisation plane.
        Options: "numpy", "gmsh".

    Returns
    -------
    points : numpy.ndarray
        The visualisation points.
    plane : Any
        The grid, with format depending on the algorithm.
    """

    from ..utils.generic import bold_ul_text

    ax1_min, ax1_max, ax2_min, ax2_max = bounding_box
    if mode.lower() == "numpy":
        plot_grid = _np.mgrid[
            ax1_min : ax1_max : resolution[0] * 1j,
            ax2_min : ax2_max : resolution[1] * 1j,
        ]
        points_tmp = [_np.ones(plot_grid[0].size) * plane_offset] * 3
        points_tmp[plane_axes[0]] = plot_grid[0].ravel()
        points_tmp[plane_axes[1]] = plot_grid[1].ravel()
        points = _np.vstack((points_tmp,))
        plane = None

    elif mode.lower() == "gmsh":
        if 2 not in plane_axes:
            axis1_lims = bounding_box[0:2]
            axis2_lims = bounding_box[2:]
            rotation_axis = [0, 0, 1]
            rotation_angle = "2*Pi"
        elif 1 not in plane_axes:
            axis1_lims = bounding_box[0:2]
            axis2_lims = bounding_box[2:]
            rotation_axis = [1, 0, 0]
            rotation_angle = "Pi/2"
        elif 0 not in plane_axes:
            axis1_lims = bounding_box[2:]
            axis2_lims = bounding_box[0:2]
            rotation_axis = [0, 1, 0]
            rotation_angle = "-Pi/2"
        else:
            raise ValueError("Plane axis not correctly defined.")

        elem_len = _np.min(
            [
                (axis1_lims[1] - axis1_lims[0]) / resolution[0],
                (axis2_lims[1] - axis2_lims[0]) / resolution[1],
            ]
        )

        plane = plane_grid(
            axis1_lims, axis2_lims, rotation_axis, rotation_angle, elem_len
        )
        points = plane.leaf_view.vertices
    else:
        raise TypeError(
            "The correct values for the argument"
            + bold_ul_text("mode")
            + "are numpy or gmsh."
        )

    return points, plane
