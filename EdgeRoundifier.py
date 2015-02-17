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

#History from 19-oct-2014 on Version 0,0,4
#19 oct (maybe romoved later)PKHG>INFO some changes are found look e.g. for "#old "
#19 oct PKHG added debugPrintNew + globals to steer the debug
#19 oct PKHG: more use of Vectors done

#PKHG>INFO if all points in 3D space are Vectors, a lot of Vector(xxx) could become xxx
# without an extra Vector 

bl_info = {
    "name": "Edge Roundifier",
    "category": "Mesh",
    'author': 'Piotr Komisarczyk (komi3D), PKHG',
    'version': (0, 0, 6),
    'blender': (2, 7, 3),
    'location': 'SPACE > Edge Roundifier or CTRL-E > Edge Roundifier',
    'description': 'Mesh editing script allowing edge rounding',
    'wiki_url': '',
    'tracker_url': '',
    'category': 'Mesh'
}

import bmesh
import bpy
import bpy.props
from math import sqrt, acos, asin, pi, radians, degrees, sin, acos
from mathutils import Vector, Euler

# CONSTANTS
two_pi = 2 * pi #PKHG>??? maybe other constantly used values too???
XY = "XY"
XZ = "XZ"
YZ = "YZ"
SPIN_END_THRESHOLD = 0.001
LINE_TOLERANCE = 0.0001

# variable controlling all print functions
#PKHG>??? to be replaced, see debugPrintNew ;-)
debug = True

def debugPrint(*text):
    if debug:
        for t in text:
            print(text)



############# for debugging PKHG ################
def debugPrintNew(debug,*text):
    if debug:
        #print("start", type(text))
        tmp = [el for el in text]
        for row in tmp:
            print(row)

