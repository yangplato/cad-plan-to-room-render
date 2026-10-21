import bpy,math,json
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parent.parent
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
def camera(name,x,y,tx,ty,lens=23,z=1.5):
 bpy.context.scene.render.resolution_y=1200 if '主卧' in name else 900
 bpy.ops.object.camera_add(location=(x*SX,-y*SY,z));o=bpy.context.object;o.name=name;o.data.lens=lens;o.data.clip_start=.05;o.rotation_euler=(Vector((tx*SX,-ty*SY,.65 if '主卧' in name else .82))-o.location).to_track_quat('-Z','Y').to_euler();bpy.context.scene.camera=o
 if '主卧' in name:
  # Open the modeled entry leaf for the doorway viewpoint; the aperture and wall remain.
  for obj in bpy.context.scene.objects:
   if obj.name in ['bedroom-entry','master-door']:obj.hide_render=True
  bed=bpy.data.objects.get('master-bed');head=bpy.data.objects.get('master-headboard')
  pts=[obj.matrix_world@Vector(v) for obj in [bed,head] for v in obj.bound_box]
  center=sum(pts,Vector())/len(pts);center.z=.70
  o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
  for focal in [26,25,24,23,22,21,20,19,18,17,16]:
   o.data.lens=focal;bpy.context.view_layer.update()
   ps=[world_to_camera_view(bpy.context.scene,o,v) for v in pts]
   if all(.055<q.x<.945 and .055<q.y<.945 and q.z>0 for q in ps):break
 CAMS[CODE+'-'+name]={'location':list(o.location),'target_note':'以实际rotation_euler为准；构图阶段已调整目标点','lens_mm':o.data.lens,'rotation_euler':list(o.rotation_euler),'画幅':[1600,bpy.context.scene.render.resolution_y],'净高假设':2.8}
 bpy.context.scene.render.filepath=str(ROOT/CODE/'空间约束图'/(name+'.png'));bpy.ops.render.render(write_still=True)
def d3():
 init('D3',17.1,17.1)
 cube('floor',.13,.15,.92,.89,-.12,0,'floor');cube('flat-ceiling-placeholder',.13,.15,.92,.89,2.8,2.92)
 # living boundary and open dining connection, copied proportionally from plan pixels
 wall('TV-wall',.355,.595,.355,.775);wall('west-jamb',.355,.855,.355,.89);door('bedroom-entry',.355,.775,.355,.855)
 wall('east-bedroom-wall',.71,.52,.71,.78);wall('east-window-jamb',.71,.78,.71,.89);window('south-living-window',.36,.89,.71,.89)
 cube('tv-low',.36,.622,.382,.765,0,.42,'cabinet');cube('TV',.362,.655,.37,.735,.85,1.63,'screen')
 cube('sofa-seat',.59,.59,.655,.795,.18,.45,'furniture');cube('sofa-back',.645,.59,.667,.795,.45,.85,'furniture');cube('chaise-seat',.57,.77,.655,.808,.18,.45,'furniture')
 disk('coffee',.546,.682,1.05);chair(.494,.587,'S')
 # dining and kitchen
 disk('dining',.563,.486,1.2,.75);chair(.516,.505);chair(.610,.475,'S')
 cube('kitchen-island',.542,.277,.585,.385,0,.91,'cabinet');cube('kitchen-left',.459,.245,.482,.40,0,.91,'cabinet');cube('kitchen-north',.46,.242,.598,.268,0,.91,'cabinet');cube('fridge',.646,.25,.676,.32,0,2.35,'cabinet')
 window('kitchen-north-window',.48,.242,.64,.242)
 wall('kitchen-west',.455,.245,.455,.395);wall('kitchen-partition-left',.447,.409,.475,.409);wall('kitchen-partition-right',.525,.409,.67,.409,2.25,2.8)
 cube('east-hall-cabinet',.646,.325,.679,.50,0,2.65,'cabinet');wall('hall-background',.68,.325,.68,.50)
 # master bedroom upper left, head west
 wall('master-west',.20,.20,.20,.405);window('master-north',.20,.20,.40,.20);wall('master-east',.40,.20,.40,.405);wall('master-south',.20,.405,.305,.405);door('master-door',.305,.405,.36,.405);wall('master-south-east',.36,.405,.40,.405)
 cube('master-bed',.22,.263,.35,.365,.12,.53,'furniture');cube('master-headboard',.214,.255,.224,.373,.40,1.12,'furniture');cube('master-dresser',.365,.267,.393,.365,0,.76,'cabinet');cube('nightstand',.22,.225,.25,.255,0,.5,'cabinet')
 camera('客厅-M01',.39,.872,.57,.70,23);camera('客厅-M02',.66,.515,.51,.725,24);camera('主卧-M01',.395,.399,.278,.307,22)
 bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'D3/过程/空间简模.blend'))
