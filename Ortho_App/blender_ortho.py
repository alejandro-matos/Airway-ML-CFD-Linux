# Msc Ortho CFD Blender 2.82 script File
# Computational Fluid Dynamics Lab
# Author = Uday Tummala
# Dr. Carlos F. Lange
# Department of Mechanical Engineering
# University of Alberta
#
# Date 2025-09-27
# cmd = blender --background --python blender_ortho.py

import bpy
import math
import mathutils
import time
import os
import bmesh

start_time = time.time()

# delete all existing objects
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# import stl file
def _expand_path(raw_path):
    return os.path.expandvars(os.path.expanduser(raw_path.strip()))

file0 = open("sdir.txt", "r")
#file0 = open("/home/uday/Desktop/msc_ortho/Automation/Ortho_App_0.2/sdir.txt", "r")
path0 = _expand_path(file0.readline())
file0.close()
file = open("geo_in.txt", "r")
#file = open("/home/uday/Desktop/msc_ortho/Automation/Ortho_App_0.2/geo_in.txt", "r")
path1 = _expand_path(file.readline())
bpy.ops.import_mesh.stl(filepath= path1)

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


# ROTATION OF MODEL
bpy.context.object.rotation_euler[1] = 0
bpy.context.object.rotation_euler[2] = 0

# Removing artifacts and grab the bounds
# Move to +ve co-ordinates
minx =  min(xValues)
maxx =  max(xValues)
miny =  min(yValues)
maxy =  max(yValues)
minz =  min(zValues)
maxz =  max(zValues)
bpy.context.object.location[0] = abs(minx)
bpy.context.object.location[1] = abs(miny)
bpy.context.object.location[2] = abs(minz)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.bisect(plane_co=(0, 0, 0.5), plane_no=(0, 0, 1), use_fill=True, clear_inner=False, xstart=1000, xend=0, ystart=0, yend=0)
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

# Make preliminary Inlet
bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, location=(0, 0, 0))
cube= bpy.context.active_object
bpy.context.view_layer.objects.active = cube
bpy.context.object.scale[0] = 100
bpy.context.object.scale[1] = 3
bpy.context.object.scale[2] = 120
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
    obj.name = "ini"
    obj.data.name = "ini"


bpy.ops.object.mode_set(mode='OBJECT')
inny = bpy.context.active_object
bpy.ops.object.select_all(action='DESELECT')
inny = bpy.context.view_layer.objects.get('ini')
if inny:
    inny.select_set(True)


bpy.context.view_layer.objects.active = inny
filepath = os.path.join(path0, "system/face_centers_i.txt")
#filepath = bpy.path.abspath("/home/uday/Desktop/msc_ortho/Automation/Ortho_App_0.2/face_centers_i.txt")
bm = bmesh.new()
# Open file for writing
with open(filepath, 'w') as file:
    for o in bpy.context.selected_objects:
        bm.clear()
        bm.from_mesh(o.data)
        file.write(f"Object: {o.name}\n")
        for f in bm.faces:
            p = o.matrix_world @ f.calc_center_median()
            file.write(f"({p.x * 0.001} {p.y * 0.001} {p.z * 0.001})\n")
            op_z0 = (p.z - 20) * 0.001



bm.free()
#

bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
bpy.ops.import_mesh.stl(filepath= path1)

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


# ROTATION OF MODEL
bpy.context.object.rotation_euler[1] = 0
bpy.context.object.rotation_euler[2] = 0

# Removing artifacts and grab the bounds
# Move to +ve co-ordinates
minx =  min(xValues)
maxx =  max(xValues)
miny =  min(yValues)
maxy =  max(yValues)
minz =  min(zValues)
maxz =  max(zValues)
bpy.context.object.location[0] = abs(minx)
bpy.context.object.location[1] = abs(miny)
bpy.context.object.location[2] = abs(minz)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.bisect(plane_co=(0, 0, 0.5), plane_no=(0, 0, 1), use_fill=True, clear_inner=False, xstart=1000, xend=0, ystart=0, yend=0)
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

