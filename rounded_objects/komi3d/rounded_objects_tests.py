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


    def testVectorAdding(self):
        v1 = Vector((2, 3, 0))
        v2 = Vector((2, 3, 0))
        result = Vector((4, 6, 0))

        self.assertEqual(result, v1 + v2)
        
    def testVectorLength(self):
        v1 = Vector((1, 1, 0))
        length = v1.length
        
        self.assertEqual(sqrt(2), length)
        
    def test1(self):
        c1 = Vector((0, 0, 0))
        r1 = 2.0
        c2 = Vector((4, 0, 0))
        r2 = 2.0
        intersection = Vector((2, 0, 0))

        output = self.roundedObj.getCircleIntersections(c1, r1, c2, r2)

        self.assertEqual(intersection, output)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