d_XABS_YABS = False
d_Edge_Info = False
d_Plane = False
d_Radius_Angle = False
d_Roots = True
d_RefObject = True
d_LineAB = True
d_Selected_edges = False
d_Rotate_Around_Spin_Center = False
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
            delta = b ** 2 - 4 * a * c
            if delta == 0:
                x = -b / (2 * a)
                return (x, x)
            elif delta < 0:
                return None
            else :
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
        debugPrintNew(d_XABS_YABS, "XABS = " + str( xabs)+ " YABS = " + str(yabs))

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
        h = (a ** 2) + (b ** 2) + (xValue ** 2) - 2 * a * xValue - (radius ** 2)
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
    #PKHG>nice if rescriction to these 3 types or planes is to be done
    #komi3D> from 0.0.2 there is a restriction. In future I would like Edge Roundifier to work on
    #komi3D> Normal and View coordinate systems. That would be great... 
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
            if v.co == vertex:
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
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}  # enable undo for the operator.PKHG>INFO and PRESET

    threshold = 0.0005  # used for remove doubles and edge selection at the end

    edgeScaleFactor = bpy.props.FloatProperty(name = '', default = 1.0, min = 0.00001, max = 100000.0, step = 0.5, precision = 5)
    r = bpy.props.FloatProperty(name = '', default = 1, min = 0.00001, max = 1000.0, step = 0.1, precision = 3)
    a = bpy.props.FloatProperty(name = '', default = 180.0, min = 0.1, max = 180.0, step = 0.5, precision = 1)
    n = bpy.props.IntProperty(name = '', default = 4, min = 1, max = 100, step = 1)
    flip = bpy.props.BoolProperty(name = 'flip', default = False)
    invertAngle = bpy.props.BoolProperty(name = 'invertAngle', default = False)
    fullCircles = bpy.props.BoolProperty(name = 'fullCircles', default = False)
    bothSides = bpy.props.BoolProperty(name = 'bothSides', default = False)
    removeDoubles = bpy.props.BoolProperty(name = 'removeDoubles', default = False)
    drawArcCenters = bpy.props.BoolProperty(name = 'drawArcCenters', default = False)
    removeEdges = bpy.props.BoolProperty(name = 'removeEdges', default = False)
    removeScaledEdges = bpy.props.BoolProperty(name = 'removeScaledEdges', default = False)
    axisAngle = bpy.props.FloatProperty(name = '', default = 0.0, min = -180.0, max = 180.0, step = 0.5, precision = 1)
    offset = bpy.props.FloatProperty(name = '', default = 0.0, min = -1000000.0, max = 1000000.0, step = 0.1, precision = 5)
    offset2 = bpy.props.FloatProperty(name = '', default = 0.0, min = -1000000.0, max = 1000000.0, step = 0.1, precision = 5)
    
    entryModeItems = [("Radius", "Radius", ""), ("Angle", "Angle", "")]
    entryMode = bpy.props.EnumProperty(
        items = entryModeItems,
        name = '',
        default = 'Radius',
        description = "Edge Roundifier entry mode")
    
    arcModeItems = [("FullEdgeArc","Full","Full"),('HalfEdgeArc',"Half","Half")]
    arcMode = bpy.props.EnumProperty(
        items = arcModeItems,
        name = '',
        default = 'HalfEdgeArc',
        description = "Edge Roundifier arc mode")
    

    angleItems = [('Other', "Other", "User defined angle"), ('180', "180", "HemiCircle"), ('120', "120", "TriangleCircle"),
                    ('90', "90", "QuadCircle"), ('60', "60", "HexagonCircle"),
                    ('45', "45", "OctagonCircle"), ('30', "30", "12-gonCircle")]

    angleItemsHalfMode = [('Other', "Other", "User defined angle"), ('90', "90", ""), ('60', "60", ""),
                    ('45', "45", "OctagonCircle"), ('30', "30", "12-gonCircle")]

    halfAngleEnum  = bpy.props.EnumProperty(
        items = angleItemsHalfMode,
        name = '',
        default = 'Other',
        description = "Presets prepare standard angles and calculate proper ray")

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
        bm.from_mesh(mesh) #PKHG>??? from_edit_mesh??? from_mesh not seen in 2.72a
        #komi3D > from_mesh seems to be working in 2.72a...
        
        edges = [ele for ele in bm.edges if ele.select]
        return edges, mesh, bm

    def prepareParameters(self):
        parameters = { "a" : "a"}
        parameters["arcMode"] = self.arcMode
        parameters["edgeScaleFactor"] = self.edgeScaleFactor
        parameters["plane"] = self.planeEnum
        parameters["radius"] = self.r
        parameters["angle"] = self.a
        parameters["segments"] = self.n
        parameters["flip"] = self.flip
        parameters["fullCircles"] = self.fullCircles
        parameters["invertAngle"] = self.invertAngle
        parameters["bothSides"] = self.bothSides
        parameters["angleEnum"] = self.angleEnum
        parameters["entryMode"] = self.entryMode
        parameters["refObject"] = self.referenceLocation
        parameters["removeDoubles"] = self.removeDoubles
        parameters["drawArcCenters"] = self.drawArcCenters
        parameters["removeEdges"] = self.removeEdges
        parameters["removeScaledEdges"] = self.removeScaledEdges
        parameters["axisAngle"] = self.axisAngle
        parameters["offset"] = self.offset
        parameters["offset2"] = self.offset2
        return parameters

    def draw(self, context):
        layout = self.layout
        layout.label('Note: possible radius >= edge_length/2.')
        row = layout.row(align = False)
        #parameters["edgeScaleFactor"]
        row.label('Edge Scale Factor:')
        row.prop(self, 'edgeScaleFactor')
        row = layout.row(align = False)

        row.label('ArcMode:')
        row.prop(self, 'arcMode', expand = True, text = "kind of arc to be created")
        row = layout.row(align = False)
        
        
        row.label('EntryMode:')
        row.prop(self, 'entryMode', expand = True, text = "type of input given by user")
        row = layout.row(align = False)
        
        layout.label('Quick angle:')

        layout.prop(self, 'angleEnum', expand = True, text = "angle presets")
        ##layout.prop(self, angleEnumChoice, expand = True, text = "abv")
        
        row = layout.row(align = False)
        row.label('Angle:')
        row.prop(self, 'a')
        row = layout.row(align = False)
        row.label('Radius:')
        row.prop(self, 'r')
        row = layout.row(align = True)
        row.label('Segments:')
        row.prop(self, 'n') #old , slider = True) 
        #PKHG>INFO dragging still works but changing 1 easier
        #komi3D > thanks for pointing that out! :)
        row = layout.row(align = False)
        row.prop(self, 'flip')
        row.prop(self, 'invertAngle')
        row = layout.row(align = False)
        row.prop(self, 'fullCircles')
        row.prop(self, 'bothSides' )
        row = layout.row(align = False)
        row.prop(self, 'drawArcCenters')
        row.prop(self, 'removeDoubles')
        row = layout.row(align = False)
        row.prop(self, 'removeEdges')
        row.prop(self, 'removeScaledEdges')

        layout.label('Reference Location:')
        layout.prop(self, 'referenceLocation', expand = True, text = "a")

        layout.label('Working Plane (LOCAL coordinates):')
        layout.prop(self, 'planeEnum', expand = True, text = "a")

        row = layout.row(align = False)
        row.label('=== EXTRA OPTIONS ===')
        row = layout.row(align = False)
        row.label('Rotation around axis angle:')
        row.prop(self,'axisAngle')
        row = layout.row(align = False)
        row.label('Orhto Offset arc:')
        row.prop(self,'offset')
        row = layout.row(align = False)
        row.label('Parallel Offset arc:')
        row.prop(self,'offset2')

    def execute(self, context):

        edges, mesh, bm = self.prepareMesh(context)
        parameters = self.prepareParameters()
        
        #TODO
        
        scaledEdges = self.scaleDuplicatedEdges(bm, edges, parameters["edgeScaleFactor"])

        if len(scaledEdges) > 0:
            self.roundifyEdges(scaledEdges, parameters, bm, mesh)
            #PKHG sel is SelectionHelper print(type(self.sel),dir(self.sel))
            self.sel.refreshMesh(bm, mesh)
            if parameters["removeDoubles"] == True:
                bpy.ops.mesh.select_all(action = "SELECT")
                bpy.ops.mesh.remove_doubles(threshold = self.threshold)
                bpy.ops.mesh.select_all(action = "DESELECT")

            self.selectEdgesAfterRoundifier(context, scaledEdges)
        else:
            debugPrint("No edges selected!")

        if parameters["removeEdges"]:
            bmesh.ops.delete(bm, geom = edges, context = 2)
        if parameters["removeScaledEdges"] and self.edgeScaleFactor != 1.0:    
            bmesh.ops.delete(bm, geom = scaledEdges, context = 2)
            
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bm.to_mesh(mesh)
        bpy.ops.object.mode_set(mode = 'EDIT')

        bm.free()
        return {'FINISHED'}

