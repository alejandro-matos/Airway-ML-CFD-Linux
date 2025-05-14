# Msc Ortho CFD Blender 2.82 script File
# Computational Fluid Dynamics Lab
# Author = Uday Tummala
# Dr. Carlos F. Lange
# Department of Mechanical Engineering
# University of Alberta
#
# Date 2023-12-27
# cmd = blender --background --python blender_ortho.py

import bpy
import math
import mathutils
import time
import os

start_time = time.time()

# delete all existing objects
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# import stl file
file0 = open("sdir.txt", "r")
path0 = file0.readline()
file0.close()
file = open("geo_in.txt", "r")
path1 = file.readline().strip()  # strip() removes any extra newline characters
bpy.ops.import_mesh.stl(filepath= path1)

# import stl file
#bpy.ops.import_mesh.stl(filepath= "/home/uday/Desktop/msc_ortho/Automation/Ortho_App_0.2/P5T1_TopCut.stl")

# Align xyz
bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN', center='MEDIAN')
active_obj = bpy.context.active_object
active_object_verts = active_obj.data.vertices
xValues = []
yValues = []
zValues = []
for v in active_object_verts:
    if v.select == True:
        xValues.append(v.co[0])
        yValues.append(v.co[1])
        zValues.append(v.co[2])

#p1t1 1=0.0261799
#p1t2 1=0
#p2t1 2=-0.05
#p2t2 2=-0.02
#p1t1 w_nozzle 1=0.025 , 2=-0.02
#p1t2 w_nozzle 1=0 , 2=-0.04
#P5T1_TopCut 2 = -0.065
bpy.context.object.rotation_euler[1] = 0
bpy.context.object.rotation_euler[2] = 0

# Removing artifacts and grab the bounds
minx =  min(xValues)
maxx =  max(xValues)
miny =  min(yValues)
maxy =  max(yValues)
minz =  min(zValues)
maxz =  max(zValues)
# Move to +ve co-ordinates
bpy.context.object.location[0] = abs(minx)
bpy.context.object.location[1] = abs(miny)
bpy.context.object.location[2] = abs(minz)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.bisect(plane_co=(0, 0, 0.5), plane_no=(0, 0, 1), use_fill=True, clear_inner=False, xstart=1000, xend=0, ystart=0, yend=0)
#p1t2 = plane_co=(0, 0, 0.2)
bpy.ops.mesh.loop_to_region(select_bigger=True)
bpy.ops.mesh.separate(type='SELECTED')
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='DESELECT')
model = bpy.context.active_object
bpy.context.active_object.select_set(True)
bpy.ops.object.delete()
bpy.ops.object.select_all(action='SELECT')
for obj in bpy.context.selected_objects:
    obj.name = "wall"
    obj.data.name = "wall"


bpy.ops.object.select_all(action='DESELECT')
ob = bpy.data.objects["wall"]

# Make Outlet
bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, location=(0, 0, 0))
cube = bpy.context.active_object
bpy.context.view_layer.objects.active = cube

#p1t1 0-100 1-100 2-15
#p1t2 0-100 1-100 2-12
#p2t1 0-100 1-120 2-12
#p2t2 0-100 1-120 2-15
#p1t1_wn 0-100 1-120 2-4
#p1t2_wn 0-100 1-120 2-4
#P5T1_TopCut 0-100 1-120 2-4

bpy.context.object.scale[0] = 100
bpy.context.object.scale[1] = 100
bpy.context.object.scale[2] = 17 #10 tk for original P5T1
ob.select_set( state = True, view_layer = bpy.context.view_layer )
bpy.context.view_layer.objects.active = ob
bpy.ops.object.modifier_add(type='BOOLEAN')
bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
bpy.context.object.modifiers["Boolean"].object = cube
bpy.context.object.modifiers["Boolean"].double_threshold = 1e-07
bpy.ops.object.modifier_apply({"object": ob}, modifier="Boolean")
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = cube
bpy.context.active_object.select_set(True)
bpy.ops.object.delete()
bpy.context.view_layer.objects.active = ob
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_mode(type="FACE")
bpy.ops.mesh.separate(type='SELECTED')
for obj in bpy.context.selected_objects:
    obj.name = "outlet"
    obj.data.name = "outlet"


bpy.ops.object.mode_set(mode='OBJECT')
out = bpy.context.active_object
bpy.ops.object.select_all(action='DESELECT')

# Make Inlet
bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, location=(0, 0, 0))
cube= bpy.context.active_object
bpy.context.view_layer.objects.active = cube
bpy.context.object.scale[0] = 100
bpy.context.object.scale[1] = 10
bpy.context.object.scale[2] = 10
bpy.context.object.rotation_euler[0] = 1
# 0.485128

bpy.context.object.location[2] = 59.5 #52
#p1t1 2-63
#p1t2 2-64
#p2t1 2-64
#p2t2 2-70
#p1t1_wn 2-83
#p1t2_wn 2-83
#P5T1_TopCut 2-52

