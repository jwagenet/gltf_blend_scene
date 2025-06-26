bl_info = {
    "name": "GLTF Scene",
    "description": "Build a studio scene from a GLTF/GLB for easy rendering",
    "author": "Jonathan Wagenet",
    "version": (0, 1),
    "blender": (2, 80, 0),
    "category": "Render",
}


import math
import os

import bpy
import bmesh

from bpy.types import Operator, Panel, Scene, PropertyGroup
from bpy.props import BoolProperty, FloatVectorProperty, StringProperty, IntProperty, FloatProperty
from mathutils import Vector, Euler


class PanelProperties(PropertyGroup):
    use_backdrop: BoolProperty(name="Use Backdrop", default=True)
    save_blend: BoolProperty(name="Save .blend File", default=False)
    render: BoolProperty(name="Render", default=True)
    backdrop_color: FloatVectorProperty(
        name="Backdrop Color", subtype="COLOR", size=4, min=0.0, max=1.0, default=(1.0, 1.0, 1.0, 1.0)
    )
    size_x: IntProperty(
        name="Size X",
        subtype="PIXEL",
        min=0,
        default=500,
    )
    size_y: IntProperty(
        name="Size Y",
        subtype="PIXEL",
        min=0,
        default=300,
    )
    gltf_path: StringProperty(name="GLTF Path", default="", subtype="FILE_PATH")
    camera_distance: FloatProperty(name="Camera Distance", subtype="DISTANCE", min=0.0, default=3.5)
    camera_angle: FloatProperty(
        name="Camera Angle",
        subtype="ANGLE",
        soft_min=0.0,
        soft_max=math.radians(90),
        default=math.radians(20),
    )
    object_rotation: FloatProperty(
        name="Object Rotation", subtype="ANGLE", min=math.radians(-360), max=math.radians(360), default=0.0
    )


class AssembleScene(Operator):
    bl_idname = "gltf.assemble_scene"
    bl_label = "Assemble Scene"

    def execute(self, context):
        props = context.scene.gltf_panel_props

        main(
            props.gltf_path,
            (props.size_x, props.size_y),
            props.backdrop_color,
            props.render,
            props.save_blend,
            props.use_backdrop,
            props.camera_angle,
            props.camera_distance,
            props.object_rotation,
        )

        return {"FINISHED"}


class RenderScene(Operator):
    bl_idname = "gltf.render_scene"
    bl_label = "Render"

    def execute(self, context):
        bpy.ops.render.render("INVOKE_DEFAULT")

        return {"FINISHED"}


class MyPanel(Panel):
    bl_label = "GLTF Scene"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "GLTF Scene"

    def draw(self, context):
        layout = self.layout
        props = context.scene.gltf_panel_props

        fields = [
            ("GLTF Path", "gltf_path"),
            ("Size X", "size_x"),
            ("Size Y", "size_y"),
            ("Camera Distance", "camera_distance"),
            ("Camera Angle", "camera_angle"),
            ("Object Rotation", "object_rotation"),
            ("Use Backdrop", "use_backdrop"),
            ("Backdrop Color", "backdrop_color"),
        ]

        for label_text, prop_id in fields:
            split = layout.split(factor=0.4)
            col_label = split.column(align=True)
            col_value = split.column(align=True)

            col_label.alignment = "RIGHT"
            col_label.label(text=label_text)

            col_value.prop(props, prop_id, text="")

        layout.operator("gltf.assemble_scene")
        layout.operator("gltf.render_scene")


def register():
    bpy.utils.register_class(MyPanel)
    bpy.utils.register_class(PanelProperties)
    bpy.utils.register_class(AssembleScene)
    bpy.utils.register_class(RenderScene)
    Scene.gltf_panel_props = bpy.props.PointerProperty(type=PanelProperties)


def unregister():
    bpy.utils.unregister_class(MyPanel)
    bpy.utils.unregister_class(PanelProperties)
    bpy.utils.unregister_class(AssembleScene)
    bpy.utils.unregister_class(RenderScene)
    del Scene.gltf_panel_props