##########################################
    
    def scaleDuplicatedEdges(self,bm, edges, factor):
        #this code is by Zeffi
        duplicateEdges=[]
        if factor == 1:
            duplicateEdges = edges
        else:
            for e in edges:
                v1 = e.verts[0].co
                v2 = e.verts[1].co
                origin = (v1+v2) * 0.5  # edge origin
                bmv1 = bm.verts.new(((v1-origin) * factor) + origin)
                bmv2 = bm.verts.new(((v2-origin) * factor) + origin)
                bme = bm.edges.new([bmv1, bmv2])
                duplicateEdges.append(bme)
        return duplicateEdges
        
        
    def roundifyEdges(self, edges, parameters, bm, mesh):
        for e in edges:
            self.roundify(e, parameters, bm, mesh)

    def getNormalizedEdgeVector (self, edge):
        V1 = edge.verts[0].co 
        V2 = edge.verts[1].co 
        edgeVector =  V2 - V1
        normEdge = edgeVector.normalized()
        return normEdge

    def getEdgePerpendicularVector (self,edge, plane):
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
        edgeVector =  V2 - V1 
        edgeLength = edgeVector.length 
        edgeCenter = (V2 + V1) * 0.5 
        debugPrintNew(d_Edge_Info, "\nEdge info=====begin=================================",\
                      "V1 info============== " + str(V1),\
                      "V2 info============== " + str(V2),\
                      "Edge Length============== " + str(edgeLength),\
                      "Edge Center============== " + str(edgeCenter),\
                      "Edge info=====end=================================")
        return V1, V2, edgeVector, edgeLength, edgeCenter

    def roundify(self, edge, parameters, bm, mesh):

        V1, V2, edgeVector, edgeLength, edgeCenter = self.getEdgeInfo(edge)
        if self.skipThisEdge(V1, V2, parameters["plane"]):
            return

        
        

        if parameters["arcMode"] == "HalfEdgeArc":
            roundifyParams = self.calculateRoundifyParamsHalfMode(edge, parameters, bm, mesh)
            if roundifyParams == None:
                return
            self.drawHalfSpin(edge, edgeCenter, roundifyParams, parameters, bm, mesh)
            
        else:
            #PKHG>TEST only once debugPrintNew(True, str(roundifyParams))
            roundifyParams = self.calculateRoundifyParams(edge, parameters, bm, mesh)
            if roundifyParams == None:
                return
                
            spinnedVerts = self.drawSpin(edge, edgeCenter, roundifyParams, parameters, bm, mesh)
            rotatedVerts = self.rotateArcAroundSpinAxis(bm, mesh, spinnedVerts, roundifyParams, parameters)
            offsetVerts = self.offsetArcPerpendicular(bm, mesh, rotatedVerts, edge, parameters)
            offsetVerts2 = self.offsetArcParallel(bm, mesh, offsetVerts, edge, parameters)
            
            
            if parameters["bothSides"]:
                lastSpinCenter = roundifyParams[0]
                roundifyParams[0] = roundifyParams[1]
                roundifyParams[1] = lastSpinCenter
                spinnedVerts = self.drawSpin(edge, edgeCenter, roundifyParams, parameters, bm, mesh)
                rotatedVerts = self.rotateArcAroundSpinAxis(bm, mesh, spinnedVerts, roundifyParams, parameters)
                offsetVerts = self.offsetArcPerpendicular(bm, mesh, rotatedVerts, edge, parameters)
                offsetVerts2 = self.offsetArcParallel(bm, mesh, offsetVerts, edge, parameters)
            

    def offsetArcPerpendicular(self, bm, mesh, Verts, edge, parameters):
        perpendicularVector = self.getEdgePerpendicularVector(edge, parameters["plane"])
        offset = parameters["offset"]
        translation = offset * perpendicularVector
        
        bmesh.ops.translate(
        bm,
        verts=Verts,
        vec=translation)
        
        indexes = [v.index for v in Verts] 
        self.sel.refreshMesh(bm, mesh)
        offsetVertices = [bm.verts[i] for i in indexes]
        return offsetVertices
    
    def offsetArcParallel(self, bm, mesh, Verts, edge, parameters):
        
        edgeVector = self.getNormalizedEdgeVector(edge)
        offset = parameters["offset2"]
        translation = offset * edgeVector
        
        bmesh.ops.translate(
        bm,
        verts=Verts,
        vec=translation)
        
        indexes = [v.index for v in Verts] 
        self.sel.refreshMesh(bm, mesh)
        offsetVertices = [bm.verts[i] for i in indexes]
        return offsetVertices
        
        
    def skipThisEdge(self, V1, V2, plane):
        #debugPrintNew(True," type of V1" + str(type(V1)))
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

        debugPrintNew(d_Plane, "PLANE: " +  parameters["plane"])
        lineAB = self.calc.getLineCoefficientsPerpendicularToVectorInPoint(edgeCenter, edgeVector, parameters["plane"])
        #lineAB = self.calc.getLineCoefficientsPerpendicularToVectorInPoint(V2, edgeVector, parameters["plane"])
        debugPrint(d_LineAB, "Line Coefficients: " +  str(lineAB))
        circleMidPoint = V1
        circleMidPointOnPlane = self.calc.getCircleMidPointOnPlane(V1, parameters["plane"])
        radius = parameters["radius"]

        #if radius < edgeLength/2:
