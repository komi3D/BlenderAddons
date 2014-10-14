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
    "name": "Edge Roundifier",
    "category": "Mesh",
    'author': 'Piotr Komisarczyk (komi3D), PKHG',
    'version': (0, 0, 2),
    'blender': (2, 7, 1),
    'location': 'SPACE > Edge Roundifier or CTRL-E > Edge Roundifier',
    'description': 'Mesh editing script allowing edge rounding',
    'wiki_url': '',
    'tracker_url': '',
    'category': 'Mesh'
}

import bmesh
import bpy
import bpy.props
import math
from mathutils import Vector

# CONSTANTS
XY = "XY"
XZ = "XZ"
YZ = "YZ"
SPIN_END_THRESHOLD = 0.001

# variable controlling all print functions
debug = False

def debugPrint(*text):
    if debug:
        for t in text:
            print(text)


###################################################################################
####################### Geometry and math calcualtion methods #####################

class CalculationHelper:
    def __init__(self):
        '''
        Constructor
        '''
    def getLineCoefficientsPerpendicularToVectorInPoint(self, point, vector, plane):
        x, y, z = point
        xVector, yVector, zVector = vector
        destinationPoint = (x + yVector, y - xVector, z)
        if plane == 'YZ':
            destinationPoint = (x , y + zVector, z - yVector)
        if plane == 'XZ':
            destinationPoint = (x + zVector, y, z - xVector)
        return self.getCoefficientsForLineThrough2Points(point, destinationPoint, plane)

    def getQuadraticRoots(self, coef):
        if len(coef) != 3:
            return NaN
        else:
            a, b, c = coef
            delta = self.getDelta(coef)
            if delta == 0:
                x = -b / (2 * a)
                return (x, x)
            elif delta < 0:
                return None
            else :
                x1 = (-b - math.sqrt(delta)) / (2 * a)
                x2 = (-b + math.sqrt(delta)) / (2 * a)
                return (x1, x2)

    def getDelta(self, coef):
        delta = math.pow(coef[1], 2) - 4 * coef[0] * coef[2]
        return delta

    def getCoefficientsForLineThrough2Points(self, point1, point2, plane):
        x1, y1, z1 = point1
        x2, y2, z2 = point2

        # mapping x1,x2, y1,y2 to proper values based on plane
        if plane == YZ:
            x1 = y1
            x2 = y2
            y1 = z1
            y2 = z2
        if plane == XZ:
            y1 = z1
            y2 = z2

        # Further calculations the same as for XY plane
        xabs = math.fabs(x2 - x1)
        yabs = math.fabs(y2 - y1)
        debugPrint("XABS = ", xabs)
        debugPrint("YABS = ", yabs)
        if xabs <= 0.0001:
            return None  # this means line x= edgeCenterX
        if yabs <= 0.0001:
            A = 0
            B = y1
            return A, B
        A = (y2 - y1) / (x2 - x1)
        B = y1 - (A * x1)
        return (A, B)

    def getLineCircleIntersections(self, lineAB, circleMidPoint, radius):
        # (x - a)**2 + (y - b)**2 = r**2 - circle equation
        # y = A*x + B - line equation
        # f * x**2 + g * x + h = 0 - quadratic equation
        A, B = lineAB
        a, b = circleMidPoint
        f = 1 + math.pow(A, 2)
        g = -2 * a + 2 * A * B - 2 * A * b
        h = math.pow(B, 2) - 2 * b * B - math.pow(radius, 2) + math.pow(a, 2) + math.pow(b, 2)
        coef = [f, g, h]
        roots = self.getQuadraticRoots(coef)
        if roots != None:
            x1 = roots[0]
            x2 = roots[1]
            point1 = [x1, A * x1 + B]
            point2 = [x2, A * x2 + B]
            return [point1, point2]
        else:
            return None

    def getLineCircleIntersectionsWhenXPerpendicular(self, edgeCenter, circleMidPoint, radius, plane):
        # (x - a)**2 + (y - b)**2 = r**2 - circle equation
        # x = xValue - line equation
        # f * x**2 + g * x + h = 0 - quadratic equation
        # TODO fix it for planes other then
        xValue = edgeCenter[0]
        if plane == YZ:
            xValue = edgeCenter[1]
        if plane == XZ:
            xValue = edgeCenter[0]

        a, b = circleMidPoint
        f = 1
        g = -2 * b
        h = math.pow(a, 2) + math.pow(b, 2) + math.pow(xValue, 2) - 2 * a * xValue - math.pow(radius, 2)
        coef = [f, g, h]
        roots = self.getQuadraticRoots(coef)
        if roots != None:
            y1 = roots[0]
            y2 = roots[1]
            point1 = [xValue, y1]
            point2 = [xValue, y2]
            return [point1, point2]
        else:
            return None

    def getEdgeLength(self, point1, point2):
        x1, y1, z1 = point1
        x2, y2, z2 = point2
        # TODO assupmtion Z=0
        length = math.sqrt(math.pow(x2 - x1, 2) + math.pow(y2 - y1, 2) + math.pow(z2 - z1, 2))
        return length

    # point1 is the point near 90 deg angle
    def getAngle(self, point1, point2, point3):
        distance1 = self.getEdgeLength(point1, point2)
        distance2 = self.getEdgeLength(point2, point3)
        cos = distance1 / distance2
        if abs(cos) > 1:  # prevents Domain Error
            cos = round(cos)
        alpha = math.acos(cos)
        degAlpha = (alpha / (math.pi * 2)) * 360
        return (alpha, degAlpha)

    def getVectorBetween2VertsXYZ(self, vert1, vert2):
        output = [vert2[0] - vert1[0], vert2[1] - vert1[1], vert2[2] - vert1[2]]
        return output

    def getVectorLength(self, vector):
        return self.getEdgeLength([0, 0, 0], vector)

    def getNormalizedVector(self, vector):
        v = Vector(vector)
        return v.normalized()

    def getCenterBetween2VertsXYZ(self, vert1, vert2):
        vector = self.getVectorBetween2VertsXYZ(vert1, vert2)
        halfvector = [vector[0] / 2, vector[1] / 2, vector[2] / 2]
        center = (vert1[0] + halfvector[0], vert1[1] + halfvector[1], vert1[2] + halfvector[2])
        return center

    # get two of three coordinates used for further calculation of spin center
    def getCircleMidPointOnPlane(self, V1, plane):
        X = V1[0]
        Y = V1[1]
        if plane == 'XZ':
            X = V1[0]
            Y = V1[2]
        elif plane == 'YZ':
            X = V1[1]
            Y = V1[2]
        return [X, Y]

