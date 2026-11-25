# -*- coding: utf-8 -*-
"""
gerar_memes_katie.py — Rota A do spec 01-memes-katie.md
Roda: "C:\Program Files\Blender Foundation\Blender 4.5\blender.exe" --background --python gerar_memes_katie.py
Gera 72 rostos (10 emoções) em 128x128 PNG em pets/katie/memes/<emo>/<emo>_N.png
+ contact sheet p/ revisão.
Estilo: quadrado gadget, moldura #1d1d26, tela #101018, olhos emissivos #00d2ff, brilho #7fe9ff.
"""
import bpy, math, os

RES = 128
OUT = r"C:/Users/9z2.pj/Downloads/pestinha-main/pestinha-main/pets/katie/memes"
SHEET = r"C:/Users/9z2.pj/AppData/Local/hermes/cache/scratch/contact_sheet_katie.png"

# ---------------- paleta (sRGB hex -> linear) ----------------
def lin(hexc):
    h = hexc.lstrip('#')
    c = [int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
    c = [((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c]
    return c

PAL = {k: lin(v) for k, v in {
    "bg": "#101018", "casca": "#0d0d12", "moldura": "#1d1d26",
    "olho": "#00d2ff", "brilho": "#7fe9ff", "escuro": "#05050a",
}.items()}

# ---------------- cena base ----------------
def limpar():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def novo_cena():
    limpar()
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = 1.35
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    bpy.context.scene.render.resolution_x = RES
    bpy.context.scene.render.resolution_y = RES
    bpy.context.scene.render.resolution_percentage = 100
    bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
    bpy.context.scene.eevee.taa_render_samples = 24
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.image_settings.color_mode = 'RGB'
    bpy.context.scene.world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    bpy.context.scene.world.use_nodes = True
    wb = next(n for n in bpy.context.scene.world.node_tree.nodes if n.type == 'BACKGROUND')
    wb.inputs['Color'].default_value = (*PAL["bg"], 1.0)
    wb.inputs['Strength'].default_value = 1.0

def box(nome, x, y, z, sx, sy, sz, mat, rotz=0.0, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, z))
    o = bpy.context.active_object
    o.name = nome
    o.scale = (sx, sy, sz)
    o.rotation_euler = (0, 0, rotz)
    o.data.materials.append(mat)
    if bevel > 0:
        m = o.modifiers.new("bev", 'BEVEL')
        m.width = bevel
        m.segments = 2
    return o

def mat_emit(nome, cor, strength):
    m = bpy.data.materials.get(nome)
    if m:
        return m
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    e = nt.nodes.new('ShaderNodeEmission')
    e.inputs['Color'].default_value = (*cor, 1.0)
    e.inputs['Strength'].default_value = strength
    nt.links.new(e.outputs['Emission'], out.inputs['Surface'])
    return m

def mat_simple(nome, cor):
    m = bpy.data.materials.get(nome)
    if m:
        return m
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (*cor, 1.0)
    b.inputs['Roughness'].default_value = 0.9
    return m

M = {}
def mats():
    if M:
        return
    M["casca"] = mat_simple("casca", PAL["casca"])
    M["moldura"] = mat_simple("moldura", PAL["moldura"])
    M["olho"] = mat_emit("olho", PAL["olho"], 3.0)
    M["brilho"] = mat_emit("brilho", PAL["brilho"], 2.2)
    M["brilho_fraco"] = mat_emit("brilho_fraco", PAL["brilho"], 0.9)
    M["boca"] = mat_emit("boca", PAL["brilho"], 1.8)

def curva_base(nome, bevel=0.02):
    c = bpy.data.curves.new(nome, 'CURVE')
    c.dimensions = '3D'
    c.bevel_depth = bevel
    c.use_fill_caps = True
    o = bpy.data.objects.new(nome, c)
    bpy.context.collection.objects.link(o)
    return o, c

def arco_poly(nome, centro, raio, a1, a2, n=9, bevel=0.02, mat=None):
    o, c = curva_base(nome, bevel)
    sp = c.splines.new('POLY')
    sp.points.add(n - 1)
    for i in range(n):
        a = math.radians(a1 + (a2 - a1) * i / (n - 1))
        sp.points[i].co = (centro[0] + raio * math.cos(a), centro[1] + raio * math.sin(a), 0.05, 1)
    c.materials.append(mat or M["boca"])
    return o

def linha(nome, pts, bevel=0.018, mat=None, z=0.05):
    o, c = curva_base(nome, bevel)
    sp = c.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for i, (x, y) in enumerate(pts):
        sp.points[i].co = (x, y, z, 1)
    c.materials.append(mat or M["boca"])
    return o

def circulo_cheio(nome, x, y, sx, sy, mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=14, radius=0.5, depth=0.02, location=(x, y, 0.05))
    o = bpy.context.active_object
    o.name = nome
    o.scale = (sx, sy, 1)
    o.data.materials.append(mat)
    return o

def coracao(nome, x, y, s, mat):
    for i, (dx, dy, r) in enumerate([(-0.045, 0.035, 0.05), (0.045, 0.035, 0.05), (0, -0.04, 0.055)]):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r * s, segments=12, ring_count=8,
                                             location=(x + dx * s, y + dy * s, 0.055))
        o = bpy.context.active_object
        o.name = f"{nome}_{i}"
        o.scale = (1, 1, 0.6)
        o.data.materials.append(mat)

def zzz(nome, x, y, s, mat):
    for k, (dx, dy, ss) in enumerate([(0, 0, 1.0), (0.09, 0.10, 0.7), (0.17, 0.18, 0.5)]):
        bx, by, bs = x + dx * s, y + dy * s, s * ss
        box(f"{nome}_t{k}", bx, by + 0.032 * bs, 0.06, 0.075 * bs, 0.016 * bs, 0.012, mat)
        box(f"{nome}_d{k}", bx + 0.012 * bs, by, 0.06, 0.016 * bs, 0.055 * bs, 0.012, mat, rotz=math.radians(35))
        box(f"{nome}_b{k}", bx, by - 0.032 * bs, 0.06, 0.075 * bs, 0.016 * bs, 0.012, mat)

# ---------------- rosto ----------------
def olho(nome, x, y, tipo):
    if tipo == "aberto":
        box(nome, x, y, 0.05, 0.15, 0.21, 0.016, M["olho"], bevel=0.035)
    elif tipo == "grande":
        box(nome, x, y, 0.05, 0.19, 0.25, 0.016, M["olho"], bevel=0.045)
    elif tipo == "semicerrado":
        box(nome, x, y, 0.05, 0.15, 0.11, 0.016, M["olho"], bevel=0.03)
    elif tipo == "estreito":
        box(nome, x, y, 0.05, 0.17, 0.07, 0.016, M["olho"], bevel=0.025)
    elif tipo == "fechado":
        box(nome, x, y, 0.05, 0.17, 0.032, 0.016, M["olho"], bevel=0.012)
    elif tipo == "coracao":
        coracao(nome, x, y, 1.1, M["olho"])
    elif tipo == "cruz":
        box(nome + "a", x, y, 0.05, 0.17, 0.032, 0.016, M["olho"], rotz=math.radians(45))
        box(nome + "b", x, y, 0.05, 0.17, 0.032, 0.016, M["olho"], rotz=math.radians(-45))

def sobrancelha(qual):
    if qual == "nenhuma":
        return
    y = 0.315
    if qual == "angry":
        box("sob_l", -0.17, y, 0.052, 0.15, 0.026, 0.012, M["olho"], rotz=math.radians(-25))
        box("sob_r", 0.17, y, 0.052, 0.15, 0.026, 0.012, M["olho"], rotz=math.radians(25))
    elif qual == "sad":
        box("sob_l", -0.17, 0.335, 0.052, 0.15, 0.024, 0.012, M["olho"], rotz=math.radians(20))
        box("sob_r", 0.17, 0.335, 0.052, 0.15, 0.024, 0.012, M["olho"], rotz=math.radians(-20))
    elif qual == "surpresa":
        box("sob_l", -0.17, 0.345, 0.052, 0.13, 0.022, 0.012, M["olho"])
        box("sob_r", 0.17, 0.345, 0.052, 0.13, 0.022, 0.012, M["olho"])
    elif qual == "foco":
        box("sob_l", -0.17, 0.27, 0.052, 0.14, 0.018, 0.012, M["olho"])
        box("sob_r", 0.17, 0.27, 0.052, 0.14, 0.018, 0.012, M["olho"])

def boca(qual):
    if qual == "smile":
        arco_poly("boca", (0, -0.10), 0.12, 200, 340)
    elif qual == "smile_peq":
        arco_poly("boca", (0, -0.12), 0.08, 205, 335)
    elif qual == "aberto":
        circulo_cheio("boca", 0, -0.16, 0.09, 0.07, M["boca"])
    elif qual == "reto":
        box("boca", 0, -0.16, 0.05, 0.14, 0.025, 0.012, M["boca"])
    elif qual == "triste":
        arco_poly("boca", (0, -0.20), 0.11, 20, 160)
    elif qual == "tremendo":
        pts = [(-0.12 + 0.06 * i, -0.16 + 0.02 * math.sin(i * 2.2)) for i in range(5)]
        linha("boca", pts)
    elif qual == "zigzag":
        pts = [(-0.12 + 0.06 * i, -0.16 + (0.035 if i % 2 == 0 else -0.035)) for i in range(5)]
        linha("boca", pts)
    elif qual == "w":
        arco_poly("boca1", (-0.07, -0.12), 0.055, 205, 335, bevel=0.016)
        arco_poly("boca2", (0.07, -0.12), 0.055, 205, 335, bevel=0.016)
    elif qual == "o":
        o, c = curva_base("boca", 0.02)
        sp = c.splines.new('BEZIER')
        sp.bezier_points.add(3)
        for i, a in enumerate((0, 90, 180, 270)):
            r = math.radians(a)
            p = sp.bezier_points[i]
            p.co = (0.045 * math.cos(r), -0.16 + 0.055 * math.sin(r), 0.05)
            p.handle_left_type = p.handle_right_type = 'AUTO'
        c.materials.append(M["boca"])

def acessorios(lista):
    for a in lista:
        if a == "oculos":
            for sx in (-1, 1):
                box(f"ocl_t{sx}", sx * 0.17, 0.155, 0.06, 0.225, 0.018, 0.012, M["brilho"])
                box(f"ocl_b{sx}", sx * 0.17, 0.105, 0.06, 0.225, 0.018, 0.012, M["brilho"])
                box(f"ocl_i{sx}", sx * (0.17 - 0.10), 0.13, 0.06, 0.018, 0.055, 0.012, M["brilho"])
                box(f"ocl_e{sx}", sx * (0.17 + 0.10), 0.13, 0.06, 0.018, 0.055, 0.012, M["brilho"])
            box("ocl_ponte", 0, 0.135, 0.06, 0.05, 0.016, 0.012, M["brilho"])
        elif a == "antena":
            bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.012, depth=0.16,
                                                location=(0.28, 0.62, 0.04))
            o = bpy.context.active_object
            o.name = "antena_ca"
            o.rotation_euler = (0, math.radians(18), 0)
            o.data.materials.append(M["brilho"])
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035, segments=10, ring_count=6,
                                                 location=(0.335, 0.70, 0.045))
            o = bpy.context.active_object
            o.name = "antena_bola"
            o.data.materials.append(M["olho"])
        elif a == "faisca":
            for i, (dx, dy, s) in enumerate([(-0.42, 0.05, 1.0), (-0.36, -0.18, 0.7)]):
                box(f"faisca{i}", dx, dy, 0.055, 0.05 * s, 0.014, 0.012, M["brilho"], rotz=math.radians(45))
                box(f"faisca{i}b", dx, dy, 0.055, 0.014, 0.05 * s, 0.012, M["brilho"])
        elif a == "coracoes":
            coracao("cor1", 0.40, 0.34, 0.8, M["brilho"])
            coracao("cor2", 0.52, 0.44, 0.55, M["brilho"])
        elif a == "suor":
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, segments=10, ring_count=6,
                                                 location=(0.30, 0.34, 0.05))
            o = bpy.context.active_object
            o.name = "suor"
            o.scale = (0.8, 1.5, 0.8)
            o.data.materials.append(M["brilho"])
        elif a == "zzz":
            zzz("zzz", -0.42, 0.42, 1.0, M["brilho_fraco"])
        elif a == "engrenagem":
            bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.05, depth=0.015,
                                                location=(-0.40, -0.34, 0.055))
            o = bpy.context.active_object
            o.name = "eng_c"
            o.data.materials.append(M["brilho_fraco"])
            for k in range(6):
                a = k * math.radians(60)
                box(f"eng_t{k}", -0.40 + 0.062 * math.cos(a), -0.34 + 0.062 * math.sin(a),
                    0.055, 0.02, 0.02, 0.012, M["brilho_fraco"], rotz=a)
        elif a == "scanlines":
            for k, yy in enumerate((0.30, 0.12, -0.06, -0.24)):
                box(f"scan{k}", 0, yy, 0.042, 0.98, 0.014, 0.004, M["brilho_fraco"])

