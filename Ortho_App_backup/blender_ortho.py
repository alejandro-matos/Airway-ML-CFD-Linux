# Msc Ortho CFD Blender 2.82 script File
# Computational Fluid Dynamics Lab
# Author = Uday Tummala
# Dr. Carlos F. Lange
# Department of Mechanical Engineering
# University of Alberta
#
# Date 2023-12-27
# cmd = blender --background --python blender_ortho.py

import bpy  # Blender Python API
import math
import mathutils
import time
import os

start_time = time.time()

# delete all existing objects
print("Deleting existing objects...")
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
print("Objects deleted.")

# import stl file
file0 = open("sdir.txt", "r")
path0 = file0.readline()
file0.close()
print(f"Read directory: {path0}")

path00 = os.path.join(path0, "geo_in.txt")
file = open(path00, "r")
path1 = file.readline()
file.close()
print(f"Reading STL file from: {path1}")

bpy.ops.import_mesh.stl(filepath= path1)
print("STL file imported successfully.")

# Move model to origin
bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN', center='MEDIAN')
active_obj = bpy.context.active_object
print(f"Active object: {active_obj.name}")

# Check if object has vertices
if active_obj is None or not hasattr(active_obj.data, 'vertices'):
    print("Error: No active object or no vertices found.")
    bpy.ops.wm.quit_blender()

active_object_verts = active_obj.data.vertices
xValues = []
yValues = []
zValues = []

# Manual alignment of geometry
bpy.context.object.rotation_euler = (0,0,-0.065)
print("Geometry successfully aligned.")

# Extracting all vertices coordinates
for vert in active_obj.data.vertices:
    xValues.append(vert.co.x)
    yValues.append(vert.co.y)
    zValues.append(vert.co.z)
print("Vertex extraction completed.")

# Removing floating objects/artifacts
minx =  min(xValues)
maxx =  max(xValues)
miny =  min(yValues)
maxy =  max(yValues)
minz =  min(zValues)
maxz =  max(zValues)
print(f"Bounding box values: minX={minx}, maxX={maxx}, minY={miny}, maxY={maxy}, minZ={minz}, maxZ={maxz}")

# Move to +ve co-ordinates
print("Moving object to positive coordinates...")

if bpy.context.object:
    print(f"Before move: Location = {bpy.context.object.location}")
    bpy.context.object.location[0] = abs(minx)
    bpy.context.object.location[1] = abs(miny)
    bpy.context.object.location[2] = abs(minz)
    print(f"After move: Location = {bpy.context.object.location}")
else:
    print("Error: No active object found when trying to move.")

# Switch to Edit Mode
print("Switching to EDIT mode...")
bpy.ops.object.mode_set(mode='EDIT')

# Select all mesh
print("Selecting all mesh elements...")
bpy.ops.mesh.select_all(action='SELECT')

# Perform bisect operation
print("Performing mesh bisect operation...")
bpy.ops.mesh.bisect(plane_co=(0, 0, 2), plane_no=(0, 0, 1), use_fill=True, clear_inner=False, xstart=1000, xend=0, ystart=0, yend=0)

# Check if selection exists before separating
print("Checking if mesh selection exists before separating...")
selected_verts = [v for v in bpy.context.object.data.vertices if v.select]
if len(selected_verts) == 0:
    print("Warning: No selected vertices before separate operation.")

# Separate the selected region
print("Separating selected region...")
bpy.ops.mesh.loop_to_region(select_bigger=True)
bpy.ops.mesh.separate(type='SELECTED')

# Switch back to Object Mode
print("Switching back to OBJECT mode...")
bpy.ops.object.mode_set(mode='OBJECT')

# Deselect all objects
print("Deselecting all objects...")
bpy.ops.object.select_all(action='DESELECT')

# Set model reference
model = bpy.context.active_object

if model:
    print(f"Active object after separate: {model.name}")
    bpy.context.active_object.select_set(True)
    print(f"Deleting object: {model.name}")
    bpy.ops.object.delete()
else:
    print("Warning: No active object found before deletion.")


# Make Outlet face
print("\n--- Creating Outlet Face ---")

# Select all objects
bpy.ops.object.select_all(action='SELECT')
selected_objects = bpy.context.selected_objects

