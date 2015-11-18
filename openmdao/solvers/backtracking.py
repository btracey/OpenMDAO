""" Line search using backtracking."""

from openmdao.solvers.solver_base import LineSearch
from openmdao.util.record_util import update_local_meta, create_local_meta


class BackTracking(LineSearch):
    """A line search subsolver using backtracking.

    Options
    -------
    options['iprint'] :  int(0)
        Set to 0 to disable printing, set to 1 to print the residual to stdout
        each iteration, set to 2 to print subiteration residuals as well.
    options['atol'] :  float(1e-10)
        Absolute convergence tolerancee for line search.
    options['maxiter'] :  int(10)
        Maximum number of line searches.
    options['rtol'] :  float(0.9)
        Relative convergence tolerancee for line search.
    options['solve_subsystems'] :  bool(True)
        Set to True to solve subsystems. You may need this for solvers nested under Newton.
    """

    def __init__(self):
        super(BackTracking, self).__init__()

        opt = self.options
        opt.add_option('atol', 1e-10, lower=0.0,
                       desc='Absolute convergence tolerancee for line search.')
        opt.add_option('rtol', 0.9, lower=0.0,
                       desc='Relative convergence tolerancee for line search.')
        opt.add_option('maxiter', 10, lower=0,
                       desc='Maximum number of line searches.')
        opt.add_option('solve_subsystems', True,
                       desc='Set to True to solve subsystems. You may need this for solvers nested under Newton.')

    def solve(self, params, unknowns, resids, system, solver, alpha, fnorm,
              fnorm0, metadata=None):
        """ Take the gradient calculated by the parent solver and figure out
        how far to go.

        Args
        ----
        params : `VecWrapper`
            `VecWrapper` containing parameters. (p)

        unknowns : `VecWrapper`
            `VecWrapper` containing outputs and states. (u)

        resids : `VecWrapper`
            `VecWrapper` containing residuals. (r)

        system : `System`
            Parent `System` object.

        metadata : dict, optional
            Dictionary containing execution metadata (e.g. iteration coordinate).

        solver : `Solver`
            Parent solver instance.

        alpha : float
            Initial over-relaxation factor as used in parent solver.

        fnorm : float
            Initial norm of the residual for absolute tolerance check.

        fnorm0 : float
            Initial norm of the residual for relative tolerance check.
        """

        atol = self.options['atol']
        rtol = self.options['rtol']
        maxiter = self.options['maxiter']
        result = system.dumat[None]

        local_meta = create_local_meta(metadata, system.pathname)
        itercount = 0
        ls_alpha = alpha

        # Backtracking Line Search
        while itercount < maxiter and \
              fnorm > atol and \
              fnorm/fnorm0 > rtol:

            ls_alpha *= 0.5
            unknowns.vec -= ls_alpha*result.vec
            itercount += 1

            # Metadata update
            update_local_meta(local_meta, (solver.iter_count, itercount))

            # Just evaluate the model with the new points
            if self.options['solve_subsystems'] is True:
                system.children_solve_nonlinear(local_meta)
            system.apply_nonlinear(params, unknowns, resids, local_meta)

            solver.recorders.record_iteration(system, local_meta)

            fnorm = resids.norm()
            if self.options['iprint'] > 0:
                self.print_norm('BK_TKG', system.pathname, itercount, fnorm,
                                fnorm0, indent=1, solver='LS')