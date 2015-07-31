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

import bmesh
import bpy
from bpy.props import *
from komi3d.geometry_calculator import GeometryCalculator

two_pi = 2 * pi
XY = "XY"
XZ = "XZ"
YZ = "YZ"

# TODO Probably to remove function removeMesh
def removeMesh(roundedProfileObject):

    mesh = roundedProfileObject.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    selectedVertices = [f for f in bm.vertices if f.select]
    bmesh.ops.delete(bm, geom = selectedVertices, context = 1)

    bm.to_mesh(mesh)


def drawModeCorners(corners, mesh, bm):
    for corner in corners:
        drawCornerCircle(corner, bm)
    bm.to_mesh(mesh)

def drawModeConnections(corners, connections, mesh, bm):
    drawConnections(corners, connections, bm)
    bm.to_mesh(mesh)


def drawModeBoth(corners, connections, mesh, bm):
    drawModeCorners(corners, mesh, bm)
    drawConnections(corners, connections, bm)
    bm.to_mesh(mesh)

def drawModeMergedResult(corners, connections, mesh, bm):
    drawConnections(corners, connections, bm)
    for corner in corners:
        drawCornerAsArc(corner, bm)

    bm.to_mesh(mesh)

    selectedVerts = [f for f in bm.verts]
    bmesh.ops.remove_doubles(bm, verts = selectedVerts, dist = 0.001)

    bm.to_mesh(mesh)



def addMesh(roundedProfileObject):
    corners = roundedProfileObject.RoundedProfileProps[0].corners
    connections = roundedProfileObject.RoundedProfileProps[0].connections
    drawMode = roundedProfileObject.RoundedProfileProps[0].drawMode

    mesh = roundedProfileObject.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    # 'Corners', 'Connections', 'Both', 'Merged result'
    if drawMode == 'Corners':
        drawModeCorners(corners, mesh, bm)
    elif drawMode == 'Connections':
        drawModeConnections(corners, connections, mesh, bm)
    elif drawMode == 'Both':
        drawModeBoth(corners, connections, mesh, bm)
    elif drawMode == 'Merged result':
        drawModeMergedResult(corners, connections, mesh, bm)


def drawCornerCircle(corner, bm):
    center = Vector((corner.x, corner.y, corner.z))
    startPoint = center + Vector((0, 1, 0)) * corner.radius
    spinAxis = Vector((0, 0, 1))
    angle = two_pi
    v0 = bm.verts.new(startPoint)
    result = bmesh.ops.spin(bm, geom = [v0], cent = center, axis = spinAxis, \
                                   angle = angle, steps = corner.sides, use_duplicate = False)
def drawCornerAsArc(corner, bm):
    center = Vector((corner.x, corner.y, corner.z))
    startPoint = Vector ((corner.startx, corner.starty, corner.startz))
    endPoint = Vector ((corner.endx, corner.endy, corner.endz))

    geomCalc = GeometryCalculator()
    angleDeg, angle = geomCalc.getAngleBetween3Points(startPoint, center, endPoint)
    spinAxis = Vector((0, 0, 1))
    v0 = bm.verts.new(startPoint)
    result = bmesh.ops.spin(bm, geom = [v0], cent = center, axis = spinAxis, \
                                   angle = angle, steps = corner.sides, use_duplicate = False)

def drawConnections(corners, connections, bm):
    lastIndex = len(corners) - 1
    for i in range(lastIndex):
        drawConnection(corners[i], corners[i + 1], connections[i], bm)
    drawConnection(corners[lastIndex], corners[0], connections[lastIndex], bm)

def drawConnection(corner1, corner2, connection, bm):
    if connection.inout == 'Outer':
        drawOuterTangentConnection(corner1, corner2, connection, bm)
    elif connection.inout == 'Inner':
        drawInnerTangentConnection(corner1, corner2, connection, bm)

def assignCornerEndPoint(corner, endPoint):
    corner.endx = endPoint[0]
    corner.endy = endPoint[1]
    corner.endz = endPoint[2]

def assignCornerStartPoint(corner, startPoint):
    corner.startx = startPoint[0]
    corner.starty = startPoint[1]
    corner.startz = startPoint[2]

