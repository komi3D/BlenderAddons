'''
Created on 2 wrz 2015

@author: Komi
'''
from math import pi, radians, degrees
import unittest

from roundedprofile.coords_converter import CoordsConverter


class Test(unittest.TestCase):

    converter = None

    def setUp(self):
        self.converter = CoordsConverter()

    def tearDown(self):
        pass

    def testToXY45degRefCenter(self):
        refX = 0.0
        refY = 0.0
        alpha = radians(45)
        r = 5

        x, y = self.converter.ToXY(refX, refY, alpha, r)

        self.assertAlmostEqual(3.536, x, 3)
        self.assertAlmostEqual(3.536, y, 3)

    def testToXY135degRefCenter(self):
        refX = 0.0
        refY = 0.0
        alpha = radians(135)
        r = 5

        x, y = self.converter.ToXY(refX, refY, alpha, r)

        self.assertAlmostEqual(-3.536, x, 3)
        self.assertAlmostEqual(3.536, y, 3)

    def testToXY225degRefCenter(self):
        refX = 0.0
        refY = 0.0
        alpha = radians(225)
        r = 5

        x, y = self.converter.ToXY(refX, refY, alpha, r)

        self.assertAlmostEqual(-3.536, x, 3)
        self.assertAlmostEqual(-3.536, y, 3)

    def testToXY315degRefCenter(self):
        refX = 0.0
        refY = 0.0
        alpha = radians(315)
        r = 5

        x, y = self.converter.ToXY(refX, refY, alpha, r)

        self.assertAlmostEqual(3.536, x, 3)
        self.assertAlmostEqual(-3.536, y, 3)

    def testToXYMinus45degRefCenter(self):
        refX = 0.0
        refY = 0.0
        alpha = radians(-45)
        r = 5

        x, y = self.converter.ToXY(refX, refY, alpha, r)

        self.assertAlmostEqual(3.536, x, 3)
        self.assertAlmostEqual(-3.536, y, 3)

    def testToXY315degOtherRef(self):
        refX = 2.0
        refY = 3.0
        alpha = radians(135)
        r = 5

        x, y = self.converter.ToXY(refX, refY, alpha, r)

        self.assertAlmostEqual(-1.536, x, 3)
        self.assertAlmostEqual(6.536, y, 3)

    def testToAngularFirstQuarterRefCenter(self):

        refX = 0.0
        refY = 0.0

        x = 3.536
        y = 3.536


        alpha, r = self.converter.ToAngular(refX, refY, x, y)

        alphaDeg = degrees(alpha)
        self.assertAlmostEqual(5.0006, r, 3)
        self.assertAlmostEqual(45, alphaDeg, 3)

    def testToAngularSecondQuarterRefCenter(self):

        refX = 0.0
        refY = 0.0

        x = -3.536
        y = 3.536


        alpha, r = self.converter.ToAngular(refX, refY, x, y)

        alphaDeg = degrees(alpha)
        self.assertAlmostEqual(5.0006, r, 3)
        self.assertAlmostEqual(135, alphaDeg, 3)

    def testToAngularThirdQuarterRefCenter(self):

        refX = 0.0
        refY = 0.0

        x = -3.536
        y = -3.536


        alpha, r = self.converter.ToAngular(refX, refY, x, y)

        alphaDeg = degrees(alpha)
        self.assertAlmostEqual(5.0006, r, 3)
        self.assertAlmostEqual(225, alphaDeg, 3)

    def testToAngularFourthQuarterRefCenter(self):

        refX = 0.0
        refY = 0.0

        x = 3.536
        y = -3.536


        alpha, r = self.converter.ToAngular(refX, refY, x, y)

        alphaDeg = degrees(alpha)
        self.assertAlmostEqual(5.0006, r, 3)
        self.assertAlmostEqual(315, alphaDeg, 3)

    def testToAngularSecondQuarterRefOther(self):

        refX = 2.0
        refY = 3.0

        x = -1.536
        y = 6.536


        alpha, r = self.converter.ToAngular(refX, refY, x, y)

        alphaDeg = degrees(alpha)
        self.assertAlmostEqual(5.0006, r, 3)
        self.assertAlmostEqual(135, alphaDeg, 3)

    def testToAngularThirdQuarterRefOther(self):

        refX = 2.0
        refY = 3.0

        x = -1.536
        y = -0.536


        alpha, r = self.converter.ToAngular(refX, refY, x, y)

        alphaDeg = degrees(alpha)
        self.assertAlmostEqual(5.0006, r, 3)
        self.assertAlmostEqual(225, alphaDeg, 3)
        
    def testToAngularFourthQuarterRefOther(self):

        refX = 2.0
        refY = 3.0

        x = 5.536
        y = -0.536

        alpha, r = self.converter.ToAngular(refX, refY, x, y)

        alphaDeg = degrees(alpha)
        self.assertAlmostEqual(5.0006, r, 3)
        self.assertAlmostEqual(315, alphaDeg, 3)

    def testToAngularFourthQuarterRefOther2(self):

        refX = 2.0
        refY = 3.0

        x = 5.536
        y = -0.536

        alpha, r = self.converter.ToAngular(refX, refY, x, y)

        alphaDeg = degrees(alpha)
        self.assertAlmostEqual(5.0006, r, 3)
        self.assertAlmostEqual(315, alphaDeg, 3)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testToXYFirstQuarterRefCenter']
    unittest.main()

