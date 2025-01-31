from garaga.definitions import CURVES
from garaga.extension_field_modulo_circuit import ModuloCircuitElement
from garaga.modulo_circuit import ModuloCircuit
from garaga.precompiled_circuits.fp2 import Fp2Circuits


class MapToCurveG2(Fp2Circuits):
    def __init__(self, name: str, curve_id: int, compilation_mode: int = 0):
        super().__init__(
            name=name,
            curve_id=curve_id,
            compilation_mode=compilation_mode,
            generic_circuit=True,
        )
        self.curve = CURVES[curve_id]

    def set_consts(self):
        # Standard G2 curve parameters for BLS12-381
        # ToDo: Derive from definitions.py
        self.swu_a = [
            self.set_or_get_constant(0),  # real part
            self.set_or_get_constant(240),  # imaginary part
        ]

        self.swu_b = [
            self.set_or_get_constant(1012),  # real part
            self.set_or_get_constant(1012),  # imaginary part
        ]

        self.swu_z = [
            self.set_or_get_constant(-2),  # real part
            self.set_or_get_constant(-1),  # imaginary part
        ]

        self.one = [
            self.set_or_get_constant(1),  # real part
            self.set_or_get_constant(0),  # imaginary part
        ]

        self.zero = [
            self.set_or_get_constant(0),  # real part
            self.set_or_get_constant(0),  # imaginary part
        ]

    def map_to_curve_part_1(self, input_value: list[ModuloCircuitElement]):
        """
        Implements the first part of the Simplified SWU map-to-curve algorithm in G2.
        This maps a field element to a point on the curve E': y² = x³ + a*x + b.

        The algorithm follows these steps:
        1. Let u be the input field element
        2. Calculate intermediate values:
            - t = z²u⁴ + zu²  (where z is the SWU constant)
            - x₁ = (-b/a) * (1 + 1/(z²u⁴ + zu²))

        Args:
            input_value: Field element u in Fp2 to be mapped to the curve

        Returns:
            tuple: (g1x, div) where:
                - g1x is x³ + ax + b evaluated at the calculated x₁
                - div is an intermediate value needed for the full calculation
        """
        # Calculate u² and related terms
        u2 = self.fp2_square(input_value)  # u²
        zeta_u2 = self.fp2_mul(self.swu_z, u2)  # z·u²
        zeta_u2_square = self.fp2_square(zeta_u2)  # z²u⁴
        ta = self.fp2_add(zeta_u2_square, zeta_u2)  # t = z²u⁴ + zu²
        neg_ta = self.fp2_sub(self.zero, ta)  # -t
        num_x1 = self.fp2_mul(self.swu_b, self.fp2_add(ta, self.one))  # b(t + 1)

        # Handle special case when t = 0
        is_non_zero = self.fp2_is_non_zero(neg_ta)  # 1 if t ≠ 0, 0 if t = 0
        neg_ta_or_z = self.fp2_add(
            self.fp2_mul(self.fp2_sub(self.one, is_non_zero), self.swu_z),  # z if t = 0
            self.fp2_mul(is_non_zero, neg_ta),  # -t if t ≠ 0
        )

        # Calculate x₁ numerator and denominator
        div = self.fp2_mul(self.swu_a, neg_ta_or_z)  # a·(-t) or a·z
        num2_x1 = self.fp2_square(num_x1)  # (b(t + 1))²
        div2 = self.fp2_square(div)  # (a·(-t))²
        div3 = self.fp2_mul(div, div2)  # (a·(-t))³

        # Calculate g(x₁) = x₁³ + ax₁ + b
        num_gx1 = self.fp2_add(
            self.fp2_mul(
                self.fp2_add(num2_x1, self.fp2_mul(self.swu_a, div2)),  # x₁²  # ax₁
                num_x1,  # ·x₁ (completing the x₁³ term)
            ),
            self.fp2_mul(self.swu_b, div3),  # + b
        )
        g1x = self.fp2_mul(num_gx1, self.fp2_inv(div3))  # Final result normalized

        return [g1x, div, num_x1, zeta_u2]

    def finalize_map_to_curve_quadratic(
        self,
        field: list[ModuloCircuitElement],
        g1x: list[ModuloCircuitElement],
        div: list[ModuloCircuitElement],
        num_x1: list[ModuloCircuitElement],
    ):
        """
        Finalizes the map-to-curve operation when g1x is a quadratic residue.
        This function computes the y-coordinate and ensures the point has the correct sign.

        IMPORTANT: This function should only be called when g1x is a quadratic residue,
        meaning there exists a y such that y² = g1x in the field Fp2.
        If g1x is not a quadratic residue, the fp2_sqrt operation will fail.

        The algorithm follows these steps:
        1. Compute y = √(g1x) where g1x = x³ + ax + b
           (requires g1x to be a quadratic residue)
        2. Compute x = num_x1/div to get the x-coordinate in affine form
        3. Adjust the sign of y to match the parity of the input field element

        The sign adjustment uses:
            - If sign(y) ≠ sign(field_element): y = -y
            - For Fp2 elements, parity is determined by the real part

        Args:
            field: The original input field element
            g1x: The value x³ + ax + b from the first part (must be a quadratic residue)
            div: The denominator from the first part
            num_x1: The numerator for x from the first part

        Returns:
            tuple: (x_affine, y_affine) representing the final curve point

        Note:
            When g1x is not a quadratic residue, the alternative function
            finalize_map_to_curve_non_quadratic should be used instead.
        """
        # Compute y-coordinate as the square root of g1x
        # This will only work if g1x is a quadratic residue
        y = self.fp2_sqrt(g1x)

        # Convert x to affine coordinates
        x_affine = self.fp2_div(num_x1, div)

        # Get parity (sign) of both y and input field element
        y_parity = self.fp2_parity(y)
        element_parity = self.fp2_parity(field)

        # Compute if parities are the same using XNOR (opposite of XOR)
        # XNOR(a,b) = 1 - (a + b - 2ab) = 2ab - a - b + 1
        same_parity = [
            self.add(
                self.sub(
                    self.mul(
                        self.set_or_get_constant(2),
                        self.mul(y_parity[0], element_parity[0]),
                    ),
                    self.add(y_parity[0], element_parity[0]),
                ),
                self.set_or_get_constant(1),
            ),
            self.zero[0],  # imaginary part is 0
        ]

        # Adjust y sign if parities don't match:
        # y_affine = same_parity ? y : -y
        y_affine = self.fp2_add(
            self.fp2_mul([same_parity[0], same_parity[1]], y),  # Keep y if same parity
            self.fp2_mul(
                [
                    self.sub(self.one[0], same_parity[0]),
                    self.zero[0],
                ],  # [1 - same_parity, 0]
                self.fp2_sub(self.zero, y),  # -y
            ),
        )

        return [x_affine, y_affine]

    def finalize_map_to_curve_non_quadratic(
        self,
        field: list[ModuloCircuitElement],
        g1x: list[ModuloCircuitElement],
        div: list[ModuloCircuitElement],
        num_x1: list[ModuloCircuitElement],
        zeta_u2: list[ModuloCircuitElement],
    ):
        """
        Finalizes the map-to-curve operation when g1x is NOT a quadratic residue.
        This function uses a clever mathematical property to compute a valid y-coordinate
        when direct square root is impossible.

        Key Mathematical Insight:
        When g1x is not a quadratic residue, we use the SWU constant z (which is also
        not a quadratic residue) to compute the y-coordinate. This works because:
        1. If g1x is not a quadratic residue, then z·g1x IS a quadratic residue
           (product of two non-quadratic residues is a quadratic residue)
        2. We can then compute y₁ = √(z·g1x)
        3. The final y is computed as y = zu·field·y₁

        The algorithm:
        1. Compute y₁ = √(z·g1x)  [This is possible because z·g1x is a quadratic residue]
        2. Compute y = zu·field·y₁
        3. Compute x = (zu·num_x1)/div
        4. Adjust y sign to match input field element parity

        Args:
            field: The original input field element
            g1x: The value x³ + ax + b (known to be a non-quadratic residue)
            zeta_u2: The value z·u² from the first part
            num_x1: The x numerator from the first part
            div: The denominator from the first part

        Returns:
            tuple: (x_affine, y_affine) representing the final curve point

        Note:
            This method relies on the careful selection of the SWU constant z as a
            non-quadratic residue in the field Fp2.
        """
        # Since z·g1x is a quadratic residue (product of two non-quadratic residues),
        # this square root is guaranteed to exist
        y1 = self.fp2_sqrt(self.fp2_mul(self.swu_z, g1x))

        # Compute final y-coordinate
        y = self.fp2_mul(zeta_u2, self.fp2_mul(field, y1))

        # Compute x-coordinate in affine form
        num_x = self.fp2_mul(zeta_u2, num_x1)
        x_affine = self.fp2_div(num_x, div)

        # Handle sign adjustment as before
        y_parity = self.fp2_parity(y)
        element_parity = self.fp2_parity(field)

        # Compute if parities are the same using XNOR (opposite of XOR)
        # XNOR(a,b) = 1 - (a + b - 2ab) = 2ab - a - b + 1
        same_parity = [
            self.add(
                self.sub(
                    self.mul(
                        self.set_or_get_constant(2),
                        self.mul(y_parity[0], element_parity[0]),
                    ),
                    self.add(y_parity[0], element_parity[0]),
                ),
                self.set_or_get_constant(1),
            ),
            self.zero[0],  # imaginary part is 0
        ]
        # Adjust y sign if parities don't match:
        # y_affine = same_parity ? y : -y
        y_affine = self.fp2_add(
            self.fp2_mul([same_parity[0], same_parity[1]], y),  # Keep y if same parity
            self.fp2_mul(
                [
                    self.sub(self.one[0], same_parity[0]),
                    self.zero[0],
                ],  # [1 - same_parity, 0]
                self.fp2_sub(self.zero, y),  # -y
            ),
        )

        return [x_affine, y_affine]