def drawInnerTangentConnection(corner1, corner2, connection, bm):
    c1 = Vector((corner1.x, corner1.y, corner1.z))
    r1 = connection.radius - (corner1.radius)
    c2 = Vector((corner2.x, corner2.y, corner2.z))
    r2 = connection.radius - (corner2.radius)

    geomCalc = GeometryCalculator()

    intersections = geomCalc.getCircleIntersections(c1, r1, c2, r2)
    if intersections == None:
        return

    center = None

    if len(intersections) == 1:
        center = intersections[0]
    elif len(intersections) == 2:
        if connection.center == 'First':
            center = intersections[1]
        else:
            center = intersections[0]

    c1ConnectionStartPoint = getFarthestTangencyPoint(geomCalc, center, c1, corner1.radius)
    c2ConnectionStartPoint = getFarthestTangencyPoint(geomCalc, center, c2, corner2.radius)
    assignCornerEndPoint(corner1, c1ConnectionStartPoint)
    assignCornerStartPoint(corner2, c2ConnectionStartPoint)

    angleDeg, angleRad = geomCalc.getAngleBetween3Points(c1ConnectionStartPoint, center, c2ConnectionStartPoint)

    spinAxis = Vector((0, 0, 1))
    v0 = bm.verts.new(c2ConnectionStartPoint)
    result = bmesh.ops.spin(bm, geom = [v0], cent = center, axis = spinAxis, \
                                   angle = angleRad, steps = connection.sides, use_duplicate = False)
    


def drawOuterTangentConnection(corner1, corner2, connection, bm):
    c1 = Vector((corner1.x, corner1.y, corner1.z))
    r1 = corner1.radius + connection.radius
    c2 = Vector((corner2.x, corner2.y, corner2.z))
    r2 = corner2.radius + connection.radius

    geomCalc = GeometryCalculator()

    intersections = geomCalc.getCircleIntersections(c1, r1, c2, r2)
    if intersections == None:
        return

    center = None

    if len(intersections) == 1:
        center = intersections[0]
    elif len(intersections) == 2:
        if connection.center == 'First':
            center = intersections[0]
        else:
            center = intersections[1]

    c1ConnectionStartPoint = getClosestTangencyPoint(geomCalc, c1, center, connection.radius)
    c2ConnectionStartPoint = getClosestTangencyPoint(geomCalc, c2, center, connection.radius)
    assignCornerEndPoint(corner1, c1ConnectionStartPoint)
    assignCornerStartPoint(corner2, c2ConnectionStartPoint)

    angleDeg, angleRad = geomCalc.getAngleBetween3Points(c1ConnectionStartPoint, center, c2ConnectionStartPoint)

    spinAxis = Vector((0, 0, 1))
    v0 = bm.verts.new(c2ConnectionStartPoint)
    result = bmesh.ops.spin(bm, geom = [v0], cent = center, axis = spinAxis, \
                                   angle = angleRad, steps = connection.sides, use_duplicate = False)

def getLineCircleIntersections(geomCalc, RefPoint, Center, Radius):
    lineAB1 = geomCalc.getCoefficientsForLineThrough2Points(RefPoint, Center)
    lineCircleIntersections = None
    if RefPoint[0] == Center[0]:
        lineCircleIntersections = geomCalc.getLineCircleIntersectionsWhenXPerpendicular(RefPoint, Center, Radius)
    else:
        lineCircleIntersections = geomCalc.getLineCircleIntersections(lineAB1, Center, Radius)
    return lineCircleIntersections


def getClosestTangencyPoint(geomCalc, refPoint, center, radius):
    lineCircleIntersections = getLineCircleIntersections(geomCalc, refPoint, center, radius)
    if lineCircleIntersections == None:
        return None
    
    tangencyPoint = geomCalc.getClosestPointToRefPoint(lineCircleIntersections, refPoint)
    return tangencyPoint

def getFarthestTangencyPoint(geomCalc, refPoint, center, radius):
    lineCircleIntersections = getLineCircleIntersections(geomCalc, refPoint, center, radius)
    if lineCircleIntersections == None:
        return None
    
    tangencyPoint = geomCalc.getFarthestPointToRefPoint(lineCircleIntersections, refPoint)
    return tangencyPoint


