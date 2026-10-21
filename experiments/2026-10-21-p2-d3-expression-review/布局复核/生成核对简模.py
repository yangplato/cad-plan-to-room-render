import bpy,math,json
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parent
CAMS={}
def init(code,sx,sy):
 global CODE,SX,SY,MATS
 CODE=code;SX=sx;SY=sy;bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 MATS={}
 for k,c in {'wall':(.78,.79,.77,1),'floor':(.88,.87,.83,1),'furniture':(.63,.52,.36,1),'cabinet':(.56,.45,.31,1),'screen':(.14,.18,.18,1),'frame':(.35,.43,.45,1),'door':(.67,.64,.56,1)}.items():
  m=bpy.data.materials.new(k);m.diffuse_color=c;MATS[k]=m
 scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='FLAT';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.show_object_outline=True;scene.display.shading.background_type='WORLD';scene.world.color=(.8,.83,.84);scene.render.resolution_x=1600;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.view_settings.view_transform='Standard'
def cube(name,x0,y0,x1,y1,z0,z1,mat='wall'):
 bpy.ops.mesh.primitive_cube_add(size=1,location=((x0+x1)*SX/2,-(y0+y1)*SY/2,(z0+z1)/2));o=bpy.context.object;o.name=name;o.dimensions=(abs(x1-x0)*SX,abs(y1-y0)*SY,z1-z0);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(MATS[mat]);return o
def wall(name,x0,y0,x1,y1,z0=0,z1=2.8):
 if x0==x1:return cube(name,x0-.004,y0,x1+.004,y1,z0,z1)
 return cube(name,x0,y0-.004,x1,y1+.004,z0,z1)
def window(name,x0,y0,x1,y1):
 wall(name+'-sill',x0,y0,x1,y1,0,.14);wall(name+'-header',x0,y0,x1,y1,2.58,2.8)
 for t in [0,.25,.5,.75,1]:
  x=x0+(x1-x0)*t;y=y0+(y1-y0)*t;cube(name+'-mullion',x-.0015,y-.0015,x+.0015,y+.0015,.14,2.58,'frame')
def door(name,x0,y0,x1,y1):
 if x0==x1:cube(name,x0-.003,y0,x1+.003,y1,0,2.25,'door')
 else:cube(name,x0,y0-.003,x1,y1+.003,0,2.25,'door')
 wall(name+'-head',x0,y0,x1,y1,2.25,2.8)
def disk(name,x,y,diam,height=.42):
 bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=diam/2,depth=.07,location=(x*SX,-y*SY,height));o=bpy.context.object;o.name=name;o.data.materials.append(MATS['furniture']);cube(name+'-base',x-.012,y-.012,x+.012,y+.012,0,height,'furniture')
def chair(x,y,face='N'):
 cube('chair-seat',x-.018,y-.016,x+.018,y+.016,.39,.47,'furniture')
 if face=='N':cube('chair-back',x-.018,y+.010,x+.018,y+.017,.47,.83,'furniture')
 else:cube('chair-back',x-.018,y-.017,x+.018,y-.010,.47,.83,'furniture')

def rect(n,a,b,c,d,h=2.8,z=0,mat='wall'):
 return cube(n,a/W,b/H,c/W,d/H,z,h,mat)
def win(n,a,b,c,d):window(n,a/W,b/H,c/W,d/H)
def table(n,x,y,r,h=.43):disk(n,x/W,y/H,2*r*S,h)
def seat(n,x,y,w,d,angle=0):
 # seat and back rotate together about center; angle 0 faces plan north
 objs=[rect(n,x-w/2,y-d/2,x+w/2,y+d/2,.46,.16,'furniture'),rect(n+'-back',x-w/2,y+d/2-8,x+w/2,y+d/2,.86,.46,'furniture')]
 for o in objs:
  v=o.location-Vector((x*S,-y*S,0));t=math.radians(-angle);o.location.x=x*S+v.x*math.cos(t)-v.y*math.sin(t);o.location.y=-y*S+v.x*math.sin(t)+v.y*math.cos(t);o.rotation_euler.z=t

