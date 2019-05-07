/* ========================================================================
 * Copyright (C) 2019 The MITRE Corporation.
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *     http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * ======================================================================== */

using System.Collections.Generic;
using System.Linq;

namespace QSharpOracles.Simon
{
    /// <summary>
    /// This class contains helper / utility functions that can do the processing
    /// on matrices that Simon's Algorithm needs.
    /// </summary>
    public static class MatrixMath
    {
        /// <summary>
        /// Runs the Gaussian elimination algorithm on the provided matrix, which
        /// converts it into an equivalent reduced-row echelon form. This makes it
        /// much easier to solve. Note that this will be a "mod-2" version of the
        /// Gaussian elimination algorithm, since we're dealing with bit strings
        /// instead of regular vectors and matrices for this problem.
        /// </summary>
        /// <param name="Matrix">The matrix to convert. This function assumes that
        /// the matrix is for a set of equations where Mx = 0. Note that because
        /// of this, and because this is a mod-2 Gaussian elimination, you don't
        /// need to include the solution vector (the "= 0" part) in the matrix - it
        /// just needs to be a collection of input strings.</param>
        /// <remarks>
        /// The fact that this is a mod-2 version of Gaussian elimination makes it
        /// a lot easier than the normal version. Basically it means the row 
        /// multiplication step doesn't matter (since the only possible multiplication
        /// value is 1, which doesn't do anything) and row addition step just turns
        /// into a bitwise XOR for each term in the rows. Also, since we know that each
        /// equation is of the form (X · S) % 2 = 0, we can drop the output column
        /// entirely. It will always start as a 0, and 0 XOR 0 is always 0, so no matter
        /// what the input rows are, it will always be 0 and thus doesn't matter at all.
        /// 
        /// This discussion on the math StackExchange has a good summary of the
        /// differences in the mod-2 world:
        /// https://math.stackexchange.com/a/45348
        /// </remarks>
        public static void ConvertToReducedRowEchelonForm(IList<IList<bool>> Matrix)
        {
            int height = Matrix.Count;
            int width = Matrix[0].Count;

            int currentRow = 0;
            for(int columnIndex = 0; columnIndex < width; columnIndex++)
            {
                // Find the first row that has a 1 in the target column,
                // ignoring rows we've already processed
                int pivotRow = FindPivotRow(Matrix, columnIndex, currentRow);
                if(pivotRow == -1)
                {
                    continue;
                }

                // If it's lower than the current row we're looking at,
                // flip the two
                if(pivotRow > currentRow)
                {
                    SwapRows(Matrix, pivotRow, currentRow);
                }

                // Reduce all of the trailing rows by XORing them with 
                // this one.
                ReduceRows(Matrix, currentRow, columnIndex);

                // Move onto the next row, but if we're out of rows, then
                // we're done here.
                currentRow++;
                if(currentRow == height)
                {
                    return;
                }
            }
        }


        /// <summary>
        /// Finds a row of the provided matrix that has a 1 in the specified column.
        /// </summary>
        /// <param name="Matrix">The matrix to evaluate</param>
        /// <param name="Column">The column to check the value of for each row</param>
        /// <param name="StartRow">The index of the row to start from</param>
        /// <returns>The 0-based index of a row containing a 1 in the specified
        /// column, or -1 if all of the rows had 0 in that column.</returns>
        public static int FindPivotRow(IList<IList<bool>> Matrix, int Column, int StartRow)
        {
            for(int i = StartRow; i < Matrix.Count; i++)
            {
                IList<bool> row = Matrix[i];
                if(row[Column])
                {
                    return i;
                }
            }

            return -1;
        }


