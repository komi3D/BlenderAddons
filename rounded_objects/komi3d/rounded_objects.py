'''
Created on 28 cze 2015

@author: Komi
'''
from math import fabs, sqrt

from mathutils import Vector


class RoundedObjects(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        pass


    def getCenterVecAndLength(self, c1, c2):
        center_vec = c2 - c1
        center_vec_len = center_vec.length
        return (center_vec, center_vec_len)

    def getCircleIntersections(self, center1, r1, center2, r2):

        center_vec, center_vec_len = self.getCenterVecAndLength(center1, center2)
        vec = None
        sumOfRadius = r1 + r2
        differenceOfRadius = fabs(r1 - r2)

        if (sumOfRadius == center_vec_len):  # one intersection
            vec = center1 + center_vec * r1 / center_vec_len
            return [vec]
        elif (differenceOfRadius == center_vec_len):  # one intersection
            vec = center1 - center_vec * r1 / center_vec_len
            return [vec]
        elif ((sumOfRadius > center_vec_len) and (differenceOfRadius > center_vec_len)) or (sumOfRadius < center_vec_len):  # none intersections:
            return None
        elif (sumOfRadius > center_vec_len) and (differenceOfRadius < center_vec_len):  # two intersections
            return self.calculateTwoIntersections(center1, r1, center2, r2)
        else:
            return 333

    def calculateTwoIntersections(self, center1, r1, center2, r2):
        center_vec, center_vec_len = self.getCenterVecAndLength(center1, center2)
        if r1 > center_vec_len or r2 > center_vec_len :
            return self.calculateCircleIntersectionWithLargeOverlap(center1, r1, center2, r2)
        else:
            return self.calculateCircleIntersectionWithSmallOverlap(center1, r1, center2, r2)

    def calculateCircleIntersectionWithLargeOverlap(self, center1, r1, center2, r2):
        #
        center_vec, center_vec_len = self.getCenterVecAndLength(center1, center2)
        A = center_vec_len
        x = ((A ** 2 + r2 ** 2) - r1 ** 2) / (-2 * A)
        h = sqrt(r2 ** 2 - x ** 2)

        intersectionX = center2 + center_vec * (x / A)
        perpendicularVec = Vector((-center_vec[1], center_vec[0], center_vec[2]))  # TODO calculate perpendicular based on selected plane
        perpendicularVecLen = perpendicularVec.length
        intersection1 = intersectionX + perpendicularVec * (h / perpendicularVecLen)
        intersection2 = intersectionX - perpendicularVec * (h / perpendicularVecLen)

        return [intersection1, intersection2]


    def calculateCircleIntersectionWithSmallOverlap(self, center1, r1, center2, r2):
        center_vec, center_vec_len = self.getCenterVecAndLength(center1, center2)
        return 222