# Make Inlet
bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, location=(0, 0, 0))
cube= bpy.context.active_object
bpy.context.view_layer.objects.active = cube
bpy.context.object.scale[0] = 100
bpy.context.object.scale[1] = 8
bpy.context.object.scale[2] = 10
bpy.context.object.rotation_euler[0] = 1.021018 #31.5 deg
bpy.context.object.location[2] = p.z-10
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
#

# Make Outlet
bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, location=(0, 0, 0))
cube = bpy.context.active_object
bpy.context.view_layer.objects.active = cube
bpy.context.object.scale[0] = 100
bpy.context.object.scale[1] = 120
bpy.context.object.scale[2] = 11
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
out = bpy.context.view_layer.objects.get('outlet')
if out:
    out.select_set(True)



bpy.context.view_layer.objects.active = out
filepath = os.path.join(path0, "system/face_centers.txt")
#filepath = bpy.path.abspath("/home/uday/Desktop/msc_ortho/Automation/Ortho_App_0.2/face_centers.txt")
bm = bmesh.new()
# Open file for writing
with open(filepath, 'w') as file:
    points = []
    normals = []
    for o in bpy.context.selected_objects:
        bm.clear()
        bm.from_mesh(o.data)
        normal_matrix = o.matrix_world.to_3x3()
        for f in bm.faces:
            p = o.matrix_world @ f.calc_center_median()
            points.append((p.x * 0.001, p.y * 0.001, (p.z + 5) * 0.001))
            n = normal_matrix @ f.normal
            if n.length:
                n.normalize()
            normals.append((n.x, n.y, n.z))
    if points:
        avg_x = sum(p[0] for p in points) / len(points)
        avg_y = sum(p[1] for p in points) / len(points)
        avg_z = sum(p[2] for p in points) / len(points)
        avg_nx = sum(n[0] for n in normals) / len(normals) if normals else 0.0
        avg_ny = sum(n[1] for n in normals) / len(normals) if normals else 0.0
        avg_nz = sum(n[2] for n in normals) / len(normals) if normals else 0.0
        n_len = (avg_nx ** 2 + avg_ny ** 2 + avg_nz ** 2) ** 0.5
        if n_len:
            # Nudge inward along the negative average normal.
            offset = 0.002
            avg_x -= (avg_nx / n_len) * offset
            avg_y -= (avg_ny / n_len) * offset
            avg_z -= (avg_nz / n_len) * offset
        file.write(f"({avg_x:.6f} {avg_y:.6f} {avg_z:.6f})\n")




bm.free()
#

# Export bounding co-ordinates
obj = bpy.context.view_layer.objects.get('wall')

# Get the world-space bounding box corners
bbox_corners = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]

# Calculate min and max values
min_x = min(corner.x for corner in bbox_corners)
max_x = max(corner.x for corner in bbox_corners)
min_y = min(corner.y for corner in bbox_corners)
max_y = max(corner.y for corner in bbox_corners)
min_z = min(corner.z for corner in bbox_corners)
max_z = max(corner.z for corner in bbox_corners)

pad = 1

bound_min_x = min_x - pad
bound_min_y = min_y - pad
bound_min_z = min_z - pad

bound_max_x = max_x + pad
bound_max_y = max_y + pad
bound_max_z = max_z + pad

bound_min_xs1 = (min_x + 10.0) * 0.001
bound_min_ys1 = (min_y - pad) * 0.001
bound_min_zs1 = (min_z - pad) * 0.001

bound_max_xs1 = (max_x - 10.0) * 0.001
bound_max_ys1 = (max_y + pad) * 0.001
bound_max_zs1 = (max_z + pad) * 0.001