#            return None
            #radius = edgeLength/2
            #parameters["radius"] = edgeLength/2 
            #self.r = edgeLength/2
            #parameters["radius"]=self.r

        angle = 0
        if (parameters["entryMode"] == 'Angle'):
            if (parameters["angleEnum"] != 'Other'):
                radius, angle = self.CalculateRadiusAndAngleForAnglePresets(parameters["angleEnum"], radius, angle, edgeLength)
            else:
                radius, angle = self.CalculateRadiusAndAngle(edgeLength)
        debugPrintNew(d_Radius_Angle, "RADIUS = " + str(radius) + "  ANGLE = " + str( angle))
        roots = None
        if angle != pi:  # mode other than 180
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
        debugPrintNew(d_Roots, "roots=" + str(roots))

        refObjectLocation = None
        objectLocation = bpy.context.active_object.location  # Origin Location

        if parameters["refObject"] == "ORG":
            refObjectLocation = [0, 0, 0]
            #refObjectLocation = objectLocation
        else:
            refObjectLocation = bpy.context.scene.cursor_location - objectLocation

        debugPrintNew(d_RefObject, parameters["refObject"], refObjectLocation)
        chosenSpinCenter, otherSpinCenter = self.getSpinCenterClosestToRefCenter(refObjectLocation, roots, parameters["flip"])

        if (parameters["entryMode"] == "Radius"):
            halfAngle = self.calc.getAngle(edgeCenter, chosenSpinCenter, circleMidPoint)
            angle = 2 * halfAngle[0]  # in radians
            self.a = degrees(angle)  # in degrees

        spinAxis = self.getSpinAxis(parameters["plane"])

        if(parameters["invertAngle"]):
            angle = -two_pi + angle

        if(parameters["fullCircles"]):
            angle = two_pi

        steps = parameters["segments"]

        if parameters["fullCircles"] == False and parameters["flip"] == True:
            angle = -angle
        X = [chosenSpinCenter, otherSpinCenter, spinAxis, angle, steps, refObjectLocation]
        return X
    
    #############################

    def calculateRoundifyParamsHalfMode(self, edge, parameters, bm, mesh):
        # V1 V2 stores Local Coordinates
        V1, V2, edgeVector, edgeLength, edgeCenter = self.getEdgeInfo(edge)

        debugPrintNew(d_Plane, "PLANE: " +  parameters["plane"])
        lineAB = self.calc.getLineCoefficientsPerpendicularToVectorInPoint(V2, edgeVector, parameters["plane"])
        debugPrint(d_LineAB, "Line Coefficients: " +  str(lineAB))
        circleMidPoint = V1
        circleMidPointOnPlane = self.calc.getCircleMidPointOnPlane(V1, parameters["plane"])
        circleMidPoint2 = V2
        circleMidPointOnPlane2 = self.calc.getCircleMidPointOnPlane(V2, parameters["plane"])
        radius = parameters["radius"]

        angle = 0
        if (parameters["entryMode"] == 'Angle'):
            if (parameters["angleEnum"] != 'Other'):
                radius, angle = self.CalculateRadiusAndAngleForAnglePresetsHalfMode(parameters["angleEnum"], edgeLength)
            else:
                radius, angle = self.CalculateRadiusFromAngleHalfMode(edgeLength)
        else:
            radius, angle = self.CalculateAngleFromRadiusHalfMode(edgeLength)
        debugPrintNew(d_Radius_Angle, "RADIUS = " + str(radius) + "  ANGLE = " + str( angle))
        roots = None
        if angle != pi/2:  # mode other than 90
            if lineAB == None:
                roots = self.calc.getLineCircleIntersectionsWhenXPerpendicular(V2, circleMidPointOnPlane2, radius, parameters["plane"])
            else:
                roots = self.calc.getLineCircleIntersections(lineAB, circleMidPointOnPlane, radius)
            if roots == None:
                debugPrint("No centers were found. Change radius to higher value")
                return None
            roots = self.addMissingCoordinate(roots, V1, parameters["plane"])  # adds X, Y or Z coordinate
        else:
            roots = [V2, V2]
        debugPrintNew(d_Roots, "roots=" + str(roots))

        refObjectLocation = None
        objectLocation = bpy.context.active_object.location  # Origin Location

        if parameters["refObject"] == "ORG":
            refObjectLocation = [0, 0, 0]
            #refObjectLocation = objectLocation
        else:
            refObjectLocation = bpy.context.scene.cursor_location - objectLocation

        debugPrintNew(d_RefObject, parameters["refObject"], refObjectLocation)
        chosenSpinCenter, otherSpinCenter = self.getSpinCenterClosestToRefCenter(refObjectLocation, roots, parameters["flip"])

        spinAxis = self.getSpinAxis(parameters["plane"])

        if(parameters["invertAngle"]):
            angle = -two_pi + angle

        if(parameters["fullCircles"]):
            angle = two_pi

        steps = parameters["segments"]

        if parameters["fullCircles"] == False and parameters["flip"] == True:
            angle = -angle
        X = [chosenSpinCenter, otherSpinCenter, spinAxis, angle, steps, refObjectLocation]
        return X

    def drawHalfSpin(self, edge, edgeCenter, roundifyParams, parameters, bm, mesh):
        [chosenSpinCenter, otherSpinCenter, spinAxis, angle, steps, refObjectLocation] = roundifyParams

        v0org, v1org = (edge.verts[0], edge.verts[1]) #old self.getVerticesFromEdge(edge)

        # Duplicate initial vertex

        v0 = bm.verts.new(v0org.co)
        
        result = bmesh.ops.spin(bm, geom = [v0], cent = chosenSpinCenter, axis = spinAxis, \
                                   angle = angle, steps = steps, use_duplicate = False)
        if parameters['drawArcCenters']: 
            vX = bm.verts.new(chosenSpinCenter)
            vX2 = bm.verts.new(otherSpinCenter)
       
 ############################################################################       
        
    def drawSpin(self, edge, edgeCenter, roundifyParams, parameters, bm, mesh):       
        [chosenSpinCenter, otherSpinCenter, spinAxis, angle, steps, refObjectLocation] = roundifyParams

        v0org, v1org = (edge.verts[0], edge.verts[1]) #old self.getVerticesFromEdge(edge)

        # Duplicate initial vertex

        v0 = bm.verts.new(v0org.co)
        
        result = bmesh.ops.spin(bm, geom = [v0], cent = chosenSpinCenter, axis = spinAxis, \
                                   angle = angle, steps = steps, use_duplicate = False)

        
       
        # it seems there is something wrong with last index of this spin...
        # I need to calculate the last index manually here...
        vertsLength = len(bm.verts)
        bm.verts.ensure_lookup_table()
        lastVertIndex = bm.verts[vertsLength - 1].index
        lastSpinVertIndices = self.getLastSpinVertIndices(steps, lastVertIndex)
        debugPrintNew(True, str(result) + "lastVertIndex =" + str(lastVertIndex))

        alternativeLastSpinVertIndices = []

        if (angle == pi or angle == -pi):

            midVertexIndex = lastVertIndex - round(steps / 2)
            bm.verts.ensure_lookup_table()
            midVert = bm.verts[midVertexIndex].co

            midVertexDistance = (Vector(refObjectLocation) - Vector(midVert)).length 
            midEdgeDistance = (Vector(refObjectLocation) - Vector(edgeCenter)).length

            debugPrint("midVertexDistance: ")
            debugPrint(midVertexDistance)
            debugPrint("midEdgeDistance: ")
            debugPrint(midEdgeDistance)

            if (parameters["invertAngle"]) or (parameters["flip"]):
                if (midVertexDistance > midEdgeDistance):
                    alternativeLastSpinVertIndices = self.alternateSpin(bm, mesh, angle, chosenSpinCenter, spinAxis, steps, v0, v1org, lastSpinVertIndices)
            elif (parameters["bothSides"]):
                #do some more testing here!!!
                alternativeLastSpinVertIndices = self.alternateSpin(bm, mesh, angle, chosenSpinCenter, spinAxis, steps, v0, v1org, [])
                alternativeLastSpinVertIndices2 = self.alternateSpin(bm, mesh, -angle, chosenSpinCenter, spinAxis, steps, v0, v1org, [])
                if alternativeLastSpinVertIndices2 != []:
                    alternativeLastSpinVertIndices = alternativeLastSpinVertIndices2
            else:
                if (midVertexDistance < midEdgeDistance):
                    alternativeLastSpinVertIndices = self.alternateSpin(bm, mesh, angle, chosenSpinCenter, spinAxis, steps, v0, v1org, lastSpinVertIndices)

        elif (angle != two_pi):  # to allow full circles :)
            if (result['geom_last'][0].co - v1org.co).length > SPIN_END_THRESHOLD:
                alternativeLastSpinVertIndices = self.alternateSpin(bm, mesh, angle, chosenSpinCenter, spinAxis, steps, v0, v1org, lastSpinVertIndices)
                ###
        #PKHG sel is SelectionHelper  print(type(self.sel),dir(self.sel))
        self.sel.refreshMesh(bm, mesh)
        if alternativeLastSpinVertIndices != []:
            lastSpinVertIndices = alternativeLastSpinVertIndices
        
        bm.verts.ensure_lookup_table()
        
        #print("LEN=" + str(len(bm.verts)))
        #print("lastSpinVertInd LEN=" + str(len(lastSpinVertIndices)) )
        #print("lastSpinVertInd =" + str(lastSpinVertIndices))
        
        spinVertices = []
        if lastSpinVertIndices.stop == len(bm.verts): #make sure arc was added to bmesh
            spinVertices = [ bm.verts[i] for i in lastSpinVertIndices]
            spinVertices = [v0] + spinVertices
        if parameters['drawArcCenters']: # TODO MORE TESTING - invert+ flip, hexagon
            vX = bm.verts.new(chosenSpinCenter)
        return spinVertices

