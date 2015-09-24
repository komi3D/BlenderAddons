'''
Created on 20 sie 2015

@author: Komi
'''
from math import fabs, sqrt, acos, degrees, pi

from mathutils import Vector

import bmesh
import bpy
from roundedprofile.geometry_calculator import GeometryCalculator

two_pi = 2 * pi
defaultZ = 0

class Updater():
    @staticmethod
    def addMesh(roundedProfileObject):
        corners = roundedProfileObject.RoundedProfileProps[0].corners
        connections = roundedProfileObject.RoundedProfileProps[0].connections
        drawMode = roundedProfileObject.RoundedProfileProps[0].drawMode

        mesh = roundedProfileObject.data
        bm = bmesh.new()
        bm.from_mesh(mesh)

        drawFunction = StrategyFactory.getDrawStrategy(drawMode)
        drawFunction(corners, connections, mesh, bm)

    @staticmethod
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

        Updater.addMesh(roundedProfileObject)
        # we select, and activate, main object for the room.
        roundedProfileObject.select = True
        bpy.context.scene.objects.active = roundedProfileObject

    @staticmethod
    def adjustCornersAndConnections(self, context):
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
        Updater.updateCornerAndConnectionProperties(self, context)

    @staticmethod
    def updateConnectionsRadiusForAutoadjust(self, context):
        roundedProfileObject = bpy.context.active_object
        props = roundedProfileObject.RoundedProfileProps[0]
        autoadjust = props.connectionAutoAdjustEnabled
        if autoadjust:
            corners = props.corners
            connections = props.connections
            lastIndex = len(corners) - 1
            for i in range(lastIndex):
                Updater.updateConnectionRadius(corners[i], corners[i + 1], connections[i])
            Updater.updateConnectionRadius(corners[lastIndex], corners[0], connections[lastIndex])
        Updater.updateProfile(self, context)

    @staticmethod
    def updateConnectionRadius(corner1, corner2, connection):
        c1 = Vector((corner1.x, corner1.y, defaultZ))
        c2 = Vector((corner2.x, corner2.y, defaultZ))
        geomCalc = GeometryCalculator()
        c1c2, c1c2Length = geomCalc.getVectorAndLengthFrom2Points(c1, c2)
        if (corner1.radius + corner2.radius) <= c1c2Length:
            connection.radius = c1c2Length
        else:
            connection.radius = corner1.radius + corner2.radius

    # TODO - think it through how and when to update alpha and radius and when to update X and Y??? what about reference angular and reference XY
    @staticmethod
    def updateCoordinatesOnCoordSystemChange(self, context):
        roundedProfileObject = bpy.context.active_object
        corners = roundedProfileObject.RoundedProfileProps[0].corners
        coordSystem = roundedProfileObject.RoundedProfileProps[0].coordSystem
        converterToNewCoords = StrategyFactory.getConverterOnCoordsSystemChange(coordSystem)
        converterToNewCoords(corners)
        Updater.updateProfile(self, context)

    @staticmethod
    def updateCoordinatesOnCoordChange(self, context):
        roundedProfileObject = bpy.context.active_object
        corners = roundedProfileObject.RoundedProfileProps[0].corners
        coordSystem = roundedProfileObject.RoundedProfileProps[0].coordSystem
        converterToXY = StrategyFactory.getConverterOnCoordsValueChange(coordSystem)
        converterToXY(corners)
        Updater.updateConnectionsRadiusForAutoadjust(self, context)

    @staticmethod
    def updateCornerAndConnectionProperties(self, context):
        roundedProfileObject = bpy.context.active_object
        props = roundedProfileObject.RoundedProfileProps[0]
        if props.masterCornerEnabled:
            for c in props.corners:
                c.radius = props.masterCornerRadius
                c.sides = props.masterCornerSides
                c.flipAngle = props.masterCornerFlipAngle
        if props.masterConnectionEnabled:
            for c in props.connections:
                c.type = props.masterConnectionType
                c.inout = props.masterConnectionInout
                c.flipCenter = props.masterConnectionflipCenter
                c.flipAngle = props.masterConnectionflipAngle
                c.radius = props.masterConnectionRadius
                c.sides = props.masterConnectionSides
        Updater.updateProfile(self, context)

    @staticmethod
    def updateProfile(self, context):
        # Updater.updateConnectionsRadiusForAutoadjust(self, context)
        o = bpy.context.active_object
        o.select = False
        o.data.user_clear()
        bpy.data.meshes.remove(o.data)
        roundedProfileMesh = bpy.data.meshes.new("RoundedProfile")
        o.data = roundedProfileMesh
        o.data.use_fake_user = True

        Updater.refreshTotalSides(o)
        Updater.addMesh(o)
        o.select = True
        bpy.context.scene.objects.active = o

    @staticmethod
    def refreshTotalSides(roundedProfileObject):
        corners = roundedProfileObject.RoundedProfileProps[0].corners
        connections = roundedProfileObject.RoundedProfileProps[0].connections
        drawMode = roundedProfileObject.RoundedProfileProps[0].drawMode

        sidesAccumulator = 0
        if drawMode == 'Both' or drawMode == 'Merged result':
            for c in corners:
                sidesAccumulator = sidesAccumulator + c.sides
            for c in connections:
                sidesAccumulator = sidesAccumulator + c.sides
        elif drawMode == 'Corners':
            for c in corners:
                sidesAccumulator = sidesAccumulator + c.sides
        elif drawMode == 'Connections':
            for c in connections:
                sidesAccumulator = sidesAccumulator + c.sides
        roundedProfileObject.RoundedProfileProps[0].totalSides = sidesAccumulator


