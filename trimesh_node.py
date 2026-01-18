import os
import trimesh
import numpy as np
import folder_paths
import io
import time

class TrimeshCoasterNode:
    """
    Final Coaster Node:
    - Direct SVG String Support
    - Correct Visual Centering
    - Flush Inlays
    - Short Unique Suffix (Time only)
    """
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "output_name": ("STRING", {"default": "Abhishek_Coaster"}),
                "diameter": ("FLOAT", {"default": 100.0, "min": 50.0, "max": 200.0}),
                "thickness": ("FLOAT", {"default": 5.0, "min": 2.0, "max": 20.0}),
                "logo_depth": ("FLOAT", {"default": 0.6, "min": 0.2, "max": 5.0}),
                "scale": ("FLOAT", {"default": 0.85, "min": 0.1, "max": 1.0}),
                "flip_horizontal": ("BOOLEAN", {"default": True}), 
                "top_rotate": ("INT", {"default": 0, "min": -360, "max": 360, "step": 90}),
                "bottom_rotate": ("INT", {"default": 0, "min": -360, "max": 360, "step": 90}),
            },
            "optional": {
                "svg_path": ("STRING", {"default": "", "multiline": False}),
                "svg_string": ("STRING", {"default": "", "multiline": True, "forceInput": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("stl_paths",)
    FUNCTION = "generate"
    OUTPUT_NODE = True
    CATEGORY = "Abhishek/3D"

    def generate(self, output_name, diameter, thickness, logo_depth, scale, flip_horizontal, top_rotate, bottom_rotate, svg_path="", svg_string=""):
        
        print(f"[Trimesh] Starting Generation...")

        # 1. Base Cylinder
        base = trimesh.creation.cylinder(radius=diameter/2, height=thickness, sections=120)
        
        # 2. Load SVG
        path_obj = None
        try:
            if svg_string and len(svg_string.strip()) > 10:
                print("[Trimesh] Loading from SVG String...")
                f_obj = io.BytesIO(svg_string.encode('utf-8'))
                path_obj = trimesh.load_path(f_obj, file_type='svg')
            elif svg_path and os.path.exists(svg_path):
                print(f"[Trimesh] Loading from File: {svg_path}")
                path_obj = trimesh.load_path(svg_path)
            else:
                return ("Error: No valid SVG string or file path provided.",)
        except Exception as e:
            return (f"Error parsing SVG: {e}",)

        # 3. Convert to Polygons
        poly_list = path_obj.polygons_full if path_obj.polygons_full else path_obj.polygons_closed
        if not poly_list:
            return ("Error: No valid closed shapes found in SVG.",)

        # 4. Extrude
        logo_meshes = []
        for poly in poly_list:
            clean_poly = poly.buffer(0)
            if not clean_poly.is_empty:
                try:
                    m = trimesh.creation.extrude_polygon(clean_poly, height=logo_depth)
                    logo_meshes.append(m)
                except: pass

        if not logo_meshes:
            return ("Error: Geometry extrusion failed.",)

        full_logo = trimesh.util.concatenate(logo_meshes)

        # 5. Scale & Mirror
        bounds = full_logo.bounds
        current_size = max(bounds[1][0]-bounds[0][0], bounds[1][1]-bounds[0][1])
        target_size = diameter * scale
        
        mirror_x = -1.0 if flip_horizontal else 1.0
        
        matrix = np.eye(4)
        matrix[0, 0] *= (mirror_x * target_size / current_size) 
        matrix[1, 1] *= (target_size / current_size)
        full_logo.apply_transform(matrix)
        
        # 6. Center (Visual Bounding Box Center)
        new_bounds = full_logo.bounds
        center_x = (new_bounds[0][0] + new_bounds[1][0]) / 2
        center_y = (new_bounds[0][1] + new_bounds[1][1]) / 2
        
        trans = np.eye(4)
        trans[0, 3] = -center_x
        trans[1, 3] = -center_y
        full_logo.apply_transform(trans)

        # 7. Flush Positioning
        
        # Top Logo
        top = full_logo.copy()
        if top_rotate != 0:
            rz = trimesh.transformations.rotation_matrix(np.radians(top_rotate), [0,0,1])
            top.apply_transform(rz)
            
        top_z = (thickness / 2) - logo_depth
        top.apply_translation([0, 0, top_z])
        
        # Bottom Logo
        bot = full_logo.copy()
        if bottom_rotate != 0:
            rz = trimesh.transformations.rotation_matrix(np.radians(bottom_rotate), [0,0,1])
            bot.apply_transform(rz)
            
        rx = trimesh.transformations.rotation_matrix(np.pi, [1,0,0])
        bot.apply_transform(rx)
        
        bot_z = (-thickness / 2) + logo_depth
        bot.apply_translation([0, 0, bot_z])

        # 8. Export with SHORT Suffix
        # Format: _HHMMSS (e.g. _143005)
        timestamp = time.strftime("%H%M%S")
        unique_name = f"{output_name}_{timestamp}"

        out_dir = folder_paths.get_output_directory()
        body_path = os.path.join(out_dir, f"{unique_name}_Body.stl")
        logo_path = os.path.join(out_dir, f"{unique_name}_Logos.stl")
        
        base.export(body_path)
        trimesh.util.concatenate([top, bot]).export(logo_path)
        
        print(f"[Trimesh] Saved: {unique_name}")
        return (f"{body_path} \n {logo_path}",)
