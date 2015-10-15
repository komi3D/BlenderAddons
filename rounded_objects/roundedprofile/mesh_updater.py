'''
Created on 20 sie 2015

@author: Komi
'''
from math import fabs, sqrt, acos, degrees, pi, radians

from mathutils import Vector

import bmesh
import bpy
from roundedprofile.coords_converter import CoordsConverter
from roundedprofile.geometry_calculator import GeometryCalculator

WRONG_FLOAT = 1e10
two_pi = 2 * pi
defaultZ = 0

class Updater():

    @staticmethod
    def addMesh(roundedProfileObject):
        corners = roundedProfileObject.RoundedProfileProps[0].corners
        connections = roundedProfileObject.RoundedProfileProps[0].connections
        drawMode = roundedProfileObject.RoundedProfileProps[0].drawMode
        roundedtype = roundedProfileObject.RoundedProfileProps[0].type

        mesh = roundedProfileObject.data
        bm = bmesh.new()
        bm.from_mesh(mesh)

        drawFunction = StrategyFactory.getDrawStrategy(drawMode, roundedtype)
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
    def adjustCornersAndConnectionsInPolygonMode(rpp, actualNum, delta):
        if delta > 0:
            for cont in range(0, delta):
                rpp.corners.add()
                rpp.connections.add()
        
        elif delta < 0:
            for cont in range(0, (delta) * (-1)):
                rpp.corners.remove(actualNum - 1)
                rpp.connections.remove(actualNum - 1)

    @staticmethod
    def adjustCornersAndConnectionsInChainMode(rpp, actualNum, delta):
        if delta > 0:
            for cont in range(0, delta):
                rpp.corners.add()
                rpp.connections.add()

        elif delta < 0:
            for cont in range(0, (delta) * (-1)):
                rpp.corners.remove(actualNum - 1)
                rpp.connections.remove(actualNum - 1)
                # TODO: connections number


    @staticmethod
    def adjustNumberOfCornersAndConnections(self, context):
        props = context.object.RoundedProfileProps[0]
        uiNum = props.numOfCorners


        previousType = props.type
#         print(" ======= ")
#         print("adjustNumberOfCornersAndConnections - prevtype: " + str(previousType))
#         print("adjustNumberOfCornersAndConnections - len(corners) " + str(len(props.corners)))
        props.type = 'Polygon'
        actualNum = len(props.corners)
        delta = uiNum - actualNum
#         print("adjustNumberOfCornersAndConnections - len(corners) in Polygon: " + str(len(props.corners)))

        Updater.adjustCornersAndConnectionsInPolygonMode(props, actualNum, delta)
#         print("adjustNumberOfCornersAndConnections - len(corners) in Polygon after adjust: " + str(len(props.corners)))
        Updater.updateCornerAndConnectionPropertiesFromMaster(self, context)
#         print("adjustNumberOfCornersAndConnections - len(corners) in Polygon after update: " + str(len(props.corners)))
        props.previousNumOfCorners = uiNum
        props.type = previousType
#         print("adjustNumberOfCornersAndConnections: " + str(len(props.corners)))


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
        roundedProfileObject.RoundedProfileProps[0].coordSystemChangingFlag = True
        converterToNewCoords = StrategyFactory.getConverterOnCoordsSystemChange(coordSystem)
        converterToNewCoords(corners)
        roundedProfileObject.RoundedProfileProps[0].coordSystemChangingFlag = False

    @staticmethod
    def updateCoordinatesOnCoordChange(self, context):
        roundedProfileObject = bpy.context.active_object
        corners = roundedProfileObject.RoundedProfileProps[0].corners
        coordSystem = roundedProfileObject.RoundedProfileProps[0].coordSystem
        flag = roundedProfileObject.RoundedProfileProps[0].coordSystemChangingFlag
        if flag == False:
            converterToXY = StrategyFactory.getConverterOnCoordsValueChange(coordSystem)
            converterToXY(corners)
        Updater.updateConnectionsRadiusForAutoadjust(self, context)

    @staticmethod
    def displayCoords(self, corners):
        print("-X-Y-ALPHA-RADIUS-")
        for c in corners:
            print("------")
            print(str(c.x) + " --- " + str(c.y) + " --- " + str(c.coordAngle) + " --- " + str(c.coordRadius))
        print("========================")

    @staticmethod
    def updateCornerAndConnectionPropertiesFromMaster(self, context):
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
    def updateType(self, context):
        props = Updater.getPropertiesFromContext(self, context)
        profileType = props.type
        previousCoordSystem = props.coordSystem
        props.coordSystem = 'XY'  # this is to allow changing profileType in XY coords space
        adjust = StrategyFactory.getTypeAdjust(profileType)
        adjust(props)
        props.coordSystem = previousCoordSystem  # switch back to original coords system
        Updater.updateProfile(self, context)

    @staticmethod
    def updateProfile(self, context):
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
                if c.radius > 0:
                    sidesAccumulator = sidesAccumulator + c.sides
            for c in connections:
                sidesAccumulator = sidesAccumulator + c.sides
        elif drawMode == 'Corners':
            for c in corners:
                if c.radius > 0:
                    sidesAccumulator = sidesAccumulator + c.sides
        elif drawMode == 'Connections':
            for c in connections:
                sidesAccumulator = sidesAccumulator + c.sides
        roundedProfileObject.RoundedProfileProps[0].totalSides = sidesAccumulator

    @staticmethod
    def getPropertiesFromContext(self, context):
        roundedProfileObject = bpy.context.active_object
        props = roundedProfileObject.RoundedProfileProps[0]
        return props