class StrategyFactory():
    @staticmethod
    def getDrawStrategy(drawMode):
        if drawMode == 'Corners':
            return drawModeCorners
        elif drawMode == 'Connections':
            return drawModeConnections
        elif drawMode == 'Both':
            return drawModeBoth
        elif drawMode == 'Merged result':
            return drawModeMergedResult

    @staticmethod
    def getDrawTangentStrategy(inout):
        if inout == 'Outer':
            return drawOuterTangentConnection
        elif inout == 'Inner':
            return drawInnerTangentConnection
        # TODO: add for lines, out-in and in-out


    @staticmethod
    def getConverterOnCoordsSystemChange(coords):
        if coords == 'XY':
            return convertXYFake
        elif coords == 'Angular':
            return convertFromXYToGlobalAngular
        elif coords == 'PreviousRefXY':
            return convertFromXYToDxDy
        elif coords == 'PreviousRefAngular':
            return convertFromXYToRefAngular

    @staticmethod
    def getConverterOnCoordsValueChange(coords):
        if coords == 'XY':
            return convertXYFake
        elif coords == 'Angular':
            return convertFromGlobalAngularToXY
        elif coords == 'PreviousRefXY':
            return convertFromDxDyToXY
        elif coords == 'PreviousRefAngular':
            return convertFromRefAngularToXY

def convertXYFake(corners):
    pass

# TODO:
def convertFromXYToGlobalAngular(corners):
    pass

def convertFromXYToDxDy(corners):
    pass

def convertFromXYToRefAngular(corners):
    pass

def convertFromGlobalAngularToXY(corners):
    pass

def convertFromDxDyToXY(corners):
    pass

def convertFromRefAngularToXY(corners):
    pass

# ## 'XY', 'Angular', 'PreviousRefXY','PreviousRefAngular'

def drawModeCorners(corners, connections, mesh, bm):
    for corner in corners:
        drawCornerCircle(corner, bm)
    bm.to_mesh(mesh)

def drawModeConnections(corners, connections, mesh, bm):
    drawConnections(corners, connections, bm)
    bm.to_mesh(mesh)


def drawModeBoth(corners, connections, mesh, bm):
    drawModeCorners(corners, connections, mesh, bm)
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

def drawCornerCircle(corner, bm):
    center = Vector((corner.x, corner.y, defaultZ))
    startPoint = center + Vector((0, 1, 0)) * corner.radius
    spinAxis = Vector((0, 0, 1))
    angle = two_pi
    v0 = bm.verts.new(startPoint)
    result = bmesh.ops.spin(bm, geom = [v0], cent = center, axis = spinAxis, \
                                   angle = angle, steps = corner.sides, use_duplicate = False)
