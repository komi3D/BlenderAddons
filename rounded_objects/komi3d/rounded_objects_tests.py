'''
Created on 28 cze 2015

@author: Komi
'''
from math import sqrt
import unittest

from mathutils import Vector

from komi3d.rounded_objects import RoundedObjects


class Test(unittest.TestCase):

    def setUp(self):
        self.roundedObj = RoundedObjects()
    
    def tearDown(self):
        pass

    ### Tangency tests ###
    def testCIForTangentCirclesWithEqualRadiusReturnOnePoint2(self):
        c1 = Vector((0, 0, 0))
        r1 = 2.0
        c2 = Vector((4, 0, 0))
        r2 = 2.0
        intersection = Vector((2, 0, 0))

        output = self.roundedObj.getCircleIntersections(c1, r1, c2, r2)

        self.assertEqual(1, len(output))
        self.assertEqual(intersection, output[0])

    def testCIForTangentCirclesWithEqualRadiusReturnOnePoint3(self):
        c1 = Vector((0, 0, 0))
        r1 = 3.0
        c2 = Vector((6, 0, 0))
        r2 = 3.0
        intersection = Vector((3, 0, 0))

        output = self.roundedObj.getCircleIntersections(c1, r1, c2, r2)

        self.assertEqual(1, len(output))
        self.assertEqual(intersection, output[0])

    def testCIForTangentCirclesAlongXReturnOnePoint(self):
        c1 = Vector((0, 0, 0))
        r1 = 2.0
        c2 = Vector((6, 0, 0))
        r2 = 4.0
        intersection = Vector((2, 0, 0))

        output = self.roundedObj.getCircleIntersections(c1, r1, c2, r2)

        self.assertEqual(1, len(output))
        self.assertEqual(intersection, output[0])

    def testCIForInnerTangentCirclesAlongXReturnOnePoint(self):
        c1 = Vector((3, 0, 0))
        r1 = 1.0
        c2 = Vector((6, 0, 0))
        r2 = 4.0
        intersection = Vector((2, 0, 0))

        output = self.roundedObj.getCircleIntersections(c1, r1, c2, r2)

        self.assertEqual(1, len(output))
        self.assertEqual(intersection, output[0])

    def testCIForTangentCirclesAlongYReturnOnePoint(self):
        c1 = Vector((0, 0, 0))
        r1 = 2.0
        c2 = Vector((0, 6, 0))
        r2 = 4.0
        intersection = Vector((0, 2, 0))

        output = self.roundedObj.getCircleIntersections(c1, r1, c2, r2)

        self.assertEqual(1, len(output))
        self.assertEqual(intersection, output[0])
    ###################################################

    # ## no intersection

    def testCIForNoIntersectionsWhenCenterDistanceLargerThenRadiusesSum(self):
        c1 = Vector((0, 0, 0))
        r1 = 2.0
        c2 = Vector((10, 0, 0))
        r2 = 4.0
        intersection = None

        output = self.roundedObj.getCircleIntersections(c1, r1, c2, r2)

        self.assertEqual(intersection, output)

    def testCIForNoIntersectionsWhenCircleInsideTheOtherCircle(self):
        c1 = Vector((0, 0, 0))
        r1 = 20.0
        c2 = Vector((10, 0, 0))
        r2 = 4.0
        intersection = None

        output = self.roundedObj.getCircleIntersections(c1, r1, c2, r2)

        self.assertEqual(intersection, output)

    # ## 2 intersections

    def testCIForTwoIntersectionsSmallOverlap(self):
        c1 = Vector((0, 0, 0))
        r1 = 1.0
        c2 = Vector((4, 0, 0))
        r2 = 3.5
        intersection = [2, 4]

        output = self.roundedObj.getCircleIntersections(c1, r1, c2, r2)

        # self.assertEqual(2, len(output))
        self.assertEqual(intersection, output)

    def testCIForTwoIntersectionsLargeOverlap(self):
        c1 = Vector((0, 0, 0))
        r1 = 6.0
        c2 = Vector((4, 0, 0))
        r2 = 2.5
        intersection1 = [5.5, 2.0]
        intersection2 = [5.5, -2.0]

        output = self.roundedObj.getCircleIntersections(c1, r1, c2, r2)

        self.assertEqual(2, len(output))
        self.assertEqual(intersection1, output[0])
        self.assertEqual(intersection2, output[1])

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