##########################################


    def rotateArcAroundSpinAxis(self, bm, mesh, vertices, roundifyParams, parameters):
        [chosenSpinCenter, otherSpinCenter, spinAxis, angle, steps, refObjectLocation] = roundifyParams
        axisAngle = parameters["axisAngle"]
        plane = parameters["plane"]
        #compensate rotation center
        objectLocation = bpy.context.active_object.location
        center = objectLocation + chosenSpinCenter 
        
        rot = Euler( (0.0, 0.0, radians(axisAngle)),'XYZ' ).to_matrix()
        if plane == YZ:
            rot = Euler( (radians(axisAngle),0.0, 0.0 ),'XYZ' ).to_matrix()
        if plane == XZ:
            rot = Euler( (0.0, radians(axisAngle),0.0),'XYZ' ).to_matrix()
           
        indexes = [v.index for v in vertices] 
        bmesh.ops.rotate(
                    bm,
                    cent=center,
                    matrix=rot,
                    verts=vertices,
                    space=bpy.context.edit_object.matrix_world
                    )
        self.sel.refreshMesh(bm, mesh)
        bm.verts.ensure_lookup_table()
        rotatedVertices = [bm.verts[i] for i in indexes]
        
        return rotatedVertices
            
    def deleteSpinVertices(self, bm, mesh, lastSpinVertIndices):
        verticesForDeletion = []
        bm.verts.ensure_lookup_table()
        for i in lastSpinVertIndices:
            vi = bm.verts[i]
            vi.select = True
            debugPrint(str(i) + ") " + str(vi))
            verticesForDeletion.append(vi)

        bmesh.ops.delete(bm, geom = verticesForDeletion, context = 1)
        bmesh.update_edit_mesh(mesh, True)
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.mode_set(mode = 'EDIT')


    def alternateSpin(self, bm, mesh, angle, chosenSpinCenter, spinAxis, steps, v0, v1org, lastSpinVertIndices):
        debugPrint("== begin alternate spin ==")
        for v in bm.verts:
            debugPrint (v.index)
        debugPrint("== indices for deletion ==")
        debugPrint(lastSpinVertIndices)
        for i in lastSpinVertIndices:
            debugPrint (i)

        self.deleteSpinVertices(bm, mesh, lastSpinVertIndices)
