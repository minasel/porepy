import numpy as np
import scipy.sparse as sps

from porepy.viz.exporter import Exporter

from porepy.grids.grid import FaceTag
from porepy.grids import coarsening as co

from porepy.numerics.vem import vem_dual, vem_source

import example_1_create_grid
import example_1_data

#------------------------------------------------------------------------------#

def main(id_problem, is_coarse=False, tol=1e-5, if_export=False):

    folder_export = "example_1_vem_coarse/"
    file_name_error = folder_export + "vem_error.txt"
    gb = example_1_create_grid.create(0.5/float(id_problem), tol)

    if is_coarse:
        co.coarsen(gb, 'by_tpfa')

    if if_export:
        save = Exporter(gb, "vem", folder_export)

    example_1_data.assign_frac_id(gb)

    internal_flag = FaceTag.FRACTURE
    [g.remove_face_tag_if_tag(FaceTag.BOUNDARY, internal_flag) for g, _ in gb]

    # Assign parameters
    example_1_data.add_data(gb, tol)

    # Choose and define the solvers and coupler
    solver_flow = vem_dual.DualVEMDFN(gb.dim_max(), 'flow')
    A_flow, b_flow = solver_flow.matrix_rhs(gb)

    solver_source = vem_source.IntegralDFN(gb.dim_max(), 'flow')
    A_source, b_source = solver_source.matrix_rhs(gb)

    up = sps.linalg.spsolve(A_flow+A_source, b_flow+b_source)
    solver_flow.split(gb, "up", up)

    gb.add_node_props(["discharge", "p", "P0u", "err"])
    solver_flow.extract_u(gb, "up", "discharge")
    solver_flow.extract_p(gb, "up", "p")
    solver_flow.project_u(gb, "discharge", "P0u")

    only_max_dim = lambda g: g.dim==gb.dim_max()
    diam = gb.diameter(only_max_dim)
    error_pressure = example_1_data.error_pressure(gb, "p")
    error_discharge = example_1_data.error_discharge(gb, "P0u")
    print("h=", diam, "- err(p)=", error_pressure, "- err(P0u)=", error_discharge)

    with open(file_name_error, 'a') as f:
        info = str(gb.num_cells(only_max_dim)) + " " +\
               str(gb.num_cells(only_max_dim)) + " " +\
               str(error_pressure) + " " +\
               str(error_discharge) + " " +\
               str(gb.num_faces(only_max_dim))  + "\n"
        f.write(info)

    if if_export:
        save.write_vtk(["p", "err", "P0u"])

#------------------------------------------------------------------------------#

num_simu = 25
is_coarse = True
if_export = False
for i in np.arange(num_simu):
    main(i+1, is_coarse, if_export=if_export)

#------------------------------------------------------------------------------#