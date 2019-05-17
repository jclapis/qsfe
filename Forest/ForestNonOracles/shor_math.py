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


# This file contains some implementations of quantum arithmetic functions
# that are used by Shor's algorithm. All of this code was ported directly over
# from Microsoft's Quantum Development Kit (Q#) into Cirq-compatible code.
# I tried to keep things as faithful as possible, but some things are just
# fundamentally different between the frameworks (like how registers work and
# the way Q# deals with Controlled and Adjoint functions) so it's not a
# 1-to-1 port.
# 
# All of the original Q# source for these functions can be found in Microsoft's
# Canon repository:
# https://github.com/Microsoft/QuantumLibraries/tree/master/Canon/src
# Each function that I ported over lists the name of the original, and a link to
# its source file in the Remarks section of the docstring.


from pyquil import Program
from pyquil.quilatom import QubitPlaceholder
from pyquil.gates import *
import qft
import math


# ==============================
# == Classical Math Functions ==
# ==============================


def gcd_recursion(sign_a, sign_b, r, s, t):
    """
    Internal recursive call to calculate the GCD.

    Remarks:
        See the Q# source for the "_gcd" function at 
        https://github.com/Microsoft/QuantumLibraries/blob/master/Canon/src/Math/Functions.qs
    """

    # Unpack the tuples
    (r_1, r_2) = r
    (s_1, s_2) = s
    (t_1, t_2) = t

    if r_2 == 0:
        return (s_1 * sign_a, t_1 * sign_b)

    quotient = r_1 // r_2
    r_ = (r_2, r_1 - quotient * r_2)
    s_ = (s_2, s_1 - quotient * s_2)
    t_ = (t_2, t_1 - quotient * t_2)
    return gcd_recursion(sign_a, sign_b, r_, s_, t_)


def sign(value):
    """
    Returns an integer that indicates the sign of a number.

    Parameters:
        value (int): The number to get the sign of

    Returns:
        -1 if the number is negative, 0 if the number is 0, or 1
        if the number is positive.
    """

    if value < 0:
        return -1
    elif value == 0:
        return 0
    else:
        return 1


def extended_gcd(a, b):
    """
    Computes a tuple (u, v) such that u*a + v*b = GCD(a, b), where GCD is a
    greatest common divisor of a and b. The GCD is always positive.

    Parameters:
        a (int): The first number to compute the GCD of
        b (int): The second number to compute the GCD of

    Returns:
        A tuple (u, v) where u*a + v*b = GCD(a, b).

    Remarks:
        See the Q# source for the "ExtendedGCD" function at
        https://github.com/Microsoft/QuantumLibraries/blob/master/Canon/src/Math/Functions.qs
    """

    sign_a = sign(a)
    sign_b = sign(b)
    s = (1, 0)
    t = (0, 1)
    r = (a * sign_a, b * sign_b)
    return gcd_recursion(sign_a, sign_b, r, s, t)


def get_modulus_residue(value, modulus):
    """
    Computes the canonical residue of value mod modulus.

    Parameters:
        value (int): The value to compute the residue of
        modulus (int): The modulus used to calculate the residue

    Returns:
        An integer "r" between 0 and modulus - 1, where value - r is divisible
        by the modulus.

    Remarks:
        See the Q# source for the "Modulus" function at 
        https://github.com/Microsoft/QuantumLibraries/blob/master/Canon/src/Math/Functions.qs
    """

    if modulus <= 0:
        raise ValueError(f"Modulus {modulus} must be positive.")

    r = value % modulus
    if r < 0:
        return r + modulus
    else:
        return r


def inverse_mod(a, modulus):
    """
    Returns b such that a*b = 1 (mod modulus).

    Parameters:
        a (int): The number being inverted
        modulus (int): The modulus to use when inverting the number a

    Returns:
        An integer b where a*b = 1 (mod modulus).

    Remarks:
        See the Q# source for the "InverseMod" function at
        https://github.com/Microsoft/QuantumLibraries/blob/master/Canon/src/Math/Functions.qs
    """

    (u, v) = extended_gcd(a, modulus)
    gcd = u * a + v * modulus
    if gcd != 1:
        raise ValueError(f"{a} and {modulus} must be co-prime.")
    return get_modulus_residue(u, modulus)