########################################################
################# SELECTION METHODS ####################

class SelectionHelper:
    def selectVertexInMesh(self, mesh, vertex):
        bpy.ops.object.mode_set(mode = "OBJECT")
        for v in mesh.vertices:
            if (v.co[0] == vertex[0]) and (v.co[1] == vertex[1]) and (v.co[2] == vertex[2]):
                v.select = True
                break

        bpy.ops.object.mode_set(mode = "EDIT")

    def getSelectedVertex(self, mesh):
        bpy.ops.object.mode_set(mode = "OBJECT")
        for v in mesh.vertices:
            if v.select == True :
                bpy.ops.object.mode_set(mode = "EDIT")
                return v

        bpy.ops.object.mode_set(mode = "EDIT")
        return None

    def refreshMesh(self, bm, mesh):
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bm.to_mesh(mesh)
        bpy.ops.object.mode_set(mode = 'EDIT')



###################################################################################

class EdgeRoundifier(bpy.types.Operator):
    """Edge Roundifier"""  # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mesh.edge_roundifier"  # unique identifier for buttons and menu items to reference.
    bl_label = "Edge Roundifier"  # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    threshold = 0.0005  # used for remove doubles and edge selection at the end
# TODO:
# 1) offset - move arcs perpendicular to edges
# 2) allow other spin axes X and Y (global)

    r = bpy.props.FloatProperty(name = '', default = 1, min = 0.00001, max = 1000.0, step = 0.1, precision = 3)
    a = bpy.props.FloatProperty(name = '', default = 180, min = 0.1, max = 180.0, step = 0.5, precision = 1)
    n = bpy.props.IntProperty(name = '', default = 4, min = 1, max = 100, step = 1)
    flip = bpy.props.BoolProperty(name = 'flip', default = False)
    invertAngle = bpy.props.BoolProperty(name = 'invertAngle', default = False)
    fullCircles = bpy.props.BoolProperty(name = 'fullCircles', default = False)
    removeDoubles = bpy.props.BoolProperty(name = 'removeDoubles', default = False)
    # FUTURE TODO: OFFSET
    # offset = bpy.props.BoolProperty(name = 'offset', default = False)

    modeItems = [('Radius', "Radius", ""), ("Angle", "Angle", "")]
    modeEnum = bpy.props.EnumProperty(
        items = modeItems,
        name = '',
        default = 'Radius',
        description = "Edge Roundifier mode")

    angleItems = [('Other', "Other", "User defined angle"), ('180', "180", "HemiCircle"), ('120', "120", "TriangleCircle"),
                    ('90', "90", "QuadCircle"), ('60', "60", "HexagonCircle"),
                    ('45', "45", "OctagonCircle"), ('30', "30", "12-gonCircle")]

    angleEnum = bpy.props.EnumProperty(
        items = angleItems,
        name = '',
        default = 'Other',
        description = "Presets prepare standard angles and calculate proper ray")

    refItems = [('ORG', "Origin", "Use Origin Location"), ('CUR', "3D Cursor", "Use 3DCursor Location")]
    referenceLocation = bpy.props.EnumProperty(
        items = refItems,
        name = '',
        default = 'ORG',
        description = "Reference location used by Edge Roundifier to calculate initial centers of drawn arcs")

    planeItems = [(XY, XY, "XY Plane (Z=0)"), (YZ, YZ, "YZ Plane (X=0)"), (XZ, XZ, "XZ Plane (Y=0)")]
    planeEnum = bpy.props.EnumProperty(
        items = planeItems,
        name = '',
        default = 'XY',
        description = "Plane used by Edge Roundifier to calculate spin plane of drawn arcs")


    calc = CalculationHelper()
    sel = SelectionHelper()

    def prepareMesh(self, context):
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.mode_set(mode = 'EDIT')

        mesh = context.scene.objects.active.data
        bm = bmesh.new()
        bm.from_mesh(mesh)
        edges = self.getSelectedEdges(bm)
        return edges, mesh, bm

    def prepareParameters(self):

        parameters = { "a" : "a"}
        parameters["plane"] = self.planeEnum
        parameters["radius"] = self.r
        parameters["angle"] = self.a
        parameters["segments"] = self.n
        parameters["flip"] = self.flip
        parameters["fullCircles"] = self.fullCircles
        parameters["invertAngle"] = self.invertAngle
        parameters["angleEnum"] = self.angleEnum
        parameters["modeEnum"] = self.modeEnum
        parameters["refObject"] = self.referenceLocation
        parameters["removeDoubles"] = self.removeDoubles
        # FUTURE TODO OFFSET
        # parameters["offset"] = self.offset
        return parameters

    def draw(self, context):
        layout = self.layout
        layout.label('Note: possible radius >= edge_length/2.')
        row = layout.row(align = False)
        row.label('Mode:')
        row.prop(self, 'modeEnum', expand = True, text = "a")
        row = layout.row(align = False)
        layout.label('Quick angle:')
        layout.prop(self, 'angleEnum', expand = True, text = "abv")
        row = layout.row(align = False)
        row.label('Angle:')
        row.prop(self, 'a')
        row = layout.row(align = False)
        row.label('Radius:')
        row.prop(self, 'r')
        row = layout.row(align = True)
        row.label('Segments:')
        row.prop(self, 'n', slider = True)
        row = layout.row(align = False)
        row.prop(self, 'flip')
        row.prop(self, 'invertAngle')
        row = layout.row(align = False)
        row.prop(self, 'fullCircles')
        row.prop(self, 'removeDoubles')
        # FUTURE TODO OFFSET
        # row.prop(self, 'offset')

        layout.label('Reference Location:')
        layout.prop(self, 'referenceLocation', expand = True, text = "a")

        layout.label('Working Plane (LOCAL coordinates):')
        layout.prop(self, 'planeEnum', expand = True, text = "a")


    def execute(self, context):

        edges, mesh, bm = self.prepareMesh(context)
        parameters = self.prepareParameters()

        debugPrint ("EDGES ", edges)

        if len(edges) > 0:
            self.roundifyEdges(edges, parameters, bm, mesh)
            self.sel.refreshMesh(bm, mesh)
            if parameters["removeDoubles"] == True:
                bpy.ops.mesh.select_all(action = "SELECT")
                bpy.ops.mesh.remove_doubles(threshold = self.threshold)
                bpy.ops.mesh.select_all(action = "DESELECT")

            self.selectEdgesAfterRoundifier(context, edges)
        else:
            debugPrint("No edges selected!")

        bm.free()
        return {'FINISHED'}