        /// <summary>
        /// Swaps two rows of a matrix.
        /// </summary>
        /// <param name="Matrix">The matrix to swap the rows in</param>
        /// <param name="FirstRow">The index of one of the rows to swap</param>
        /// <param name="SecondRow">The index of the other row to swap</param>
        public static void SwapRows(IList<IList<bool>> Matrix, int FirstRow, int SecondRow)
        {
            IList<bool> firstRow = Matrix[FirstRow];
            Matrix[FirstRow] = Matrix[SecondRow];
            Matrix[SecondRow] = firstRow;
        }


        /// <summary>
        /// Reduces the rows of the matrix, converting it into a partial RREF form.
        /// </summary>
        /// <param name="Matrix">The matrix to reduce</param>
        /// <param name="SourceRow">The index of the row to use as the reduction source
        /// (the one that will be XOR'd with the other rows)</param>
        /// <param name="StartColumn">The column to use as the starting point for the
        /// reduction</param>
        public static void ReduceRows(IList<IList<bool>> Matrix, int SourceRow, int StartColumn)
        {
            IList<bool> sourceRow = Matrix[SourceRow];
            for(int row = SourceRow + 1; row < Matrix.Count; row++)
            {
                IList<bool> targetRow = Matrix[row];
                if (targetRow[StartColumn])
                {
                    // Only do the XORing on rows that have a 1 in the target column - the
                    // rows with a 0 here can be left alone.
                    for (int column = StartColumn; column < sourceRow.Count; column++)
                    {
                        targetRow[column] ^= sourceRow[column];
                    }
                }
            }
        }


        /// <summary>
        /// Checks a potential input string to see if it's linearly independent with the collection
        /// of confirmed inputs so far, and adds it to the collection if it is.
        /// </summary>
        /// <param name="Candidate">The new input string to test</param>
        /// <param name="Matrix">The collection of valid, linearly independent strings found so far
        /// </param>
        /// <returns>True if the row was linearly independent and has been added to the matrix,
        /// false if it was not.</returns>
        /// <remarks>
        /// The algorithm here is described in section 18.13.1 (Linear Independence) of the Loceff
        /// document:
        /// http://lapastillaroja.net/wp-content/uploads/2016/09/Intro_to_QC_Vol_1_Loceff.pdf
        /// </remarks>
        public static bool CheckLinearIndependence(IReadOnlyList<bool> Candidate, IList<IList<bool>> Matrix)
        {
            // Add the candidate to the list of valid inputs and run GE on the list
            Matrix.Add(Candidate.ToList());
            ConvertToReducedRowEchelonForm(Matrix);

            // Check to see if the last row is all zeros, meaning one of the inputs is no longer
            // linearly independent with the other we've found so far
            bool isLinearlyIndependent = false;
            IList<bool> lastRow = Matrix[Matrix.Count - 1];
            for (int i = 0; i < lastRow.Count; i++)
            {
                if (lastRow[i])
                {
                    isLinearlyIndependent = true;
                    break;
                }
            }

            // If it's not linearly independent, discard it
            if (!isLinearlyIndependent)
            {
                Matrix.RemoveAt(Matrix.Count - 1);
            }

            return isLinearlyIndependent;
        }


