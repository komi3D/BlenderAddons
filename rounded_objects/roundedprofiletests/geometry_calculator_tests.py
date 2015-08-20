'''
Created on 28 cze 2015

@author: Komi
'''
from math import sqrt
import unittest

from mathutils import Vector

from roundedprofile.geometry_calculator import GeometryCalculator


class TestGCCircleIntersections(unittest.TestCase):

    def setUp(self):
        self.geomCalc = GeometryCalculator()
    
    def tearDown(self):
        pass

    # ## 2 intersections

    def testTwoIntersectionsSmallOverlap(self):
        c2 = Vector((0, 0, 0))
        r2 = 1.0
        c1 = Vector((4, 0, 0))
        r1 = 3.5

        intersection2 = Vector((0.5937, 0.805, 0.0))
        intersection1 = Vector((0.5937, -0.805, 0.0))

        output = self.geomCalc.getCircleIntersections(c1, r1, c2, r2)

        self.assertEqual(2, len(output))
        self.assertAlmostEqual(intersection1[0], output[0][0], places = 3)
        self.assertAlmostEqual(intersection1[1], output[0][1], places = 3)
        self.assertAlmostEqual(intersection1[2], output[0][2], places = 3)

        self.assertAlmostEqual(intersection2[0], output[1][0], places = 3)
        self.assertAlmostEqual(intersection2[1], output[1][1], places = 3)
        self.assertAlmostEqual(intersection2[2], output[1][2], places = 3)

    def testTwoIntersectionsSmallOverlapMinusDiagonal(self):
        c2 = Vector((0, 0, 0))
        r2 = 3.5
        c1 = Vector((-4, -2, 0))
        r1 = 1.0

        intersection1 = Vector((-3.2177, -1.3770, 0.0))
        intersection2 = Vector((-3.0322, -1.7479, 0.0))

        output = self.geomCalc.getCircleIntersections(c1, r1, c2, r2)

        self.assertEqual(2, len(output))
        self.assertAlmostEqual(intersection1[0], output[0][0], places = 3)
        self.assertAlmostEqual(intersection1[1], output[0][1], places = 3)
        self.assertAlmostEqual(intersection1[2], output[0][2], places = 3)

        self.assertAlmostEqual(intersection2[0], output[1][0], places = 3)
        self.assertAlmostEqual(intersection2[1], output[1][1], places = 3)
        self.assertAlmostEqual(intersection2[2], output[1][2], places = 3)

    def testTwoIntersectionsLargeOverlapDiagonal(self):
        c2 = Vector((0, 0, 0))
        r2 = 3.5
        c1 = Vector((2, 2, 0))
        r1 = 1.5

        intersection2 = Vector((1.2192, 3.2807, 0.0))
        intersection1 = Vector((3.2807, 1.2192, 0.0))

        output = self.geomCalc.getCircleIntersections(c1, r1, c2, r2)

        self.assertEqual(2, len(output))
        self.assertAlmostEqual(intersection1[0], output[0][0], places = 3)
        self.assertAlmostEqual(intersection1[1], output[0][1], places = 3)
        self.assertAlmostEqual(intersection1[2], output[0][2], places = 3)

        self.assertAlmostEqual(intersection2[0], output[1][0], places = 3)
        self.assertAlmostEqual(intersection2[1], output[1][1], places = 3)
        self.assertAlmostEqual(intersection2[2], output[1][2], places = 3)

    def testForTwoIntersectionsLargeOverlapPlusX(self):
        c1 = Vector((0, 0, 0))
        r1 = 6.0
        c2 = Vector((4, 0, 0))
        r2 = 2.5
        intersection1 = Vector((5.71875, 1.8155, 0.0))
        intersection2 = Vector((5.71875, -1.8155, 0.0))

        output = self.geomCalc.getCircleIntersections(c1, r1, c2, r2)

        self.assertEqual(2, len(output))
        self.assertAlmostEqual(intersection1[0], output[0][0], places = 3)
        self.assertAlmostEqual(intersection1[1], output[0][1], places = 3)
        self.assertAlmostEqual(intersection1[2], output[0][2], places = 3)

        self.assertAlmostEqual(intersection2[0], output[1][0], places = 3)
        self.assertAlmostEqual(intersection2[1], output[1][1], places = 3)
        self.assertAlmostEqual(intersection2[2], output[1][2], places = 3)

    def testTwoIntersectionsLargeOverlapMinusX(self):
        self.geomCalc.selectedPlane = self.geomCalc.YZ
        c1 = Vector((0, 0, 0))
        r1 = 6.0
        # c2 = Vector((-4, 0, 0))
        c2 = Vector((0, -4, 0))
        r2 = 2.5

        # intersection1 = Vector((-5.71875, -1.8155, 0.0))
        # intersection2 = Vector((-5.71875, 1.8155, 0.0))

        intersection1 = Vector((0.0, -5.71875, -1.8155))
        intersection2 = Vector((0.0, -5.71875, 1.8155))

        output = self.geomCalc.getCircleIntersections(c1, r1, c2, r2)

        self.assertEqual(2, len(output))
        self.assertAlmostEqual(intersection1[0], output[0][0], places = 3)
        self.assertAlmostEqual(intersection1[1], output[0][1], places = 3)
        self.assertAlmostEqual(intersection1[2], output[0][2], places = 3)

        self.assertAlmostEqual(intersection2[0], output[1][0], places = 3)
        self.assertAlmostEqual(intersection2[1], output[1][1], places = 3)
        self.assertAlmostEqual(intersection2[2], output[1][2], places = 3)

    def testIntersectionsLargeOverlapMinusY(self):
        c1 = Vector((0, 0, 0))
        r1 = 6.0
        c2 = Vector((0, -4, 0))
        r2 = 2.5
        intersection1 = Vector((1.8155, -5.71875, 0.0))
        intersection2 = Vector((-1.8155, -5.71875, 0.0))

        output = self.geomCalc.getCircleIntersections(c1, r1, c2, r2)

        self.assertEqual(2, len(output))
        self.assertAlmostEqual(intersection1[0], output[0][0], places = 3)
        self.assertAlmostEqual(intersection1[1], output[0][1], places = 3)
        self.assertAlmostEqual(intersection1[2], output[0][2], places = 3)

        self.assertAlmostEqual(intersection2[0], output[1][0], places = 3)
        self.assertAlmostEqual(intersection2[1], output[1][1], places = 3)
        self.assertAlmostEqual(intersection2[2], output[1][2], places = 3)

    ### Tangency tests ###
    def testTangentCirclesWithEqualRadiusReturnOnePoint2(self):
        c1 = Vector((0, 0, 0))
        r1 = 2.0
        c2 = Vector((4, 0, 0))
        r2 = 2.0
        intersection = Vector((2, 0, 0))

        output = self.geomCalc.getCircleIntersections(c1, r1, c2, r2)

        self.assertEqual(1, len(output))
        self.assertEqual(intersection, output[0])

    def testTangentCirclesWithEqualRadiusReturnOnePoint3(self):
        c1 = Vector((0, 0, 0))
        r1 = 3.0
        c2 = Vector((6, 0, 0))
        r2 = 3.0
        intersection = Vector((3, 0, 0))

        output = self.geomCalc.getCircleIntersections(c1, r1, c2, r2)

        self.assertEqual(1, len(output))
        self.assertEqual(intersection, output[0])

    def testTangentCirclesAlongXReturnOnePoint(self):
        c1 = Vector((0, 0, 0))
        r1 = 2.0
        c2 = Vector((6, 0, 0))
        r2 = 4.0
        intersection = Vector((2, 0, 0))

        output = self.geomCalc.getCircleIntersections(c1, r1, c2, r2)

        self.assertEqual(1, len(output))
        self.assertEqual(intersection, output[0])

    def testInnerTangentCirclesAlongXReturnOnePoint(self):
        c1 = Vector((3, 0, 0))
        r1 = 1.0
        c2 = Vector((6, 0, 0))
        r2 = 4.0
        intersection = Vector((2, 0, 0))

        output = self.geomCalc.getCircleIntersections(c1, r1, c2, r2)

        self.assertEqual(1, len(output))
        self.assertEqual(intersection, output[0])

    def testTangentCirclesAlongYReturnOnePoint(self):
        c1 = Vector((0, 0, 0))
        r1 = 2.0
        c2 = Vector((0, 6, 0))
        r2 = 4.0
        intersection = Vector((0, 2, 0))

        output = self.geomCalc.getCircleIntersections(c1, r1, c2, r2)

        self.assertEqual(1, len(output))
        self.assertEqual(intersection, output[0])
    ###################################################

    # ## no intersection

    def testNoIntersectionsWhenCenterDistanceLargerThenRadiusesSum(self):
        c1 = Vector((0, 0, 0))
        r1 = 2.0
        c2 = Vector((10, 0, 0))
        r2 = 4.0
        intersection = None

        output = self.geomCalc.getCircleIntersections(c1, r1, c2, r2)

        self.assertEqual(intersection, output)

    def testNoIntersectionsWhenCircleInsideTheOtherCircle(self):
        c1 = Vector((0, 0, 0))
        r1 = 20.0
        c2 = Vector((10, 0, 0))
        r2 = 4.0
        intersection = None

        output = self.geomCalc.getCircleIntersections(c1, r1, c2, r2)

        self.assertEqual(intersection, output)