##########################################
    def roundifyEdges(self, edges, parameters, bm, mesh):
        for e in edges:
            self.roundify(e, parameters, bm, mesh)


    def getEdgeInfo(self, edge):
        vertices = self.getVerticesFromEdge(edge)
        v1, v2 = vertices
        V1 = [v1.co.x, v1.co.y, v1.co.z]
        V2 = [v2.co.x, v2.co.y, v2.co.z]
        edgeVector = self.calc.getVectorBetween2VertsXYZ(V1, V2)
        edgeLength = self.calc.getVectorLength(edgeVector)
        edgeCenter = self.calc.getCenterBetween2VertsXYZ(V1, V2)
        debugPrint("Edge info======================================")
        debugPrint("V1 info==============")
        debugPrint(V1)
        debugPrint("V2 info==============")
        debugPrint(V2)
        debugPrint("Edge Length==============")
        debugPrint(edgeLength)
        debugPrint("Edge Center==============")
        debugPrint(edgeCenter)
        debugPrint("Edge info======================================")
        return V1, V2, edgeVector, edgeLength, edgeCenter

    def roundify(self, edge, parameters, bm, mesh):

        V1, V2, edgeVector, edgeLength, edgeCenter = self.getEdgeInfo(edge)
        if self.skipThisEdge(V1, V2, parameters["plane"]):
            return

        roundifyParams = self.calculateRoundifyParams(edge, parameters, bm, mesh)
        self.drawSpin(edge, edgeCenter, roundifyParams, parameters, bm, mesh)

    def skipThisEdge(self, V1, V2, plane):
        # Check If It is possible to spin selected verts on this plane if not exit roundifier
        if(plane == XY):
            if (V1[0] == V2[0] and V1[1] == V2[1]):
                return True
        elif(plane == YZ):
            if (V1[1] == V2[1] and V1[2] == V2[2]):
                return True
        elif(plane == XZ):
            if (V1[0] == V2[0] and V1[2] == V2[2]):
                return True
        return False

    def calculateRoundifyParams(self, edge, parameters, bm, mesh):
        # BECAUSE ALL DATA FROM MESH IS IN LOCAL COORDINATES
        # AND SPIN OPERATOR WORKS ON GLOBAL COORDINATES
        # WE FIRST NEED TO TRANSLATE ALL INPUT DATA BY VECTOR EQUAL TO ORIGIN POSITION AND THEN PERFORM CALCULATIONS
        # At least that is my understanding :) <komi3D>

        # V1 V2 stores Local Coordinates
        V1, V2, edgeVector, edgeLength, edgeCenter = self.getEdgeInfo(edge)

        debugPrint("PLANE: ", parameters["plane"])
        lineAB = self.calc.getLineCoefficientsPerpendicularToVectorInPoint(edgeCenter, edgeVector, parameters["plane"])
        debugPrint("Line Coefficients:", lineAB)
        circleMidPoint = V1
        circleMidPointOnPlane = self.calc.getCircleMidPointOnPlane(V1, parameters["plane"])
        radius = parameters["radius"]
        
        if radius < edgeLength/2:
            radius = edgeLength/2
            parameters["radius"] = edgeLength/2 
        
        angle = 0
        if (parameters["modeEnum"] == 'Angle'):
            if (parameters["angleEnum"] != 'Other'):
                radius, angle = self.CalculateRadiusAndAngleForAnglePresets(parameters["angleEnum"], radius, angle, edgeLength)
            else:
                radius, angle = self.CalculateRadiusAndAngleForOtherAngle(edgeLength)

        debugPrint("RADIUS = ", radius)
        debugPrint("ANGLE = ", angle)
        roots = None
        if angle != math.pi:  # mode other than 180
            if lineAB == None:
                roots = self.calc.getLineCircleIntersectionsWhenXPerpendicular(edgeCenter, circleMidPointOnPlane, radius, parameters["plane"])
            else:
                roots = self.calc.getLineCircleIntersections(lineAB, circleMidPointOnPlane, radius)
            if roots == None:
                debugPrint("No centers were found. Change radius to higher value")
                return None
            roots = self.addMissingCoordinate(roots, V1, parameters["plane"])  # adds X, Y or Z coordinate

        else:
            roots = [edgeCenter, edgeCenter]
        debugPrint("roots=")
        debugPrint(roots)

        refObjectLocation = None
        objectLocation = bpy.context.active_object.location  # Origin Location

        if parameters["refObject"] == "ORG":
            refObjectLocation = [0, 0, 0]
        else:
            refObjectLocation = bpy.context.scene.cursor_location