def createRoundedProfile(self, context):
    # deselect all objects
    for o in bpy.data.objects:
        o.select = False

    # we create main object and mesh for walls
    roundedProfileMesh = bpy.data.meshes.new("RoundedProfile")
    roundedProfileObject = bpy.data.objects.new("RoundedProfile", roundedProfileMesh)
    roundedProfileObject.location = bpy.context.scene.cursor_location

    bpy.context.scene.objects.link(roundedProfileObject)
    roundedProfileObject.RoundedProfileProps.add()
    roundedProfileObject.RoundedProfileProps[0].corners.add()
    roundedProfileObject.RoundedProfileProps[0].corners.add()
    roundedProfileObject.RoundedProfileProps[0].connections.add()
    roundedProfileObject.RoundedProfileProps[0].connections.add()

    addMesh(roundedProfileObject)
    # we select, and activate, main object for the room.
    roundedProfileObject.select = True
    bpy.context.scene.objects.active = roundedProfileObject

def addCorner(self, context):
    rpp = context.object.RoundedProfileProps[0]
    uiNum = rpp.numOfCorners
    actualNum = len(rpp.corners)
    delta = uiNum - actualNum

    if delta > 0:
        for cont in range(0, delta):
            rpp.corners.add()
            rpp.connections.add()
    elif delta < 0:
        for cont in range(0, (delta) * (-1)):
            rpp.corners.remove(actualNum - 1)
            rpp.connections.remove(actualNum - 1)
    updateCornerAndConnectionProperties(self, context)


def updateCornerAndConnectionProperties(self, context):
    roundedProfileObject = bpy.context.active_object
    props = roundedProfileObject.RoundedProfileProps[0]
    if props.masterCornerEnabled:
        for c in props.corners:
            c.radius = props.masterCornerRadius
            c.sides = props.masterCornerSides
    if props.masterConnectionEnabled:
        for c in props.connections:
            c.type = props.masterConnectionType
            c.inout = props.masterConnectionInout
            c.center = props.masterConnectionCenter
            c.radius = props.masterConnectionRadius
            c.sides = props.masterConnectionSides
    updateProfile(self, context)


def updateProfile(self, context):
    o = bpy.context.active_object
    o.select = False
    o.data.user_clear()
    bpy.data.meshes.remove(o.data)
    roundedProfileMesh = bpy.data.meshes.new("RoundedProfile")
    o.data = roundedProfileMesh
    o.data.use_fake_user = True

    addMesh(o)

    o.select = True
    bpy.context.scene.objects.active = o


class CornerProperties(bpy.types.PropertyGroup):
    x = bpy.props.FloatProperty(name = 'X' , min = -1000, max = 1000, default = 0, precision = 1,
                                description = 'Center X', update = updateProfile)

    y = bpy.props.FloatProperty(name = 'Y' , min = -1000, max = 1000, default = 0, precision = 1,
                                description = 'Center Y', update = updateProfile)

    z = bpy.props.FloatProperty(name = 'Z' , min = -1000, max = 1000, default = 0, precision = 1,
                                description = 'Center Z', update = updateProfile)

    startx = bpy.props.FloatProperty(name = 'X' , min = -1000, max = 1000, default = 0, precision = 1,
                                description = 'Start X')

    starty = bpy.props.FloatProperty(name = 'Y' , min = -1000, max = 1000, default = 0, precision = 1,
                                description = 'Start Y')

    startz = bpy.props.FloatProperty(name = 'Z' , min = -1000, max = 1000, default = 0, precision = 1,
                                description = 'Start Z')


    endx = bpy.props.FloatProperty(name = 'X' , min = -1000, max = 1000, default = 0, precision = 1,
                                description = 'End X')

    endy = bpy.props.FloatProperty(name = 'Y' , min = -1000, max = 1000, default = 0, precision = 1,
                                description = 'End Y')

    endz = bpy.props.FloatProperty(name = 'Z' , min = -1000, max = 1000, default = 0, precision = 1,
                                description = 'End Z')


    radius = bpy.props.FloatProperty(name = 'R' , min = 0, max = 100000, default = 1, precision = 1,
                                description = 'Radius', update = updateProfile)

    sides = bpy.props.IntProperty(name = 'Sides' , min = 1, max = 200, default = 16,
                                description = 'Number of sides', update = updateProfile)
bpy.utils.register_class(CornerProperties)


