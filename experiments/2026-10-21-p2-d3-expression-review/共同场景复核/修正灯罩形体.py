import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
src=(ROOT/'生成共同场景.py').read_text();exec(src.split("for c in ['P2','D3']:")[0])
exec(src[src.index('def scene_export'):src.index("for c in ['P2','D3']:")].replace('shared-v1','shared-v3').replace('约束图-v1','约束图-v3').replace('场景配置.json','场景配置-v3.json').replace('共用场景-v1','共用场景-v3'))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'D3/共用场景-v2.blend'));S=19/1600
old=bpy.data.objects['living pendant shade'];pos=old.location.copy();material=old.data.materials[0];bpy.data.objects.remove(old,do_unlink=True)
bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,location=pos);ob=bpy.context.object;ob.name='living pendant shade';ob.dimensions=(.68,.68,.36);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);ob.data.materials.append(material)
for p in ob.data.polygons:p.use_smooth=True
scene_export('D3')
