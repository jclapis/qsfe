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
# from Microsoft's Quantum Development Kit (Q#) into Qiskit-compatible code.
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


from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
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


def qft_reverse_register(circuit, register):
    """
    Inverts a register (changes it from little-endian to big-endian) and runs QFT on it.
    
    Parameters:
        circuit (QuantumCircuit): The circuit being constructed
        register (list[Qubit]): The register to run QFT on after inversion

    Remarks:
        See the Q# source for the "QFTLE" function at
        https://github.com/Microsoft/QuantumLibraries/blob/master/Canon/src/QFT.qs
    """

    reverse_register = register[::-1]
    qft.qft(circuit, reverse_register)


def adjoint_qft_reverse_register(circuit, register):
    """
    The adjoint version of qft_reverse_register.
    """

    reverse_register = register[::-1]
    qft.iqft(circuit, reverse_register)


def controlled_apply_phase_operation_on_register(circuit, control, operation, target, operation_args):
    """
    Converts the register to the QFT basis, applies the operation, then
    converts the register back to its original basis.

    Parameters:
        circuit (QuantumCircuit): The circuit being constructed
        control (Qubit): The control qubit
        operation (function): The operation to run
        target (list[Qubit]): The register to run the operation on
        operation_args (anything): Operation-specific arguments to pass to the operation

    Remarks:
        See the Q# source for the "ApplyPhaseLEOperationOnLECA" function at
        https://github.com/Microsoft/QuantumLibraries/blob/master/Canon/src/UnsignedIntegers.qs
    """

    qft_reverse_register(circuit, target)
    operation(circuit, control, target, operation_args)
    adjoint_qft_reverse_register(circuit, target)


def integer_increment_phase(circuit, increment, target):
    """
    Unsigned integer increment by an integer constant, based on phase rotations.

    Remarks:
        See the Q# source for the "IntegerIncrementPhaseLE" function at 
        https://github.com/Microsoft/QuantumLibraries/blob/master/Canon/src/Arithmetic/Arithmetic.qs
    """

    d = len(target)
    for i in range(0, d):
        y = math.pi * increment / (2 ** (d - 1 - i))
        circuit.u(0, 0, y, target[i])


def adjoint_integer_increment_phase(circuit, increment, target):
    """
    The adjoint version of integer_increment_phase.
    """

    d = len(target)
    for i in range(d - 1, -1, -1):
        y = math.pi * increment / (2 ** (d - 1 - i))
        circuit.u(0, 0, -y, target[i])


def controlled_integer_increment_phase(circuit, control_list, increment, target):
    """
    The controlled version of integer_increment_phase.
    """

    control = control_list[0]
    if len(control_list) == 2:
        control = QuantumRegister(1, "integer_increment_multicontrol_ancilla")
        if not control in circuit.qregs:
            circuit.add_register(control)
        circuit.ccx(control_list[0], control_list[1], control[0])

    d = len(target)
    for i in range(0, d):
        y = math.pi * increment / (2 ** (d - 1 - i))
        circuit.cu(0, 0, y, 0, control, target[i])

    if len(control_list) == 2:
        circuit.ccx(control_list[0], control_list[1], control[0])


def controlled_adjoint_integer_increment_phase(circuit, control_list, increment, target):
    """
    The adjoint version of controlled_integer_increment_phase.
    """

    control = control_list[0]
    if len(control_list) == 2:
        control = QuantumRegister(1, "integer_increment_multicontrol_ancilla")
        if not control in circuit.qregs:
            circuit.add_register(control)
        circuit.ccx(control_list[0], control_list[1], control[0])

    d = len(target)
    for i in range(d - 1, -1, -1):
        y = math.pi * increment / (2 ** (d - 1 - i))
        circuit.cu(0, 0, -y, 0, control, target[i])

    if len(control_list) == 2:
        circuit.ccx(control_list[0], control_list[1], control[0])