#             print("3D cursor Translated:")
#             print(bpy.context.scene.cursor_location)
#             print(objectLocation
#             print(refObjectLocation)

        print(parameters["refObject"])
        chosenSpinCenter = self.getSpinCenterClosestToRefCenter(refObjectLocation, roots, parameters["flip"])

        if (parameters["modeEnum"] == "Radius"):
            halfAngle = self.calc.getAngle(edgeCenter, chosenSpinCenter, circleMidPoint)
            angle = 2 * halfAngle[0]  # in radians
            self.a = math.degrees(angle)  # in degrees

        spinAxis = self.getSpinAxis(parameters["plane"])

        if(parameters["invertAngle"]):
            angle = -2 * math.pi + angle

        if(parameters["fullCircles"]):
            angle = 2 * math.pi

        # FUTURE TODO OFFSET
#        if parameters["offset"]:
#            offset = self.getOffsetVectorForTangency(edgeCenter, chosenSpinCenter, radius, self.invertAngle)
#            self.moveSelectedVertexByVector(mesh,offset)
#            chosenSpinCenterOffset = self.translateByVector(chosenSpinCenter, offset)
#            chosenSpinCenter = chosenSpinCenterOffset

        steps = parameters["segments"]

        if parameters["fullCircles"] == False and parameters["flip"] == True:
            angle = -angle
        X = [chosenSpinCenter, spinAxis, angle, steps, refObjectLocation]
        print (X)
        return X





    def drawSpin(self, edge, edgeCenter, roundifyParams, parameters, bm, mesh):
        [chosenSpinCenter, spinAxis, angle, steps, refObjectLocation] = roundifyParams

        (v0org, v1org) = self.getVerticesFromEdge(edge)

        # Duplicate initial vertex
        v0 = bm.verts.new(v0org.co)

        print("chosenSpinCenter= ")
        print(chosenSpinCenter)

        result = bmesh.ops.spin(bm, geom = [v0], cent = chosenSpinCenter, axis = spinAxis, \
                                   angle = angle, steps = steps, use_duplicate = False)

        print ("LEN after=")
        print(len(bm.verts))

        # it seems there is something wrong with last index of this spin...
        # I need to calculate the last index manually here...
        vertsLength = len(bm.verts)
        lastVertIndex = bm.verts[vertsLength - 1].index
        lastSpinVertIndices = self.getLastSpinVertIndices(steps, lastVertIndex)

        print("result1:")
        print(lastVertIndex)
        print(lastSpinVertIndices)
        #TODO CLean UP!!!

        if (angle == math.pi or angle == -math.pi):

            midVertexIndex = lastVertIndex - round(steps / 2)
            midVert = bm.verts[midVertexIndex].co

            midVertexDistance = self.calc.getEdgeLength(refObjectLocation, midVert)
            midEdgeDistance = self.calc.getEdgeLength(refObjectLocation, edgeCenter)

            print("midVertexDistance: ")
            print(midVertexDistance)
            print("midEdgeDistance: ")
            print(midEdgeDistance)

            if (parameters["invertAngle"]) or (parameters["flip"]):
                if (midVertexDistance > midEdgeDistance):
                    self.alternateSpin(bm, mesh, angle, chosenSpinCenter, spinAxis, steps, v0, v1org, lastSpinVertIndices)
            else:
                if (midVertexDistance < midEdgeDistance):
                    self.alternateSpin(bm, mesh, angle, chosenSpinCenter, spinAxis, steps, v0, v1org, lastSpinVertIndices)
        elif (angle != 2 * math.pi):  # to allow full circles :)
            if (result['geom_last'][0].co - v1org.co).length > SPIN_END_THRESHOLD:
                self.alternateSpin(bm, mesh, angle, chosenSpinCenter, spinAxis, steps, v0, v1org, lastSpinVertIndices)

        self.sel.refreshMesh(bm, mesh)