def drawCornerAsArc(corner, bm):
    if corner.startx == None or corner.starty == None or corner.endx == None or corner.endy == None:
        return
    center = Vector((corner.x, corner.y, defaultZ))
    startPoint = Vector ((corner.startx, corner.starty, defaultZ))
    endPoint = Vector ((corner.endx, corner.endy, defaultZ))

    geomCalc = GeometryCalculator()
    angleDeg, angle = geomCalc.getPositiveAngleBetween3Points(startPoint, center, endPoint)

    spinAxis = Vector((0, 0, 1))
    v0 = bm.verts.new(startPoint)
    if corner.flipAngle:
        v0 = bm.verts.new(endPoint)
        angle = two_pi - angle
    result = bmesh.ops.spin(bm, geom = [v0], cent = center, axis = spinAxis, \
                                   angle = -angle, steps = corner.sides, use_duplicate = False)

def drawConnections(corners, connections, bm):
    lastIndex = len(corners) - 1
    for i in range(lastIndex):
        drawConnection(corners[i], corners[i + 1], connections[i], bm)
    drawConnection(corners[lastIndex], corners[0], connections[lastIndex], bm)

def drawConnection(corner1, corner2, connection, bm):
    drawTangentConnection = StrategyFactory.getDrawTangentStrategy(connection.inout)
    drawTangentConnection(corner1, corner2, connection, bm)

def assignCornerEndPoint(corner, endPoint):
    if endPoint != None:
        corner.endx = endPoint[0]
        corner.endy = endPoint[1]
        corner.endz = defaultZ
    else:
        corner.endx = None
        corner.endy = None
        corner.endz = None

def assignCornerStartPoint(corner, startPoint):
    if startPoint != None:
        corner.startx = startPoint[0]
        corner.starty = startPoint[1]
        corner.startz = defaultZ
    else:
        corner.startx = None
        corner.starty = None
        corner.startz = None

def drawInnerTangentConnection(corner1, corner2, connection, bm):
    c1 = Vector((corner1.x, corner1.y, defaultZ))
    r1 = connection.radius - (corner1.radius)
    c2 = Vector((corner2.x, corner2.y, defaultZ))
    r2 = connection.radius - (corner2.radius)

    geomCalc = GeometryCalculator()

    intersections = geomCalc.getCircleIntersections(c1, r1, c2, r2)
    if intersections == None:
        return

    center = None

    if len(intersections) == 1:
        center = intersections[0]
    elif len(intersections) == 2:
        if not connection.flipCenter:
            center = intersections[1]
        else:
            center = intersections[0]

    c1ConnectionStartPoint = getFarthestTangencyPoint(geomCalc, center, c1, corner1.radius)
    c2ConnectionStartPoint = getFarthestTangencyPoint(geomCalc, center, c2, corner2.radius)
    assignCornerEndPoint(corner1, c1ConnectionStartPoint)
    assignCornerStartPoint(corner2, c2ConnectionStartPoint)

    angleDeg, angleRad = geomCalc.getPositiveAngleBetween3Points(c1ConnectionStartPoint, center, c2ConnectionStartPoint)

    if connection.flipAngle:
        angleRad = -(2 * pi - angleRad)

    spinAxis = Vector((0, 0, 1))
    v0 = bm.verts.new(c2ConnectionStartPoint)
    result = bmesh.ops.spin(bm, geom = [v0], cent = center, axis = spinAxis, \
                                   angle = angleRad, steps = connection.sides, use_duplicate = False)



def drawOuterTangentConnection(corner1, corner2, connection, bm):
    c1 = Vector((corner1.x, corner1.y, defaultZ))
    r1 = corner1.radius + connection.radius
    c2 = Vector((corner2.x, corner2.y, defaultZ))
    r2 = corner2.radius + connection.radius

    geomCalc = GeometryCalculator()

    intersections = geomCalc.getCircleIntersections(c1, r1, c2, r2)
    if intersections == None:
        return

    center = None

    if len(intersections) == 1:
        center = intersections[0]
    elif len(intersections) == 2:
        if not connection.flipCenter:
            center = intersections[1]
        else:
            center = intersections[0]

    c1ConnectionStartPoint = getClosestTangencyPoint(geomCalc, c1, center, connection.radius)
    c2ConnectionStartPoint = getClosestTangencyPoint(geomCalc, c2, center, connection.radius)
    assignCornerEndPoint(corner1, c1ConnectionStartPoint)
    assignCornerStartPoint(corner2, c2ConnectionStartPoint)

    angleDeg, angleRad = geomCalc.getPositiveAngleBetween3Points(c1ConnectionStartPoint, center, c2ConnectionStartPoint)

    if connection.flipAngle :
        angleRad = -(2 * pi - angleRad)

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