class ConnectionProperties(bpy.types.PropertyGroup):
    # if line then only sides available??
    type = bpy.props.EnumProperty(
        items = (('Arc', "Arc", ""), ('Line', "Line", "")),
        name = "type", description = "Type of connection", update = updateProfile)

    inout = bpy.props.EnumProperty(
        items = (('Outer', "Outer", ""), ('Inner', "Inner", ""), ('Outer-Inner', "Outer-Inner", ""), ('Inner-Outer', "Inner-Outer", "")),
        name = "inout", description = "Tangency type for the connection", update = updateProfile)

    center = bpy.props.EnumProperty(
        items = (('First', "First", ""), ('Second', "Second", "")),
        name = "center", description = "Center of spinned connection", update = updateProfile)


    radius = bpy.props.FloatProperty(name = 'R' , min = 0, max = 100000, default = 4, precision = 1,
                                description = 'Radius', update = updateProfile)

    sides = bpy.props.IntProperty(name = 'Sides' , min = 2, max = 200, default = 8,
                                description = 'Number of sides in connection', update = updateProfile)

bpy.utils.register_class(ConnectionProperties)

class RoundedProfileProperties(bpy.types.PropertyGroup):
    drawMode = bpy.props.EnumProperty(
        items = (('Corners', "Corners", ""), ('Connections', "Connections", ""), ('Both', "Both", ""),
                 ('Merged result', "Merged result", ""),),
        name = "drawMode", description = "Mode of drawing the profile", update = updateProfile)

    numOfCorners = bpy.props.IntProperty(name = 'Number of corners' , min = 2, max = 100, default = 2,
                                description = 'Number of corners', update = addCorner)

    masterCornerEnabled = bpy.props.BoolProperty(name = 'Master corner', default = False, update = updateCornerAndConnectionProperties)
    masterCornerRadius = bpy.props.FloatProperty(name = 'R' , min = 0, max = 100000, default = 1, precision = 1,
                                description = 'Master corner radius', update = updateCornerAndConnectionProperties)

    masterCornerSides = bpy.props.IntProperty(name = 'Sides' , min = 1, max = 200, default = 16,
                                description = 'Number of sides in all corners', update = updateCornerAndConnectionProperties)

    masterConnectionEnabled = bpy.props.BoolProperty(name = 'Master connection', default = False)
    masterConnectionType = bpy.props.EnumProperty(
        items = (('Arc', "Arc", ""), ('Line', "Line", "")),
        name = "type", description = "Type of connection", update = updateCornerAndConnectionProperties)

    masterConnectionInout = bpy.props.EnumProperty(
        items = (('Outer', "Outer", ""), ('Inner', "Inner", ""), ('Outer-Inner', "Outer-Inner", ""), ('Inner-Outer', "Inner-Outer", "")),
        name = "inout", description = "Tangency type for the connection", update = updateCornerAndConnectionProperties)

    masterConnectionCenter = bpy.props.EnumProperty(
        items = (('First', "First", ""), ('Second', "Second", "")),
        name = "center", description = "Center of spinned connection", update = updateCornerAndConnectionProperties)

    masterConnectionRadius = bpy.props.FloatProperty(name = 'R' , min = 0, max = 100000, default = 4, precision = 1,
                                description = 'Master connection radius', update = updateCornerAndConnectionProperties)

    masterConnectionSides = bpy.props.IntProperty(name = 'Sides' , min = 2, max = 200, default = 8,
                                description = 'Number of sides in all connection', update = updateCornerAndConnectionProperties)

    corners = bpy.props.CollectionProperty(type = CornerProperties)

    connections = bpy.props.CollectionProperty(type = ConnectionProperties)


    planeEnum = bpy.props.EnumProperty(
        items = ((XY, XY, "XY Plane (Z=0)"), (YZ, YZ, "YZ Plane (X=0)"), (XZ, XZ, "XZ Plane (Y=0)")),
        name = '',
        default = 'XY',
        description = "Plane used by addon to calculate plane of drawn arcs")


bpy.utils.register_class(RoundedProfileProperties)
bpy.types.Object.RoundedProfileProps = bpy.props.CollectionProperty(type = RoundedProfileProperties)

class AddRoundedProfile(bpy.types.Operator):
    """Add rounded profile"""  # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mesh.rounded_profile_add"  # unique identifier for buttons and menu items to reference.
    bl_label = "Add rounded profile"  # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):
        if bpy.context.mode == "OBJECT":
            createRoundedProfile(self, context)
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "RoundedProfile: works only in Object mode")
            return {'CANCELLED'}

    def draw (self, context):
        layout = self.layout
        row = layout.row()
        row.label('Edit Rounded Profile Parameters in:')
        row = layout.row()
        row.label('Tools > Addons > Rounded Profile panel')
        

    ##### POLL #####
    @classmethod
    def poll(cls, context):
        # return bpy.context.mode == "OBJECT"
        return True
    
class RoundedProfilePanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_RoundedProfile"
    bl_label = "Rounded Profile"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'Addons'

    @classmethod
    def poll(cls, context):
        o = context.object
        if o is None:
            return False
        if 'RoundedProfileProps' not in o:
            return False
        else:
            return True



    def drawMasterCornerProperties(self, layout, properties):
        box = layout.box()
        row = box.row()
        row.prop(properties, 'masterCornerEnabled')
        if properties.masterCornerEnabled:
            row = box.row()
            row.prop(properties, 'masterCornerRadius')
            row.prop(properties, 'masterCornerSides')
        return box, row


    def drawMasterConnection(self, layout, properties, row, box):
        box = layout.box()
        row = box.row()
        row.prop(properties, 'masterConnectionEnabled')
        if properties.masterConnectionEnabled:
            row = box.row()
            row.prop(properties, 'masterConnectionType', expand=True)
            if properties.masterConnectionType == 'Arc':
                row = box.row()
                row.prop(properties, 'masterConnectionInout', expand=True)
                row = box.row()
                row.prop(properties, 'masterConnectionCenter', expand=True)
                row = box.row()
                row.prop(properties, 'masterConnectionRadius')
                row.prop(properties, 'masterConnectionSides')
        return box


    def drawCornersAndConnections(self, layout, properties, box):
        numOfCorners = properties.numOfCorners
        if numOfCorners > 0:
            for id in range(0, len(properties.corners)):
                box = layout.box()
                self.addCornerToMenu(id + 1, box, properties.corners[id], properties.masterCornerEnabled)
            
            if not properties.masterConnectionEnabled:
                for id in range(0, len(properties.connections)):
                    box = layout.box()
                    self.addConnectionToMenu(id + 1, box, properties.connections[id], numOfCorners)


    def drawGeneralProperties(self, layout, properties):
        row = layout.row()
        row.prop(properties, 'drawMode')
        row = layout.row()
        row.prop(properties, 'numOfCorners')
        return row

    def drawProperties(self, o, layout):
        properties = o.RoundedProfileProps[0]

        row = self.drawGeneralProperties(layout, properties)
        box, row = self.drawMasterCornerProperties(layout, properties)
        box = self.drawMasterConnection(layout, properties, row, box)

        self.drawCornersAndConnections(layout, properties, box)

    def draw(self, context):
        o = context.object
        try:
            if 'RoundedProfileProps' not in o:
                return
        except:
            return

        layout = self.layout
        if bpy.context.mode == 'EDIT_MESH':
            layout.label('Warning: Operator does not work in edit mode.', icon = 'ERROR')
        else:
            self.drawProperties(o, layout)



    def addCornerToMenu(self, id, box, corners, master):
        box.label("Corner " + str(id))
        row = box.row()
        row.prop(corners, 'x')
        row.prop(corners, 'y')
        row.prop(corners, 'z')
        if not master:
            row = box.row()
            row.prop(corners, 'radius')
            row.prop(corners, 'sides')

    def addConnectionToMenu(self, id, box, connections, numOfCorners):
        if id < numOfCorners:
            box.label("Connection " + str(id) + "-" + str(id+1))
        elif id == numOfCorners:
            box.label("Connection " + str(id) + "-" + str(1))
        else:
            return 
        row = box.row()
        row.prop(connections, 'type', expand = True)
        if connections.type == 'Arc' :
            row = box.row()
            row.prop(connections, 'inout', expand = True)
            row = box.row()
            row.prop(connections, 'center', expand = True)
            row = box.row()
            row.prop(connections, 'radius')
            row.prop(connections, 'sides')

################################
def menu_func(self, context):
    self.layout.operator(AddRoundedProfile.bl_idname, text = bl_info['name'], icon = "PLUGIN")
    
def register():
    bpy.utils.register_class(RoundedProfilePanel)
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_mesh_add.append(menu_func)
    pass

def unregister():
    bpy.utils.unregister_class(RoundedProfilePanel)
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_mesh_add.remove(menu_func)
    pass

if __name__ == "__main__":
    register()


