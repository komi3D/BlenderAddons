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
    'version': (2, 0, 0),
    'blender': (2, 7, 8),
    'location': 'SPACE > Edge Roundifier or CTRL-E > Edge Roundifier or Tools > Addons > Edge Roundifier',
    'description': 'Mesh editing script allowing edge rounding',
    'wiki_url': '',
    'tracker_url': '',
    'category': 'Mesh'
}

import bmesh
import bpy
import bpy.props
import imp
from math import sqrt, acos, asin, pi, radians, degrees, sin, acos, cos
from mathutils import Vector, Euler, Matrix, Quaternion
from time import sleep
import types


# CONSTANTS
two_pi = 2 * pi  # PKHG>??? maybe other constantly used values too???
XY = "XY"
XZ = "XZ"
YZ = "YZ"
SPIN_END_THRESHOLD = 0.001
LINE_TOLERANCE = 0.0001


# variable controlling all print functions
# PKHG>??? to be replaced, see debugPrintNew ;-)
debug = True


def debugPrint(*text):
    if debug:
        for t in text:
            print(text)


############# for debugging PKHG ################
def debugPrintNew(debug, *text):
    if debug:
        tmp = [el for el in text]
        for row in tmp:
            print(row)

d_XABS_YABS = False
d_Edge_Info = False
d_Plane = False
d_Radius_Angle = False
d_Roots = False
d_RefObject = False
d_LineAB = False
d_Selected_edges = False
d_Rotate_Around_Spin_Center = False
##########################################################################


def isAngleDifferentFromPredefined(angle):
    return (angle != 30 and angle != 45 and angle != 60
            and angle != 72 and angle != 90 and angle != 120 and angle != 180)


def updateAngleForAnglePresets(self, context):
    activeOperator = context.active_operator
    if activeOperator != None:
        if activeOperator.angleEnum == "180":
            activeOperator.a = 180
        elif activeOperator.angleEnum == "120":
            activeOperator.a = 120
        elif activeOperator.angleEnum == "90":
            activeOperator.a = 90
        elif activeOperator.angleEnum == "72":
            activeOperator.a = 72
        elif activeOperator.angleEnum == "60":
            activeOperator.a = 60
        elif activeOperator.angleEnum == "45":
            activeOperator.a = 45
        elif activeOperator.angleEnum == "30":
            activeOperator.a = 30


def updateAnglePresetsForAngle(self, context):
    activeOperator = context.active_operator
    if activeOperator != None:
        if isAngleDifferentFromPredefined(activeOperator.a):
            activeOperator.angleEnum = "Other"


class EdgeWorksPanel(bpy.types.Panel):
    bl_label = "Edge Works"
    bl_idname = "EdgeWorksPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Addons"

    @classmethod
    def poll(cls, context):
        return (context.object is not None and context.object.type == "MESH")

    def draw(self, context):
        row = self.layout.row(True)
        col = row.column(True)
        col.operator(EdgeRoundifier.bl_idname, text="Edge Roundifier")


####################### Geometry and math calcualtion methods ############

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
            destinationPoint = (x, y + zVector, z - yVector)
        if plane == 'XZ':
            destinationPoint = (x + zVector, y, z - xVector)
        return self.getCoefficientsForLineThrough2Points(point, destinationPoint, plane)

    def getQuadraticRoots(self, coef):
        if len(coef) != 3:
            return NaN
        else:
            a, b, c = coef
            delta = b ** 2 - 4 * a * c
            if delta == 0:
                x = -b / (2 * a)
                return (x, x)
            elif delta < 0:
                return None
            else:
                x1 = (-b - sqrt(delta)) / (2 * a)
                x2 = (-b + sqrt(delta)) / (2 * a)
                return (x1, x2)

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
        xabs = abs(x2 - x1)
        yabs = abs(y2 - y1)
        debugPrintNew(d_XABS_YABS, "XABS = " +
                      str(xabs) + " YABS = " + str(yabs))

        if xabs <= LINE_TOLERANCE:
            return None  # this means line x = edgeCenterX
        if yabs <= LINE_TOLERANCE:
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
        f = 1 + (A ** 2)
        g = -2 * a + 2 * A * B - 2 * A * b
        h = (B ** 2) - 2 * b * B - (radius ** 2) + (a ** 2) + (b ** 2)
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
        xValue = edgeCenter[0]
        if plane == YZ:
            xValue = edgeCenter[1]
        if plane == XZ:
            xValue = edgeCenter[0]

        a, b = circleMidPoint
        f = 1
        g = -2 * b
        h = (a ** 2) + (b ** 2) + (xValue ** 2) - \
            2 * a * xValue - (radius ** 2)
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

    # point1 is the point near 90 deg angle
    def getAngle(self, point1, point2, point3):
        distance1 = (Vector(point1) - Vector(point2)).length
        distance2 = (Vector(point2) - Vector(point3)).length
        cos = distance1 / distance2

        if abs(cos) > 1:  # prevents Domain Error
            cos = round(cos)

        alpha = acos(cos)
        return (alpha, degrees(alpha))

    # get two of three coordinates used for further calculation of spin center
    # PKHG>nice if rescriction to these 3 types or planes is to be done
    # komi3D> from 0.0.2 there is a restriction. In future I would like Edge Roundifier to work on
    # komi3D> Normal and View coordinate systems. That would be great...
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

    def getEdgeReference(self, edge, edgeCenter, plane):
        vert1 = edge.verts[1].co
        V = vert1 - edgeCenter
        orthoVector = Vector((V[1], -V[0], V[2]))
        if plane == 'XZ':
            orthoVector = Vector((V[2], V[1], -V[0]))
        elif plane == 'YZ':
            orthoVector = Vector((V[0], V[2], -V[1]))
        refPoint = edgeCenter + orthoVector
        return refPoint


########################################################
################# SELECTION METHODS ####################

