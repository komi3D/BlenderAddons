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
        self.extrudeEdges(context)
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
        normal = (0,0,0)
        facesWithEdge = edge.link_faces
        lenFacesWithEdge = len(facesWithEdge)
        if lenFacesWithEdge == 2:
            n1 = facesWithEdge[0].normal
            n2 = facesWithEdge[1].normal
            normal = n1 + n2
        else:
            print("getEdgeNormal - error getting normal, lenFacesWithEdge = " +  str(lenFacesWithEdge))
        return normal

    def createObjAndAlignToFace(self, face, bm):
        destVector = face.normal
        srcVector = Vector((0, 0, 1))
        idMatrix = Matrix.Identity(3)
        rotMatrix = idMatrix * srcVector.rotation_difference(destVector).to_matrix()
        bmesh.ops.create_circle(bm, segments=6, diameter=1, matrix=rotMatrix)
    
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