class MapToCurveG1(ModuloCircuit):
    def __init__(self, name: str, curve_id: int, compilation_mode: int = 0):
        super().__init__(
            name=name,
            curve_id=curve_id,
            compilation_mode=compilation_mode,
            generic_circuit=True,
        )
        self.curve = CURVES[curve_id]

    def set_consts(self):
        params = self.curve.swu_params
        self.swu_a = self.set_or_get_constant(params.A)
        self.swu_b = self.set_or_get_constant(params.B)
        self.swu_z = self.set_or_get_constant(params.Z)
        self.zero = self.set_or_get_constant(0)
        self.one = self.set_or_get_constant(1)

    def map_to_curve_part_1(self, input_value: ModuloCircuitElement):
        """
        Implements the first part of the Simplified SWU map-to-curve algorithm for G1.
        This maps a field element to a point on the curve E': y² = x³ + ax + b.

        The algorithm follows these steps:
        1. Let u be the input field element
        2. Calculate t = z²u⁴ + zu² (where z is the SWU constant)
        3. Calculate x₁ = (-b/a) * (1 + 1/t) if t ≠ 0, or x₁ = (-b/(az)) if t = 0
        4. Calculate g(x₁) = x₁³ + ax₁ + b

        Args:
            input_value (ModuloCircuitElement): Field element u to be mapped to the curve

        Returns:
            list: [g1x, div, num_x1, zeta_u2] where:
                - g1x: The value g(x₁) = x₁³ + ax₁ + b
                - div: The denominator used in x₁ calculation (needed for finalization)
                - num_x1: The numerator of x₁ (needed for finalization)
                - zeta_u2: The value z·u² (needed for non-quadratic case)

        Note:
            This is part 1 of the map-to-curve operation. The result needs to be finalized
            using either finalize_map_to_curve_quadratic or finalize_map_to_curve_non_quadratic,
            depending on whether g1x is a quadratic residue.
        """
        # Calculate u² and related terms
        u2 = self.square(input_value)  # u²
        zeta_u2 = self.mul(self.swu_z, u2)  # z·u²
        zeta_u2_square = self.square(zeta_u2)  # z²u⁴
        ta = self.add(zeta_u2_square, zeta_u2)  # t = z²u⁴ + zu²
        neg_ta = self.sub(self.zero, ta)  # -t
        num_x1 = self.mul(self.swu_b, self.add(ta, self.one))  # b(t + 1)

        # Handle special case when t = 0
        is_non_zero = self.fp_is_non_zero(neg_ta)  # 1 if t ≠ 0, 0 if t = 0
        neg_ta_or_z = self.add(
            self.mul(self.sub(self.one, is_non_zero), self.swu_z),  # z if t = 0
            self.mul(is_non_zero, neg_ta),  # -t if t ≠ 0
        )

        # Calculate x₁ numerator and denominator
        div = self.mul(self.swu_a, neg_ta_or_z)  # a·(-t) or a·z
        num2_x1 = self.square(num_x1)  # (b(t + 1))²
        div2 = self.square(div)  # (a·(-t))²
        div3 = self.mul(div, div2)  # (a·(-t))³

        # Calculate g(x₁) = x₁³ + ax₁ + b
        num_gx1 = self.add(
            self.mul(
                self.add(num2_x1, self.mul(self.swu_a, div2)),  # x₁²  # ax₁
                num_x1,  # ·x₁ (completing the x₁³ term)
            ),
            self.mul(self.swu_b, div3),  # + b
        )
        g1x = self.mul(num_gx1, self.inv(div3))  # Final result normalized

        return [g1x, div, num_x1, zeta_u2]

    def finalize_map_to_curve_quadratic(
        self,
        field: ModuloCircuitElement,
        g1x: ModuloCircuitElement,
        div: ModuloCircuitElement,
        num_x1: ModuloCircuitElement,
    ):
        """
        Finalizes the map-to-curve operation when g1x is a quadratic residue.
        This function computes the y-coordinate and ensures the point has the correct sign.

        IMPORTANT: This function should only be called when g1x is a quadratic residue,
        meaning there exists a y such that y² = g1x in the field.

        The algorithm follows these steps:
        1. Compute y = √(g1x) where g1x = x³ + ax + b
           (requires g1x to be a quadratic residue)
        2. Compute x = num_x1/div to get the x-coordinate in affine form
        3. Adjust the sign of y to match the parity of the input field element

        The sign adjustment uses:
            - If sign(y) ≠ sign(field_element): y = -y
            - For field elements, parity is determined by the real part

        Args:
            field: The original input field element
            g1x: The value x³ + ax + b from the first part (must be a quadratic residue)
            div: The denominator from the first part
            num_x1: The numerator for x from the first part

        Returns:
            list: [x_affine, y_affine] representing the final curve point

        Note:
            When g1x is not a quadratic residue, the alternative function
            finalize_map_to_curve_non_quadratic should be used instead.
        """
        # Compute y-coordinate as the square root of g1x
        y = self.fp_sqrt(g1x)

        # Convert x to affine coordinates
        x_affine = self.div(num_x1, div)

        # Get parity (sign) of both y and input field element
        y_parity = self.fp_parity(y)
        element_parity = self.fp_parity(field)

        # Compute if parities are the same using XNOR (opposite of XOR)
        # XNOR(a,b) = 1 - (a + b - 2ab) = 2ab - a - b + 1
        same_parity = self.add(
            self.sub(
                self.mul(
                    self.set_or_get_constant(2),
                    self.mul(y_parity, element_parity),
                ),
                self.add(y_parity, element_parity),
            ),
            self.set_or_get_constant(1),
        )

        # Adjust y sign if parities don't match:
        # y_affine = same_parity ? y : -y
        y_affine = self.add(
            self.mul(same_parity, y),  # Keep y if same parity
            self.mul(
                self.sub(self.one, same_parity),
                self.sub(self.zero, y),  # -y
            ),
        )

        return [x_affine, y_affine]

    def finalize_map_to_curve_non_quadratic(
        self,
        field: ModuloCircuitElement,
        g1x: ModuloCircuitElement,
        div: ModuloCircuitElement,
        num_x1: ModuloCircuitElement,
        zeta_u2: ModuloCircuitElement,
    ):
        """
        Finalizes the map-to-curve operation when g1x is NOT a quadratic residue.
        This function uses a clever mathematical property to compute a valid y-coordinate
        when direct square root is impossible.

        Key Mathematical Insight:
        When g1x is not a quadratic residue, we use the SWU constant z (which is also
        not a quadratic residue) to compute the y-coordinate. This works because:
        1. If g1x is not a quadratic residue, then z·g1x IS a quadratic residue
           (product of two non-quadratic residues is a quadratic residue)
        2. We can then compute y₁ = √(z·g1x)
        3. The final y is computed as y = zu·field·y₁

        The algorithm:
        1. Compute y₁ = √(z·g1x)  [This is possible because z·g1x is a quadratic residue]
        2. Compute y = zu·field·y₁
        3. Compute x = (zu·num_x1)/div
        4. Adjust y sign to match input field element parity

        Args:
            field: The original input field element
            g1x: The value x³ + ax + b (known to be a non-quadratic residue)
            zeta_u2: The value z·u² from the first part
            num_x1: The x numerator from the first part
            div: The denominator from the first part

        Returns:
            tuple: (x_affine, y_affine) representing the final curve point

        Note:
            This method relies on the careful selection of the SWU constant z as a
            non-quadratic residue in the field Fp2.
        """
        # Since z·g1x is a quadratic residue (product of two non-quadratic residues),
        # this square root is guaranteed to exist
        y1 = self.fp_sqrt(self.mul(self.swu_z, g1x))

        # Compute final y-coordinate
        y = self.mul(zeta_u2, self.mul(field, y1))

        # Compute x-coordinate in affine form
        num_x = self.mul(zeta_u2, num_x1)
        x_affine = self.div(num_x, div)

        # Handle sign adjustment as before
        y_parity = self.fp_parity(y)
        element_parity = self.fp_parity(field)

        # Compute if parities are the same using XNOR (opposite of XOR)
        # XNOR(a,b) = 1 - (a + b - 2ab) = 2ab - a - b + 1
        same_parity = self.add(
            self.sub(
                self.mul(
                    self.set_or_get_constant(2),
                    self.mul(y_parity, element_parity),
                ),
                self.add(y_parity, element_parity),
            ),
            self.set_or_get_constant(1),
        )

        # Adjust y sign if parities don't match:
        # y_affine = same_parity ? y : -y
        y_affine = self.add(
            self.mul(same_parity, y),  # Keep y if same parity
            self.mul(
                self.sub(self.one, same_parity),
                self.sub(self.zero, y),  # -y
            ),
        )

        return [x_affine, y_affine]


if __name__ == "__main__":
    circuit = MapToCurveG1("map_to_curve", 1)  # BLS12-381
    circuit.set_consts()

    field = circuit.write_element(
        circuit.field(
            2231413721970278425038638834062370180699174210864795385441649994565282274875534254514118105433862522641883533654145
        )
    )

    g1x, div, num_x1, zeta_u2 = circuit.map_to_curve_part_1(field)

    print("g1x", g1x)
    print("div", div)
    print("num_x1", num_x1)
    print("zeta_u2", zeta_u2)

    if g1x.felt.is_quad_residue():
        print("Quadratic residue")
        (x_affine, y) = circuit.finalize_map_to_curve_quadratic(field, g1x, div, num_x1)
    else:
        print("Non quadratic residue")
        (x_affine, y) = circuit.finalize_map_to_curve_non_quadratic(
            field, g1x, div, num_x1, zeta_u2
        )  # circuit.field(1556800727266659224486307223710983989761661593776178353933175239605467918853638579207638742450628877266610077644019),
        # circuit.field(2231413721970278425038638834062370180699174210864795385441649994565282274875534254514118105433862522641883533654145),

    print("x_affine", x_affine)
    print("y", y)
