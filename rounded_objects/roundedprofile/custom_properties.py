'''
Created on 20 sie 2015

@author: Komi
'''
from math import fabs, sqrt, acos, degrees, pi
from mathutils import Vector

import bpy
from bpy.props import *
from roundedprofile.mesh_updater import Updater

XY = 'XY'
XZ = 'XZ'
YZ = 'YZ'

class CornerProperties(bpy.types.PropertyGroup):
    x = bpy.props.FloatProperty(name = 'X' , min = -1000, max = 1000, default = 0, precision = 1,
                                description = 'Center X', update = Updater.updateConnectionsRadiusForAutoadjust)

    y = bpy.props.FloatProperty(name = 'Y' , min = -1000, max = 1000, default = 0, precision = 1,
                                description = 'Center Y', update = Updater.updateConnectionsRadiusForAutoadjust)

    dx = bpy.props.FloatProperty(name = 'deltaX' , min = -1000, max = 1000, default = 0, precision = 1,
                                description = 'Delta X', update = Updater.updateCoordinatesOnCoordChange)

    dy = bpy.props.FloatProperty(name = 'deltaY' , min = -1000, max = 1000, default = 0, precision = 1,
                                description = 'Delta Y', update = Updater.updateCoordinatesOnCoordChange)

    coordAngle = bpy.props.FloatProperty(name = 'Angle' , min = -360, max = 360, default = 0, precision = 1,
                                description = 'Angular coordinate angle', update = Updater.updateCoordinatesOnCoordChange)

    coordRadius = bpy.props.FloatProperty(name = 'Radius' , min = 0, max = 100000, default = 0, precision = 1,
                                description = 'Angular coordinate radius', update = Updater.updateCoordinatesOnCoordChange)

    startx = bpy.props.FloatProperty(name = 'X' , min = -1000, max = 1000, default = 0, precision = 1,
                                description = 'Start X')

    starty = bpy.props.FloatProperty(name = 'Y' , min = -1000, max = 1000, default = 0, precision = 1,
                                description = 'Start Y')

    endx = bpy.props.FloatProperty(name = 'X' , min = -1000, max = 1000, default = 0, precision = 1,
                                description = 'End X')

    endy = bpy.props.FloatProperty(name = 'Y' , min = -1000, max = 1000, default = 0, precision = 1,
                                description = 'End Y')

    flipAngle = bpy.props.BoolProperty(name = "Flip Angle", default = False, description = "Change angle to 2pi - angle", update = Updater.updateProfile)


    radius = bpy.props.FloatProperty(name = 'R' , min = 0, max = 100000, default = 1, precision = 1,
                                description = 'Radius', update = Updater.updateProfile)

    sides = bpy.props.IntProperty(name = 'Sides' , min = 1, max = 200, default = 8,
                                description = 'Number of sides', update = Updater.updateProfile)



class ConnectionProperties(bpy.types.PropertyGroup):
    # if line then only sides available??
    type = bpy.props.EnumProperty(
        items = (('Arc', "Arc", ""), ('Line', "Line", "")),
        name = "type", description = "Type of connection", update = Updater.updateProfile)

    inout = bpy.props.EnumProperty(
        items = (('Outer', "Outer", ""), ('Inner', "Inner", ""), ('Outer-Inner', "Outer-Inner", ""), ('Inner-Outer', "Inner-Outer", "")),
        name = "inout", description = "Tangency type for the connection", update = Updater.updateProfile)

    flipCenter = bpy.props.BoolProperty(name = "Flip Center", default = False, description = "Change center of spinned connection", update = Updater.updateProfile)

    flipAngle = bpy.props.BoolProperty(name = "Flip Angle", default = False, description = "Change angle to 2pi - angle", update = Updater.updateProfile)


    radius = bpy.props.FloatProperty(name = 'R' , min = 0, max = 100000, default = 4, precision = 1,
                                description = 'Radius', update = Updater.updateProfile)

    sides = bpy.props.IntProperty(name = 'Sides' , min = 1, max = 200, default = 4,
                                description = 'Number of sides in connection', update = Updater.updateProfile)