def main(
    gltf_path,
    size,
    backdrop_color,
    render,
    save_blend,
    use_backdrop,
    camera_angle=20,
    camera_distance=3.5,
    object_rotate=0,
):
    # Extract parts
    print({"INFO"}, f"{gltf_path}")
    folder = os.path.dirname(gltf_path)
    filename = os.path.basename(gltf_path)
    basename, ext = os.path.splitext(filename)

    # config
    render_path = os.path.join(folder, basename + ".png")
    blend_path = os.path.join(folder, basename + ".blend")
    camera_lens = 70
    distance = -camera_distance
    angle_rad = -camera_angle
    background_color = (1, 1, 1, 1)

    print(camera_angle, angle_rad)

    ## Scene
    try:
        bpy.ops.object.mode_set(mode="OBJECT")
    except RuntimeError:
        pass
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)

    scene = bpy.data.scenes["Scene"]
    scene.view_settings.view_transform = "Filmic"
    bpy.context.scene.render.engine = "CYCLES"
    bpy.context.scene.view_settings.look = "High Contrast"
    bpy.context.scene.cycles.use_denoising = True

    background = bpy.data.worlds["World"].node_tree.nodes["Background"]
    background.inputs[0].default_value = background_color
    background.inputs[1].default_value = 0
    bpy.context.scene.world.cycles_visibility.diffuse = False
    bpy.context.scene.world.cycles_visibility.diffuse = False

    bpy.context.scene.render.resolution_x = size[0]
    bpy.context.scene.render.resolution_y = size[1]
    bpy.context.scene.render.filepath = render_path

    ## Object
    bpy.ops.import_scene.gltf(filepath=gltf_path)
    top_level_empties = [
        obj for obj in bpy.context.scene.objects if obj.type == "EMPTY" and obj.parent is None
    ]

    if len(top_level_empties) > 0:
        bpy.ops.object.select_all(action="DESELECT")
        root_empty = top_level_empties[0]
        root_empty.select_set(True)
        bpy.context.view_layer.objects.active = root_empty

    objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]

    def find_corners(objects):
        min_corner = Vector((float("inf"), float("inf"), float("inf")))
        max_corner = Vector((float("-inf"), float("-inf"), float("-inf")))

        for obj in objects:
            # Convert local bounding box to world coordinates
            for vertex in obj.bound_box:
                world_vertex = obj.matrix_world @ Vector(vertex)
                min_corner = Vector(
                    (
                        min(min_corner.x, world_vertex.x),
                        min(min_corner.y, world_vertex.y),
                        min(min_corner.z, world_vertex.z),
                    )
                )
                max_corner = Vector(
                    (
                        max(max_corner.x, world_vertex.x),
                        max(max_corner.y, world_vertex.y),
                        max(max_corner.z, world_vertex.z),
                    )
                )

        return (min_corner, max_corner)

    min_corner, max_corner = find_corners(objects)
    obj_center = (min_corner + max_corner) / 2

    # Compute size
    size = max_corner - min_corner
    target_size = 1.0
    current_max_dimension = max(size)

    if current_max_dimension > 0:
        scale_factor = target_size / current_max_dimension
        bpy.ops.transform.resize(value=(scale_factor, scale_factor, scale_factor))

    else:
        print("Bounding box has zero size; cannot scale.")

    min_corner, max_corner = find_corners(objects)
    loc = (min_corner + max_corner) / 2
    bpy.ops.transform.translate(value=(-loc.x, -loc.y, 0))
    bpy.ops.transform.translate(value=(0, 0, -min_corner.z))

    # Apply rotation
    bpy.context.scene.tool_settings.transform_pivot_point = "CURSOR"
    bpy.ops.transform.rotate(value=object_rotate, orient_axis="Z")

    min_corner, max_corner = find_corners(objects)
    obj_center = (min_corner + max_corner) / 2

    ## Backdrop
    if use_backdrop:
        bpy.ops.mesh.primitive_plane_add(
            enter_editmode=False, align="WORLD", location=(0, 0, 0), scale=(1, 1, 1)
        )
        plane = bpy.context.active_object
        bpy.context.view_layer.objects.active = plane
        bpy.ops.object.shade_smooth()
        bpy.ops.object.mode_set(mode="EDIT")

        # Extend and bevel
        mesh = bmesh.from_edit_mesh(plane.data)
        edges = [e for e in mesh.edges if ((e.verts[0].co + e.verts[1].co) / 2).y > 0]
        bpy.ops.mesh.select_all(action="DESELECT")

        corner = edges[0]
        corner.select = True

        bpy.ops.mesh.extrude_edges_move(
            MESH_OT_extrude_edges_indiv={"use_normal_flip": False, "mirror": False},
            TRANSFORM_OT_translate={
                "value": (0, 0, 2),
                "orient_type": "GLOBAL",
                "orient_matrix": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
            },
        )

        bpy.ops.mesh.select_all(action="DESELECT")
        corner.select = True

        bpy.ops.mesh.bevel(offset=0.3, offset_pct=0, segments=10, affect="EDGES")
        bpy.ops.object.mode_set(mode="OBJECT")

        scale = 5
        bpy.ops.transform.resize(value=(scale, scale, scale), orient_type="GLOBAL")

        # Material
        backdrop_material = bpy.data.materials.new(name="Backdrop")
        backdrop_material.use_nodes = True
        backdrop_material.node_tree.nodes["Principled BSDF"].inputs[0].default_value = backdrop_color
        plane.data.materials.append(backdrop_material)
        plane.active_material_index = 0

    ## Camera
    bpy.ops.object.camera_add(location=obj_center, rotation=(math.radians(90), 0, 0))
    camera = bpy.context.active_object
    camera.name = "Camera"
    camera.data.lens = camera_lens
    bpy.context.scene.camera = camera

    # Initial camera offset vector relative to pivot
    offset = Vector((0, distance, 0))

    # Rotate offset vector around X axis by angle_rad (pitch)
    rotation = Euler((angle_rad, 0, 0), "XYZ")
    rotation_matrix = rotation.to_matrix()
    rotated_offset = rotation_matrix @ offset

    # Set camera location to pivot plus rotated offset
    camera.location = obj_center + rotated_offset

    # Point at pivot
    direction = obj_center - camera.location
    rot_quat = direction.to_track_quat("-Z", "Y")
    camera.rotation_euler = rot_quat.to_euler()

    ## Lights
    def add_area_light(name, location, rotation, size=2, energy=1000):
        bpy.ops.object.light_add(type="AREA", location=location, rotation=rotation)
        light = bpy.context.active_object
        light.name = name
        light.data.energy = energy
        light.data.shape = "SQUARE"
        light.data.size = size
        return light

    add_area_light("KeyLight", (12.7, -12.7, 10.4), (math.radians(60), 0, math.radians(45)), 3, 1600)
    add_area_light("FillLight", (-12.7, -12.7, 10.4), (math.radians(60), 0, math.radians(-45)), 5, 1000)
    add_area_light("BackLight", (5.2, 3.8, 2.2), (math.radians(285), 0, math.radians(-50)), 3, 100)


if __name__ == "__main__":
    register()