##########################################


    def deleteSpinVertices(self, bm, mesh, lastSpinVertIndices):
        verticesForDeletion = []
        for i in lastSpinVertIndices:
            vi = bm.verts[i]
            vi.select = True
            print(str(i) + ") " + str(vi))
            verticesForDeletion.append(vi)

        bmesh.ops.delete(bm, geom = verticesForDeletion, context = 1)
        bmesh.update_edit_mesh(mesh, True)
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.mode_set(mode = 'EDIT')


    def alternateSpin(self, bm, mesh, angle, chosenSpinCenter, spinAxis, steps, v0, v1org, lastSpinVertIndices):
        print("== begin alternate spin ==")
        for v in bm.verts:
            print (v.index)
        print("== indices for deletion ==")
        print(lastSpinVertIndices)
        for i in lastSpinVertIndices:
            print (i)

        self.deleteSpinVertices(bm, mesh, lastSpinVertIndices)
#        v0prim = bm.verts.new(v0.co)
        v0prim = v0
        print("== v0prim index: ==")
        print(v0prim.index)

        print("== BEFORE 2nd spin performed==")
        for v in bm.verts:
            print (v.index)

        print ("LEN before=")
        print(len(bm.verts))

        result2 = bmesh.ops.spin(bm, geom = [v0prim], cent = chosenSpinCenter, axis = spinAxis,
            angle = -angle, steps = steps, use_duplicate = False)
        # it seems there is something wrong with last index of this spin...
        # I need to calculate the last index manually here...
        print ("LEN after=")
        print(len(bm.verts))
        vertsLength = len(bm.verts)
        lastVertIndex2 = bm.verts[vertsLength - 1].index
        print("== 2nd spin performed==")
        for v in bm.verts:
            print (v.index)

        print("last:")
        print(result2['geom_last'][0].index)