# ============================
# == Quantum Math Functions ==
# ============================


def qft_reverse_register(register):
    """
    Inverts a register (changes it from little-endian to big-endian) and runs QFT on it.
    
    Parameters:
        program (Program): The program being constructed
        register (list[QubitPlaceholder]): The register to run QFT on after inversion

    Remarks:
        See the Q# source for the "QFTLE" function at
        https://github.com/Microsoft/QuantumLibraries/blob/master/Canon/src/QFT.qs
    """

    reverse_register = register[::-1]
    program = qft.qft(reverse_register)
    return program


def controlled_apply_phase_operation_on_register(ancilla_cache, program, control, operation, target, operation_args):
    """
    Converts the register to the QFT basis, applies the operation, then
    converts the register back to its original basis.

    Parameters:
        program (Program): The program being constructed
        control (QubitPlaceholder): The control qubit
        operation (function): The operation to run
        target (list[QubitPlaceholder]): The register to run the operation on
        operation_args (anything): Operation-specific arguments to pass to the operation

    Remarks:
        See the Q# source for the "ApplyPhaseLEOperationOnLECA" function at
        https://github.com/Microsoft/QuantumLibraries/blob/master/Canon/src/UnsignedIntegers.qs
    """

    program += qft_reverse_register(target)
    program += operation(ancilla_cache, control, target, operation_args)
    program += qft_reverse_register(target).dagger()


def integer_increment_phase(increment, target):
    """
    Unsigned integer increment by an integer constant, based on phase rotations.

    Remarks:
        See the Q# source for the "IntegerIncrementPhaseLE" function at 
        https://github.com/Microsoft/QuantumLibraries/blob/master/Canon/src/Arithmetic/Arithmetic.qs
    """

    d = len(target)
    program = Program()
    for i in range(0, d):
        y = math.pi * increment / (2 ** (d - 1 - i))
        program += PHASE(y, target[i])

    return program


def controlled_integer_increment_phase(control_list, increment, target):
    """
    The controlled version of integer_increment_phase.
    """

    d = len(target)
    program = Program()
    for i in range(0, d):
        y = math.pi * increment / (2 ** (d - 1 - i))
        gate = PHASE(y, target[i])
        for control in control_list:
            gate = gate.controlled(control)
        program += gate

    return program


def copy_most_significant_bit(program, register, target):
    """
    Copies the most significant bit of the qubit register into the target qubit.

    Remarks:
        See the Q# source for the "CopyMostSignificantBitLE" function at
        https://github.com/Microsoft/QuantumLibraries/blob/master/Canon/src/Arithmetic/Arithmetic.qs
    """

    most_significant_qubit = register[len(register) - 1]
    program += CNOT(most_significant_qubit, target)


def apply_register_operation_on_phase(program, operation, target, operation_args):
    """
    Applies an operation that takes a normal register to a register in the QFT basis.

    Remarks:
        See the Q# source for the "ApplyLEOperationOnPhaseLEA" function at 
        https://github.com/Microsoft/QuantumLibraries/blob/master/Canon/src/UnsignedIntegers.qs
    """

    program += qft_reverse_register(target).dagger()
    operation(program, target, operation_args)
    program += qft_reverse_register(target)


def controlled_modular_increment_phase(ancilla_cache, control_list, increment, modulus, target):
    """
    Performs a modular increment of a qubit register by an integer constant.
    The operation is |y> ==> |y + a (mod N)>.

    Remarks:
        See the Q# source for the "ModularIncrementPhaseLE" fuction at
        https://github.com/Microsoft/QuantumLibraries/blob/master/Canon/src/Arithmetic/Arithmetic.qs
    """

    if modulus > 2 ** (len(target) - 1):
        raise ValueError(f"Multiplier must be big enough to fit integers mod {modulus} with the highest bit set to 0.")

    program = Program()
    
    less_than_modulus_flag = None
    if not "less_than_modulus_flag" in ancilla_cache:
        less_than_modulus_flag = QubitPlaceholder()
        ancilla_cache["less_than_modulus_flag"] = less_than_modulus_flag
    else:
        less_than_modulus_flag = ancilla_cache["less_than_modulus_flag"]

    program += controlled_integer_increment_phase(control_list, increment, target)
    program += integer_increment_phase(modulus, target).dagger()
    apply_register_operation_on_phase(program, copy_most_significant_bit, target, less_than_modulus_flag)
    program += controlled_integer_increment_phase([less_than_modulus_flag], modulus, target)
    program += controlled_integer_increment_phase(control_list, increment, target).dagger()
    program += X(less_than_modulus_flag)
    apply_register_operation_on_phase(program, copy_most_significant_bit, target, less_than_modulus_flag)
    program += controlled_integer_increment_phase(control_list, increment, target)

    return program


