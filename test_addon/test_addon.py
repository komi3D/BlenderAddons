bl_info = {
    "name": "Test Addon",
    "category": "Mesh",
    'author': 'Piotr Komisarczyk (komi3D), PKHG',
    'version': (1, 0, 0),
    'blender': (2, 7, 8),
    'location': 'SPACE > Test Addon',
    'description': 'test addon',
    'wiki_url': '',
    'tracker_url': '',
    'category': 'Mesh'
}

import bpy
import bmesh
import math
from mathutils import Vector, Matrix

class TestAddon(bpy.types.Operator):
    """TestAddon"""
    bl_idname = "mesh.test_addon"
    bl_label = "Test Addon Operator"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    normalFaces = []

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        #self.extrudeEdges(context)
        self.processEdges(context)
        return {'FINISHED'}

    
    def prepareMesh(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')

        mesh = context.scene.objects.active.data
        bm = bmesh.new()
        bm.from_mesh(mesh)
        
        edges = [ele for ele in bm.edges if ele.select]
        return edges, mesh, bm

    def refreshMesh(self, bm, mesh):
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bm.to_mesh(mesh)
        bpy.ops.object.mode_set(mode = 'EDIT')

    def processEdges(self, context):
        edges, mesh, bm = self.prepareMesh(context)
        for e in edges:
            matrix = self.creteTransformOrientation(e, mesh, bm)
            self.spinOnEdge(e, mesh, bm, matrix)

#########################################################
    def extrudeEdges(self, context):
        edges, mesh, bm = self.prepareMesh(context)
        for e in edges:
            self.extrudeEdge([e], mesh, bm)
    
    def extrudeEdge(self, edgeList, mesh, bm):
        edge = edgeList[0]
        normal = self.getEdgeNormalWithLinkFaces(edge, bm)   

        ret = bmesh.ops.extrude_edge_only(
            bm,
            edges=edgeList)
        geom = ret["geom"]

        verts_extruded = [ele for ele in geom if isinstance(ele, bmesh.types.BMVert)]
        faceAfterExtrude = [e for e in geom if isinstance(e, bmesh.types.BMFace)]
 
        bmesh.ops.translate(bm, verts=verts_extruded, vec=normal)
        faceNormal = faceAfterExtrude[0].normal
        self.createObjAndAlignToFace(faceAfterExtrude[0], bm)
        print("normal of extruded face:")
        print(faceNormal)
        self.refreshMesh(bm,mesh)
    
    def getEdgeNormalWithLinkFaces(self, edge, bm):
        normal = Vector((0,0,0))
        facesWithEdge = edge.link_faces
        lenFacesWithEdge = len(facesWithEdge)
        if lenFacesWithEdge == 2:
            n1 = facesWithEdge[0].normal
            n2 = facesWithEdge[1].normal
            normal = n1 + n2
        elif lenFacesWithEdge == 1:
            n = facesWithEdge[0].normal
            v0 = edge.verts[0].co
            v1 = edge.verts[1].co
            a = v1-v0
            normal = a.cross(n)
        else:
            print("getEdgeNormal - error getting normal, lenFacesWithEdge = " +  str(lenFacesWithEdge))
        return normal

    def createObjAndAlignToFace(self, face, bm):
        destVector = face.normal
        srcVector = Vector((0, 0, 1))
        idMatrix = Matrix.Identity(3)
        rotMatrix = idMatrix * srcVector.rotation_difference(destVector).to_matrix()
        bmesh.ops.create_circle(bm, segments=6, diameter=1, matrix=rotMatrix)
        self.newTransformOrientation(rotMatrix)
##########################################################

    def creteTransformOrientation(self, e, mesh, bm):
        matrix = self.makeMatrixFromEdge(e, bm)
        self.newTransformOrientation(matrix,'balbina')
        return matrix


    def newTransformOrientation(self, mat, orientationName):
        context = bpy.context
        scene = context.scene

        # create view
        bpy.ops.transform.create_orientation(name=orientationName, overwrite=True)
        orientation = scene.orientations.get(orientationName)

        mat3 = mat.to_3x3()

        orientation.matrix = mat3

        # find 3d views to set to "new"
        screen = context.screen
        views = [area.spaces.active for area in screen.areas if area.type == 'VIEW_3D']
        for view in views:
            view.transform_orientation = orientation.name
        
    def makeMatrixFromEdge(self, edge, bm):
        edgeNormal = self.getEdgeNormalWithLinkFaces(edge,bm)
        v1 = edge.verts[0].co
        v2 = edge.verts[1].co
        v3 = v1 + edgeNormal
        self.displayVerts([v1,v2,v3])
        mat = self.makeMatrixFromVerts(v1,v2,v3)
        print('MATRIX:')
        print(mat)
        return mat
        
    def makeMatrixFromVerts(self, v1, v2, v3):
        a = v2-v1
        b = v3-v1
        c = a.cross(b)
        if c.magnitude>0:
            c = c.normalized()
        else:
            raise BaseException("A B C are colinear")

        b2 = c.cross(a).normalized()
        a2 = a.normalized()
        print('matrix Z=')
        print(c)
        m = Matrix([a2, b2, c]).transposed()
        #s = a.magnitude
        s = 1
        m = Matrix.Translation(v1) * Matrix.Scale(s,4) * m.to_4x4()
        m = m.to_3x3()
        return m

    def spinOnEdge(self, edge, mesh, bm, matrix):
        center = (edge.verts[0].co + edge.verts[1].co )/2

        v0org = edge.verts[1]
        v0 = bm.verts.new(v0org.co)
        angle = math.pi
        steps = 8
        print('center=' + str(center))
        
        result = bmesh.ops.spin(bm, geom = [v0], cent = center, axis = matrix.transposed()[2], \
                                   angle = angle, steps = steps, use_duplicate = False)
        self.refreshMesh(bm, mesh)


    def displayVerts(self, verts):
        print('verts:')
        for v in verts:
            print (str(v))
        print('---')
    
    def displayFaces(self, faces):
        print ('=== FACES ===')
        for f in faces:
            print('---')
            print (str(f))
            print (' edges')
            for e in f.edges:
                print (str(e))
                print('  verts')
                for v in e.verts:
                    print (str(v.co))
        print ('=== END FACES ===')

def register():
    bpy.utils.register_class(TestAddon)


def unregister():
    bpy.utils.unregister_class(TestAddon)


if __name__ == "__main__":
    register()

    # # test call
    # bpy.ops.object.simple_operator()