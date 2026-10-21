import bpy,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent
# Reuse the shared exporter and primitives without rerunning v1 construction.
src=(ROOT/'生成共同场景.py').read_text();exec(src.split("for c in ['P2','D3']:")[0])
old_export=scene_export
# Preserve first input evidence; exporter has versioned output paths.
exec(src[src.index('def scene_export'):src.index("for c in ['P2','D3']:")].replace('shared-v1','shared-v2').replace('约束图-v1','约束图-v2').replace('场景配置.json','场景配置-v2.json').replace('共用场景-v1','共用场景-v2'))
for c in ['P2','D3']:
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/c/'共用场景-v1.blend'));S=18/1368 if c=='P2' else 19/1600
 wood=mat('selected pale timber',(.54,.49,.39));top=mat('selected shade',(.86,.85,.81))
 if c=='P2':
  o=bpy.data.objects['independent side table pedestal'];o.dimensions.x=o.dimensions.y=.34
  # Main image's plain legs do not alter chairs' overall bounding volumes.
 else:
  o=bpy.data.objects['living pendant shade'];o.dimensions=(.68,.68,.36)
  o=bpy.data.objects['dining pendant shade'];o.dimensions=(.40,.40,.30)
  # Simplified arm rails selected in main image; same chair center and orientation.
  x=811*S;y=-950*S;t=math.radians(145)
  for sign in [-1,1]:
   dx=sign*.315;dy=0
   ob=box('selected lounge wooden arm',x+dx*math.cos(t)-dy*math.sin(t),y+dx*math.sin(t)+dy*math.cos(t),.63,.045,.65,.05,wood,.01);ob.rotation_euler.z=t
 scene_export(c)