n_ip = 5
ip_y0 = (p.y - 13) * 0.001
ip_y4 = (min_y + 2) * 0.001
ip_y1 = ip_y0 - ((ip_y0 - ip_y4) * 1 / (n_ip-1))
ip_y2 = ip_y0 - ((ip_y0 - ip_y4) * 2 / (n_ip-1))
ip_y3 = ip_y0 - ((ip_y0 - ip_y4) * 3 / (n_ip-1))
n_op = 6
op_z5 = (min_z + 2) * 0.001
op_z1 = op_z0 - ((op_z0 - op_z5) * 1 / (n_op-1))
op_z2 = op_z0 - ((op_z0 - op_z5) * 2 / (n_op-1))
op_z3 = op_z0 - ((op_z0 - op_z5) * 3 / (n_op-1))
op_z4 = op_z0 - ((op_z0 - op_z5) * 4 / (n_op-1))

# Calculate number of cells along each axis (rounded to integer)
nx = int(round((bound_max_x - bound_min_x)*1.000))
ny = int(round((bound_max_y - bound_min_y)*1.000))
nz = int(round((bound_max_z - bound_min_z)*1.000))

# Generate the output string in OpenFOAM dictionary format
output = (
    f"BOUND_MIN_X {bound_min_x:.3f};\n"
    f"BOUND_MIN_Y {bound_min_y:.3f};\n"
    f"BOUND_MIN_Z {bound_min_z:.3f};\n"
    f"BOUND_MAX_X {bound_max_x:.3f};\n"
    f"BOUND_MAX_Y {bound_max_y:.3f};\n"
    f"BOUND_MAX_Z {bound_max_z:.3f};\n"
    f"BOUND_MIN_X1 {bound_min_xs1:.3f};\n"
    f"BOUND_MIN_Y1 {bound_min_ys1:.3f};\n"
    f"BOUND_MIN_Z1 {bound_min_zs1:.3f};\n"
    f"BOUND_MAX_X1 {bound_max_xs1:.3f};\n"
    f"BOUND_MAX_Y1 {bound_max_ys1:.3f};\n"
    f"BOUND_MAX_Z1 {bound_max_zs1:.3f};\n"
    f"OUT_PLANE_Z0 {op_z0:.3f};\n"
    f"OUT_PLANE_Z1 {op_z1:.3f};\n"
    f"OUT_PLANE_Z2 {op_z2:.3f};\n"
    f"OUT_PLANE_Z3 {op_z3:.3f};\n"
    f"OUT_PLANE_Z4 {op_z4:.3f};\n"
    f"OUT_PLANE_Z5 {op_z5:.3f};\n"
    f"IN_PLANE_Y0 {ip_y0:.3f};\n"
    f"IN_PLANE_Y1 {ip_y1:.3f};\n"
    f"IN_PLANE_Y2 {ip_y2:.3f};\n"
    f"IN_PLANE_Y3 {ip_y3:.3f};\n"
    f"IN_PLANE_Y4 {ip_y4:.3f};\n"
    f"NX {nx};\n"
    f"NY {ny};\n"
    f"NZ {nz};\n"
)

# Choose the output path
output_path = os.path.join(path0, "system/bb_min_max.txt")
#output_path = bpy.path.abspath("/home/uday/Desktop/msc_ortho/Automation/Ortho_App_0.2/bb_min_max.txt")

# Write to file
with open(output_path, "w") as file:
    file.write(output)


#
# Export as STL
path2 = os.path.join(path0, "constant/triSurface/")
bpy.ops.export_mesh.stl(filepath=path2, check_existing=True, filter_glob='*.stl', use_selection=False, global_scale=1.0, use_scene_unit=False, ascii=True, use_mesh_modifiers=True, batch_mode='OBJECT', axis_forward='Y', axis_up='Z')

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
bpy.context.scene.view_settings.exposure = 2.25
path3 = os.path.join(path0,"blendout.jpg")
bpy.context.scene.render.filepath = path3
bpy.ops.render.render('INVOKE_DEFAULT', write_still=True)

# Quit Blender
print("Finished running preprocessing of model in Blenderv2.82")
print("Please check output image blendout.jpg")
print("Time taken for preprocessing: ",time.time()-start_time)
bpy.ops.wm.quit_blender()
