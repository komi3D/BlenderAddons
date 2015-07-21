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


    ##### POLL #####
    @classmethod
    def poll(cls, context):
        return context.scene is not None

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

