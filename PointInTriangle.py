import unittest

###############################################################################


def point_in_triangle(point, triangle):
    """Returns True if the point is inside the triangle
    and returns False if it falls outside.
    - The argument *point* is a tuple with two elements
    containing the X,Y coordinates respectively.
    - The argument *triangle* is a tuple with three elements each
    element consisting of a tuple of X,Y coordinates.

    It works like this:
    Walk clockwise or counterclockwise around the triangle
    and project the point onto the segment we are crossing
    by using the dot product.
    Finally, check that the vector created is on the same side
    for each of the triangle's segments.
    """
    # Unpack arguments
    x, y = point
    ax, ay, az = triangle[0]
    bx, by, bz = triangle[1]
    cx, cy, cz = triangle[2]
    # Segment A to B
    side_1 = (x - bx) * (ay - by) - (ax - bx) * (y - by)
    # Segment B to C
    side_2 = (x - cx) * (by - cy) - (bx - cx) * (y - cy)
    # Segment C to A
    side_3 = (x - ax) * (cy - ay) - (cx - ax) * (y - ay)
    # All the signs must be positive or all negative
    return (side_1 < -0.002) == (side_2 < -0.002) == (side_3 < -0.002)

###############################################################################


class TestPointInTriangle(unittest.TestCase):

    triangle = ((22, 8, 0),
                (12, 55, 0),
                (7, 19, 0))

    def test_inside(self):
        point = (15, 20)
        self.assertTrue(point_in_triangle(point, self.triangle))

    def test_outside(self):
        point = (1, 7)
        self.assertFalse(point_in_triangle(point, self.triangle))

    def test_border_case(self):
        """If the point is exactly on one of the triangle's edges,
        we consider it is inside."""
        point = (7, 19)
        self.assertTrue(point_in_triangle(point, self.triangle))


###############################################################################
if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestPointInTriangle)
    unittest.TextTestRunner().run(suite)
