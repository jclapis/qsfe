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


import numpy as np
import math
import unittest
import oracles
import grover


class GroverTests(unittest.TestCase):
    """
    This class contains some special tests that run Grover's algorithm.
    I purposefully designed these tests to demonstrate how a user would
    write a hybrid algorithm that does some classical processing and some
    quantum processing, since almost every useful algorithm involves both
    domains.
    """


    def get_encoded_message(self, message, pad):
        """
        Encodes a message with the XOR cipher.

        Parameters:
            message (list[int]): The original message to encode
            pad (list[int]): A pad / key to use while encrypting the
                original message

        Returns:
            An encrypted string, which represents message XOR pad.
        """

        encoded_message = []
        for i in range(0, len(message)):
            encoded_message.append(message[i] ^ pad[i])
        return encoded_message


    def get_random_pad(self, message_length):
        """
        Creates a random pad to use as the encryption key during a test.

        Parameters:
            message_length (int): >The number of bits in the message to encrypt

        Returns:
            A random bit string with the same size as the message to encrypt.
        """

        return np.random.randint(2, size=message_length).tolist()


    def run_grover_search_on_xor(self, original_message):
        """
        Runs a test of the quantum Grover implementation. This will use
        Grover to search for a lost encryption key when given a ciphertext
        and a plaintext (i.e. the original message and the encrypted version
        of it). The algorithm being used is XOR, which is trivial but an easy
        example for this kind of problem. You could just as easily apply this
        on a harder problem like SHA256 or AES or something.

        Parameters:
            original_message (list[int]): The message to encode during the test.
                The message's length will determine the number of qubits used
                in the search.
        """

        # Get the random XOR pad (the "encryption key") and encrypt the original
        # message with it
        pad = self.get_random_pad(len(original_message))
        encoded_message = self.get_encoded_message(original_message, pad)

        print("Running Grover's Algorithm on the XOR code with a random pad.")
        print(f"Target bitstring: {original_message}")
        print(f"Encoded message: {encoded_message}")
        print("")

        # Run the algorithm, and print some details about the number of iterations
        # vs. the conventional search space
        oracle_args = (encoded_message, original_message)
        key_space_size = 2 ** len(original_message)
        iterations = round(math.sqrt(key_space_size))
        attempts = 10
        for i in range(0, attempts):
            # Try running the algorithm
            print(f"Running {iterations} iterations (vs {key_space_size} for brute force)...")
            solution = grover.run_grover_search(len(original_message), oracles.check_xor_pad, 
                                                oracle_args)

            # Check if it found the right answer
            if solution == pad:
                print(f"Found the pad! {solution}")
                return

            # If not, try again - since it's a probablistic algorithm, it's entirely
            # possible that it might miss a few times.
            print(f"Incorrect result returned: {solution}")
            print("Trying again...");
            print("");

        self.fail(f"Couldn't find the pad after {attempts} attempts.")


    def test_5_bits(self):
        """
        Tests Grover's algorithm on a 5-qubit search.
        """

        self.run_grover_search_on_xor([1, 0, 0, 1, 1])


    def test_10_bits(self):
        """
        Tests Grover's algorithm on a 10-qubit search.
        """

        self.run_grover_search_on_xor([0, 1, 0, 1, 0, 0, 1, 0, 1, 1])


    def test_12_bits(self):
        """
        Tests Grover's algorithm on a 12-qubit search.
        """

        self.run_grover_search_on_xor([0, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0])



if __name__ == '__main__':
    unittest.main()