if selected_objects:
    print(f"Selected {len(selected_objects)} objects. Renaming to 'wall'.")
    for obj in selected_objects:
        obj.name = "wall"
        obj.data.name = "wall"
else:
    print("Warning: No objects selected when trying to rename to 'wall'.")

# Deselect all
print("Deselecting all objects...")
bpy.ops.object.select_all(action='DESELECT')

# Add a cube for Boolean operation
print("Adding a cube for Boolean difference...")
bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, location=(0, 0, 0))

cube = bpy.context.active_object
if cube:
    print(f"Cube created: {cube.name}")
else:
    print("Error: Cube was not created.")

# Scale cube
bpy.context.view_layer.objects.active = cube
bpy.context.object.scale[0] = 100
bpy.context.object.scale[1] = 100
bpy.context.object.scale[2] = 10
print(f"Cube scaled to: {bpy.context.object.scale[:]}")

# Retrieve the "wall" object
if "wall" in bpy.data.objects:
    ob = bpy.data.objects["wall"]
    print(f"'wall' object found: {ob.name}")
else:
    print("Error: 'wall' object not found in bpy.data.objects.")

# Apply Boolean modifier
print("Applying Boolean modifier...")
ob.select_set(state=True, view_layer=bpy.context.view_layer)
bpy.context.view_layer.objects.active = ob
bpy.ops.object.modifier_add(type='BOOLEAN')
bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
bpy.context.object.modifiers["Boolean"].object = cube

# Apply the Boolean modifier
try:
    bpy.ops.object.modifier_apply({"object": ob}, modifier="Boolean")
    print("Boolean modifier applied successfully.")
except RuntimeError as e:
    print(f"Error applying Boolean modifier: {e}")

# Delete the cube
print("Deleting the Boolean cube...")
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = cube
bpy.context.active_object.select_set(True)
bpy.ops.object.delete()
print("Cube deleted.")

# Switch to Edit Mode
print("Switching to Edit Mode for separation...")
bpy.context.view_layer.objects.active = ob
bpy.ops.object.mode_set(mode='EDIT')

# Check if mesh is selectable before separating
bpy.ops.mesh.select_mode(type="FACE")
print("Separating selected faces...")
bpy.ops.mesh.separate(type='SELECTED')

# Rename separated object as 'outlet'
bpy.ops.object.mode_set(mode='OBJECT')
selected_objects = bpy.context.selected_objects
if selected_objects:
    print(f"Separated {len(selected_objects)} objects. Renaming to 'outlet'.")
    for obj in selected_objects:
        obj.name = "outlet"
        obj.data.name = "outlet"
else:
    print("Warning: No objects selected after separation.")

# Deselect all objects
bpy.ops.object.select_all(action='DESELECT')
print("--- Outlet Face Creation Complete ---\n")


# Make Inlet Face
print("\n--- Creating Inlet Face ---")

# Create cube for Boolean operation
print("Adding a cube for Boolean difference...")
bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, location=(0, 0, 0))

cube = bpy.context.active_object
if cube:
    print(f"Cube created: {cube.name}")
else:
    print("Error: Cube was not created.")

# Scale cube
bpy.context.view_layer.objects.active = cube
bpy.context.object.scale[0] = 100
bpy.context.object.scale[1] = 10
bpy.context.object.scale[2] = 10
bpy.context.object.rotation_euler[0] = 1
bpy.context.object.location[2] = 62
print(f"Cube scaled to: {bpy.context.object.scale[:]}, rotated, and moved.")

# Retrieve the "wall" object
if "wall" in bpy.data.objects:
    ob = bpy.data.objects["wall"]
    print(f"'wall' object found: {ob.name}")
else:
    print("Error: 'wall' object not found in bpy.data.objects.")

# Apply Boolean modifier
print("Applying Boolean modifier to 'wall' with cube...")
ob.select_set(state=True, view_layer=bpy.context.view_layer)
bpy.context.view_layer.objects.active = ob
bpy.ops.object.modifier_add(type='BOOLEAN')
bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
bpy.context.object.modifiers["Boolean"].object = cube

# Apply the Boolean modifier
try:
    bpy.ops.object.modifier_apply({"object": ob}, modifier="Boolean")
    print("Boolean modifier applied successfully.")
