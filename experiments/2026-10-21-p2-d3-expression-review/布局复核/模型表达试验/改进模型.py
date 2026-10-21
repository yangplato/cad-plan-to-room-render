import bpy,math,json
from pathlib import Path
from mathutils import Vector
ROOT=Path('/Users/huaceyang/Documents/1.Projects/宜宾工作/04-AI数字转型和制度研究/AI制图部/04-多平面测试/20261021-v1.4.1跨户型复测/布局复核')
OUT=ROOT/'模型表达试验';LIB=Path('/Users/huaceyang/Documents/4.Archives/室内元素模型库');records=[]
def mat(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);return m
def box(n,x,y,z,dx,dy,dz,m,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=(x,y,z));o=bpy.context.object;o.name=n;o.dimensions=(dx,dy,dz);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if bevel:
  q=o.modifiers.new('soft edges','BEVEL');q.width=bevel;q.segments=4;o.modifiers.new('normals','WEIGHTED_NORMAL')
 return o
def remove(names):
 for n in names:
  o=bpy.data.objects.get(n)
  if o:bpy.data.objects.remove(o,do_unlink=True)
def asset(id,x,y,z,maxw,maxd,m):
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(LIB/'modules/kitchens/models'/f'{id}.glb'));objects=list(set(bpy.data.objects)-before);meshes=[o for o in objects if o.type=='MESH'];bpy.context.view_layer.update()
 points=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box];lo=Vector(tuple(min(p[i] for p in points) for i in range(3)));hi=Vector(tuple(max(p[i] for p in points) for i in range(3)));fac=min(maxw/(hi.x-lo.x),maxd/(hi.y-lo.y));center=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z))
 if 'sink_' in id:z-=(hi.z-lo.z)*fac
 for o in meshes:
  mw=o.matrix_world.copy();o.parent=None
  for v in o.data.vertices:v.co=(mw@v.co-center)*fac+Vector((x,y,z))
  o.matrix_world.identity();o.data.materials.clear();o.data.materials.append(m)
 records.append({'id':id,'uniform_scale':fac,'native_bbox':list(hi-lo),'target_xy':[x,y]})
def render(c,cam):
 s=bpy.context.scene;s.camera=bpy.data.objects[cam];s.render.resolution_x=1600;s.render.resolution_y=1100;s.render.resolution_percentage=100
 s.render.filepath=str(OUT/f'{c}-空间约束图.png');bpy.ops.render.render(write_still=True);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'{c}-改进模型.blend'))
# preserve original camera and all room geometry
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'P2/过程/核对简模.blend'))
S=18/1368;remove(['sofa-west','sofa-east','shared-back'])
cloth=mat('neutral upholstery',(.58,.57,.53));base=mat('base',(.34,.33,.30));leg=mat('legs',(.24,.25,.24))
x=229*S;y=-1230*S;length=218*S
box('double-sided slim base',x,y,.22,1.40,length,.18,base,.04)
# symmetrical shared back, divided upholstered pads with modest thickness
for j in range(3):
 yy=y+(j-1)*(length-.12)/3
 for side in [-1,1]:
  box('separate seat cushion',x+side*.40,yy,.43,.61,(length-.16)/3-.025,.20,cloth,.065)
  ob=box('separate back cushion',x+side*.085,yy,.70,.17,(length-.16)/3-.03,.43,cloth,.05);ob.rotation_euler.y=side*math.radians(-6)
for xx in [-.55,.55]:
 for yy in [-length/2+.16,0,length/2-.16]:box('exposed short leg',x+xx,y+yy,.09,.045,.045,.18,leg,.008)
# no full-height end blocks or armrests in original circulation
render('P2','客厅-M02')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'D3/过程/核对简模.blend'));S=19/1600
cab=mat('cabinet fronts',(.53,.55,.54));top=mat('worktop',(.87,.86,.81));metal=mat('fixtures',(.30,.32,.33));dark=mat('hob sink',(.16,.18,.19))
for n in ['kitchen-left-counter','kitchen-north-counter','island']:
 o=bpy.data.objects[n];o.data.materials.clear();o.data.materials.append(cab);o.dimensions.z=.84;o.location.z=.42
 bpy.context.view_layer.update();d=o.dimensions
 box(n+' worktop',o.location.x,o.location.y,.89,d.x+.025,d.y+.025,.045,top,.008)
 # recessed plinth and visible small door joints; preserve footprint
 box(n+' plinth',o.location.x,o.location.y,.06,d.x-.06,d.y-.06,.12,dark)
 if n=='island':
  for yy in [570,610]:box('island door joint',954*S+.001,-yy*S,.47,.005,.009,.65,dark)
# library fixtures at original source positions; all uniform scaling
asset('kitchen_fixture_sink_undermount_rectangular',919*S,-423*S,.895,.60,.40,dark)
asset('kitchen_fixture_faucet_bent_tube_swivel',919*S,-402*S,.91,.30,.23,metal)
asset('kitchen_fixture_cooktop_with_circular_inlet',798*S,-528*S,.914,.43,.62,dark)
render('D3','客厅-M01')
(OUT/'模型使用记录.json').write_text(json.dumps({'library_assets':records,'P2':'库中没有匹配双面沙发，采用本案原创简模：分离坐垫、窄共背、短腿和薄底座；原双向使用组合、占地及机位不变','D3':'保留柜体范围及机位，台面分层和柜缝由本案补建，水槽、龙头、灶面导入本地库GLB；未改墙或遮挡'},ensure_ascii=False,indent=2))
