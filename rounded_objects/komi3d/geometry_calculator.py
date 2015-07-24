'''
Created on 28 cze 2015

@author: Komi
'''
from math import fabs, sqrt, acos, degrees, pi

from mathutils import Vector


class GeometryCalculator(object):
    '''
    classdocs
    '''
    XY = 'XY'
    XZ = 'XZ'
    YZ = 'YZ'

    selectedPlane = XY

    def __init__(self):
        '''
        Constructor
        '''
        pass



    def getVectorAndLengthFrom2Points(self, c1, c2):
        center_vec = c2 - c1
        center_vec_len = center_vec.length
        return (center_vec, center_vec_len)

    def getCircleIntersections(self, center1, r1, center2, r2):

        center_vec, center_vec_len = self.getVectorAndLengthFrom2Points(center1, center2)
        vec = None
        sumOfRadius = r1 + r2
        differenceOfRadius = fabs(r1 - r2)

        if ((center1 == center2) and (r1 == r2)):
            return None
        if center_vec_len == 0:
            return None

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
        center_vec, center_vec_len = self.getVectorAndLengthFrom2Points(center1, center2)
        x = None
        if r1 > center_vec_len or r2 > center_vec_len :
            x = self._getXWhenCirclesHaveLargeOverlap(center_vec_len, r1, r2)
            return self.calculateCircleIntersectionsWithLargeOverlap(center1, r1, center2, r2, x)
        else:
            x = self._getXWhenCirclesHaveSmallOverlap(center_vec_len, r1, r2)
            return self.calculateCircleIntersectionsWithSmallOverlap(center1, r1, center2, r2, x)

    def _getXWhenCirclesHaveLargeOverlap(self, A, r1, r2):
        return ((A ** 2 + r2 ** 2) - r1 ** 2) / (-2 * A)

    def _getXWhenCirclesHaveSmallOverlap(self, A, r1, r2):
        return ((A ** 2 + r2 ** 2) - r1 ** 2) / (2 * A)


    def getPerpendicularVector(self, center_vec):
        if self.selectedPlane == self.XY:
            return Vector((-center_vec[1], center_vec[0], center_vec[2]))
        elif self.selectedPlane == self.YZ:
            return Vector((center_vec[0], -center_vec[2], center_vec[1]))
        elif self.selectedPlane == self.XZ:
            return Vector((-center_vec[2], center_vec[1], center_vec[0]))

    def calculateCircleIntersectionsWithLargeOverlap(self, center1, r1, center2, r2, x):
        #
        center_vec, center_vec_len = self.getVectorAndLengthFrom2Points(center1, center2)
        A = center_vec_len
        h = sqrt(r2 ** 2 - x ** 2)

        intersectionX = center2 + center_vec * (x / A)
        perpendicularVec = self.getPerpendicularVector(center_vec)  # TODO calculate perpendicular based on selected plane
        perpendicularVecLen = perpendicularVec.length
        intersection1 = intersectionX + perpendicularVec * (h / perpendicularVecLen)
        intersection2 = intersectionX - perpendicularVec * (h / perpendicularVecLen)

        return [intersection1, intersection2]

    def calculateCircleIntersectionsWithSmallOverlap(self, center1, r1, center2, r2, x):
        #
        center_vec, center_vec_len = self.getVectorAndLengthFrom2Points(center1, center2)
        A = center_vec_len
        h = sqrt(r2 ** 2 - x ** 2)

        intersectionX = center1 + center_vec * ((A - x) / A)
        perpendicularVec = self.getPerpendicularVector(center_vec)  # TODO calculate perpendicular based on selected plane
        perpendicularVecLen = perpendicularVec.length
        intersection1 = intersectionX + perpendicularVec * (h / perpendicularVecLen)
        intersection2 = intersectionX - perpendicularVec * (h / perpendicularVecLen)

        return [intersection1, intersection2]




    def getAngleBetween3Points(self, point1, point2, point3):
        p2p1Vector, p2p1Length = self.getVectorAndLengthFrom2Points(point2, point1)
        p1p3Vector, p1p3Length = self.getVectorAndLengthFrom2Points(point1, point3)
        p2p3Vector, p2p3Length = self.getVectorAndLengthFrom2Points(point2, point3)

        if p2p1Vector.normalized() == p2p3Vector.normalized() :
            angle = 0.0
            return angle, angle

        if p2p1Vector.normalized() == p2p3Vector.normalized().negate() :
            angle = pi
            return angle, degrees(angle)

        A = p2p1Length
        B = p2p3Length
        C = p1p3Length

        y = (A ** 2 + C ** 2 - B ** 2) / (2 * C)
        x = sqrt(A ** 2 - y ** 2)

        alpha = acos(x / A)
        beta = acos(x / B)
        angle = alpha + beta
        angle = self._adjustAnglePlusOrMinus(point1, point3, p2p1Vector, angle)
        angleDeg = degrees(angle)

        return (angleDeg, angle)

    def _adjustAnglePlusOrMinus(self, point1, point3, p2p1Vector, angle):
        MinusVector = self.getPerpendicularVector(p2p1Vector)
        PlusVector = (-1) * MinusVector
        P1Plus = point1 + PlusVector
        P1Minus = point1 + MinusVector
        P1PlusP3Vector, P1PlusP3Length = self.getVectorAndLengthFrom2Points(P1Plus, point3)
        P1MinusP3Vector, P1MinusP3Length = self.getVectorAndLengthFrom2Points(P1Minus, point3)
        if (P1MinusP3Length < P1PlusP3Length):
            angle = -angle
        return angle