        /// <summary>
        /// Completes a matrix in RREF form of size N x N-1 (that is, it contains N-1 bit strings
        /// that are N bits long) by finding the missing row and adding a linearly independent
        /// string in its position.
        /// </summary>
        /// <param name="Matrix">The matrix to complete. It must be in RREF form already, and be
        /// size N x N-1.</param>
        /// <returns>The solution vector (AKA the right-hand-side vector) for the equations
        /// represented by the matrix. This is what the matrix must be evaluated against during
        /// back substitution (because it's not going to be all 0s after this step).</returns>
        /// <remarks>
        /// The algorithm here is described in section 18.13.2 (Completing the Basis with an
        /// nth Vector Not Orthogonal to a) of the Loceff document:
        /// http://lapastillaroja.net/wp-content/uploads/2016/09/Intro_to_QC_Vol_1_Loceff.pdf
        /// 
        /// You should really go look at that to understand what's going on here. It's hard
        /// to describe it all in the code, but basically the matrix is N by N-1 right now
        /// and this will find the missing row and insert a valid, linearly independent string
        /// at its location.
        /// </remarks>
        public static IList<bool> CompleteMatrix(IList<IList<bool>> Matrix)
        {
            // This is the index of the row that is missing. It defaults to the row past the
            // bottom of the matrix, because if the entire walk doesn't find a missing
            // row, that means the missing one comes after everything that's already in
            // there.
            int missingRowIndex = Matrix.Count;

            for(int i = 0; i < Matrix.Count; i++)
            {
                IList<bool> currentRow = Matrix[i];
                if(!currentRow[i])
                {
                    // Check if this row has a 0 in the diagonal position. If it
                    // does, the missing row that we need to add goes here.
                    missingRowIndex = i;
                    break;
                }
            }

            // Create the missing row, with a 1 in the diagonal position
            bool[] missingRow = new bool[Matrix[0].Count];
            missingRow[missingRowIndex] = true;

            // Insert the row into the missing index. Note that this handles all
            // three cases described in the paper. Row = 0 means all diagonals are
            // 0 so this gets added to the top, row = N means all diagonals are 1
            // so this gets added to the bottom, row = anything else means it
            // gets put into that particular index.
            Matrix.Insert(missingRowIndex, missingRow);

            // Now we need to return the vector that represents the right-hand side of the
            // equations being solved for with the matrix. If the matrix represents the
            // problem (M · S) % 2 = 0 (where M is the matrix and S is the secret string
            // hidden in the function being evaluated), this represents that 0 on the
            // right-hand side of the equation. For the missing string we just added to
            // be truly independent, the equation for it has to equal 1 instead of 0 at the
            // row position where we just added the missing string.
            // Conveniently enough, that ends up being exactly the same thing as the string
            // itself, so we can just return the missing string as the solution vector.
            return missingRow;
        }


        /// <summary>
        /// Performs back substitution on an N x N boolean matrix in RREF form to determine the
        /// solution to each equation represented by its rows (noting that the equations are
        /// of the form [X · S] % 2 = 0). For Simon's Algorithm, this gives you the secret
        /// string S that's hidden in the original function being evaluated.
        /// </summary>
        /// <param name="Matrix">The matrix representing the equations to solve. It must be
        /// N x N and already in RREF form.</param>
        /// <param name="RightHandSide">A vector representing the right-hand-side of the
        /// equations held in the matrix. These are the "solutions" to each equation.</param>
        /// <returns>The solution to the matrix, in this case the secret string S.</returns>
        /// <remarks>
        /// For a good, visual example of how this process works, take a look at this math
        /// StackExchange post:
        /// https://math.stackexchange.com/a/45348
        /// </remarks>
        public static IList<bool> SolveMatrix(IList<IList<bool>> Matrix, IList<bool> RightHandSide)
        {
            bool[] secretString = new bool[Matrix.Count];

            // Start at the bottom row and work our way up to the top
            for(int rowIndex = Matrix.Count - 1; rowIndex >= 0; rowIndex--)
            {
                IList<bool> row = Matrix[rowIndex];
                bool rightHandSideValue = RightHandSide[rowIndex]; // Solution for this equation

                // Walk through the values of the row (these correspond to the variables for each
                // row beneath it, which have already been solved at this point since we're going
                // bottom up); if this row has a 1 for that variable, XOR the solution value with
                // whatever that row's value ended up being.
                for(int columnIndex = rowIndex + 1; columnIndex < row.Count; columnIndex++)
                {
                    if(row[columnIndex])
                    {
                        rightHandSideValue ^= secretString[columnIndex];
                    }
                }

                // Once the terms have been calculated, assign the solution value at this row's
                // index to the result of the equation.
                secretString[rowIndex] = rightHandSideValue;
            }

            return secretString;
        }

    }
}