# second spin also does not hit the v1org
        if (result2['geom_last'][0].co - v1org.co).length > SPIN_END_THRESHOLD:
            lastSpinVertIndices2 = self.getLastSpinVertIndices(steps, lastVertIndex2)
            print("== lastVertIndex2: ==")
            print(result2['geom_last'][0].index)
            print(lastVertIndex2)

            print("== 2nd spin ==")
            for v in bm.verts:
                print (v.index)
            print("== indices for deletion ==")
            print(lastSpinVertIndices2)
            for i in lastSpinVertIndices2:
                print (i)

            print("result2:")
            print(lastSpinVertIndices2)
            self.deleteSpinVertices(bm, mesh, lastSpinVertIndices2)
            self.deleteSpinVertices(bm, mesh, range(v0.index, v0.index + 1))


    def getLastSpinVertIndices(self, steps, lastVertIndex):
        arcfirstVertexIndex = lastVertIndex - steps + 1
        lastSpinVertIndices = range(arcfirstVertexIndex, lastVertIndex + 1)
        return lastSpinVertIndices


    def getOffsetVectorForTangency(self, edgeCenter, chosenSpinCenter, radius, invertAngle):
        if invertAngle == False:
            edgeCentSpinCentVector = self.calc.getVectorBetween2VertsXYZ(edgeCenter, chosenSpinCenter)
        else:
            edgeCentSpinCentVector = self.calc.getVectorBetween2VertsXYZ(chosenSpinCenter, edgeCenter)

        vectorLength = self.calc.getVectorLength(edgeCentSpinCentVector)
        if invertAngle == False:
            offsetLength = radius - vectorLength
        else:
            offsetLength = radius + vectorLength
        normalizedVector = self.calc.getNormalizedVector(edgeCentSpinCentVector)
        offsetVector = (offsetLength * normalizedVector[0],
                        offsetLength * normalizedVector[1],
                        offsetLength * normalizedVector[2])
        return offsetVector

    def moveSelectedVertexByVector(self, mesh, offset):
        vert = self.sel.getSelectedVertex(mesh)
        vert.co.x = vert.co.x + offset[0]
        vert.co.y = vert.co.y + offset[1]
        vert.co.z = vert.co.z + offset[2]

    def translateRoots(self, roots, objectLocation):
        # translationVector = self.calc.getVectorBetween2VertsXYZ(objectLocation, [0,0,0])
        r1 = self.translateByVector(roots[0], objectLocation)
        r2 = self.translateByVector(roots[1], objectLocation)
        return [r1, r2]

    def getOppositeVector(self, originalVector):
        x, y, z = originalVector
        return [-x, -y, -z]

    def translateByVector(self, point, vector):
        translated = (point[0] + vector[0],
        point[1] + vector[1],
        point[2] + vector[2])
        return translated

    def CalculateRadiusAndAngleForOtherAngle(self, edgeLength):
        degAngle = self.a
        angle = math.radians(degAngle)
        self.r = radius = edgeLength / (2 * math.sin(angle / 2))
        return radius, angle

    def CalculateRadiusAndAngleForAnglePresets(self, mode, initR, initA, edgeLength):
        radius = initR
        angle = initA

        if mode == "180":
            radius = edgeLength / 2
            angle = math.pi
        elif mode == "120":
            radius = edgeLength / 3 * math.sqrt(3)
            angle = 2 * math.pi / 3
        elif mode == "90":
            radius = edgeLength / 2 * math.sqrt(2)
            angle = math.pi / 2
        elif mode == "60":
            radius = edgeLength
            angle = math.pi / 3
        elif mode == "45":
            radius = edgeLength / (2 * math.sin(math.pi / 8))
            angle = math.pi / 4
        elif mode == "30":
            radius = edgeLength / (2 * math.sin(math.pi / 12))
            angle = math.pi / 6
        self.a = math.degrees(angle)
        self.r = radius
        debugPrint ("mode output, radius = ", radius, "angle = ", angle)
        return radius, angle

    def getSpinCenterClosestToRefCenter(self, objLocation, roots, flip):
        root0Distance = self.calc.getEdgeLength(objLocation, roots[0])
        root1Distance = self.calc.getEdgeLength(objLocation, roots[1])
