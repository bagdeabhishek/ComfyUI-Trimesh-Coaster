from .trimesh_node import TrimeshCoasterNode

NODE_CLASS_MAPPINGS = {
    "TrimeshCoaster": TrimeshCoasterNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TrimeshCoaster": "Generate Coaster (Trimesh)"
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
