import os
from collections import defaultdict

from dimod import BINARY, INTEGER, ConstrainedQuadraticModel, sym
from tabulate import tabulate


def print_cqm_stats(cqm: ConstrainedQuadraticModel) -> None:
    """Print some information about the CQM model

    Args:
        cqm: a dimod cqm model (dimod.cqm)

    """
    if not isinstance(cqm, ConstrainedQuadraticModel):
        raise ValueError("input instance should be a dimod CQM model")
    num_binaries = sum(cqm.vartype(v) is BINARY for v in cqm.variables)
    num_integers = sum(cqm.vartype(v) is INTEGER for v in cqm.variables)
    num_discretes = len(cqm.discrete)
    num_linear_constraints = sum(
        constraint.lhs.is_linear() for constraint in cqm.constraints.values()
    )
    num_quadratic_constraints = sum(
        not constraint.lhs.is_linear() for constraint in cqm.constraints.values()
    )
    num_le_inequality_constraints = sum(
        constraint.sense is sym.Sense.Le for constraint in cqm.constraints.values()
    )
    num_ge_inequality_constraints = sum(
        constraint.sense is sym.Sense.Ge for constraint in cqm.constraints.values()
    )
    num_equality_constraints = sum(
        constraint.sense is sym.Sense.Eq for constraint in cqm.constraints.values()
    )

    assert num_binaries + num_integers == len(cqm.variables)

    assert num_quadratic_constraints + num_linear_constraints == len(cqm.constraints)

    print(" \n" + "=" * 25 + "MODEL INFORMATION" + "=" * 25)
    print(" " * 10 + "Variables" + " " * 10 + "Constraints" + " " * 15 + "Sensitivity")
    print("-" * 20 + " " + "-" * 28 + " " + "-" * 18)

    print(
        tabulate(
            [
                ["Binary", "Integer", "Quad", "Linear", "One-hot", "EQ  ", "LT", "GT"],
                [
                    num_binaries,
                    num_integers,
                    num_quadratic_constraints,
                    num_linear_constraints,
                    num_discretes,
                    num_equality_constraints,
                    num_le_inequality_constraints,
                    num_ge_inequality_constraints,
                ],
            ],
            headers="firstrow",
        )
    )


def read_instance(instance_path: str) -> dict:
    """A method that reads input instance file

    Args:
        instance_path:  path to the job shop instance file

    Returns:
        Job_dict: dictionary containing jobs as keys and a list of tuple of
                machines and their processing time as values.
    """
    job_dict = defaultdict(list)

    with open(instance_path) as f:
        for i, line in enumerate(f):
            if i == 0:
                num_jobs = int(line.split()[-1])
            elif i == 1:
                num_machines = int(line.split()[-1])
            elif 2 <= i <= 4:
                continue
            else:
                job_task = list(map(int, line.split()))
                job_dict[i - 5] = [
                    x
                    for x in zip(job_task[1::2], job_task[2::2])  # machines  # processing duration
                ]
        assert len(job_dict) == num_jobs
        assert len(job_dict[0]) == num_machines

        return job_dict


def write_solution_to_file(
    model_data, solution: dict, completion: int, solution_file_path: str
) -> None:
    """Write solution to a file.

    Args:
        data: a class containing JSS data
        solution: a dictionary containing solution
        completion: completion time or objective function of the the JSS problem
        solution_file_path: path to the output solution file. If doesn't exist
                                a new file is created

    """

    main_header = " " * 10
    for i in model_data.resources:
        main_header += " " * 8 + f"machine {i}" + " " * 7

    header = ["job id"]
    for i in model_data.resources:
        header.extend(["task", "start", "dur"])

    job_sol = {}
    for j in model_data.jobs:
        job_sol[j] = [j]
        for i in model_data.resources:
            job_sol[j].extend(list(solution[j, i]))

    with open(solution_file_path, "w") as f:
        f.write("#Number of jobs: " + str(model_data.get_job_count()) + "\n")
        f.write("#Number of machines: " + str(model_data.get_resource_count()) + "\n")
        f.write("#Completion time: " + str(completion) + "\n\n")

        f.write(main_header)
        f.write("\n")
        f.write(tabulate([header, *[v for l, v in job_sol.items()]], headers="firstrow"))

    f.close()

    print(f"\nSaved schedule to " f"{os.path.join(os.getcwd(), solution_file_path)}")


def read_taillard_instance(instance_path: str) -> dict:
    """A method that reads input instance file from the taillard
    dataset

    Args:
        instance_path:  path to the job shop instance file

    Returns:
        Job_dict: dictionary containing jobs as keys and a list of tuple of
                machines and their processing time as values.
    """
    job_dict = defaultdict(list)

    with open(instance_path) as f:
        # ignore the first line
        f.readline()
        # the second line contains Nb of jobs, Nb of Machines as first two values
        line = f.readline()
        num_jobs = int(line.split()[0])
        num_machines = int(line.split()[1])

        # ignore the next line
        f.readline()

        # the next lines contain the processing times for each job for each resource; read this in as
        # as matrix until "Machine" is encountered
        processing_times = []
        line = f.readline()
        while "Machine" not in line:
            processing_times.append(list(map(int, line.split())))
            line = f.readline()

        # the next lines contain the machine order for each job; read this in as
        # as matrix until a blank line is encountered
        machine_order = []
        line = f.readline()
        while line != "\n" and line != "" and line is not None:
            machine_order.append(list(map(int, line.split())))
            line = f.readline()

        for job in range(num_jobs):
            for machine in range(num_machines):
                job_dict[job].append((machine_order[job][machine], processing_times[job][machine]))

        assert len(job_dict) == num_jobs
        assert len(job_dict[0]) == num_machines

        return job_dict