def controlled_modular_add_product_phase(ancilla_cache, control, phase_summand, operation_args):
    """
    The same as controlled_modular_add_product, but assumes the summand is encoded in the
    QFT basis.

    Remarks:
        See the Q# source for the "ModularAddProductPhaseLE" function at
        https://github.com/Microsoft/QuantumLibraries/blob/master/Canon/src/Arithmetic/Arithmetic.qs
    """

    (constant, modulus, multiplier) = operation_args
    if modulus > 2 ** (len(phase_summand) - 1):
        raise ValueError(f"Multiplier must be big enough to fit integers mod {modulus} with the highest bit set to 0.")
    if constant < 0 or constant >= modulus:
        raise ValueError(f"Constant {constant} must be between 0 and {modulus - 1}.")

    program = Program()
    for i in range(0, len(multiplier)):
        summand = (pow(2, i, modulus) * constant) % modulus
        control_list = [control, multiplier[i]]
        program += controlled_modular_increment_phase(ancilla_cache, control_list, summand, modulus, phase_summand)

    return program


def controlled_modular_add_product(ancilla_cache, control, constant, modulus, multiplier, summand):
    """
    Performs a modular multiply-and-add by integer constants on a qubit register.
    Implements the map |x, y> ==> |x, y + a*x mod N> for the given modulus N,
    constant multiplier a, and summand y.

    Parameters:
        control (QubitPlaceholder): The control qubit
        constant (int): An integer "a" to be added to each basis state label
        modulus (int): The modulus "N" which addition and multiplication is taken with respect to.
        multiplier (list[QubitPlaceholder]): A quantum register representing an unsigned integer whose value is to
            be added to each basis state label of "summand".
        summand (list[QubitPlaceholder]): A quantum register representing an unsigned integer to use as the target
            for this operation.

    Remarks:
        See the Q# source for the "ModularAddProductLE" function at 
        https://github.com/Microsoft/QuantumLibraries/blob/master/Canon/src/Arithmetic/Arithmetic.qs
    """
    
    extra_zero_bit = None
    if not "extra_zero_bit" in ancilla_cache:
        extra_zero_bit = QubitPlaceholder()
        ancilla_cache["extra_zero_bit"] = extra_zero_bit
    else:
        extra_zero_bit = ancilla_cache["extra_zero_bit"]

    operation_args = (constant, modulus, multiplier)
    phase_summand = summand + [extra_zero_bit]
    program = Program()
    controlled_apply_phase_operation_on_register(ancilla_cache, program, control, controlled_modular_add_product_phase,
                                                 phase_summand, operation_args)

    return program


def controlled_modular_multiply(ancilla_cache, program, control, constant, modulus, multiplier):
    """
    This function implements the operation (A*B mod C), where A and C are constants,
    and B is a qubit register representing a little-endian integer.

    Remarks:
        See the Q# source for the "ModularMultiplyByConstantLE" function at
        https://github.com/Microsoft/QuantumLibraries/blob/master/Canon/src/Arithmetic/Arithmetic.qs
    """
    
    summand = None
    if not "summand" in ancilla_cache:
        summand = QubitPlaceholder.register(len(multiplier))
        ancilla_cache["summand"] = summand
    else:
        summand = ancilla_cache["summand"]

    program += controlled_modular_add_product(ancilla_cache, control, constant, modulus, multiplier, summand)

    for i in range(0, len(multiplier)):
        program += CSWAP(control, summand[i], multiplier[i])

    inverse_mod_value = inverse_mod(constant, modulus)

    program += controlled_modular_add_product(ancilla_cache, control, inverse_mod_value, modulus, multiplier, summand).dagger()