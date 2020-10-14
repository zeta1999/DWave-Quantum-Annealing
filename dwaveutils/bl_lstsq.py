"""binary linear least square."""

from collections import defaultdict

import numpy as np
from tqdm import tqdm


def discretize_matrix(matrix, bit_value):
    return np.kron(matrix, bit_value)


def get_bit_value(num_bits, fixed_point=0):
    """The value of each bit in two's-complement binary fixed-point numbers."""
    return np.array([-2 ** fixed_point if i == 0
                     else 2. ** (fixed_point - i)
                     for i in range(0, num_bits)])


def bruteforce(A_discrete, b, bit_value):
    """Solve A_discrete*q=b where q is a binary vector by brute force."""

    # number of predictor
    num_predictor_discrete = A_discrete.shape[1]
    # total number of solutions
    num_solution = 2 ** num_predictor_discrete
    # initialize minimum 2-norm
    min_norm = np.inf

    # loop all solutions
    with tqdm(range(num_solution), desc='brute force') as pbar:
        for i in pbar:
            # assign solution
            # https://stackoverflow.com/questions/13557937/how-to-convert-decimal-to-binary-list-in-python/13558001
            # https://stackoverflow.com/questions/13522773/convert-an-integer-to-binary-without-using-the-built-in-bin-function
            q = np.array([int(bit)
                          for bit in format(i, f'0{num_predictor_discrete}b')])
            # calculate 2-norm
            new_norm = np.linalg.norm(A_discrete @ q - b, 2)
            # update best solution
            if new_norm < min_norm:
                min_norm = new_norm
                best_q = np.copy(q)

    if 'best_q' in locals():
        best_x = q2x(best_q, bit_value)
        return best_q, best_x, min_norm
    else:
        raise NameError("name 'best_q' is not defined")


def q2x(q, bit_value):
    """Convert vector of bit to vector of real value."""
    num_q_entry = len(q)
    num_bits = len(bit_value)
    num_x_entry = num_q_entry // num_bits

    if num_x_entry * num_bits != num_q_entry:
        raise ValueError('The length of q or bit_value is incorrect.')

    x = np.array(
        [
            bit_value @ q[i*num_bits:(i+1)*num_bits]
            for i in range(num_x_entry)
        ]
    )
    return x


def get_qubo(A_discrete, b, eq_scaling_val=1 / 8):
    """
    Get coefficients of a quadratic unconstrained binary optimization (QUBO)
    problem defined by the dictionary.
    """

    # number of predictor and number of response
    num_predictor = A_discrete.shape[1]
    num_response = b.size  # or A_discrete.shape[0]

    # initialize QUBO
    qubo_a = np.zeros(num_predictor)
    qubo_b = np.zeros((num_predictor, num_predictor))
    Q = defaultdict(int)

    # define weights
    for i in range(num_response):
        for j in range(num_predictor):
            qubo_a[j] += A_discrete[i, j] * (A_discrete[i, j] - 2 * b[i])
            for k in range(j):
                qubo_b[j, k] += 2 * A_discrete[i, j] * A_discrete[i, k]

    # define objective
    for i in range(num_predictor):
        if qubo_a[i] != 0:
            Q[(i, i)] = eq_scaling_val * qubo_a[i]
        for j in range(num_predictor):
            if qubo_b[i, j] != 0:
                Q[(i, j)] = eq_scaling_val * qubo_b[i, j]

    # define constrait
    # for i in range(qubo_a.size):
    #     Q[(i, i)] += 0.0001

    return Q