#        v0prim = bm.verts.new(v0.co) #komi3d > I am not sure if it should be new vert here or not...
        v0prim = v0
        debugPrint("== v0prim index: ==")
        debugPrint(v0prim.index)

        debugPrint("== BEFORE 2nd spin performed==")
        for v in bm.verts:
            debugPrint (v.index)

        debugPrint ("LEN before=")
        debugPrint(len(bm.verts))

        result2 = bmesh.ops.spin(bm, geom = [v0prim], cent = chosenSpinCenter, axis = spinAxis,
            angle = -angle, steps = steps, use_duplicate = False)
        # it seems there is something wrong with last index of this spin...
        # I need to calculate the last index manually here...
        debugPrint ("LEN after=")
        debugPrint(len(bm.verts))
        vertsLength = len(bm.verts)
        bm.verts.ensure_lookup_table()
        lastVertIndex2 = bm.verts[vertsLength - 1].index
        debugPrint("== 2nd spin performed==")
        for v in bm.verts:
            debugPrint (v.index)

        debugPrint("last:")
        debugPrint(result2['geom_last'][0].index)

        lastSpinVertIndices2 = self.getLastSpinVertIndices(steps, lastVertIndex2)
        
# second spin also does not hit the v1org
        if (result2['geom_last'][0].co - v1org.co).length > SPIN_END_THRESHOLD:
            
            debugPrint("== lastVertIndex2: ==")
            debugPrint(result2['geom_last'][0].index)
            debugPrint(lastVertIndex2)

            debugPrint("== 2nd spin ==")
            for v in bm.verts:
                debugPrint (v.index)
            debugPrint("== indices for deletion ==")
            debugPrint(lastSpinVertIndices2)
            for i in lastSpinVertIndices2:
                debugPrint (i)

            debugPrint("result2:")
            debugPrint(lastSpinVertIndices2)
            self.deleteSpinVertices(bm, mesh, lastSpinVertIndices2)
            self.deleteSpinVertices(bm, mesh, range(v0.index, v0.index + 1))
            return []
        else:
            return lastSpinVertIndices2

    def getLastSpinVertIndices(self, steps, lastVertIndex):
        arcfirstVertexIndex = lastVertIndex - steps + 1
        lastSpinVertIndices = range(arcfirstVertexIndex, lastVertIndex + 1)
        return lastSpinVertIndices

    def translateRoots(self, roots, objectLocation):
        # translationVector = self.calc.getVectorBetween2VertsXYZ(objectLocation, [0,0,0])
        r1 = Vector(roots[0]) + Vector(objectLocation) 
        r2 = Vector(roots[1]) + Vector(objectLocation)
        return [r1, r2]
    #PKHg>INFO not needed if 3D or 2D lists are replaced by Vector
    def getOppositeVector(self, originalVector):
        x, y, z = originalVector
        return [-x, -y, -z]

    def translateByVector(self, point, vector):
        translated = (point[0] + vector[0],
        point[1] + vector[1],
        point[2] + vector[2])
        return translated

    def CalculateRadiusAndAngle(self, edgeLength):
        degAngle = self.a
        angle = radians(degAngle)
        self.r = radius = edgeLength / (2 * sin(angle / 2))
        return radius, angle
    
    def CalculateRadiusAndAngleForAnglePresets(self, angleEnum, initR, initA, edgeLength):
        radius = initR
        angle = initA

        if angleEnum == "180":
            self.a = 180
        elif angleEnum == "120":
            self.a = 120
        elif angleEnum == "90":
            self.a = 90
        elif angleEnum == "60":
            self.a = 60
        elif angleEnum == "45":
            self.a = 45
        elif angleEnum == "30":
            self.a = 30
        return self.CalculateRadiusAndAngle(edgeLength)
        
    def CalculateRadiusAndAngleForAnglePresetsHalfMode(self, angleEnum, edgeLength):
        if angleEnum == "90":
            self.a = 90
        elif angleEnum == "60":
            self.a = 60
        elif angleEnum == "45":
            self.a = 45
        elif angleEnum == "30":
            self.a = 30
        else:
            self.a = 90    
        return self.CalculateRadiusFromAngleHalfMode(edgeLength)
        
    def CalculateRadiusFromAngleHalfMode(self, edgeLength):
        degAngle = self.a
        if degAngle > 90:
            degAngle = 90
        angle = radians(degAngle)
        radius = edgeLength / sin(angle)
        self.a = degrees(angle)
        self.r = radius
        return radius, angle

    def CalculateAngleFromRadiusHalfMode(self, edgeLength):
        radius = self.r
        if radius < edgeLength:
            radius = edgeLength
            self.r = radius
        
        angle = asin(edgeLength / radius)
        self.a = degrees(angle)
        return radius, angle
                    
    def getSpinCenterClosestToRefCenter(self, objLocation, roots, flip):
        root0Distance = (Vector(objLocation) - Vector(roots[0])).length
        root1Distance = (Vector(objLocation) - Vector(roots[1])).length 

        chosenId = 0
        rejectedId = 1
        if (root0Distance > root1Distance):
            chosenId = 1
            rejectedId = 0
        if flip:
            return roots[rejectedId], roots[chosenId] 
        else:
            return roots[chosenId], roots[rejectedId]

    def addMissingCoordinate(self, roots, startVertex, plane):
        if roots != None:
            a, b = roots[0]
            c, d = roots[1]
            if plane == XY:
                roots[0] = Vector((a, b, startVertex[2]))
                roots[1] = Vector((c, d, startVertex[2]))
            if plane == YZ:
                roots[0] = Vector((startVertex[0], a, b))
                roots[1] = Vector((startVertex[0], c, d))
            if plane == XZ:
                roots[0] = Vector((a, startVertex[1], b))
                roots[1] = Vector((c, startVertex[1], d))
        return roots

    def selectEdgesAfterRoundifier(self, context, edges):
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.mode_set(mode = 'EDIT')
        mesh = context.scene.objects.active.data
        bmnew = bmesh.new()
        bmnew.from_mesh(mesh)
        self.deselectEdges(bmnew)
        for selectedEdge in edges:
            for e in bmnew.edges:
                if (e.verts[0].co - selectedEdge.verts[0].co).length <= self.threshold \
                   and (e.verts[1].co - selectedEdge.verts[1].co).length <= self.threshold:
                    e.select_set(True)

        bpy.ops.object.mode_set(mode = 'OBJECT')
        bmnew.to_mesh(mesh)
        bmnew.free()
        bpy.ops.object.mode_set(mode = 'EDIT')


    def deselectEdges(self, bm):
        for edge in bm.edges:
            edge.select_set(False)

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