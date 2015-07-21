# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

bl_info = {
    "name": "Add rounded profile",
    "category": "Mesh",
    'author': 'Piotr Komisarczyk (komi3D)',
    'version': (0, 0, 1),
    'blender': (2, 7, 4),
    'location': 'SHIFT-A > Mesh > Rounded profile',
    'description': 'Add rounded profile',
    'wiki_url': '',
    'tracker_url': '',
    'category': 'Mesh'
}

from math import fabs, sqrt, acos, degrees, pi

from mathutils import Vector

import bpy
from bpy.props import *


class AddRoundedProfile(bpy.types.Operator):
    """Add rounded profile"""  # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mesh.rounded_profile_add"  # unique identifier for buttons and menu items to reference.
    bl_label = "Add rounded profile"  # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def draw(self, context):
        layout = self.layout
        layout.label('mesh.rounded_profile_add')
        row = layout.row(align = False)
        row.label('Mode:')
#         row.prop(self, 'modeEnum', expand = True, text = "a")
        row = layout.row(align = False)
        layout.label('Quick angle:')
#         layout.prop(self, 'angleEnum', expand = True, text = "abv")
        row = layout.row(align = False)
    
    def execute(self, context):
        return {'FINISHED'}

#
#
#     def __init__(self, params):
#         '''
#         Constructor
#         '''
#         pass
    
    ##### POLL #####
    @classmethod
    def poll(cls, context):
        return context.scene is not None

'''
Created on 28 cze 2015

@author: Komi
'''

# TODO How to register/unregister GeometryCalculator - so that it stays a separate class in other file??

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





################################
def menu_func(self, context):
    self.layout.operator(AddRoundedProfile.bl_idname, text = bl_info['name'], icon = "PLUGIN")
    
# def draw_item(self, context):
#     self.layout.operator_context = 'INVOKE_DEFAULT'
#     self.layout.operator('mesh.rounded_profile_add')


def register():
    # bpy.utils.register_class(AddRoundedProfile)
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_mesh_add.append(menu_func)
    pass

def unregister():
    # bpy.utils.unregister_class(AddRoundedProfile)
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_mesh_add.remove(menu_func)
    pass

if __name__ == "__main__":
    register()