def render_rusto(emo, i, olhos, bocaq, sobq, accs):
    mats()
    novo_cena()
    box("casca", 0, 0, 0.0, 1.30, 1.30, 0.02, M["casca"], bevel=0.06)
    box("moldura", 0, 0, 0.015, 1.22, 1.22, 0.02, M["moldura"], bevel=0.05)
    box("tela", 0, 0, 0.03, 1.10, 1.10, 0.02, M["casca"], bevel=0.04)
    ol = olhos if isinstance(olhos, tuple) else (olhos, olhos)
    olho("ol_l", -0.17, 0.13, ol[0])
    olho("ol_r", 0.17, 0.13, ol[1])
    sobrancelha(sobq)
    boca(bocaq)
    acessorios(accs)
    d = os.path.join(OUT, emo)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f"{emo}_{i}.png").replace('\\', '/')
    bpy.context.scene.render.filepath = p
    bpy.ops.render.render(write_still=True)
    print(f"[memes] {os.path.basename(p)}")

# ---------------- grid (10 emoções, 72 imagens) ----------------
E = {
    "feliz": [
        ("aberto", "smile", "nenhuma", []),
        ("semicerrado", "smile_peq", "nenhuma", []),
        ("aberto", "aberto", "surpresa", ["faisca"]),
        ("coracao", "smile", "nenhuma", ["coracoes"]),
        ("estreito", "smile_peq", "foco", ["oculos"]),
        ("grande", "aberto", "surpresa", ["antena"]),
        ("semicerrado", "w", "nenhuma", []),
        ("aberto", "smile", "nenhuma", ["engrenagem"]),
    ],
    "contente": [
        ("semicerrado", "smile_peq", "nenhuma", []),
        ("semicerrado", "smile", "nenhuma", []),
        ("aberto", "smile_peq", "nenhuma", ["faisca"]),
        ("estreito", "smile_peq", "nenhuma", ["antena"]),
        ("semicerrado", "w", "nenhuma", ["coracoes"]),
        ("aberto", "smile", "nenhuma", []),
        ("grande", "aberto", "surpresa", ["faisca"]),
    ],
    "observando": [
        ("aberto", "reto", "nenhuma", []),
        ("aberto", "reto", "surpresa", ["antena"]),
        ("semicerrado", "reto", "foco", []),
        ("aberto", "smile_peq", "nenhuma", ["antena"]),
        ("estreito", "reto", "foco", ["oculos"]),
        ("aberto", "w", "nenhuma", []),
        ("grande", "reto", "surpresa", []),
    ],
    "curioso": [
        (("grande", "aberto"), "o", "surpresa", []),
        ("aberto", "w", "nenhuma", ["faisca"]),
        (("estreito", "aberto"), "reto", "foco", ["antena"]),
        ("grande", "o", "surpresa", []),
        ("semicerrado", "smile_peq", "nenhuma", ["oculos"]),
        ("aberto", "reto", "nenhuma", ["faisca"]),
        ("grande", "o", "surpresa", ["antena"]),
    ],
    "bravo": [
        ("estreito", "zigzag", "angry", []),
        ("aberto", "zigzag", "angry", ["faisca"]),
        ("semicerrado", "reto", "angry", []),
        ("aberto", "tremendo", "angry", ["suor"]),
        ("estreito", "aberto", "angry", ["faisca"]),
        ("estreito", "tremendo", "angry", ["antena"]),
        ("aberto", "zigzag", "angry", ["engrenagem"]),
        ("grande", "aberto", "angry", ["faisca", "suor"]),
    ],
    "triste": [
        ("semicerrado", "triste", "sad", ["suor"]),
        ("fechado", "triste", "sad", []),
        ("aberto", "triste", "sad", ["suor"]),
        ("estreito", "reto", "sad", []),
        ("semicerrado", "tremendo", "sad", ["suor"]),
        ("fechado", "reto", "sad", ["suor"]),
        ("grande", "triste", "sad", ["suor"]),
    ],
    "assustado": [
        ("grande", "tremendo", "surpresa", ["suor"]),
        ("grande", "aberto", "surpresa", ["suor"]),
        ("cruz", "tremendo", "surpresa", ["faisca"]),
        ("grande", "o", "surpresa", ["suor"]),
        ("aberto", "tremendo", "surpresa", []),
        ("cruz", "aberto", "surpresa", ["suor"]),
        ("grande", "reto", "surpresa", ["antena"]),
    ],
    "dramatico": [
        ("grande", "aberto", "surpresa", ["suor"]),
        ("cruz", "aberto", "angry", ["faisca"]),
        ("fechado", "aberto", "sad", ["suor"]),
        ("grande", "w", "surpresa", []),
        (("grande", "fechado"), "aberto", "surpresa", ["suor"]),
        ("estreito", "tremendo", "angry", ["faisca"]),
        ("grande", "aberto", "surpresa", ["antena", "suor"]),
    ],
    "dormindo": [
        ("fechado", "reto", "nenhuma", ["zzz"]),
        ("fechado", "w", "nenhuma", ["zzz"]),
        ("fechado", "smile_peq", "nenhuma", ["zzz"]),
        (("fechado", "semicerrado"), "reto", "nenhuma", ["zzz"]),
        ("fechado", "aberto", "sad", ["zzz"]),
        ("fechado", "reto", "nenhuma", ["zzz", "antena"]),
        ("fechado", "w", "nenhuma", ["suor"]),
    ],
    "trabalhando": [
        ("estreito", "reto", "foco", ["oculos", "scanlines"]),
        ("semicerrado", "smile_peq", "foco", ["oculos", "scanlines"]),
        ("aberto", "reto", "foco", ["oculos"]),
        ("estreito", "w", "foco", ["oculos", "engrenagem"]),
        (("estreito", "aberto"), "reto", "foco", ["oculos"]),
        ("semicerrado", "aberto", "foco", ["oculos", "scanlines"]),
        ("aberto", "smile_peq", "foco", ["oculos", "antena"]),
    ],
}

# ---------------- compositor: glare p/ glow neon ----------------
def set_glare():
    sc = bpy.context.scene
    sc.use_nodes = True
    nt = sc.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    rl = nt.nodes.new('CompositorNodeRLayers')
    glare = nt.nodes.new('CompositorNodeGlare')
    glare.glare_type = 'FOG_GLOW'
    glare.threshold = 0.7
    glare.quality = 'HIGH'
    glare.mix = -0.4
    comp = nt.nodes.new('CompositorNodeComposite')
    nt.links.new(rl.outputs['Image'], glare.inputs['Image'])
    nt.links.new(glare.outputs['Image'], comp.inputs['Image'])

total = 0
set_glare()
for emo, vars_ in E.items():
    for i, (ol, bq, sq, accs) in enumerate(vars_, 1):
        render_rusto(emo, i, ol, bq, sq, accs)
        total += 1
print(f"[memes] TOTAL {total} rostos gerados em {OUT}")