class SelectionHelper:

    def selectVertexInMesh(self, mesh, vertex):
        bpy.ops.object.mode_set(mode="OBJECT")
        for v in mesh.vertices:
            if v.co == vertex:
                v.select = True
                break

        bpy.ops.object.mode_set(mode="EDIT")

    def getSelectedVertex(self, mesh):
        bpy.ops.object.mode_set(mode="OBJECT")
        for v in mesh.vertices:
            if v.select == True:
                bpy.ops.object.mode_set(mode="EDIT")
                return v

        bpy.ops.object.mode_set(mode="EDIT")
        return None

    def refreshMesh(self, bm, mesh):
        bpy.ops.object.mode_set(mode='OBJECT')
        bm.to_mesh(mesh)
        bpy.ops.object.mode_set(mode='EDIT')

##########################################################################


class EdgeRoundifier(bpy.types.Operator):
    """Edge Roundifier"""  # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mesh.edge_roundifier"  # unique identifier for buttons and menu items to reference.
    bl_label = "Edge Roundifier"  # display name in the interface.
    # enable undo for the operator.PKHG>INFO and PRESET
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    threshold = 0.0001
    obj = None

    calc = CalculationHelper()
    sel = SelectionHelper()

    index = 0

    arcCentersArr = []

    edgeScaleFactor = bpy.props.FloatProperty(
        name='', default=1.0, min=0.00001, max=100000.0, step=0.5, precision=5)
    r = bpy.props.FloatProperty(
        name='', default=1, min=0.00001, max=1000.0, step=0.1, precision=3)
    a = bpy.props.FloatProperty(name='', default=180.0, min=0.1, max=180.0,
                                step=0.5, precision=1, update=updateAnglePresetsForAngle)
    n = bpy.props.IntProperty(name='', default=4, min=1, max=100, step=1)
    flip = bpy.props.BoolProperty(name='Flip', default=False)

    invertAngle = bpy.props.BoolProperty(name='Invert', default=False)
    fullCircles = bpy.props.BoolProperty(name='Circles', default=False)
    bothSides = bpy.props.BoolProperty(name='Both sides', default=False)

    removeEdges = bpy.props.BoolProperty(name='Edges', default=False)
    removeScaledEdges = bpy.props.BoolProperty(
        name='Scaled edges', default=False)

    connectArcWithEdge = bpy.props.BoolProperty(
        name='Arc - Edge', default=False)
    connectArcs = bpy.props.BoolProperty(name='Arcs', default=False)
    connectScaledAndBase = bpy.props.BoolProperty(
        name='Scaled - Base Edge', default=False)
    connectArcsFlip = bpy.props.BoolProperty(name='Flip Arcs', default=False)
    connectArcWithEdgeFlip = bpy.props.BoolProperty(
        name='Flip Arc - Edge', default=False)

    axisAngle = bpy.props.FloatProperty(
        name='', default=0.0, min=-180.0, max=180.0, step=0.5, precision=1)
    edgeAngle = bpy.props.FloatProperty(
        name='', default=0.0, min=-180.0, max=180.0, step=0.5, precision=1)
    offset = bpy.props.FloatProperty(
        name='', default=0.0, min=-1000000.0, max=1000000.0, step=0.1, precision=5)
    offset2 = bpy.props.FloatProperty(
        name='', default=0.0, min=-1000000.0, max=1000000.0, step=0.1, precision=5)
    ellipticFactor = bpy.props.FloatProperty(
        name='', default=0.0, min=-1000000.0, max=1000000.0, step=0.1, precision=5)

    workModeItems = [("Normal", "Normal", ""), ("Reset", "Reset", "")]
    workMode = bpy.props.EnumProperty(
        items=workModeItems,
        name='',
        default='Normal',
        description="Edge Roundifier work mode")

    entryModeItems = [("Radius", "Radius", ""), ("Angle", "Angle", "")]
    entryMode = bpy.props.EnumProperty(
        items=entryModeItems,
        name='',
        default='Angle',
        description="Edge Roundifier entry mode")

    rotateCenterItems = [("Spin", "Spin", ""), ("V1", "V1", ""),
                         ("Edge", "Edge", ""), ("V2", "V2", ""),
                         ('Cursor', 'Cursor', 'Closest to 3d cursor')]
    rotateCenter = bpy.props.EnumProperty(
        items=rotateCenterItems,
        name='',
        default='Edge',
        description="Rotate center for spin axis rotate")

    firstVertStrategyItems = [("V1", "V1", "First vertex of edge"),("V2", "V2", "Second vertex of edge"),
                         ('Cursor', 'Cursor', "Closest to 3d cursor")]
    firstVertStrategy = bpy.props.EnumProperty(
        items=firstVertStrategyItems,
        name='',
        default='V1',
        description="Strategy for choosing first vertex")

    arcModeItems = [("FullEdgeArc", "Full", "Full"),
                    ('HalfEdgeArc', "Half", "Half")]
    arcMode = bpy.props.EnumProperty(
        items=arcModeItems,
        name='',
        default='FullEdgeArc',
        description="Edge Roundifier arc mode")

    angleItems = [('Other', "Other", "User defined angle"), ('180', "180", "HemiCircle"), ('120', "120", "TriangleCircle"),
                  ('90', "90", "QuadCircle"), ('72', "72",
                                               "PentagonCircle"), ('60', "60", "HexagonCircle"),
                  ('45', "45", "OctagonCircle"), ('30', "30", "12-gonCircle")]

    angleEnum = bpy.props.EnumProperty(
        items=angleItems,
        name='',
        default='180',
        description="Presets prepare standard angles and calculate proper ray",
        update=updateAngleForAnglePresets)

    refItems = [('ORG', "Origin", "Use Origin Location"), ('CUR', "3D Cursor",
                                                           "Use 3DCursor Location"), ('EDG', "Edge", "Use Individual Edge Reference")]
    referenceLocation = bpy.props.EnumProperty(
        items=refItems,
        name='',
        default='ORG',
        description="Reference location used by Edge Roundifier to calculate initial centers of drawn arcs")

    planeItems = [('Auto', 'Auto', "Automatic"), ('Ortho', 'Ortho','Orthogonal'), ('Selected face', 'Selected face', "Selected face plane"), 
                  ('Face1', 'Face1', "Face1 Plane"), ('Face2', 'Face2', "Face2 Plane"),
                  ('View', 'View', "View Plane"), (XY, XY, "Top view plane"), 
                  (YZ, YZ, "Right view plane"), (XZ, XZ, "Front view plane"),
                  ('AlongX', 'AlongX', 'AlongX'), ('AlongY', 'AlongY', 'AlongY'), ('AlongZ', 'AlongZ', 'AlongZ')]
    planeEnum = bpy.props.EnumProperty(
        items=planeItems,
        name='',
        default='Auto',
        description="Plane used by Edge Roundifier to calculate spin plane of drawn arcs")

    edgeScaleCenterItems = [
        ('V1', "V1", "v1"), ('CENTER', "Center", "cent"), ('V2', "V2", "v2"), ('Cursor', "Cursor", "Closest to 3d cursor")]
    edgeScaleCenterEnum = bpy.props.EnumProperty(
        items=edgeScaleCenterItems,
        name='edge scale center',
        default='CENTER',
        description="Center used for scaling initial edge")

    def prepareMesh(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')

        mesh = context.scene.objects.active.data
        bm = bmesh.new()
        bm.from_mesh(mesh)

        edges = [ele for ele in bm.edges if ele.select]
        return edges, mesh, bm

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        uiPercentage = 0.333

        self.addEnumParameterToUI(
            box, False, uiPercentage, 'Mode:', 'workMode')
        self.addEnumParameterToUI(
            box, False, uiPercentage, 'Plane:', 'planeEnum', False)
        self.addEnumParameterToUI(
            box, False, uiPercentage, 'Strategy:', 'firstVertStrategy', False)

        box = layout.box()
        self.addEnumParameterToUI(
            box, False, uiPercentage, 'Scale base:', 'edgeScaleCenterEnum')
        self.addParameterToUI(box, False, uiPercentage,
                              'Scale factor:', 'edgeScaleFactor')

        box = layout.box()
        self.addEnumParameterToUI(
            box, False, uiPercentage, 'Entry mode:', 'entryMode')
        row = box.row(align=False)
        row.prop(self, 'angleEnum', expand=True, text="angle presets")
        self.addParameterToUI(box, False, uiPercentage, 'Angle:', 'a')
        self.addParameterToUI(box, False, uiPercentage, 'Radius:', 'r')
        self.addParameterToUI(box, False, uiPercentage, 'Segments:', 'n')

###################################
        box = layout.box()
        self.addTwoCheckboxesToUI(
            box, False, 'Options:', 'flip', 'invertAngle')
        self.addTwoCheckboxesToUI(box, False, '', 'bothSides', 'fullCircles')

        box = layout.box()
        self.addTwoCheckboxesToUI(
            box, False, 'Remove:', 'removeEdges', 'removeScaledEdges')

        box = layout.box()
        self.addTwoCheckboxesToUI(
            box, False, 'Connect:', 'connectArcs', 'connectArcsFlip')
        self.addTwoCheckboxesToUI(
            box, False, '', 'connectArcWithEdge', 'connectArcWithEdgeFlip')
        self.addCheckboxToUI(box, False, '', 'connectScaledAndBase')
################################

        box = layout.box()
        self.addParameterToUI(box, False, uiPercentage,
                              'Ortho offset:', 'offset')
        self.addParameterToUI(box, False, uiPercentage,
                              'Parallel offset:', 'offset2')

        box = layout.box()
        self.addParameterToUI(box, False, uiPercentage,
                              'Edge rotate :', 'edgeAngle')
        self.addEnumParameterToUI(
            box, False, uiPercentage, 'Axis rotate center:', 'rotateCenter')
        self.addParameterToUI(box, False, uiPercentage,
                              'Axis rotate:', 'axisAngle')

        box = layout.box()
        self.addParameterToUI(box, False, uiPercentage,
                              'Elliptic factor:', 'ellipticFactor')

    def addParameterToUI(self, layout, alignment, percent, label, property):
        row = layout.row(align=alignment)
        split = row.split(percentage=percent)
        col = split.column()
        col.label(label)
        col2 = split.column()
        row = col2.row(align=alignment)
        row.prop(self, property)

    def addTwoCheckboxesToUI(self, layout, alignment, label, property1, property2):
        row = layout.row(align=alignment)
        row.label(label)
        row.prop(self, property1)
        row.prop(self, property2)

    def addCheckboxToUI(self, layout, alignment, label, property1):
        row = layout.row(align=alignment)
        row.label(label)
        row.prop(self, property1)
        row.label('')

    def addEnumParameterToUI(self, layout, alignment, percent, label, property, expanded=True):
        row = layout.row(align=alignment)
        split = row.split(percentage=percent)
        col = split.column()
        col.label(label)
        col2 = split.column()
        row = col2.row(align=alignment)
        if (expanded):
            # text allows to display expanded in UI, maybe a bug?
            row.prop(self, property, expand=expanded, text=" ")
        else:
            row.prop(self, property, expand=expanded)

    def execute(self, context):

        edges, mesh, bm = self.prepareMesh(context)

        self.resetValues(self.workMode)

        self.obj = context.scene.objects.active

        if len(edges) > 0:
            self.roundifyEdges(edges, bm, mesh)
            self.sel.refreshMesh(bm, mesh)
            # self.selectEdgesAfterRoundifier(context, edges)
        else:
            debugPrint("No edges selected!")

        if self.removeEdges:
            bmesh.ops.delete(bm, geom=edges, context=2)

        bpy.ops.object.mode_set(mode='OBJECT')
        bm.to_mesh(mesh)
        bpy.ops.object.mode_set(mode='EDIT')

        bm.free()
        return {'FINISHED'}

##########################################
    def resetValues(self, workMode):
        if workMode == "Reset":
            self.setAllParamsToDefaults()

    def setAllParamsToDefaults(self):
        self.edgeScaleFactor = 1.0
        self.r = 1
        self.a = 180.0
        self.n = 4
        self.flip = False
        self.invertAngle = False
        self.fullCircles = False
        self.bothSides = False
        self.removeEdges = False
        self.removeScaledEdges = False

        self.connectArcWithEdge = False
        self.connectArcs = False
        self.connectScaledAndBase = False
        self.connectArcsFlip = False
        self.connectArcWithEdgeFlip = False

        self.axisAngle = 0.0
        self.edgeAngle = 0.0
        self.offset = 0.0
        self.offset2 = 0.0
        self.ellipticFactor = 0.0

        self.workMode = 'Normal'
        self.entryMode = 'Angle'
        self.angleEnum = '180'
        self.referenceLocation = 'ORG'
        self.planeEnum = 'Auto'
        self.edgeScaleCenterEnum = 'CENTER'
        self.rotateCenter = 'Edge'
        ######

    def roundifyEdges(self, edges, bm, mesh):
        arcs = []
        self.index = 0
        for e in edges:
            print('=======================================')
            matrix = self.makeMatrixFromEdge(e, bm)
            arcVerts = self.processEdge(e, bm, mesh, matrix)
            self.transformArc(arcVerts, bm, mesh)
            arcs.append(arcVerts)

        if self.connectArcs:
            self.connectArcsTogether(arcs, bm, mesh)
        #self.arcPostprocessing

    def processEdge(self, edge, bm, mesh, matrix):
        # TODO Here we can handle different profiles for edge like smooth, cos,
        return self.createArc(edge, bm, mesh, matrix)


####################### NEW CODE ###################################
    def getAxisRotationCenter(self, arcVerts):
        if self.rotateCenter == 'V1':
            return arcVerts['start'].co 
        elif self.rotateCenter == 'V2':
            return arcVerts['end'].co
        elif self.rotateCenter == 'Spin':
            return arcVerts['center']
        elif self.rotateCenter == 'Edge':
            return ( arcVerts['start'].co + arcVerts['end'].co ) / 2
        elif self.rotateCenter == 'Cursor':
            return self.getVertClosestToCursor(arcVerts['start'].co, arcVerts['end'].co)
            

    def transformArc(self, arcVerts, bm, mesh):
        mat = arcVerts['matrix']
        verts = arcVerts['verts']
        center = ( arcVerts['start'].co + arcVerts['end'].co ) / 2\
        
        # edgeRotate
        edgeAxis = mat.transposed()[0]
        a_mat = Quaternion(edgeAxis, radians(self.edgeAngle)).normalized().to_matrix()
        bmesh.ops.rotate(bm, cent=center, matrix=a_mat, verts=verts)
        # self.sel.refreshMesh(bm, mesh)
        # axisRotate
        center = self.getAxisRotationCenter(arcVerts)
        axis = mat.transposed()[2]
        b_mat = Quaternion(axis, radians(self.axisAngle)).normalized().to_matrix()
        bmesh.ops.rotate(bm, cent=center, matrix=b_mat, verts=verts)
        # arcVerts = self.offsetArcPerpendicular(arcVerts,bm,mesh)
        # arcVerts = self.offsetArcParallel(arcVerts, bm, mesh)
        self.sel.refreshMesh(bm, mesh)
        
        

# TODO: rework offsetArcPerpendicular and parallel
    def offsetArcPerpendicular(self, verts, mat, bm, mesh):
        # mat = arcVerts['matrix']
        # verts = arcVerts['verts']
        perpendicularVector = mat.transposed()[1]
        translation = self.offset * perpendicularVector

        try:
            bmesh.ops.translate(
                bm,
                verts=verts,
                vec=translation)
        except ValueError:
            print("[Edge Roundifier]: Perpendicular translate value error - multiple vertices in list - try unchecking 'Centers'")
        
        indexes = [v.index for v in verts]
        self.sel.refreshMesh(bm, mesh)
        bm.verts.ensure_lookup_table()
        offsetVertices = [bm.verts[i] for i in indexes]
        return offsetVertices
        # return arcVerts

    def offsetArcParallel(self, verts, mat, bm, mesh):
        # mat = arcVerts['matrix']
        # verts = arcVerts['verts']
        edgeVector = mat.transposed()[0]
        translation = self.offset2 * edgeVector
        
        try:
            bmesh.ops.translate(
                bm,
                verts=verts,
                vec=translation)
        except ValueError:
            print("[Edge Roundifier]: Parallel translate value error - multiple vertices in list - try unchecking 'Centers'")

        indexes = [v.index for v in verts]
        self.sel.refreshMesh(bm, mesh)
        bm.verts.ensure_lookup_table()
        offsetVertices = [bm.verts[i] for i in indexes]
        return offsetVertices
        # return arcVerts

    def makeElliptic(self, bm, mesh, arcVertices, edge):
        if self.ellipticFactor != 0:  # if 0 then nothing has to be done
            lastVert = int(len(arcVertices)/2) - 1 if self.bothSides else len(arcVertices) - 1
            
            v0co = edge.verts[0].co
            v1co = edge.verts[1].co
            for vertex in arcVertices:  # range(len(res_list)):
                # PKHg>INFO compute the base on the edge  of the height-vector
                top = vertex.co  # res_list[nr].co
                t = 0
                if v1co - v0co != 0:
                    t = (v1co - v0co).dot(top - v0co) / \
                        (v1co - v0co).length ** 2
                h_bottom = v0co + t * (v1co - v0co)
                height = (h_bottom - top)
                vertex.co = top + self.ellipticFactor * height

        return arcVertices

    def calculateSelectionCenter(self, edges):
        selectionCenter = Vector((0, 0, 0))
        for e in edges:
            V1, V2, edgeVector, edgeLength, edgeCenter = self.getEdgeInfo(e)
            selectionCenter += edgeCenter
        selectionCenter /= len(edges)
        print('CENTER = ' + str(selectionCenter))
        return selectionCenter

    def getVertClosestToCursor(self, v1, v2):
        cursorGlobalLoc = bpy.context.scene.cursor_location
        objectGlobalLoc = bpy.context.active_object.location  # Origin Location
        cursorLocalLoc = cursorGlobalLoc - objectGlobalLoc
        vec1 = v1 - cursorLocalLoc
        vec2 = v2 - cursorLocalLoc
        if vec1.length <= vec2.length:
            return v1
        else:
            return v2

    def getVertIndexClosestToCursor(self, edge):
        cursorGlobalLoc = bpy.context.scene.cursor_location
        objectGlobalLoc = bpy.context.active_object.location  # Origin Location
        cursorLocalLoc = cursorGlobalLoc - objectGlobalLoc
        v1 = edge.verts[0].co
        v2 = edge.verts[1].co
        vec1 = v1 - cursorLocalLoc
        vec2 = v2 - cursorLocalLoc
        if vec1.length <= vec2.length:
            return 0
        else:
            return 1

    def scaleEdge(self, edge, bm):
        scaleCenter = self.edgeScaleCenterEnum
        factor = self.edgeScaleFactor
        if (factor == 1):
            return edge

        v1 = edge.verts[0].co
        v2 = edge.verts[1].co
        origin = None
        if scaleCenter == 'CENTER':
            origin = (v1 + v2) * 0.5
        elif scaleCenter == 'V1':
            origin = v1
        elif scaleCenter == 'V2':
            origin = v2
        elif scaleCenter == 'Cursor':
            origin = self.getVertClosestToCursor(v1, v2)

        bmv1 = bm.verts.new(((v1 - origin) * factor) + origin)
        bmv2 = bm.verts.new(((v2 - origin) * factor) + origin)
        return bm.edges.new([bmv1, bmv2])

    def getFirstIndex(self, edge):
        firstIndex = None
        if self.firstVertStrategy == 'V1':
            firstIndex = 0
        elif self.firstVertStrategy == 'V2':
            firstIndex = 1
        elif self.firstVertStrategy == 'Cursor':
            firstIndex = self.getVertIndexClosestToCursor(edge)
        else:
            firstIndex = 0
        return firstIndex

    def getEdgeVertices(self, edge):
        firstIndex = self.getFirstIndex(edge)
        otherIndex = self.getOtherIndex(firstIndex)
        v1 = edge.verts[firstIndex].co
        v2 = edge.verts[otherIndex].co
        return v1, v2

    def makeMatrixFromEdge(self, edge, bm):
        edgeNormal = self.getEdgeNormalWithLinkFaces(edge, bm)
        v1, v2 = self.getEdgeVertices(edge)
        v3 = v1 + edgeNormal
        mat = self.makeMatrixFromVerts(v1, v2, v3)
        return mat

    def makeMatrixFromVerts(self, v1, v2, v3):
        a = v2 - v1
        b = v3 - v1
        c = a.cross(b)
        if c.magnitude > 0:
            c = c.normalized()
        else:
            self.report(
                {'WARNING'}, "Impossible to draw arc. Use other plane.")

        b2 = c.cross(a).normalized()
        a2 = a.normalized()
        m = Matrix([a2, b2, c]).transposed()
        #s = a.magnitude
        s = 1
        m = Matrix.Translation(v1) * Matrix.Scale(s, 4) * m.to_4x4()
        m = m.to_3x3()
        return m

    def adjustAngle(self, angle):
        if self.invertAngle:
            angle = 360 - angle
        if self.fullCircles:
            angle = 360
        return angle

    def getFirstEdgeVertexClone(self, edge, bm):
        v1, v2 = self.getEdgeVertices(edge)
        firstIndex = self.getFirstIndex(edge)
        startVertIndex = self.getOtherIndex(firstIndex) 

        if self.invertAngle:
            startVertIndex = self.getOtherIndex(startVertIndex)
        v0org = edge.verts[startVertIndex]
        v0 = bm.verts.new(v0org.co)
        return startVertIndex, v0

    def getOtherIndex(self, startVertIndex):
        if (startVertIndex == 1):
            otherIndex = 0
        else:
            otherIndex = 1
        return otherIndex

    def getOtherEdgeVertexClone(self, startVertIndex, edge, bm):
        otherIndex = self.getOtherIndex(startVertIndex)
        v1org = edge.verts[otherIndex]
        v1 = bm.verts.new(v1org.co)
        return v1

    def drawArcAndSelect(self, v0, center, axis, angle, steps, bm, mesh):
        result = bmesh.ops.spin(bm, geom=[v0], cent=center, axis=axis,
                                angle=radians(angle), steps=steps, use_duplicate=False)
        self.selectResultVerts(steps, bm, mesh)

    def selectResultVerts(self, steps, bm, mesh):
        vertsLength = len(bm.verts)
        bm.verts.ensure_lookup_table()
        lastVertIndex = bm.verts[vertsLength - 1].index

        lastSpinVertIndices = self.getLastSpinVertIndices(steps, lastVertIndex)
        for i in lastSpinVertIndices:
            bm.verts[i].select = True
        edges = bm.edges
        for e in edges:
            if e.verts[0].index in lastSpinVertIndices and e.verts[1].index in lastSpinVertIndices:
                if e.verts[0].select and e.verts[1].select:
                    e.select = True
        self.sel.refreshMesh(bm, mesh)

    def createArc(self, originalEdge, bm, mesh, matrix):
        edge = self.scaleEdge(originalEdge, bm)
        V1, V2, edgeVector, edgeLength, edgeCenter = self.getEdgeInfo(edge)
        self.updateRadiusAndAngle(edgeLength)
        print('originalEdge: v1 = ' + str(originalEdge.verts[0].co) + ' v2 = ' + str(originalEdge.verts[1].co))
        print('scaledEdge: V1 = ' + str(V1) + 'V2 = ' + str(V2))
        steps = self.n
        angle = self.a
        distance = cos(radians(angle / 2)) * self.r
        center = edgeCenter - (distance * matrix.transposed()[1])
        startVertIndex, v0 = self.getFirstEdgeVertexClone(edge, bm)
        print('scaledEdge: v0 = ' + str(v0.co))
        axis = matrix.transposed()[2]
        angle = self.adjustAngle(angle)
        result1 = self.drawArcAndSelect(v0, center, axis, angle, steps, bm, mesh)

        arcVerts = self.prepareArcVerts(len(bm.verts) - 1, steps, bm )
        endVert = arcVerts[0]
        startVert = arcVerts[len(arcVerts) - 1]
        if(self.bothSides):
            center2 = edgeCenter + (distance * matrix.transposed()[1])
            v1 = self.getOtherEdgeVertexClone(startVertIndex, edge, bm)
            self.drawArcAndSelect(v1, center2, axis, angle, steps, bm, mesh)
            arcVerts2 = self.prepareArcVerts(len(bm.verts) - 1, steps, bm )
            for el in arcVerts2:
                arcVerts.append(el)
        arcVerts = self.offsetArcParallel(arcVerts,matrix,bm, mesh)
        arcVerts = self.offsetArcPerpendicular(arcVerts,matrix,bm, mesh)
        arcVerts = self.makeElliptic(bm, mesh, arcVerts, edge)
        #TODO Axis Rotate & connect
        self.connectEdges(originalEdge, edge, arcVerts, bm, mesh)
        
        if self.removeScaledEdges and self.edgeScaleFactor != 1.0:
            bmesh.ops.delete(bm, geom=[edge], context=2)
        return {'start': startVert, 'end': endVert, 'verts': arcVerts, 'matrix': matrix, 'center': center}

    def prepareArcVerts(self, lastVertIndex, steps, bm):
        bm.verts.ensure_lookup_table()
        lastSpinVertIndices = self.getLastSpinVertIndices(steps, lastVertIndex)
        arcVerts = [bm.verts[i] for i in lastSpinVertIndices]
        return arcVerts

# === CONNECT ===
    def connectEdges(self, originalEdge, edge, arcVerts, bm, mesh):
        if self.connectArcWithEdge:
            self.connectArcTogetherWithEdge(edge, arcVerts, bm, mesh)
        if self.connectScaledAndBase:
            self.connectScaledEdgeWithBaseEdge(edge, originalEdge, bm, mesh)
        
        #TODO call subfunctions

    def connectArcTogetherWithEdge(self, edge, arcVertices, bm, mesh):
        lastVert = len(arcVertices) - 1
        edgeV1 = edge.verts[0].co
        edgeV2 = edge.verts[1].co
        arcV1 = arcVertices[0].co
        arcV2 = arcVertices[lastVert].co

        bmv1 = bm.verts.new(edgeV1)
        bmv2 = bm.verts.new(arcV1)

        bmv3 = bm.verts.new(edgeV2)
        bmv4 = bm.verts.new(arcV2)

        if self.connectArcWithEdgeFlip == False:
            bme = bm.edges.new([bmv1, bmv2])
            bme2 = bm.edges.new([bmv3, bmv4])
        else:
            bme = bm.edges.new([bmv1, bmv4])
            bme2 = bm.edges.new([bmv3, bmv2])
        self.sel.refreshMesh(bm, mesh)

    def connectScaledEdgeWithBaseEdge(self, scaledEdge, baseEdge, bm, mesh):
        scaledEdgeV1 = scaledEdge.verts[0].co
        baseEdgeV1 = baseEdge.verts[0].co
        scaledEdgeV2 = scaledEdge.verts[1].co
        baseEdgeV2 = baseEdge.verts[1].co

        bmv1 = bm.verts.new(baseEdgeV1)
        bmv2 = bm.verts.new(scaledEdgeV1)
        bme = bm.edges.new([bmv1, bmv2])

        bmv3 = bm.verts.new(scaledEdgeV2)
        bmv4 = bm.verts.new(baseEdgeV2)
        bme = bm.edges.new([bmv3, bmv4])
        self.sel.refreshMesh(bm, mesh)

    def connectArcsTogether(self, arcs, bm, mesh):
        for i in range(0, len(arcs) - 1):
            # in case on XZ or YZ there are no arcs drawn
            if arcs[i] == None or arcs[i + 1] == None:
                return
            # {'start': startVert, 'end': endVert, 'verts': arcVerts}

            # take last vert of arc i and first vert of arc i+1
            V1 = arcs[i]['end'].co
            V2 = arcs[i + 1]['start'].co

            if self.connectArcsFlip:
                V1 = arcs[i]['start'].co
                V2 = arcs[i + 1]['end'].co

            bmv1 = bm.verts.new(V1)
            bmv2 = bm.verts.new(V2)
            bme = bm.edges.new([bmv1, bmv2])

        # connect last arc and first one
        lastArcId = len(arcs) - 1
        V1 = arcs[lastArcId]['end'].co
        V2 = arcs[0]['start'].co
        if self.connectArcsFlip:
            V1 = arcs[lastArcId]['start'].co
            V2 = arcs[0]['end'].co

        bmv1 = bm.verts.new(V1)
        bmv2 = bm.verts.new(V2)
        bme = bm.edges.new([bmv1, bmv2])
        self.sel.refreshMesh(bm, mesh)

# === EDGE NORMALS ===
    def calculateEdgeNormalWithSelectionCenter(self, edge, n, selectionCenter):
        # v0 = edge.verts[0].co
        # v1 = edge.verts[1].co
        v0, v1 = self.getEdgeVertices(edge)
        a = (v1 - v0).normalized()
        n = n.normalized()
        s = (selectionCenter - v0).normalized()
        test = s.cross(a).normalized()
        normal = a.cross(n)
        check = normal.cross(a)
        print('CHECK: ' + str(check), 'TEST:' + str(test))

        if (check - test).length > self.threshold:
            print('RECALCULATE')
            n = -n
            print('n=' + str(n))
            normal = a.cross(n)
        normal = -normal # this is to make arcs outside
        if self.flip:
            normal = -normal
        return normal

    def getSelectedFace(self, facesWithEdge, lenFacesWithEdge):
        selectedFace = None
        if (lenFacesWithEdge >= 1 and facesWithEdge[0].select):
            selectedFace = facesWithEdge[0]
        elif(lenFacesWithEdge > 1 and facesWithEdge[1].select):
            selectedFace = facesWithEdge[1]
        return selectedFace

    def getEdgeNormalWithLinkFaces(self, edge, bm):
        normal = self.getEdgeVector(edge)
        facesWithEdge = edge.link_faces
        lenFacesWithEdge = len(facesWithEdge)
        if (self.planeEnum == 'Auto'):
            normal = self.getEdgeNormalAuto(edge, facesWithEdge, lenFacesWithEdge)
        elif (self.planeEnum == 'Ortho'):
            normal = self.getEdgeNormalOrtho(edge, facesWithEdge, lenFacesWithEdge)
        elif (self.planeEnum == 'View'):
            normal = self.getEdgeNormalView(edge)
        elif (self.planeEnum == 'Selected face'):
            normal = self.getEdgeNormalSelectedFace(edge, facesWithEdge, lenFacesWithEdge)
        elif (self.planeEnum == 'Face1'):
            normal = self.getEdgeNormalFace1(edge, facesWithEdge, lenFacesWithEdge)
        elif (self.planeEnum == 'Face2'):
            normal = self.getEdgeNormalFace2(edge, facesWithEdge, lenFacesWithEdge)
        elif (self.planeEnum == 'XY'):
            normal = self.getEdgeNormalForAxis(
                edge, Vector((0, 0, 1)), bm, 'Z')
        elif (self.planeEnum == 'XZ'):
            normal = self.getEdgeNormalForAxis(
                edge, Vector((0, 1, 0)), bm, 'Y')
        elif (self.planeEnum == 'YZ'):
            normal = self.getEdgeNormalForAxis(
                edge, Vector((1, 0, 0)), bm, 'X')
        elif (self.planeEnum == 'AlongX'):
            normal = self.getVector(Vector((1, 0, 0)))
        elif (self.planeEnum == 'AlongY'):
            normal = self.getVector(Vector((0, 1, 0)))
        elif (self.planeEnum == 'AlongZ'):
            normal = self.getVector(Vector((0, 0, 1)))

        print('Actual Normal = ' + str(normal))

# TEMPORARY NORMAL DRAWN 
        # v0, v1 = self.getEdgeVertices(edge)
        # edgeV1 = v0
        # bmv1 = bm.verts.new(edgeV1)
        # bmv2 = bm.verts.new(edgeV1 + normal)
        # bm.edges.new([bmv1, bmv2])
        return normal

    def getEdgeVector(self, edge):
        # V1, V2, edgeVector, edgeLength, center = self.getEdgeInfo(edge)
        v1, v2 = self.getEdgeVertices(edge)
        return v2 - v1

    def getEdgeNormalAuto(self, edge, facesWithEdge, lenFacesWithEdge):
        normal = self.getEdgeVector(edge)
        if lenFacesWithEdge == 2:
            normal = self.getEdgeNormalBetween2Faces(edge, facesWithEdge)
        elif lenFacesWithEdge == 1:
            normal = self.calculateEdgeNormal(edge, facesWithEdge[0].normal)
        else:
            normal = self.getEdgeNormalView(edge)
        return normal

    def getEdgeNormalOrtho(self, edge, facesWithEdge, lenFacesWithEdge):
        normal = self.getEdgeVector(edge)
        if lenFacesWithEdge == 2:
            normal = self.getEdgeNormalBetween2Faces(edge, facesWithEdge)
        elif lenFacesWithEdge == 1:
            normal = self.getFaceNormal(facesWithEdge[0])
        else:
            normal = self.getEdgeNormalView(edge)
        return normal

    def getEdgeNormalView(self, edge):
        normal = self.getEdgeVector(edge)
        viewMatrix = self.getViewMatrix()
        print('viewMatrix = ' + str(viewMatrix))
        if viewMatrix != None:
            n = viewMatrix[2]
            normal = self.calculateEdgeNormal(edge, n)
            print("getEdgeNormalView - Using View Normal")
        return normal

    def getEdgeNormalBetween2Faces(self, edge, faces):
        n1 = faces[0].normal
        n2 = faces[1].normal
        normal = n1 + n2
        if self.flip:
            normal = -normal
        print("getEdgeNormalBetween2Faces")
        return normal

    def calculateEdgeNormal(self, edge, n):
        v0, v1 = self.getEdgeVertices(edge)
        a = v1 - v0
        normal = a.cross(n)
        if self.flip:
            normal = -normal
        return normal

    def getEdgeNormalFace(self, edge, face):
        n = face.normal
        faceCenter = face.calc_center_median()
        normal = self.calculateEdgeNormalWithSelectionCenter(
            edge, n, faceCenter)
        print("getEdgeNormalFace - Using Face Normal")
        return normal

    def getFaceNormal(self, face):
        normal = face.normal
        if self.flip:
            normal = -face.normal
        return normal

    def getEdgeNormalSelectedFace(self, edge, facesWithEdge, lenFacesWithEdge):
        normal = self.getEdgeVector(edge)
        if (lenFacesWithEdge >= 1):
            selectedFace = self.getSelectedFace(facesWithEdge, lenFacesWithEdge)
            if selectedFace != None:
                normal = self.getEdgeNormalFace(edge, selectedFace)
            else:
                self.report({'WARNING'}, "No faces selected. Use other plane.")
        else:
            self.report({'WARNING'}, "No faces selected. Use other plane.")
        return normal

    def getEdgeNormalFace1(self, edge, facesWithEdge, lenFacesWithEdge):
        normal = self.getEdgeVector(edge)
        if (lenFacesWithEdge >= 1):
            normal = self.getEdgeNormalFace(edge, facesWithEdge[0])
        else:
            self.report(
                {'WARNING'}, "Edge has no faces attached. Use other plane.")
        return normal

    def getEdgeNormalFace2(self, edge, facesWithEdge, lenFacesWithEdge):
        normal = self.getEdgeVector(edge)
        if (lenFacesWithEdge > 1):
            normal = self.getEdgeNormalFace(edge, facesWithEdge[1])
        elif (lenFacesWithEdge == 1):
            self.report(
                {'WARNING'}, "Edge has only 1 face attached. Use other face plane.")
        else:
            self.report(
                {'WARNING'}, "Edge has no faces attached. Use other plane.")
        return normal

    def getEdgeNormalForAxis(self, edge, vec, bm, axis):
        selectionCenter = self.calculateSelectionCenter(bm.edges)
        if axis == 'Z':
            selectionCenter.z = edge.verts[0].co.z
        elif axis == 'Y':
            selectionCenter.y = edge.verts[0].co.y
        elif axis == 'X':
            selectionCenter.x = edge.verts[0].co.x

        print("getEdgeNormalForAxis - modified vec = " + str(vec))
        normal = self.calculateEdgeNormalWithSelectionCenter(
            edge, vec, selectionCenter)
        print("getEdgeNormalForAxis - normal = " + str(normal))
        return normal

    def getVector(self, vec):
        normal = vec
        if self.flip:
            normal = -vec
        return normal

    def getViewMatrix(self):
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                r3d = area.spaces.active.region_3d
                return r3d.view_matrix.to_3x3()
        return None

####################### NEW CODE END ###################################

    def getNormalizedEdgeVector(self, edge):
        V1 = edge.verts[0].co
        V2 = edge.verts[1].co
        edgeVector = V2 - V1
        normEdge = edgeVector.normalized()
        return normEdge

    def getEdgePerpendicularVector(self, edge, plane):
        normEdge = self.getNormalizedEdgeVector(edge)

        edgePerpendicularVector = Vector((normEdge[1], -normEdge[0], 0))
        if plane == YZ:
            edgePerpendicularVector = Vector((0, normEdge[2], -normEdge[1]))
        if plane == XZ:
            edgePerpendicularVector = Vector((normEdge[2], 0, -normEdge[0]))
        return edgePerpendicularVector

    def getEdgeInfo(self, edge):
        V1 = edge.verts[0].co
        V2 = edge.verts[1].co
        edgeVector = V2 - V1
        edgeLength = edgeVector.length
        edgeCenter = (V2 + V1) * 0.5
        return V1, V2, edgeVector, edgeLength, edgeCenter


    def getLastSpinVertIndices(self, steps, lastVertIndex):
        arcfirstVertexIndex = lastVertIndex - steps  # + 1
        lastSpinVertIndices = range(arcfirstVertexIndex, lastVertIndex + 1)
        return lastSpinVertIndices

    def updateRadiusAndAngle(self, edgeLength):
        #        print('updateRadiusAndAngle: EntryMode: ' + str(self.entryMode))
        if self.entryMode == "Angle":
            self.CalculateRadius(edgeLength)
        else:
            self.CalculateAngle(edgeLength)

    def CalculateAngle(self, edgeLength):
        halfEdgeLength = edgeLength / 2
        if halfEdgeLength > self.r:
            self.a = 180
        else:
            halfAngle = asin(halfEdgeLength / self.r)
            angle = 2 * halfAngle  # in radians
            self.a = degrees(angle)  # in degrees
        print('CalculateAngle: a = ' + str(self.a) + ' r = ' + str(self.r))

    def CalculateRadius(self, edgeLength):
        degAngle = self.a
        angle = radians(degAngle)
        self.r = edgeLength / (2 * sin(angle / 2))
        print('CalculateRadius: a = ' + str(self.a) + ' r = ' + str(self.r))

    def selectEdgesAfterRoundifier(self, context, edges):
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        mesh = context.scene.objects.active.data
        bmnew = bmesh.new()
        bmnew.from_mesh(mesh)
        self.deselectEdges(bmnew)
        for selectedEdge in edges:
            for e in bmnew.edges:
                if (e.verts[0].co - selectedEdge.verts[0].co).length <= self.threshold \
                   and (e.verts[1].co - selectedEdge.verts[1].co).length <= self.threshold:
                    e.select_set(True)

        bpy.ops.object.mode_set(mode='OBJECT')
        bmnew.to_mesh(mesh)
        bmnew.free()
        bpy.ops.object.mode_set(mode='EDIT')

    def deselectEdges(self, bm):
        for edge in bm.edges:
            edge.select_set(False)


    @classmethod
    def poll(cls, context):
        return (context.scene.objects.active.type == 'MESH') and (context.scene.objects.active.mode == 'EDIT')


def draw_item(self, context):
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator('mesh.edge_roundifier')


def register():
    bpy.utils.register_class(EdgeRoundifier)
    bpy.utils.register_class(EdgeWorksPanel)
    bpy.types.VIEW3D_MT_edit_mesh_edges.append(draw_item)


def unregister():
    bpy.utils.unregister_class(EdgeRoundifier)
    bpy.utils.unregister_class(EdgeWorksPanel)
    bpy.types.VIEW3D_MT_edit_mesh_edges.remove(draw_item)

if __name__ == "__main__":
    register()