##############################
    def testGetPerpendicularVectorXY(self):
        self.geomCalc.selectedPlane = self.geomCalc.XY
        v = Vector((1, 2, 0))
        vp = Vector((-2, 1, 0))

        calcVec = self.geomCalc.getPerpendicularVector(v)
        self.assertEqual(calcVec, vp)

    def testGetPerpendicularVectorXZ(self):
        self.geomCalc.selectedPlane = self.geomCalc.XZ
        v = Vector((1, 0, 5))
        vp = Vector((-5, 0, 1))

        calcVec = self.geomCalc.getPerpendicularVector(v)
        self.assertEqual(calcVec, vp)

    def testGetPerpendicularVectorYZ(self):
        self.geomCalc.selectedPlane = self.geomCalc.YZ
        v = Vector((0, 2, 3))
        vp = Vector((0, -3, 2))

        calcVec = self.geomCalc.getPerpendicularVector(v)
        self.assertEqual(calcVec, vp)

#############################################

class TestGCGetAngleFrom3Points(unittest.TestCase):

    def setUp(self):
        self.geomCalc = GeometryCalculator()

    def tearDown(self):
        pass

    def testPositive3PointsAngle120(self):

        p1 = Vector((0, 5, 0))
        p2 = Vector((0, 1, 0))
        p3 = Vector((5, -2, 0))


        angleDeg, angleRad = self.geomCalc.getAngleBetween3Points(p1, p2, p3)

        self.assertGreaterEqual(angleDeg, 120)
        self.assertLessEqual(angleDeg, 130)

    def testNegative3PointsAngle120(self):

        p1 = Vector((0, 5, 0))
        p2 = Vector((0, 1, 0))
        p3 = Vector((-5, -2, 0))


        angleDeg, angleRad = self.geomCalc.getAngleBetween3Points(p1, p2, p3)

        self.assertLessEqual(angleDeg, -120)
        self.assertGreaterEqual(angleDeg, -130)


    def testNegative3PointsAngle60(self):
        p1 = Vector((0, 5, 0))
        p2 = Vector((0, 1, 0))
        p3 = Vector((-5, 3, 0))


        angleDeg, angleRad = self.geomCalc.getAngleBetween3Points(p1, p2, p3)

        self.assertGreaterEqual(angleDeg, -70)
        self.assertLessEqual(angleDeg, -60)


    def testPositive3PointsAngle60(self):

        p1 = Vector((1, 5, 0))
        p2 = Vector((0, 1, 0))
        p3 = Vector((5, 2, 0))


        angleDeg, angleRad = self.geomCalc.getAngleBetween3Points(p1, p2, p3)

        self.assertGreaterEqual(angleDeg, 60)
        self.assertLessEqual(angleDeg, 70)

    def test3PointsAngle180(self):

        p1 = Vector((0, 5, 0))
        p2 = Vector((0, 1, 0))
        p3 = Vector((0, -6, 0))


        angleDeg, angleRad = self.geomCalc.getAngleBetween3Points(p1, p2, p3)

        self.assertEqual(180, angleDeg)

    def test3PointsAngle180Diagonal(self):

        p1 = Vector((3, 3, 0))
        p2 = Vector((2, 2, 0))
        p3 = Vector((-6, -6, 0))


        angleDeg, angleRad = self.geomCalc.getAngleBetween3Points(p1, p2, p3)

        self.assertAlmostEqual(180.0, angleDeg, places = 3)


    def test3PointsAngle0(self):

        p1 = Vector((2, 0, 0))
        p2 = Vector((5, 0, 0))
        p3 = Vector((1, 0, 0))


        angleDeg, angleRad = self.geomCalc.getAngleBetween3Points(p1, p2, p3)

        self.assertEqual(0, angleDeg)