##################################
class StrategyFactory():
    @staticmethod
    def getDrawStrategy(drawMode, roundedProfileType):
        if drawMode == 'Corners':
            return drawModeCorners
        elif drawMode == 'Connections':
            return drawModeConnections
        elif drawMode == 'Both':
            return drawModeBoth
        elif drawMode == 'Merged result' and roundedProfileType != 'Curve':
            return drawModeMergedResult
        elif drawMode == 'Merged result' and roundedProfileType == 'Curve':
            return drawModeMergedResultForCurve

    @staticmethod
    def getDrawTangentStrategy(inout):
        if inout == 'Outer':
            return drawOuterTangentConnection
        elif inout == 'Inner':
            return drawInnerTangentConnection
        elif inout == 'Outer-Inner':
            return drawOuterInnerTangentConnection
        elif inout == 'Inner-Outer':
            return drawInnerOuterTangentConnection

    @staticmethod
    def getConverterOnCoordsSystemChange(coords):
        if coords == 'XY':
            return convertXYFake
        elif coords == 'Angular':
            return convertFromXYToGlobalAngular
        elif coords == 'DeltaXY':
            return convertFromXYToDxDy
        elif coords == 'DeltaAngular':
            return convertFromXYToRefAngular

    @staticmethod
    def getConverterOnCoordsValueChange(coords):
        if coords == 'XY':
            return convertXYFake
        elif coords == 'Angular':
            return convertFromGlobalAngularToXY
        elif coords == 'DeltaXY':
            return convertFromDxDyToXY
        elif coords == 'DeltaAngular':
            return convertFromRefAngularToXY

    @staticmethod
    def getTypeAdjust(profileType):
        if profileType == 'Polygon':
            return adjustToPolygon
        elif profileType == 'Curve':
            return adjustToCurve
        elif profileType == 'Chain':
            return adjustToChain
##################################

def adjustToPolygon(properties):
    corners = properties.corners
    corners_count = len(corners)
    connections = properties.connections
    previousNumOfCorners = properties.previousNumOfCorners

    # if switching from chain remove additional
    while corners_count > previousNumOfCorners:
        corners.remove(corners_count - 1)
        corners_count = len(corners)

    connections_count = len(connections)
    if(connections_count > corners_count):
        while(connections_count > corners_count):
            connections.remove(connections_count - 1)
            connections_count = len(connections)
    else:
        while(connections_count < corners_count):
            connections.add()
            connections_count = len(connections)

def adjustToCurve(properties):
    corners = properties.corners
    corners_count = len(corners)
    connections = properties.connections
    previousNumOfCorners = properties.previousNumOfCorners

    # if switching from chain remove additional
    while corners_count > previousNumOfCorners:
        corners.remove(corners_count - 1)
        corners_count = len(corners)
    
    connections_count = len(connections)
    if(connections_count >= corners_count):
        while(connections_count >= corners_count):
            connections.remove(connections_count - 1)
            connections_count = len(connections)
    else:
        while(connections_count < corners_count - 1):
            connections.add()
            connections_count = len(connections)
    

def adjustToChain(properties):
    adjustToCurve(properties)
    corners = properties.corners
    baseCornersCount = len(corners)
    connections = properties.connections
    baseConnectionsCount = len(connections)

    # middle corners are duplicated (2,3,4), start and end stays the same
    # original 1 - 2 - 3 - 4 - 5
    #          /  2  -  3 -  4 \
    #        1                   5
    #          \  2' -  3'-  4'/

    for k in reversed(range(0, baseConnectionsCount)):
        connections.add()
        lastConnectionIndex = len(connections) - 1
        assignConnectionProperties(connections[lastConnectionIndex], connections[k])
    for i in reversed(range(1, baseCornersCount - 1)):
        corners.add()
        lastCornerIndex = len(corners) - 1
        assignCornerProperties(corners[lastCornerIndex], corners[i])


