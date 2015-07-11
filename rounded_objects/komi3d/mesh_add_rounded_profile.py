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

class AddRoundedProfile(bpy.types.Operator):
    """Add rounded profile"""  # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mesh.rounded_profile_add"  # unique identifier for buttons and menu items to reference.
    bl_label = "Add rounded profile"  # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def draw(self, context):
        layout = self.layout
        layout.label('Radius < edge_length/2 causes arcs to disappear.')
        row = layout.row(align = False)
        row.label('Mode:')
        row.prop(self, 'modeEnum', expand = True, text = "a")
        row = layout.row(align = False)
        layout.label('Quick angle:')
        layout.prop(self, 'angleEnum', expand = True, text = "abv")
        row = layout.row(align = False)
    
    def execute(self, context):

        edges, mesh, bm = self.prepareMesh(context)
        parameters = self.prepareParameters()


    def __init__(self, params):
        '''
        Constructor
        '''
        pass
    
    @classmethod
    def poll(cls, context):
        return (context.scene.objects.active.type == 'MESH') and (context.scene.objects.active.mode == 'EDIT')

def draw_item(self, context):
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator('mesh.rounded_profile_add')


def register():
    #bpy.utils.register_class(EdgeRoundifier)
    #bpy.types.VIEW3D_MT_edit_mesh_edges.append(draw_item)
    pass


def unregister():
    #bpy.utils.unregister_class(EdgeRoundifier)
    #bpy.types.VIEW3D_MT_edit_mesh_edges.remove(draw_item)
    pass

if __name__ == "__main__":
    register()

