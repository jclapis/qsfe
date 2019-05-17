# ========================================================================
# Copyright (C) 2019 The MITRE Corporation.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ========================================================================


# This file contains helper / utility functions that can do the processing
# on matrices that Simon's Algorithm needs.


def find_pivot_row(matrix, column, start_row):
    """
    Finds a row of the provided matrix that has a 1 in the specified column.

    Parameters:
        matrix (list[list[bool]]): The matrix to evaluate
        column (int): The column to check the value of for each row
        start_row (int): The index of the row to start from

    Returns:
        The 0-based index of a row containing a 1 in the specified
        column, or -1 if all of the rows had 0 in that column.
    """

    for i in range(start_row, len(matrix)):
        row = matrix[i]
        if row[column]:
            return i

    return -1


def swap_rows(matrix, first_row_index, second_row_index):
    """
    Swaps two rows of a matrix.

    Parameters:
        matrix (list[list[bool]]): The matrix to swap the rows in
        first_row_index (int): The index of one of the rows to swap
        second_row_index (int): The index of the other row to swap
    """

    first_row = matrix[first_row_index]
    matrix[first_row_index] = matrix[second_row_index]
    matrix[second_row_index] = first_row


def reduce_rows(matrix, source_row_index, start_column):
    """
    Reduces the rows of the matrix, converting it into a partial RREF form.

    Parameters:
        matrix (list[list[bool]]): The matrix to reduce
        source_row_index (int): The index of the row to use as the reduction source
            (the one that will be XOR'd with the other rows)
        start_column (int): The column to use as the starting point for the
            reduction
    """

    source_row = matrix[source_row_index]
    for row in range(source_row_index + 1, len(matrix)):
        target_row = matrix[row]
        if target_row[start_column]:
            # Only do the XORing on rows that have a 1 in the target column - the
            # rows with a 0 here can be left alone.
            for column in range(start_column, len(source_row)):
                target_row[column] ^= source_row[column]


def convert_to_reduced_row_echelon_form(matrix):
    """
    Runs the Gaussian elimination algorithm on the provided matrix, which
    converts it into an equivalent reduced-row echelon form. This makes it
    much easier to solve. Note that this will be a "mod-2" version of the
    Gaussian elimination algorithm, since we're dealing with bit strings
    instead of regular vectors and matrices for this problem.

    Parameters:
        matrix (list[list[bool]]): The matrix to convert. This function assumes that
            the matrix is for a set of equations where Mx = 0. Note that because
            of this, and because this is a mod-2 Gaussian elimination, you don't
            need to include the solution vector (the "= 0" part) in the matrix - it
            just needs to be a collection of input strings.

    Remarks:
        The fact that this is a mod-2 version of Gaussian elimination makes it
        a lot easier than the normal version. Basically it means the row 
        multiplication step doesn't matter (since the only possible multiplication
        value is 1, which doesn't do anything) and row addition step just turns
        into a bitwise XOR for each term in the rows. Also, since we know that each
        equation is of the form (X · S) % 2 = 0, we can drop the output column
        entirely. It will always start as a 0, and 0 XOR 0 is always 0, so no matter
        what the input rows are, it will always be 0 and thus doesn't matter at all.
        
        This discussion on the math StackExchange has a good summary of the
        differences in the mod-2 world:
        https://math.stackexchange.com/a/45348
    """

    height = len(matrix)
    width = len(matrix[0])

    current_row = 0
    for column_index in range(0, width):
        # Find the first row that has a 1 in the target column,
        # ignoring rows we've already processed
        pivot_row = find_pivot_row(matrix, column_index, current_row)
        if pivot_row == -1:
            continue

        # If it's lower than the current row we're looking at,
        # flip the two
        if pivot_row > current_row:
            swap_rows(matrix, pivot_row, current_row)

        # Reduce all of the trailing rows by XORing them with 
        # this one.
        reduce_rows(matrix, current_row, column_index)

        # Move onto the next row, but if we're out of rows, then
        # we're done here.
        current_row += 1
        if current_row == height:
            return


def check_linear_independence(candidate, matrix):
    """
    Checks a potential input string to see if it's linearly independent with the collection
    of confirmed inputs so far, and adds it to the collection if it is.

    Parameters:
        candidate (list[bool]): The new input string to test
        matrix (list[list[bool]]): The collection of valid, linearly independent strings
            found so far

    Returns:
        True if the row was linearly independent and has been added to the matrix,
        false if it was not.
    """

    # Add the candidate to the list of valid inputs and run GE on the list
    matrix.append(candidate)
    convert_to_reduced_row_echelon_form(matrix)

    # Check to see if the last row is all zeros, meaning one of the inputs is no longer
    # linearly independent with the other we've found so far
    is_linearly_independent = False
    last_row = matrix[-1]
    for element in last_row:
        if element:
            is_linearly_independent = True
            break

    # If it's not linearly independent, discard it
    if not is_linearly_independent:
        matrix.pop(-1)

    return is_linearly_independent