def shot(n,x,y,tx,ty,lens=24,ratio=(1600,1100),targetz=1.1):
 sc=bpy.context.scene;sc.render.resolution_x,sc.render.resolution_y=ratio
 bpy.ops.object.camera_add(location=(x*S,-y*S,1.48));cam=bpy.context.object;cam.name=n;cam.data.lens=lens;cam.data.clip_start=.03
 cam.rotation_euler=(Vector((tx*S,-ty*S,1.48))-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam
 cam.data.shift_y=(targetz-1.48)*lens/(36*math.hypot((tx-x)*S,(ty-y)*S))
 if '主卧' in n:
  bed=bpy.data.objects.get('master-bed');bpy.context.view_layer.update();points=[bed.matrix_world@Vector(v) for v in bed.bound_box]
  for mm in range(lens,17,-1):
   cam.data.lens=mm;bpy.context.view_layer.update();qs=[world_to_camera_view(sc,cam,v) for v in points]
   cam.data.shift_x+=((min(q.x for q in qs)+max(q.x for q in qs))/2-.5)
   cam.data.shift_y+=((min(q.y for q in qs)+max(q.y for q in qs))/2-.43)*ratio[1]/ratio[0]
   bpy.context.view_layer.update();qs=[world_to_camera_view(sc,cam,v) for v in points]
   if all(.07<q.x<.93 and .07<q.y<.93 for q in qs):break
 sc.render.filepath=str(ROOT/CODE/'空间约束图'/(n+'.png'));bpy.ops.render.render(write_still=True)
 CAMS[CODE+'-'+n]={'xy':[x,y],'target':[tx,ty],'lens':cam.data.lens,'shift':[cam.data.shift_x,cam.data.shift_y],'frame':ratio}
def save():
 bpy.context.view_layer.update()
 footprints=[]
 for o in bpy.context.scene.objects:
  if o.type!='MESH' or o.name in ['floor','ceiling']:continue
  vs=[o.matrix_world@v.co for v in o.data.vertices];footprints.append({'name':o.name,'mat':o.data.materials[0].name.split('.')[0],'xy':[[v.x/S,-v.y/S] for v in vs]})
 (ROOT/CODE/'过程/模型投影.json').write_text(json.dumps({'W':W,'H':H,'scale_m_per_pixel':S,'objects':footprints,'cameras':{k:v for k,v in CAMS.items() if k.startswith(CODE)}},ensure_ascii=False))
 bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/CODE/'过程/核对简模.blend'))

def d3():
 global W,H,S
 W=H=1600;S=19/1600;init('D3',W*S,H*S)
 rect('floor',215,240,1460,1420,0,-.12,'floor');rect('ceiling',215,240,1460,1420,2.93,2.8)
 # actual west TV wall and door to son's room: door is SOUTH of TV; north cabinet remains
 rect('TV-wall',567,1019,588,1218);rect('TV-north-cabinet',560,912,605,1018,2.4,0,'cabinet')
 rect('TV-low',588,1020,628,1194,.4,0,'cabinet');rect('TV-screen',589,1036,595,1159,1.65,.8,'screen')
 rect('south-TV-return',567,1194,647,1218);rect('balcony-storage',588,1220,646,1285,.7,0,'cabinet')
 # north-right bedroom/wardrobe partition and original L return
 rect('east-partition',1188,980,1208,1218);rect('east-return',1113,1194,1208,1218)
 rect('east-wardrobe',1137,927,1187,1193,2.65,0,'cabinet');rect('east-upper-wardrobe',1137,906,1309,928,2.65,0,'cabinet')
 win('south-balcony',585,1408,1198,1408);win('west-balcony',575,1286,575,1408);win('east-balcony',1198,1218,1198,1408)
 # sofa footprint follows source taper and angled south return
 pts=[(994,951),(1062,951),(1062,1216),(975,1254),(928,1230),(928,1195),(971,1164)]
 verts=[(x*S,-y*S,z) for z in [.17,.47] for x,y in pts];nn=len(pts);faces=[tuple(range(nn-1,-1,-1)),tuple(range(nn,2*nn))]+[(i,(i+1)%nn,(i+1)%nn+nn,i+nn) for i in range(nn)]
 mesh=bpy.data.meshes.new('sofa');mesh.from_pydata(verts,[],faces);mesh.update();ob=bpy.data.objects.new('sofa',mesh);bpy.context.collection.objects.link(ob);ob.data.materials.append(MATS['furniture'])
 rect('sofa-back',1046,952,1062,1216,.86,.47,'furniture')
 table('coffee',874,1076,51);seat('armchair',811,950,58,64,145)
 table('dining',888,775,50,.75);seat('dining-east',950,776,45,48,270);seat('dining-southwest',855,818,45,48,45)
 # kitchen and hall, formerly omitted source boundaries
 rect('kitchen-left-counter',773,438,824,648,.91,0,'cabinet');rect('kitchen-north-counter',774,399,960,447,.91,0,'cabinet');rect('island',902,537,954,646,.91,0,'cabinet')
 rect('kitchen-east-tall',1033,399,1087,648,2.5,0,'cabinet');rect('east-core-wall',1087,372,1107,803)
 rect('hall-south-wall',1087,803,1136,823);rect('hall-south-wall2',1194,803,1292,823)
 rect('hall-east-wall',1340,665,1359,803);rect('hall-north-core',1107,540,1340,560)
 rect('west-kitchen-partition',764,400,774,648);rect('kitchen-left-return',701,647,750,669);rect('kitchen-door-head',750,647,1033,665,2.8,2.25)
 rect('west-dining-cabinet',700,669,736,821,2.5,0,'cabinet');rect('east-dining-cabinet',1033,669,1087,821,2.5,0,'cabinet');win('kitchen-north',774,387,960,387)
 # master exactly on source room: entrance south x490..571; head west; dresser east
 rect('master-west',310,350,330,648);rect('master-east',621,377,643,568);rect('master-south',310,648,490,669);rect('master-south-east',571,635,643,669);rect('master-entry-head',490,648,571,669,2.8,2.25)
 win('master-north',330,325,621,325);rect('master-east-upper',621,325,641,377)
 rect('master-bed',348,409,524,575,.53,.13,'furniture');rect('headboard',341,408,352,575,1.05,.53,'furniture')
 rect('nightstand-north',330,360,364,407,.49,0,'cabinet');rect('nightstand-south',330,578,364,632,.49,0,'cabinet');rect('dresser',586,416,621,568,.76,0,'cabinet')
 rect('bedroom-entry-east-wardrobe',718,440,763,633,2.65,0,'cabinet');rect('bedroom-hall-north',643,377,764,398)
 shot('客厅-M01',649,1330,893,1060,26)
 shot('客厅-M02',1010,856,780,1120,25)
 shot('主卧-M01',604,623,424,493,21,(1600,1200),.55)
 save()