def copy_most_significant_bit(circuit, register, target):
    """
    Copies the most significant bit of the qubit register into the target qubit.

    Remarks:
        See the Q# source for the "CopyMostSignificantBitLE" function at
        https://github.com/Microsoft/QuantumLibraries/blob/master/Canon/src/Arithmetic/Arithmetic.qs
    """

    most_significant_qubit = register[len(register) - 1]
    circuit.cx(most_significant_qubit, target)


def apply_register_operation_on_phase(circuit, operation, target, operation_args):
    """
    Applies an operation that takes a normal register to a register in the QFT basis.

    Remarks:
        See the Q# source for the "ApplyLEOperationOnPhaseLEA" function at 
        https://github.com/Microsoft/QuantumLibraries/blob/master/Canon/src/UnsignedIntegers.qs
    """

    adjoint_qft_reverse_register(circuit, target)
    operation(circuit, target, operation_args)
    qft_reverse_register(circuit, target)


def controlled_modular_increment_phase(circuit, control_list, increment, modulus, target):
    """
    Performs a modular increment of a qubit register by an integer constant.
    The operation is |y> ==> |y + a (mod N)>.

    Remarks:
        See the Q# source for the "ModularIncrementPhaseLE" fuction at
        https://github.com/Microsoft/QuantumLibraries/blob/master/Canon/src/Arithmetic/Arithmetic.qs
    """

    if modulus > 2 ** (len(target) - 1):
        raise ValueError(f"Multiplier must be big enough to fit integers mod {modulus} with the highest bit set to 0.")

    less_than_modulus_flag = QuantumRegister(1, "less_than_modulus_flag")
    if not less_than_modulus_flag in circuit.qregs:
        circuit.add_register(less_than_modulus_flag)

    controlled_integer_increment_phase(circuit, control_list, increment, target)
    adjoint_integer_increment_phase(circuit, modulus, target)
    apply_register_operation_on_phase(circuit, copy_most_significant_bit, target, less_than_modulus_flag)
    controlled_integer_increment_phase(circuit, [less_than_modulus_flag], modulus, target)
    controlled_adjoint_integer_increment_phase(circuit, control_list, increment, target)
    circuit.x(less_than_modulus_flag)
    apply_register_operation_on_phase(circuit, copy_most_significant_bit, target, less_than_modulus_flag)
    controlled_integer_increment_phase(circuit, control_list, increment, target)


def controlled_adjoint_modular_increment_phase(circuit, control_list, increment, modulus, target):
    """
    The adjoint version of controlled_modular_increment_phase.
    """

    if modulus > 2 ** (len(target) - 1):
        raise ValueError(f"Multiplier must be big enough to fit integers mod {modulus} with the highest bit set to 0.")

    less_than_modulus_flag = QuantumRegister(1, "less_than_modulus_flag")
    if not less_than_modulus_flag in circuit.qregs:
        circuit.add_register(less_than_modulus_flag)
        
    controlled_adjoint_integer_increment_phase(circuit, control_list, increment, target)
    apply_register_operation_on_phase(circuit, copy_most_significant_bit, target, less_than_modulus_flag)
    circuit.x(less_than_modulus_flag)
    controlled_integer_increment_phase(circuit, control_list, increment, target)
    controlled_adjoint_integer_increment_phase(circuit, [less_than_modulus_flag], modulus, target)
    apply_register_operation_on_phase(circuit, copy_most_significant_bit, target, less_than_modulus_flag)
    integer_increment_phase(circuit, modulus, target)
    controlled_adjoint_integer_increment_phase(circuit, control_list, increment, target)



def controlled_modular_add_product_phase(circuit, control, phase_summand, operation_args):
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

    for i in range(0, len(multiplier)):
        summand = (pow(2, i, modulus) * constant) % modulus
        control_list = [control, multiplier[i]]
        controlled_modular_increment_phase(circuit, control_list, summand, modulus, phase_summand)