#############################################

class ATestGCLineCircleIntersections(unittest.TestCase):

    def setUp(self):
        self.geomCalc = GeometryCalculator()

    def tearDown(self):
        pass
    
    
    def testLineABHorizontal(self):
        
        p1 = Vector((2, 3, 0))
        p2 = Vector((5, 3, 0))
        A, B = self.geomCalc.getCoefficientsForLineThrough2Points(p1, p2)
        
        self.assertEqual(0, A)
        self.assertEqual(3, B)

    def testLineABVertical(self):
        p1 = Vector((5, 7, 0))
        p2 = Vector((5, 3, 0))
        outcome = self.geomCalc.getCoefficientsForLineThrough2Points(p1, p2)

        self.assertEqual(None, outcome)
    
    def testLineABDiagonalRise(self):
        p1 = Vector((2, 4, 0))
        p2 = Vector((4, 7, 0))
        A, B = self.geomCalc.getCoefficientsForLineThrough2Points(p1, p2)

        self.assertEqual(1.5, A)
        self.assertEqual(1, B)
    
    def testLineABDiagonalFall(self):
        p1 = Vector((2, 4, 0))
        p2 = Vector((4, 1, 0))
        A, B = self.geomCalc.getCoefficientsForLineThrough2Points(p1, p2)

        self.assertEqual(-1.5, A)
        self.assertEqual(7, B)
    
    def testHorizontalLineCircleIntersect(self):
        lineAB = [0, 3]
        c1 = Vector((4, 0, 0))
        r = 4

        X1, X2 = self.geomCalc.getLineCircleIntersections(lineAB, c1, r)

        self.assertAlmostEqual(1.354, X1[0], places = 3)
        self.assertAlmostEqual(3, X1[1])
        self.assertAlmostEqual(6.646, X2[0], places = 3)
        self.assertAlmostEqual(3, X2[1])

    def testFallingLineCircleIntersect(self):
        lineAB = [-1.5, 6]
        c1 = Vector((4, 0, 0))
        r = 4

        X1, X2 = self.geomCalc.getLineCircleIntersections(lineAB, c1, r)

        self.assertAlmostEqual(1.781, X1[0], places = 3)
        self.assertAlmostEqual(3.328, X1[1], places = 3)
        self.assertAlmostEqual(6.219, X2[0], places = 3)
        self.assertAlmostEqual(-3.328, X2[1], places = 3)

    def testRisingLineCircleIntersect(self):
        lineAB = [0.66666666, -2.66666666]
        c1 = Vector((4, 0, 0))
        r = 4

        X1, X2 = self.geomCalc.getLineCircleIntersections(lineAB, c1, r)

        self.assertAlmostEqual(0.672, X1[0], places = 3)
        self.assertAlmostEqual(-2.219, X1[1], places = 3)
        self.assertAlmostEqual(7.328, X2[0], places = 3)
        self.assertAlmostEqual(2.219, X2[1], places = 3)

    def testHorizontalLineCircleTangency(self):

        lineAB = [0, 4]
        c1 = Vector((4, 0, 0))
        r = 4

        X1, X2 = self.geomCalc.getLineCircleIntersections(lineAB, c1, r)

        self.assertAlmostEqual(4, X1[0], places = 3)
        self.assertAlmostEqual(4, X1[1])
        self.assertAlmostEqual(4, X2[0], places = 3)
        self.assertAlmostEqual(4, X2[1])

    def testGetClosestPointToRefPoint(self):
        points = [Vector((1, 3, 0)), Vector((4, 9, 0)) ]
        refCenter = Vector ((-1, -1, 0))
        p = self.geomCalc.getClosestPointToRefPoint(points, refCenter)

        self.assertEqual(p, points[0])

    def testGetFarthestPointToRefPoint(self):
        points = [Vector((1, 3, 0)), Vector((4, 9, 0)) ]
        refCenter = Vector ((-1, -1, 0))
        p = self.geomCalc.getFarthestPointToRefPoint(points, refCenter)

        self.assertEqual(p, points[1])

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