def p2():
 global W,H,S
 W=1368;H=1824;S=18/1368;init('P2',W*S,H*S)
 rect('floor',47,655,1323,1408,0,-.12,'floor');rect('ceiling',47,655,1323,1408,2.93,2.8)
 win('living-west',53,930,53,1374);win('living-south',80,1391,459,1391)
 rect('west-wall',47,735,61,926);rect('southwest-pier',47,1374,80,1408)
 # TV is on tea-room western fixed cabinetry; north end is NOT solid wall
 rect('tea-west-cabinet',460,1088,482,1258,2.65,0,'cabinet');rect('TV-partition',466,1258,484,1390)
 rect('retractable-TV',458,1267,465,1348,1.65,.8,'screen');rect('tea-south-pier',459,1390,484,1408)
 # source sofa two-sided with shared NS spine; preserve original footprint
 rect('sofa-west',173,1135,221,1339,.46,.16,'furniture');rect('sofa-east',236,1121,285,1340,.46,.16,'furniture');rect('shared-back',221,1121,236,1342,.83,.46,'furniture')
 table('east-coffee',356,1238,31);table('west-coffee',166,1304,29)
 seat('northeast-armchair',408,1140,44,46,225);rect('southeast-ottoman',348,1329,386,1367,.44,.1,'furniture');seat('southwest-armchair',126,1346,38,38,45);rect('west-ottoman',103,1254,134,1283,.4,.1,'furniture');table('sofa-north-side-table',260,1118,15,.52)
 # north dining and kitchen along original locations
 rect('dining-table',202,909,344,964,.77,.70,'furniture')
 for x in [228,271,315]:seat('dining-north',x,895,34,33,180);seat('dining-south',x,980,34,33)
 rect('kitchen-left',193,669,236,790,.91,0,'cabinet');rect('kitchen-north',236,670,425,711,.91,0,'cabinet');rect('kitchen-right',425,709,467,826,2.5,0,'cabinet');rect('bar',239,787,353,827,.93,0,'cabinet')
 for x in [288,326]:table('barstool',x,834,13,.62)
 rect('dining-east-cabinet',425,831,467,1008,2.65,0,'cabinet');rect('core-west',467,655,481,1012);rect('core-return',481,998,530,1012)
 rect('kitchen-west',181,655,194,831);win('kitchen-north',248,660,425,660)
 rect('elevator-hall-leftcab',481,833,507,999,2.65,0,'cabinet');rect('core-south-cabinet',685,1015,826,1039,2.65,0,'cabinet')
 rect('core-south-wall',660,998,835,1015);rect('core-east',822,655,836,998);rect('hall-door-head',530,998,660,1012,2.8,2.3)
 # tea room north sliding opening and east partition exist; keep all doors open in guides
 rect('tea-north-head',484,1134,684,1145,2.8,2.25);rect('tea-east-cabinet',684,1138,713,1381,2.65,0,'cabinet');rect('tea-table',557,1194,607,1345,.75,0,'furniture');rect('tea-bench',518,1231,548,1334,.45,0,'furniture')
 # bedroom wall coordinates follow original, not color plan
 rect('master-west',933,751,949,923);rect('master-east',1137,751,1150,1041);rect('master-south',909,1026,1140,1042)
 rect('master-entry-head',909,947,949,994,2.8,2.25);rect('master-door-jamb',900,992,914,1041)
 win('master-north',949,744,1137,744)
 rect('master-bed',993,803,1135,904,.54,.13,'furniture');rect('master-headboard',1125,799,1137,907,1.1,.54,'furniture')
 rect('wardrobe',915,994,1137,1027,2.65,0,'cabinet');rect('dresser',1098,904,1137,994,.76,0,'cabinet');rect('nightstand',1107,765,1134,800,.48,0,'cabinet')
 shot('客厅-M01',390,1000,255,1245,26,targetz=.68)
 shot('客厅-M02',87,1035,320,1250,25,targetz=.72)
 shot('主卧-M01',951,974,1062,853,21,(1600,1200),.58)
 save()
d3();p2()