def assignCornerProperties(target, source):
    target.x = source.x
    target.y = source.y
    target.flipAngle = source.flipAngle
    target.radius = source.radius
    target.sides = source.sides

def assignConnectionProperties(target, source):
    target.type = source.type
    target.inout = source.inout
    target.flipCenter = source.flipCenter
    target.flipAngle = source.flipAngle
    target.radius = source.radius
    target.sides = source.sides

def convertXYFake(corners):
    pass

def convertFromXYToGlobalAngular(corners):
    for c in corners:
        angle, radius = CoordsConverter.ToAngular(0, 0, c.x, c.y)
        c.coordAngle = degrees(angle)
        c.coordRadius = radius

def convertFromGlobalAngularToXY(corners):
    for c in corners:
        c.x, c.y = CoordsConverter.ToXY(0, 0, radians(c.coordAngle), c.coordRadius)

def convertFromXYToDxDy(corners):
    lastIndex = len(corners) - 1
    corners[0].dx = corners[0].x
    corners[0].dy = corners[0].y
    for i in range(0, lastIndex):
        corners[i + 1].dx = corners[i + 1].x - corners[i].x
        corners[i + 1].dy = corners[i + 1].y - corners[i].y

def convertFromDxDyToXY(corners):
    lastIndex = len(corners) - 1
    corners[0].x = corners[0].dx
    corners[0].y = corners[0].dy
    for i in range(0, lastIndex):
        corners[i + 1].x = corners[i].x + corners[i + 1].dx
        corners[i + 1].y = corners[i].y + corners[i + 1].dy

def convertFromXYToRefAngular(corners):
    c0 = corners[0]
    angle, c0.coordRadius = CoordsConverter.ToAngular(0, 0, c0.x, c0.y)
    c0.coordAngle = degrees(angle)

    lastIndex = len(corners) - 1
    for i in range(0, lastIndex):
        angle, radius = CoordsConverter.ToAngular(corners[i].x, corners[i].y, corners[i + 1].x, corners[i + 1].y)
        corners[i + 1].coordAngle = degrees(angle)
        corners[i + 1].coordRadius = radius

def convertFromRefAngularToXY(corners):
    c0 = corners[0]
    c0.x, c0.y = CoordsConverter.ToXY(0, 0, radians(c0.coordAngle), c0.coordRadius)

    lastIndex = len(corners) - 1
    for i in range(0, lastIndex):
        corners[i + 1].x, corners[i + 1].y = CoordsConverter.ToXY(corners[i].x, corners[i].y,
                                                               radians(corners[i + 1].coordAngle), corners[i + 1].coordRadius)

# 'XY', 'Angular', 'DeltaXY','DeltaAngular'
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

def drawModeMergedResultForCurve(corners, connections, mesh, bm):
    drawConnections(corners, connections, bm)

    for index in range(1, len(corners) - 1):
        drawCornerAsArc(corners[index], bm)

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
    if corner.startx == WRONG_FLOAT or corner.starty == WRONG_FLOAT or corner.endx == WRONG_FLOAT or corner.endy == WRONG_FLOAT:
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
    connectionsLastIndex = len(connections) - 1
    cornersLastIndex = len(corners) - 1
    for i in range(cornersLastIndex):
        drawConnection(corners[i], corners[i + 1], connections[i], bm)
    if connectionsLastIndex == cornersLastIndex:
        drawConnection(corners[cornersLastIndex], corners[0], connections[cornersLastIndex], bm)

def drawConnection(corner1, corner2, connection, bm):
    drawTangentConnection = StrategyFactory.getDrawTangentStrategy(connection.inout)
    print(drawTangentConnection)
    drawTangentConnection(corner1, corner2, connection, bm)

def assignCornerEndPoint(corner, endPoint):
    if endPoint != None:
        corner.endx = endPoint[0]
        corner.endy = endPoint[1]
        corner.endz = defaultZ
    else:
        corner.endx = WRONG_FLOAT
        corner.endy = WRONG_FLOAT
        corner.endz = WRONG_FLOAT

def assignCornerStartPoint(corner, startPoint):
    if startPoint != None:
        corner.startx = startPoint[0]
        corner.starty = startPoint[1]
        corner.startz = defaultZ
    else:
        corner.startx = WRONG_FLOAT
        corner.starty = WRONG_FLOAT
        corner.startz = WRONG_FLOAT