#         print("------------------------------")
#         print(objLocation)
#         print("roots[0]: ")
#         print(roots[0])
#         #print(translatedRoots[0])
#         print(root0Distance)
#         print("roots[1]: ")
#         print(roots[1])
#         #print(translatedRoots[1])
#         print(root1Distance)

        chosenId = 0
        rejectedId = 1
        if (root0Distance > root1Distance):
            chosenId = 1
            rejectedId = 0
        if flip == True:
            return roots[rejectedId]
        else:
            return roots[chosenId]

    def addMissingCoordinate(self, roots, startVertex, plane):
        if roots != None:
            a, b = roots[0]
            c, d = roots[1]
            if plane == XY:
                roots[0] = [a, b, startVertex[2]]
                roots[1] = [c, d, startVertex[2]]
            if plane == YZ:
                roots[0] = [startVertex[0], a, b]
                roots[1] = [startVertex[0], c, d]
            if plane == XZ:
                roots[0] = [a, startVertex[1], b]
                roots[1] = [c, startVertex[1], d]
        return roots

    def getSelectedEdges(self, bm):
        listOfSelectedEdges = []
        for e in bm.edges:
            if e.select == True:
                debugPrint("edges:", e)
                listOfSelectedEdges.append(e)
        return listOfSelectedEdges

    def selectEdgesAfterRoundifier(self, context, edges):
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.mode_set(mode = 'EDIT')
        mesh = context.scene.objects.active.data
        bmnew = bmesh.new()
        bmnew.from_mesh(mesh)
        self.deselectEdges(bmnew)
        for selectedEdge in edges:
            for e in bmnew.edges:
                if math.fabs(e.verts[0].co.x - selectedEdge.verts[0].co.x) <= self.threshold \
                and math.fabs(e.verts[0].co.y - selectedEdge.verts[0].co.y) <= self.threshold \
                and math.fabs(e.verts[0].co.y - selectedEdge.verts[0].co.y) <= self.threshold \
                and math.fabs(e.verts[1].co.x - selectedEdge.verts[1].co.x) <= self.threshold \
                and math.fabs(e.verts[1].co.y - selectedEdge.verts[1].co.y) <= self.threshold \
                and math.fabs(e.verts[1].co.y - selectedEdge.verts[1].co.y) <= self.threshold:
                    e.select_set(True)

        bpy.ops.object.mode_set(mode = 'OBJECT')
        bmnew.to_mesh(mesh)
        bmnew.free()
        bpy.ops.object.mode_set(mode = 'EDIT')


    def deselectEdges(self, bm):
        for edge in bm.edges:
            edge.select_set(False)


    def getVerticesFromEdge(self, edge):
        v1 = edge.verts[0]
        v2 = edge.verts[1]
        return (v1, v2)

    def debugPrintEdgesInfo(self, edges):
        debugPrint("=== Selected edges ===")
        for e in edges:
            v1 = e.verts[0]
            v2 = e.verts[1]
            debugPrint(v1.co.x, v1.co.y, v1.co.z)
            debugPrint(v2.co.x, v2.co.y, v2.co.z)
            debugPrint("----------")

    def getSpinAxis(self, plane):
        axis = (0, 0, 1)
        if plane == YZ:
            axis = (1, 0, 0)
        if plane == XZ:
            axis = (0, 1, 0)
        return axis


    @classmethod
    def poll(cls, context):
        return (context.scene.objects.active.type == 'MESH') and (context.scene.objects.active.mode == 'EDIT')



def draw_item(self, context):
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator('mesh.edge_roundifier')


def register():
    bpy.utils.register_class(EdgeRoundifier)
    bpy.types.VIEW3D_MT_edit_mesh_edges.append(draw_item)


def unregister():
    bpy.utils.unregister_class(EdgeRoundifier)
    bpy.types.VIEW3D_MT_edit_mesh_edges.remove(draw_item)

if __name__ == "__main__":
    register()


