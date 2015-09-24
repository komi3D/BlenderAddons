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

import bpy

class RoundedProfilePanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_RoundedProfile"
    bl_label = "Rounded Profile"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
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
            row.prop(properties, 'masterCornerFlipAngle')
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
            row.prop(properties, 'masterConnectionType', expand = True)
            if properties.masterConnectionType == 'Arc':
                row = box.row()
                row.prop(properties, 'masterConnectionInout', expand = True)
                row = box.row()
                row.prop(properties, 'masterConnectionRadius')
                row.prop(properties, 'masterConnectionSides')
                row = box.row()
                row.prop(properties, 'masterConnectionflipCenter')
                row.prop(properties, 'masterConnectionflipAngle')


        return box


    def drawCornersAndConnections(self, layout, properties, box):
        numOfCorners = properties.numOfCorners
        coordSystem = properties.coordSystem
        if numOfCorners > 0:
            for id in range(0, len(properties.corners)):
                box = layout.box()
                self.addCornerToMenu(id + 1, box, properties.corners[id], properties.masterCornerEnabled, coordSystem)

            if not properties.masterConnectionEnabled:
                for id in range(0, len(properties.connections)):
                    box = layout.box()
                    self.addConnectionToMenu(id + 1, box, properties.connections[id], numOfCorners)


    def drawGeneralProperties(self, layout, properties):
        row = layout.row()
        row.prop(properties, 'type')
        row = layout.row()
        row.prop(properties, 'drawMode')
        row = layout.row()
        row.prop(properties, 'coordSystem')
        row = layout.row()
        row.prop(properties, 'numOfCorners')
        row = layout.row()
        row.prop(properties, 'connectionAutoAdjustEnabled')
        return row


    def drawInfo(self, layout, properties, row):
        row = layout.row()
        totalSidesText = "Total sides = " + str(properties.totalSides)
        row.label(totalSidesText)

    def drawProperties(self, o, layout):
        properties = o.RoundedProfileProps[0]

        row = self.drawGeneralProperties(layout, properties)
        box, row = self.drawMasterCornerProperties(layout, properties)
        box = self.drawMasterConnection(layout, properties, row, box)

        self.drawCornersAndConnections(layout, properties, box)
        self.drawInfo(layout, properties, row)

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


    def addCoordsForCorner(self, corners, coordSystem, row):
        if coordSystem == 'XY':
            row.prop(corners, 'x')
            row.prop(corners, 'y')
        elif coordSystem == 'Angular':
            row.prop(corners, 'coordAngle')
            row.prop(corners, 'coordRadius')


    def addCornerToMenu(self, id, box, corners, master, coordSystem):
        row = box.row()
        row.label("Corner " + str(id))
        if not master:
            row.prop(corners, 'flipAngle')
        row = box.row()

        self.addCoordsForCorner(corners, coordSystem, row)

        if not master:
            row = box.row()
            row.prop(corners, 'radius')
            row.prop(corners, 'sides')


    def addConnectionToMenu(self, id, box, connections, numOfCorners):
        if id < numOfCorners:
            box.label("Connection " + str(id) + "-" + str(id + 1))
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
            row.prop(connections, 'radius')
            row.prop(connections, 'sides')
            row = box.row()
            row.prop(connections, 'flipCenter')
            row.prop(connections, 'flipAngle')