bpy.context.view_layer.objects.active = ob
bpy.ops.object.modifier_add(type='BOOLEAN')
bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
bpy.context.object.modifiers["Boolean"].object = cube
bpy.context.object.modifiers["Boolean"].double_threshold = 1e-07
bpy.ops.object.modifier_apply({"object": ob}, modifier="Boolean")
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = cube
bpy.context.active_object.select_set(True)
bpy.ops.object.delete()
bpy.context.view_layer.objects.active = ob
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_mode(type="FACE")
bpy.ops.mesh.separate(type='SELECTED')
for obj in bpy.context.selected_objects:
    obj.name = "inlet"
    obj.data.name = "inlet"


bpy.ops.object.mode_set(mode='OBJECT')
inl = bpy.context.active_object
bpy.ops.object.select_all(action='DESELECT')


# Export as STL
path2 = os.path.join(path0, "constant/triSurface/")
bpy.ops.export_mesh.stl(filepath=path2, check_existing=True, filter_glob='*.stl', use_selection=False, global_scale=1.0, use_scene_unit=False, ascii=True, use_mesh_modifiers=True, batch_mode='OBJECT', axis_forward='Y', axis_up='Z')

#bpy.ops.export_mesh.stl(filepath="/home/uday/Desktop/msc_ortho/geo_files/cfd_models/w⁄o_nozzle/p5t1/", check_existing=True, filter_glob='*.stl', use_selection=False, global_scale=1.0, use_scene_unit=False, ascii=True, use_mesh_modifiers=True, batch_mode='OBJECT', axis_forward='Y', axis_up='Z')

# Export IMAGE
# create color
mat = bpy.data.materials.new('Material1')
mat.diffuse_color = (0.8, 0.00269661, 0.00091005, 1)
mat1 = bpy.data.materials.new('Material2')
mat1.diffuse_color = (0.0103095, 0.8, 0.0170713, 1)
# get the object
obj = bpy.data.objects['wall']
# get the material
mat = bpy.data.materials['Material1']
mat.use_nodes = True
bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[1].default_value = 5.3
# assign material to object
obj.data.materials.append(mat)
bpy.ops.object.select_all(action='DESELECT')
obj1 = bpy.data.objects['inlet']
mat1 = bpy.data.materials['Material2']
obj1.data.materials.append(mat1)
mat1.use_nodes = True
bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[1].default_value = 5.3
bpy.ops.object.select_all(action='DESELECT')
obj2 = bpy.data.objects['outlet']
mat1 = bpy.data.materials['Material2']
mat1.use_nodes = True
obj2.data.materials.append(mat1)
bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[1].default_value = 5.3
bpy.ops.object.select_all(action='DESELECT')
#bpy.context.scene.view_settings.view_transform = 'Standard'
#bpy.context.scene.render.film_transparent = True
# create light
light_data = bpy.data.lights.new(name="light-data1", type='POINT')
light_data.energy = 5000
# Create new object, pass the light data
light1 = bpy.data.objects.new(name="light1", object_data=light_data)
# Link object to collection in context
bpy.context.collection.objects.link(light1)
light1.location = (abs(minx)+abs(maxx), abs(miny)+abs(maxy), abs(minz)+abs(maxz))
# create the camera
scn = bpy.context.scene
cam_ob1 = bpy.data.cameras.new("camera1")
cam_ob1.lens = 45
cam1 = bpy.data.objects.new("camera1", cam_ob1)
cam1.location = ((abs(minx)+abs(maxx))*2.15, -(abs(minz)+abs(maxz))/2, -(abs(miny)+abs(maxy))/2)
cam1.rotation_euler = (math.radians(0), math.radians(0), math.radians(90))
scn.collection.objects.link(cam1)
bpy.context.scene.camera = bpy.data.objects['camera1']
bpy.context.scene.cycles.samples = 1
scn.render.use_border = True
bpy.context.scene.render.resolution_x = 600
bpy.context.scene.render.resolution_y = 600
bpy.context.scene.render.resolution_percentage = 100
bpy.context.scene.render.image_settings.file_format='JPEG'

# Point camera at the object
constraint = cam1.constraints.new(type='TRACK_TO')
constraint.target = obj
constraint.track_axis = 'TRACK_NEGATIVE_Z'
constraint.up_axis = 'UP_Y'

path3 = os.path.join(path0,"blendout.jpg")
bpy.context.scene.render.filepath = path3
#bpy.context.scene.render.filepath = "/home/uday/Desktop/msc_ortho/geo_files/cfd_models/w⁄o_nozzle/p5t1/blendout.jpg"

bpy.context.scene.view_settings.exposure = 2.25
bpy.ops.render.render('INVOKE_DEFAULT', write_still=True)

# Quit Blender
print("Finished running preprocessing of model in Blenderv2.82")
print("Please check output image blendout.jpg")
print("Time taken for preprocessing: ",time.time()-start_time)
bpy.ops.wm.quit_blender()


#Inlet part 1 centroid: 45.758636 4.933601 68.216125
#Inlet part 2 centroid: 32.608170 5.303648 67.978516