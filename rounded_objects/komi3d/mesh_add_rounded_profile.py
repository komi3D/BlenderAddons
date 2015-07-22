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

from komi3d.geometry_calculator import GeometryCalculator








class AddRoundedProfile(bpy.types.Operator):
    """Add rounded profile"""  # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mesh.rounded_profile_add"  # unique identifier for buttons and menu items to reference.
    bl_label = "Add rounded profile"  # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    corners = bpy.props.IntProperty(name = 'Corners' , min = 2, max = 100, default = 2, precision = 1,
                                description = 'Number of corners')

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
            if properties.numOfCorners > 0:
                for id in range(0, properties.numOfCorners):
                    box = layout.box()
                    self.addCornerToMenu(id + 1, box, properties.corners[id])

    def addCornerToMenu(self, id, box, corners):
        box.label("Corner " + str(id))
        row = box.row()
        row.prop(corners, 'x')
        row.prop(corners, 'y')
        row.prop(corners, 'z')
        row = box.row()
        row.prop(corners, 'radius')
        row.prop(corners, 'sides')


    def execute(self, context):
        if bpy.context.mode == "OBJECT":
            createRoundedProfile(self, context)
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "RoundedProfile: works only in Object mode")
            return {'CANCELLED'}


        

    ##### POLL #####
    @classmethod
    def poll(cls, context):
        return bpy.context.mode == "OBJECT"
    
def addMeshElements(roundedProfileObject):
    pass

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
    roundedProfileObject.RoundedProfileProps[0].connections.add()

    addMeshElements(roundedProfileObject)
    # we select, and activate, main object for the room.
    roundedProfileObject.select = True
    bpy.context.scene.objects.active = roundedProfileObject
    pass

def update_profile(self, context):
    # When we update, the active object is the main object of the room.
    o = bpy.context.active_object
    # Now we deselect that room object to not delete it.
    o.select = False
    # Remove walls (mesh of room/active object),
    o.data.user_clear()
    bpy.data.meshes.remove(o.data)
    # and we create a new mesh for the RoundedProfile:
    roundedProfileMesh = bpy.data.meshes.new("RoundedProfile")
    o.data = roundedProfileMesh
    o.data.use_fake_user = True
    # deselect all objects
    for obj in bpy.data.objects:
        obj.select = False
    # Remove children created by this addon:
#     for child in o.children:
#         # noinspection PyBroadException
#         try:
#             if child["archimesh.room_object"]:
#                 # noinspection PyBroadException
#                 try:
#                     # remove child relationship
#                     for grandchild in child.children:
#                         grandchild.parent = None
#                     # remove modifiers
#                     for mod in child.modifiers:
#                         bpy.ops.object.modifier_remove(mod)
#                 except:
#                     pass
#                     # clear data
#                 child.data.user_clear()
#                 bpy.data.meshes.remove(child.data)
#                 child.select = True
#                 bpy.ops.object.delete()
#         except:
#             pass
            # Finally we create all that again (except main object),
    addMeshElements(o)
    # and select, and activate, the main object of the room.
    o.select = True
    bpy.context.scene.objects.active = o


class CornerProperties(bpy.types.PropertyGroup):
    x = bpy.props.FloatProperty(name = 'X' , min = -1000, max = 1000, default = 0, precision = 1,
                                description = 'Center X', update = update_profile)

    y = bpy.props.FloatProperty(name = 'Y' , min = -1000, max = 1000, default = 0, precision = 1,
                                description = 'Center Y', update = update_profile)

    z = bpy.props.FloatProperty(name = 'Z' , min = -1000, max = 1000, default = 0, precision = 1,
                                description = 'Center Z', update = update_profile)

    radius = bpy.props.FloatProperty(name = 'r' , min = 0, max = 180, default = 0, precision = 1,
                                description = 'Radius', update = update_profile)

    sides = bpy.props.IntProperty(name = 'numOfSides' , min = 1, max = 100, default = 4,
                                description = 'Number of sides', update = update_profile)

bpy.utils.register_class(CornerProperties)

class ConnectionProperties(bpy.types.PropertyGroup):
    # if line then only sides available??
    type = bpy.props.EnumProperty(
        items = (('0', "Arc", ""), ('1', "Line", "")),
        name = "", description = "Type of connection", update = update_profile)

    inout = bpy.props.EnumProperty(
        items = (('0', "Inside", ""), ('1', "Outside", "")),
        name = "", description = "Inside or outside connection", update = update_profile)

    center = bpy.props.EnumProperty(
        items = (('0', "First", ""), ('1', "Second", "")),
        name = "", description = "Center of spinned connection", update = update_profile)


    radius = bpy.props.FloatProperty(name = 'r' , min = 0, max = 100000, default = 0, precision = 1,
                                description = 'Radius', update = update_profile)

    sides = bpy.props.IntProperty(name = 'numOfSides' , min = 2, max = 500, default = 4,
                                description = 'Number of sides in connection', update = update_profile)


bpy.utils.register_class(ConnectionProperties)

class RoundedProfileProperties(bpy.types.PropertyGroup):
    numOfCorners = bpy.props.IntProperty(name = 'NumOfCorners' , min = 2, max = 100, default = 2,
                                description = 'Number of corners', update = update_profile)

    corners = bpy.props.CollectionProperty(type = CornerProperties)

    connections = bpy.props.CollectionProperty(type = ConnectionProperties)


bpy.utils.register_class(RoundedProfileProperties)
bpy.types.Object.RoundedProfileProps = bpy.props.CollectionProperty(type = RoundedProfileProperties)


################################
def menu_func(self, context):
    self.layout.operator(AddRoundedProfile.bl_idname, text = bl_info['name'], icon = "PLUGIN")
    
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

