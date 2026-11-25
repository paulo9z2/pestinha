# -*- coding: utf-8 -*-
"""Contact sheet dos memes da KATIE: 8 colunas x 10 linhas (1 emocao por linha).
Roda DEPOIS de gerar_memes_katie.py.
"""
import bpy, os, re

OUT = r"C:/Users/9z2.pj/Downloads/pestinha-main/pestinha-main/pets/katie/memes"
SHEET = r"C:/Users/9z2.pj/AppData/Local/hermes/cache/scratch/contact_sheet_katie.png"
ORDER = ["feliz", "contente", "observando", "curioso", "bravo",
         "triste", "assustado", "dramatico", "dormindo", "trabalhando"]

# limpa tudo
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# materiais por imagem
def mat_img(nome, path):
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(path)
    nt.links.new(tex.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 1.0
    return m

# fundo
bpy.context.scene.world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
bpy.context.scene.world.use_nodes = True
wb = next(n for n in bpy.context.scene.world.node_tree.nodes if n.type == 'BACKGROUND')
wb.inputs['Color'].default_value = (0.006, 0.006, 0.012, 1.0)
wb.inputs['Strength'].default_value = 1.0

col = 0
row = 0
for emo in ORDER:
    d = os.path.join(OUT, emo)
    if not os.path.isdir(d):
        continue
    files = sorted(os.listdir(d), key=lambda f: int(re.search(r'(\d+)\.png$', f).group(1)))
    for f in files:
        p = os.path.join(d, f).replace('\\', '/')
        m = mat_img(f"img_{emo}_{f}", p)
        bpy.ops.mesh.primitive_plane_add(size=1.0, location=(col * 1.0 - 3.5, 4.5 - row * 1.0, 0.0))
        o = bpy.context.active_object
        o.scale = (0.94, 0.94, 1.0)
        o.data.materials.append(m)
        col += 1
        if col == 8:
            col = 0
            row += 1

cam_data = bpy.data.cameras.new("cam")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 10.15
cam = bpy.data.objects.new("cam", cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam

sc = bpy.context.scene
sc.render.resolution_x = 1024
sc.render.resolution_y = 1280
sc.render.resolution_percentage = 100
sc.render.engine = 'BLENDER_EEVEE_NEXT'
sc.eevee.taa_render_samples = 4
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGB'
sc.render.filepath = SHEET.replace('\\', '/')
bpy.ops.render.render(write_still=True)
print(f"[sheet] OK {SHEET} (linhas: {ORDER})")
