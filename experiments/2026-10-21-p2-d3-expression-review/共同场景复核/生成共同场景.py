import bpy,math,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'布局复核'
def mat(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);return m
def box(n,x,y,z,dx,dy,dz,m,b=.02):
 bpy.ops.mesh.primitive_cube_add(size=1,location=(x,y,z));o=bpy.context.object;o.name=n;o.dimensions=(dx,dy,dz);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.clear();o.data.materials.append(m)
 if b:q=o.modifiers.new('soft edge','BEVEL');q.width=b;q.segments=3;o.modifiers.new('normals','WEIGHTED_NORMAL')
 return o
def cyl(n,x,y,z,r,h,m):
 bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=r,depth=h,location=(x,y,z));o=bpy.context.object;o.name=n;o.data.materials.append(m);return o
def remove(prefixes):
 for o in list(bpy.data.objects):
  if any(o.name==p or o.name.startswith(p+'.') or o.name.startswith(p+'-') for p in prefixes):bpy.data.objects.remove(o,do_unlink=True)
def chair(n,x,y,angle,cloth,wood,w=.52,d=.55):
 origin=Vector((x,y,0));parts=[box(n+' seat',x,y,.45,w,d,.14,cloth,.06),box(n+' back',x,y-d/2+.05,.72,w,.10,.43,cloth,.05)]
 for xx in [-w/2+.065,w/2-.065]:
  for yy in [-d/2+.065,d/2-.065]:parts.append(box(n+' leg',x+xx,y+yy,.2,.045,.045,.40,wood,.008))
 for o in parts:
  v=o.location-origin;t=math.radians(angle);o.location.x=x+v.x*math.cos(t)-v.y*math.sin(t);o.location.y=y+v.x*math.sin(t)+v.y*math.cos(t);o.rotation_euler.z=t
 return parts