def p2():
 init('P2',18,24)
 cube('floor',.035,.36,.967,.77,-.12,0,'floor');cube('flat-ceiling-placeholder',.035,.36,.967,.77,2.8,2.92)
 window('west-living-window',.037,.555,.037,.759);window('south-living-window',.037,.764,.34,.764)
 wall('east-TV-partition',.341,.60,.341,.76);cube('retractable-tv',.331,.679,.338,.726,.83,1.67,'screen');cube('tv-base',.325,.668,.34,.735,0,.38,'cabinet')
 # back to back sofa, central back along north/south
 cube('sofa-west-seat',.127,.622,.161,.733,.18,.46,'furniture');cube('sofa-east-seat',.171,.622,.205,.733,.18,.46,'furniture');cube('sofa-shared-back',.160,.615,.172,.737,.43,.86,'furniture')
 disk('east-coffee',.262,.680,.95);disk('west-coffee',.115,.719,.78);chair(.294,.627,'S');chair(.090,.742);chair(.274,.743)
 # dining six seats
 cube('dining-top',.16,.498,.25,.527,.72,.79,'furniture')
 for x in [.167,.204,.241]:chair(x,.484,'S');chair(x,.543)
 cube('kitchen-left',.14,.37,.16,.43,0,.91,'cabinet');cube('kitchen-north',.14,.37,.31,.39,0,.91,'cabinet');cube('kitchen-right',.31,.38,.34,.54,0,2.65,'cabinet');cube('breakfast-bar',.176,.432,.255,.45,0,.95,'cabinet');chair(.207,.46);chair(.241,.46)
 wall('kitchen-top',.14,.365,.34,.365);wall('core-west',.35,.37,.35,.55);cube('east-kitchen-return',.315,.50,.34,.553,0,2.65,'cabinet')
 # adjacent tearoom behind TV partition
 wall('tea-north',.35,.623,.50,.623);cube('tea-table',.41,.655,.44,.738,0,.75,'furniture')
 # principal bedroom top right of plan. east bathroom partition and north balcony glazing
 wall('bed-west',.69,.41,.69,.50);door('bedroom-entry',.69,.50,.69,.546);wall('bed-east',.833,.41,.833,.55);window('master-balcony',.69,.41,.833,.41);wall('bed-south',.69,.563,.833,.563)
 cube('master-bed',.729,.443,.826,.495,.13,.55,'furniture');cube('master-headboard',.819,.436,.830,.503,.46,1.15,'furniture');cube('wardrobe',.69,.548,.832,.568,0,2.65,'cabinet');cube('nightstand',.805,.419,.827,.441,0,.48,'cabinet');cube('dresser',.784,.518,.827,.541,0,.75,'cabinet')
 camera('客厅-M01',.285,.555,.185,.687,24);camera('客厅-M02',.05,.756,.225,.661,22);camera('主卧-M01',.682,.54,.777,.473,22)
 bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'P2/过程/空间简模.blend'))
d3();p2()
(ROOT/'过程/模型与相机.json').write_text(json.dumps({'说明':'依据历史平面PNG按比例转绘当前空间的简模；不是本轮原生CAD尺寸提取。比例用于视觉布置，层高2.8m、门高2.25m、窗上下沿均为设计假设。平顶占位不预建吊顶和灯具。两机位共用该户型模型。','相机':CAMS},ensure_ascii=False,indent=2))