except RuntimeError as e:
    print(f"Error applying Boolean modifier: {e}")

# Delete the cube
print("Deleting the Boolean cube...")
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = cube
bpy.context.active_object.select_set(True)
bpy.ops.object.delete()
print("Cube deleted.")

# Switch to Edit Mode
print("Switching to Edit Mode for separation...")
bpy.context.view_layer.objects.active = ob
bpy.ops.object.mode_set(mode='EDIT')

# Check if mesh is selectable before separating
bpy.ops.mesh.select_mode(type="FACE")
print("Separating selected faces...")
bpy.ops.mesh.separate(type='SELECTED')

# Rename separated object as 'inlet'
bpy.ops.object.mode_set(mode='OBJECT')
selected_objects = bpy.context.selected_objects
if selected_objects:
    print(f"Separated {len(selected_objects)} objects. Renaming to 'inlet'.")
    for obj in selected_objects:
        obj.name = "inlet"
        obj.data.name = "inlet"
else:
    print("Warning: No objects selected after separation.")

# Deselect all objects
bpy.ops.object.select_all(action='DESELECT')
print("--- Inlet Face Creation Complete ---\n")

# Ensuring STL export folder exists
path2 = os.path.join(path0, "constant/triSurface/")
os.makedirs(path2, exist_ok=True)
print(f"STL export directory: {path2}")

# Export as STL
print("Exporting STL file...")
bpy.ops.export_mesh.stl(filepath=path2, check_existing=True, filter_glob='*.stl', 
                        use_selection=False, global_scale=1.0, use_scene_unit=False, 
                        ascii=True, use_mesh_modifiers=True, batch_mode='OBJECT', 
                        axis_forward='Y', axis_up='Z')
print("STL export completed.")

##################################################################################
# Export IMAGE
# create color
mat = bpy.data.materials.new('Material1')
mat.diffuse_color = (0.8, 0.00269661, 0.00091005, 1)
mat1 = bpy.data.materials.new('Material2')
mat1.diffuse_color = (0.0103095, 0.8, 0.0170713, 1)
##################################################################################
# get the object
obj = bpy.data.objects['wall']
##################################################################################
# get the material
mat = bpy.data.materials['Material1'] # name Material1 as mat
mat.use_nodes = True
bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[1].default_value = 5.3
##################################################################################
# assign material to object
obj.data.materials.append(mat) # assign mat as material to our model obj
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
##################################################################################
# create light
light_data = bpy.data.lights.new(name="light-data1", type='POINT')
light_data.energy = 5000
##################################################################################
# Create new object, pass the light data
light1 = bpy.data.objects.new(name="light1", object_data=light_data)
##################################################################################
# Link object to collection in context
bpy.context.collection.objects.link(light1)
light1.location = (abs(minx)+abs(maxx), abs(miny)+abs(maxy), abs(minz)+abs(maxz))
##################################################################################
# create the camera
scn = bpy.context.scene
cam_ob1 = bpy.data.cameras.new("camera1")
cam_ob1.lens = 45
cam1 = bpy.data.objects.new("camera1", cam_ob1)
cam1.location = ((abs(minx)+abs(maxx))*2.15, -(abs(minz)+abs(maxz))/2, -(abs(miny)+abs(maxy))/2)
cam1.rotation_euler = (math.radians(0), math.radians(125), math.radians(320))
scn.collection.objects.link(cam1)
bpy.context.scene.camera = bpy.data.objects['camera1']
bpy.context.scene.cycles.samples = 1
scn.render.use_border = True
bpy.context.scene.render.resolution_x = 600
bpy.context.scene.render.resolution_y = 600
bpy.context.scene.render.resolution_percentage = 100
bpy.context.scene.render.image_settings.file_format='JPEG'
path3 = os.path.join(path0,"blendout.jpg")
bpy.context.scene.render.filepath = path3
bpy.context.scene.view_settings.exposure = 2.25
bpy.ops.render.render('INVOKE_DEFAULT', write_still=True)
##################################################################################
# Quit Blender
print("Finished running preprocessing of model in Blenderv2.82")
print("Please check output image blendout.jpg")
print("Time taken for preprocessing: ",time.time()-start_time)
bpy.ops.wm.quit_blender()