def camera(n,x,y,tx,ty,lens,z=1.48,targetz=1.1):
 c=bpy.data.objects[n];c.location=(x*S,-y*S,z);c.rotation_euler=(Vector((tx*S,-ty*S,z))-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=lens;c.data.shift_x=0;c.data.shift_y=(targetz-z)*lens/(36*math.hypot((tx-x)*S,(ty-y)*S));return c
def scene_export(c):
 sc=bpy.context.scene;sc.render.resolution_x=1600;sc.render.resolution_y=1100;sc.render.resolution_percentage=100
 out=ROOT/c;out.mkdir(exist_ok=True)
 bpy.context.view_layer.update()
 data={'case':c,'version':'shared-v1','source':'../'+c+'/输入/整理平面.png','scale_m_per_pixel':S,'source_scale_status':'历史比例/设计假设，非本轮实测','objects':[],'cameras':{},'same_scene_proof':{}}
 for o in sc.objects:
  if o.type!='MESH':continue
  vs=[o.matrix_world@v.co for v in o.data.vertices]
  data['objects'].append({'name':o.name,'location_m':list(o.location),'rotation_rad':list(o.rotation_euler),'dimensions_m':list(o.dimensions),'xy':[[v.x/S,-v.y/S] for v in vs],'z_range':[min(v.z for v in vs),max(v.z for v in vs)]})
 digest=hashlib.sha256(json.dumps(data['objects'],sort_keys=True).encode()).hexdigest()
 for n in ['客厅-M01','客厅-M02']:
  cam=bpy.data.objects[n];sc.camera=cam;data['cameras'][n]={'location_m':list(cam.location),'rotation_rad':list(cam.rotation_euler),'lens_mm':cam.data.lens,'shift':[cam.data.shift_x,cam.data.shift_y]};data['same_scene_proof'][n]=digest
  sc.render.filepath=str(out/(n+'-约束图-v1.png'));bpy.ops.render.render(write_still=True)
 (out/'场景配置.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
 bpy.ops.wm.save_as_mainfile(filepath=str(out/'共用场景-v1.blend'))
for c in ['P2','D3']:
 bpy.ops.wm.open_mainfile(filepath=str(OLD/'模型表达试验'/f'{c}-改进模型.blend'))
 S=18/1368 if c=='P2' else 19/1600
 cloth=mat('neutral upholstery new',(.64,.64,.60));wood=mat('neutral light timber',(.52,.48,.40));top=mat('pale top',(.86,.84,.79));dark=mat('dark recess',(.16,.17,.16));ceiling=mat('ceiling detail',(.8,.8,.78))
 if c=='P2':
  remove(['west-coffee','east-coffee','sofa-north-side-table','southeast-ottoman','west-ottoman','northeast-armchair','southwest-armchair'])
  # Two serving tables and an independent north-end side table. No sofa intersection.
  for n,x,y,r,h in [('east coffee',356,1238,.40,.40),('west coffee',116,1240,.28,.43),('independent side table',229,1080,.23,.51)]:
   cyl(n+' top',x*S,-y*S,h,r,.045,top);cyl(n+' pedestal',x*S,-y*S,h/2,.095,h-.045,wood)
  chair('east lounge chair',408*S,-1140*S,135,cloth,wood,.62,.65)
  chair('west lounge chair',126*S,-1346*S,-45,cloth,wood,.55,.58)
  camera('客厅-M01',396,990,240,1230,23,targetz=1.03)
  camera('客厅-M02',87,1010,303,1230,23,targetz=1.03)
  # Already selected ceiling design: perimeter lowered 120mm, 300mm strips, not decorative islands.
  for n,a,b,d,e in [('west',57,1090,80,1389),('east',437,1090,460,1389),('south',80,1366,437,1389),('north',80,1090,437,1113)]:
   box('ceiling band '+n,(a+d)*S/2,-(b+e)*S/2,2.74,(d-a)*S,(e-b)*S,.12,ceiling,0)
  for x in [68,449]:
   for y in [1175,1310]:cyl('recessed downlight',x*S,-y*S,2.675,.035,.01,dark)
  for x in [127,351]:cyl('flat white ceiling light',x*S,-1235*S,2.76,.21,.07,top)
 else:
  remove(['dining-east','dining-southwest','armchair'])
  # Four chairs around 1.1875m table, selected here for normal four-person dining.
  for n,x,y,a in [('north',888,706,180),('east',957,775,90),('south',888,844,0),('west',819,775,-90)]:chair('dining chair '+n,x*S,-y*S,a,cloth,wood,.44,.48)
  chair('lounge chair',811*S,-950*S,145,cloth,wood,.68,.73)
  # Maintain existing tapered corner-sofa footprint, add cushion subdivisions and rounded usable edges.
  for n in ['sofa','sofa-back']:
   o=bpy.data.objects[n];o.data.materials.clear();o.data.materials.append(cloth);q=o.modifiers.new('soft upholstered edge','BEVEL');q.width=.055;q.segments=4;o.modifiers.new('weighted normals','WEIGHTED_NORMAL')
  for j in range(3):box('sofa seat cushion',1014*S,-(992+j*71)*S,.50,.82,.79,.14,cloth,.06)
  # Make a real opening in worktop and base so the existing under-mount sink is not occluded.
  cutter=box('temporary sink opening',919*S,-423*S,.87,.54,.34,.30,dark,0)
  for name in ['kitchen-north-counter worktop','kitchen-north-counter']:
   o=bpy.data.objects[name];bpy.context.view_layer.objects.active=o;q=o.modifiers.new('sink opening','BOOLEAN');q.operation='DIFFERENCE';q.object=cutter;bpy.ops.object.modifier_apply(modifier=q.name)
  bpy.data.objects.remove(cutter,do_unlink=True)
  camera('客厅-M01',649,1330,893,1060,26,targetz=1.1)
  camera('客厅-M02',1010,856,780,1120,25,targetz=1.1)
  for n,a,b,d,e in [('west',588,922,613,1390),('east',1088,922,1113,1390),('north',613,922,1088,947)]:box('ceiling band '+n,(a+d)*S/2,-(b+e)*S/2,2.74,(d-a)*S,(e-b)*S,.12,ceiling,0)
  for x in [600,1100]:
   for y in [1030,1190]:cyl('recessed downlight',x*S,-y*S,2.675,.035,.01,dark)
  for n,x,y,z,r in [('living pendant',874,1076,2.28,.27),('dining pendant',888,775,2.05,.20)]:
   cyl(n+' shade',x*S,-y*S,z,r,.17,top);cyl(n+' cable',x*S,-y*S,(2.8+z)/2,.006,2.8-z,wood)
 scene_export(c)