def drawTangentConnectionTemplate(corner1, corner2, connection, bm, getConnectionEndPoints):
    c1 = Vector((corner1.x, corner1.y, defaultZ))
    r1 = connection.radius - (corner1.radius)
    c2 = Vector((corner2.x, corner2.y, defaultZ))
    r2 = connection.radius - (corner2.radius)

    geomCalc = GeometryCalculator()

    intersections = geomCalc.getCircleIntersections(c1, r1, c2, r2)
    if intersections == None:
        assignCornerEndPoint(corner1, None)
        assignCornerStartPoint(corner2, None)
        return

    center = None

    if len(intersections) == 1:
        center = intersections[0]
    elif len(intersections) == 2:
        if not connection.flipCenter:
            center = intersections[1]
        else:
            center = intersections[0]
# getConnectionEndPointsForOuterTangent
# getConnectionEndPoints
    connectionStartPoint, connectionEndPoint = getConnectionEndPoints(geomCalc, center, c1, corner1.radius, c2, corner2.radius, connection.radius)
    print ("----")
    print (connectionStartPoint)
    print (connectionEndPoint)
    
    assignCornerEndPoint(corner1, connectionStartPoint)
    assignCornerStartPoint(corner2, connectionEndPoint)

    angleDeg, angleRad = geomCalc.getPositiveAngleBetween3Points(connectionStartPoint, center, connectionEndPoint)

    if connection.flipAngle:
        angleRad = -(2 * pi - angleRad)

    spinAxis = Vector((0, 0, 1))
    v0 = bm.verts.new(connectionEndPoint)
    result = bmesh.ops.spin(bm, geom = [v0], cent = center, axis = spinAxis, \
                                   angle = angleRad, steps = connection.sides, use_duplicate = False)


def getConnectionEndPointsForInnerTangent(geomCalc, center, c1, c1radius, c2, c2radius, connectionRadius):
    connectionStartPoint = getFarthestTangencyPoint(geomCalc, center, c1, c1radius)
    connectionEndPoint = getFarthestTangencyPoint(geomCalc, center, c2, c2radius)
    print ("INNER - " + str(connectionStartPoint) + " - " + str(connectionEndPoint))
    return connectionStartPoint, connectionEndPoint

def getConnectionEndPointsForOuterTangent(geomCalc, center, c1, c1radius, c2, c2radius, connectionRadius):
    connectionStartPoint = getClosestTangencyPoint(geomCalc, c1, center, connectionRadius)
    connectionEndPoint = getClosestTangencyPoint(geomCalc, c2, center, connectionRadius)
    print ("OUTER - " + str(connectionStartPoint) + " - " + str(connectionEndPoint))
    return connectionStartPoint, connectionEndPoint

def getConnectionEndPointsForOuterInnerTangent(geomCalc, center, c1, c1radius, c2, c2radius, connectionRadius):
    connectionStartPoint = getClosestTangencyPoint(geomCalc, c1, center, connectionRadius)
    connectionEndPoint = getFarthestTangencyPoint(geomCalc, center, c2, c2radius)
    print ("OUTER - INNER - " + str(connectionStartPoint) + " - " + str(connectionEndPoint))
    return connectionStartPoint, connectionEndPoint

def getConnectionEndPointsForInnerOuterTangent(geomCalc, center, c1, c1radius, c2, c2radius, connectionRadius):
    connectionStartPoint = getFarthestTangencyPoint(geomCalc, center, c1, c1radius)
    connectionEndPoint = getClosestTangencyPoint(geomCalc, c2, center, connectionRadius)
    print ("INNER - OUTER  - " + str(connectionStartPoint) + " - " + str(connectionEndPoint))
    return connectionStartPoint, connectionEndPoint

    
def drawInnerTangentConnection(corner1, corner2, connection, bm):
    drawTangentConnectionTemplate(corner1, corner2, connection, bm, getConnectionEndPointsForInnerTangent)

def drawOuterTangentConnection(corner1, corner2, connection, bm):
    drawTangentConnectionTemplate(corner1, corner2, connection, bm, getConnectionEndPointsForOuterTangent)

def drawOuterInnerTangentConnection(corner1, corner2, connection, bm):
    drawTangentConnectionTemplate(corner1, corner2, connection, bm, getConnectionEndPointsForOuterInnerTangent)

def drawInnerOuterTangentConnection(corner1, corner2, connection, bm):
    drawTangentConnectionTemplate(corner1, corner2, connection, bm, getConnectionEndPointsForInnerOuterTangent)


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
