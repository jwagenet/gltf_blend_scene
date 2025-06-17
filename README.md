# GLTF Blend Scene

A Blender plugin to import a GLTF and assemble a studio scene for easy rendering.

## Prerequisites

1. Blender, tested with 4.4

## Setup

1. Download `gltf_blend_scene.py`
2. In Bender, navigate to `Edit > Preferences > Add-ons`
3. Click the drop-down arrow in the upper-right arrow and select `Install form Disk...`
4. Select the downloaded py file. The add-on will appear at `GLTF Scene` in the add-on list.

## Use

1. In the 3D Viewport (with the default cube) press `N` key to open the N panel and select the `GLTF Scene` tab.
2. Paste a *full path* for GLTF Path of your GLTF file or click the folder icon to select from the file browser. Make sure to open the settings gear in the file browser and uncheck `Relative Path` otherwise the script may not find the file.
3. Some scene settings may be tweaked, but for now click `Assemble Scene` to import the GLTF contents and create a basic scene with backdrop, camera, and lighting.
4. Click `Render` to render scene (using the Cycles renderer).
5. From here you can save the .blend file and tweak the scene, object materials, etc. Clicking `Assemble Scene` again will reset the scene.

## Notes

* Blender supports importing the base GLTF material properties and [these extensions](https://docs.blender.org/manual/en/4.4/addons/import_export/scene_gltf2.html#extensions).