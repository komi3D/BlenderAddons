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

def addMesh(roundedProfileObject):
    corners = roundedProfileObject.RoundedProfileProps[0].corners
    connections = roundedProfileObject.RoundedProfileProps[0].connections

    mesh = roundedProfileObject.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    for corner in corners:
        drawCornerCircle(corner, bm)

    drawConnections(corners, connections, bm)
    bm.to_mesh(mesh)


def drawCornerCircle(corner, bm):
    center = Vector((corner.x, corner.y, corner.z))
    startPoint = center + Vector((0, 1, 0)) * corner.radius
    spinAxis = Vector((0, 0, 1))
    angle = two_pi
    v0 = bm.verts.new(startPoint)
    result = bmesh.ops.spin(bm, geom = [v0], cent = center, axis = spinAxis, \
                                   angle = angle, steps = corner.sides, use_duplicate = False)

def drawConnections(corners, connections, bm):
    drawConnection(corners[0], corners[1], connections[0], bm)

def drawConnection(corner1, corner2, connection, bm):
    c1 = Vector((corner1.x, corner1.y, corner1.z))
    r1 = corner1.radius + connection.radius
    c2 = Vector((corner2.x, corner2.y, corner2.z))
    r2 = corner1.radius + connection.radius

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

    print("StartPoints")
    print(c1ConnectionStartPoint)
    print(c2ConnectionStartPoint)

    print("---")

    angleDeg, angleRad = geomCalc.getAngleBetween3Points(c1ConnectionStartPoint, center, c2ConnectionStartPoint)

    spinAxis = Vector((0, 0, 1))
    v0 = bm.verts.new(c2ConnectionStartPoint)
    result = bmesh.ops.spin(bm, geom = [v0], cent = center, axis = spinAxis, \
                                   angle = angleRad, steps = connection.sides, use_duplicate = False)

def getClosestTangencyPoint(geomCalc, cornerCenter, connectionCenter, connectionRadius):
    lineAB1 = geomCalc.getCoefficientsForLineThrough2Points(cornerCenter, connectionCenter)
    lineCircleIntersections = None
    if cornerCenter[0] == connectionCenter[0]:
        lineCircleIntersections = geomCalc.getLineCircleIntersectionsWhenXPerpendicular(cornerCenter, connectionCenter, connectionRadius)
    else
        lineCircleIntersections = geomCalc.getLineCircleIntersections(lineAB1, connectionCenter, connectionRadius)
    if lineCircleIntersections == None:
        return None
    tangencyPoint = geomCalc.getCloserPointToRefPoint(lineCircleIntersections, connectionCenter)
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
#     print(rpp.numOfCorners)
#     print(rpp.corners)
#     print(rpp.corners[0])
    for cont in range(len(rpp.corners) - 1, rpp.numOfCorners):
        rpp.corners.add()
        rpp.connections.add()
    updateProfile(self, context)

def updateProfile(self, context):
    o = bpy.context.active_object
    o.select = False
    o.data.user_clear()
    bpy.data.meshes.remove(o.data)
    roundedProfileMesh = bpy.data.meshes.new("RoundedProfile")
    o.data = roundedProfileMesh
    o.data.use_fake_user = True
    # deselect all objects
    for obj in bpy.data.objects:
        obj.select = False
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

    radius = bpy.props.FloatProperty(name = 'R' , min = 0, max = 180, default = 0, precision = 1,
                                description = 'Radius', update = updateProfile)

    sides = bpy.props.IntProperty(name = 'Sides' , min = 1, max = 100, default = 4,
                                description = 'Number of sides', update = updateProfile)
bpy.utils.register_class(CornerProperties)


class ConnectionProperties(bpy.types.PropertyGroup):
    # if line then only sides available??
    type = bpy.props.EnumProperty(
        items = (('Arc', "Arc", ""), ('Line', "Line", "")),
        name = "type", description = "Type of connection", update = updateProfile)

    inout = bpy.props.EnumProperty(
        items = (('Outside', "Outside", ""), ('Inside', "Inside", "")),
        name = "inout", description = "Outside or inside connection", update = updateProfile)

    center = bpy.props.EnumProperty(
        items = (('First', "First", ""), ('Second', "Second", "")),
        name = "center", description = "Center of spinned connection", update = updateProfile)


    radius = bpy.props.FloatProperty(name = 'R' , min = 0, max = 100000, default = 0, precision = 1,
                                description = 'Radius', update = updateProfile)

    sides = bpy.props.IntProperty(name = 'Sides' , min = 2, max = 500, default = 4,
                                description = 'Number of sides in connection', update = updateProfile)

bpy.utils.register_class(ConnectionProperties)

class RoundedProfileProperties(bpy.types.PropertyGroup):
    numOfCorners = bpy.props.IntProperty(name = 'Number of corners' , min = 2, max = 100, default = 2,
                                description = 'Number of corners', update = addCorner)

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
            properties = o.RoundedProfileProps[0]
            row = layout.row()
            row.prop(properties, 'numOfCorners')
            # Corners
            numOfCorners = properties.numOfCorners
            if numOfCorners > 0:
                for id in range(0, numOfCorners):
                    box = layout.box()
                    self.addCornerToMenu(id + 1, box, properties.corners[id])
                for id in range(0, numOfCorners):
                    box = layout.box()
                    self.addConnectionToMenu(id + 1, box, properties.connections[id], numOfCorners)



    def addCornerToMenu(self, id, box, corners):
        box.label("Corner " + str(id))
        row = box.row()
        row.prop(corners, 'x')
        row.prop(corners, 'y')
        row.prop(corners, 'z')
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