def complete_matrix(matrix):
    """
    Completes a matrix in RREF form of size N x N-1 (that is, it contains N-1 bit strings
    that are N bits long) by finding the missing row and adding a linearly independent
    string in its position.

    Parameters:
        matrix (list[list[bool]]): The matrix to complete. It must be in RREF form already,
            and be size N x N-1.

    Returns:
        The solution vector (AKA the right-hand-side vector) for the equations
        represented by the matrix. This is what the matrix must be evaluated against during
        back substitution (because it's not going to be all 0s after this step).

    Remarks:
        The algorithm here is described in section 18.13.2 (Completing the Basis with an
        nth Vector Not Orthogonal to a) of the Loceff document:
        http://lapastillaroja.net/wp-content/uploads/2016/09/Intro_to_QC_Vol_1_Loceff.pdf
        
        You should really go look at that to understand what's going on here. It's hard
        to describe it all in the code, but basically the matrix is N by N-1 right now
        and this will find the missing row and insert a valid, linearly independent string
        at its location.
    """

    # This is the index of the row that is missing. It defaults to the row past the
    # bottom of the matrix, because if the entire walk doesn't find a missing
    # row, that means the missing one comes after everything that's already in
    # there.
    missing_row_index = len(matrix)

    for i in range(0, len(matrix)):
        current_row = matrix[i]
        if not current_row[i]:
            # Check if this row has a 0 in the diagonal position. If it
            # does, the missing row that we need to add goes here.
            missing_row_index = i
            break

    # Create the missing row, with a 1 in the diagonal position
    missing_row = [False] * len(matrix[0])
    missing_row[missing_row_index] = True

    # Insert the row into the missing index. Note that this handles all
    # three cases described in the paper. Row = 0 means all diagonals are
    # 0 so this gets added to the top, row = N means all diagonals are 1
    # so this gets added to the bottom, row = anything else means it
    # gets put into that particular index.
    matrix.insert(missing_row_index, missing_row)

    # Now we need to return the vector that represents the right-hand side of the
    # equations being solved for with the matrix. If the matrix represents the
    # problem (M · S) % 2 = 0 (where M is the matrix and S is the secret string
    # hidden in the function being evaluated), this represents that 0 on the
    # right-hand side of the equation. For the missing string we just added to
    # be truly independent, the equation for it has to equal 1 instead of 0 at the
    # row position where we just added the missing string.
    # Conveniently enough, that ends up being exactly the same thing as the string
    # itself, so we can just return the missing string as the solution vector.
    return missing_row


def solve_matrix(matrix, right_hand_side):
    """
    Performs back substitution on an N x N boolean matrix in RREF form to determine the
    solution to each equation represented by its rows (noting that the equations are
    of the form [X · S] % 2 = 0). For Simon's Algorithm, this gives you the secret
    string S that's hidden in the original function being evaluated.

    Parameters:
        matrix (list[list[bool]]): The matrix representing the equations to solve. It must be
            N x N and already in RREF form.
        right_hand_side (list[bool]): A vector representing the right-hand-side of the
            equations held in the matrix. These are the "solutions" to each equation.

    Returns:
        The solution to the matrix, in this case the secret string S.

    Remarks:
        For a good, visual example of how this process works, take a look at this math
        StackExchange post:
        https://math.stackexchange.com/a/45348
    """

    secret_string = [False] * len(matrix)

    # Start at the bottom row and work our way up to the top
    for row_index in range(len(matrix) - 1, -1, -1):
        row = matrix[row_index]
        right_hand_side_value = right_hand_side[row_index]  # Solution for this equation

        # Walk through the values of the row (these correspond to the variables for each
        # row beneath it, which have already been solved at this point since we're going
        # bottom up); if this row has a 1 for that variable, XOR the solution value with
        # whatever that row's value ended up being.
        for column_index in range(row_index + 1, len(row)):
            if row[column_index]:
                right_hand_side_value ^= secret_string[column_index]

        # Once the terms have been calculated, assign the solution value at this row's
        # index to the result of the equation.
        secret_string[row_index] = right_hand_side_value

    return secret_string