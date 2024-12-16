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
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
bpy.ops.import_mesh.stl(filepath = "/home/uday/Desktop/msc_ortho/geo_files/P1T1.stl")

# Align xyz
bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN', center='MEDIAN')
active_obj = bpy.context.active_object
active_object_verts = active_obj.data.vertices
xValues = []
yValues = []
zValues = []
d1 = []
angy1 = []
angz1 = []

def my_function():
   for v in active_object_verts:
      if v.select == True:
         bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
         xValues.append(v.co[0])
         yValues.append(v.co[1])
         zValues.append(v.co[2])

for z in range(-4, 4, 1):
   for y in range(-4, 4, 1):
      xValues.clear()
      yValues.clear()
      zValues.clear()
      bpy.context.object.rotation_euler = (0,math.radians(y),math.radians(z))
      my_function()
      minx =  min(xValues)
      maxx =  max(xValues)
      x1 = xValues.index(minx)
      x2 = xValues.index(maxx)
      miny = yValues[x1]
      maxy = yValues[x2]
      minz = zValues[x1]
      maxz = zValues[x2]
      d1.append(pow((pow((maxx-minx), 2) + pow((maxy-miny), 2) + pow((maxz-minz), 2)), 0.5))
      angy1.append(y)
      angz1.append(z)

mind1 = min(d1)
x3 = d1.index(mind1)
bpy.context.object.rotation_euler = (0,math.radians(angy1[x3]),math.radians(angz1[x3]))