class RoundedProfileProperties(bpy.types.PropertyGroup):

    type = bpy.props.EnumProperty(
        items = (('Polygon', "Polygon", ""), ('Chain', "Chain", ""), ('ClosedChain', "Closed chain", ""),),
        name = "Type", description = "Type of the profile", update = Updater.updateProfile)

    drawMode = bpy.props.EnumProperty(
        items = (('Both', "Both", ""), ('Corners', "Corners", ""),
                  ('Connections', "Connections", ""), ('Merged result', "Merged result", ""),),
        name = "Draw mode", description = "Mode of drawing the profile", update = Updater.updateProfile)

    coordSystem = bpy.props.EnumProperty(
        items = (('XY', "XY", ""), ('Angular', "Angular", ""),
                  ('PreviousRefXY', "PreviousRefXY", ""), ('PreviousRefAngular', "PreviousRefAngular", ""),),
        name = "Coordinates", description = "Mode of entering corner coordinates", update = Updater.updateCoordinatesOnCoordSystemChange)

    coordSystemChangingFlag = bpy.props.BoolProperty(name = "coordSystemChangingFlag", default = False, description = "Helper flag when changing coords system")


    totalSides = bpy.props.IntProperty(name = 'Total sides' , min = 2, max = 1000, default = 2,
                                description = 'Number of sides in the whole profile',)


    numOfCorners = bpy.props.IntProperty(name = 'Number of corners' , min = 2, max = 100, default = 2,
                                description = 'Number of corners', update = Updater.adjustCornersAndConnections)

    connectionAutoAdjustEnabled = bpy.props.BoolProperty(name = 'Auto adjust connections',
                                default = False, update = Updater.updateConnectionsRadiusForAutoadjust)

    masterCornerEnabled = bpy.props.BoolProperty(name = 'Master corner', default = False, update = Updater.updateCornerAndConnectionProperties)
    masterCornerRadius = bpy.props.FloatProperty(name = 'R' , min = 0, max = 100000, default = 1, precision = 1,
                                description = 'Master corner radius', update = Updater.updateCornerAndConnectionProperties)

    masterCornerSides = bpy.props.IntProperty(name = 'Sides' , min = 1, max = 200, default = 8,
                                description = 'Number of sides in all corners', update = Updater.updateCornerAndConnectionProperties)
    masterCornerFlipAngle = bpy.props.BoolProperty(name = "Flip Angle", default = False, description = "Change angle to 2pi - angle", update = Updater.updateCornerAndConnectionProperties)


    masterConnectionEnabled = bpy.props.BoolProperty(name = 'Master connection', default = False)
    masterConnectionType = bpy.props.EnumProperty(
        items = (('Arc', "Arc", ""), ('Line', "Line", "")),
        name = "type", description = "Type of connection", update = Updater.updateCornerAndConnectionProperties)

    masterConnectionInout = bpy.props.EnumProperty(
        items = (('Outer', "Outer", ""), ('Inner', "Inner", ""), ('Outer-Inner', "Outer-Inner", ""), ('Inner-Outer', "Inner-Outer", "")),
        name = "inout", description = "Tangency type for the connection", update = Updater.updateCornerAndConnectionProperties)

    masterConnectionflipCenter = bpy.props.BoolProperty(name = "Flip Center", default = False, description = "Change center of spinned connections", update = Updater.updateCornerAndConnectionProperties)

    masterConnectionflipAngle = bpy.props.BoolProperty(name = "Flip Angle", default = False, description = "Change angle to 2pi - angle", update = Updater.updateCornerAndConnectionProperties)

    masterConnectionRadius = bpy.props.FloatProperty(name = 'R' , min = 0, max = 100000, default = 4, precision = 1,
                                description = 'Master connection radius', update = Updater.updateCornerAndConnectionProperties)

    masterConnectionSides = bpy.props.IntProperty(name = 'Sides' , min = 1, max = 200, default = 4,
                                description = 'Number of sides in all connection', update = Updater.updateCornerAndConnectionProperties)

    corners = bpy.props.CollectionProperty(type = CornerProperties)

    connections = bpy.props.CollectionProperty(type = ConnectionProperties)


    planeEnum = bpy.props.EnumProperty(
        items = ((XY, XY, "XY Plane (Z=0)"), (YZ, YZ, "YZ Plane (X=0)"), (XZ, XZ, "XZ Plane (Y=0)")),
        name = '',
        default = 'XY',
        description = "Plane used by addon to calculate plane of drawn arcs")