def controlled_adjoint_modular_add_product_phase(circuit, control, phase_summand, operation_args):
    """
    The adjoint version of controlled_modular_add_product_phase.
    """

    (constant, modulus, multiplier) = operation_args
    if modulus > 2 ** (len(phase_summand) - 1):
        raise ValueError(f"Multiplier must be big enough to fit integers mod {modulus} with the highest bit set to 0.")
    if constant < 0 or constant >= modulus:
        raise ValueError(f"Constant {constant} must be between 0 and {modulus - 1}.")

    for i in range(0, len(multiplier)):
        summand = (pow(2, i, modulus) * constant) % modulus
        control_list = [control, multiplier[i]]
        controlled_adjoint_modular_increment_phase(circuit, control_list, summand, modulus, phase_summand)


def controlled_modular_add_product(circuit, control, constant, modulus, multiplier, summand):
    """
    Performs a modular multiply-and-add by integer constants on a qubit register.
    Implements the map |x, y> ==> |x, y + a*x mod N> for the given modulus N,
    constant multiplier a, and summand y.

    Parameters:
        circuit (QuantumCircuit): The circuit being constructed
        control (Qubit): The control qubit
        constant (int): An integer "a" to be added to each basis state label
        modulus (int): The modulus "N" which addition and multiplication is taken with respect to.
        multiplier (list[Qubit]): A quantum register representing an unsigned integer whose value is to
            be added to each basis state label of "summand".
        summand (list[Qubit]): A quantum register representing an unsigned integer to use as the target
            for this operation.

    Remarks:
        See the Q# source for the "ModularAddProductLE" function at 
        https://github.com/Microsoft/QuantumLibraries/blob/master/Canon/src/Arithmetic/Arithmetic.qs
    """
    
    extra_zero_bit = QuantumRegister(1, "extra_zero_bit")
    if not extra_zero_bit in circuit.qregs:
        circuit.add_register(extra_zero_bit)

    operation_args = (constant, modulus, multiplier)
    phase_summand = summand + [extra_zero_bit[0]]
    controlled_apply_phase_operation_on_register(circuit, control, controlled_modular_add_product_phase,
                                                 phase_summand, operation_args)


def controlled_adjoint_modular_add_product(circuit, control, constant, modulus, multiplier, summand):
    """
    The adjoint version of controlled_modular_add_product.
    """
    
    extra_zero_bit = QuantumRegister(1, "extra_zero_bit")
    if not extra_zero_bit in circuit.qregs:
        circuit.add_register(extra_zero_bit)

    operation_args = (constant, modulus, multiplier)
    phase_summand = summand + [extra_zero_bit[0]]
    controlled_apply_phase_operation_on_register(circuit, control, controlled_adjoint_modular_add_product_phase,
                                                 phase_summand, operation_args)


def controlled_modular_multiply(circuit, control, constant, modulus, multiplier):
    """
    This function implements the operation (A*B mod C), where A and C are constants,
    and B is a qubit register representing a little-endian integer.

    Remarks:
        See the Q# source for the "ModularMultiplyByConstantLE" function at
        https://github.com/Microsoft/QuantumLibraries/blob/master/Canon/src/Arithmetic/Arithmetic.qs
    """
    
    summand = QuantumRegister(len(multiplier), "summand")
    if not summand in circuit.qregs:
        circuit.add_register(summand)

    summand_list = [0] * len(multiplier)
    for i in range(0, len(multiplier)):
        summand_list[i] = summand[i]

    controlled_modular_add_product(circuit, control, constant, modulus, multiplier, summand_list)

    for i in range(0, len(multiplier)):
        circuit.cswap(control, summand[i], multiplier[i])

    inverse_mod_value = inverse_mod(constant, modulus)

    controlled_adjoint_modular_add_product(circuit, control, inverse_mod_value, modulus, multiplier, summand_list)