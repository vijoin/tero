import os

def solve_module_path(path: str, module: str) -> str:
    return os.path.join(os.path.dirname(os.path.realpath(module)), path)

def solve_asset_path(asset_path: str, module: str) -> str:
    return solve_module_path(os.path.join('assets', asset_path), module)
