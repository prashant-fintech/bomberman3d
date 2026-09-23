from ursina import AmbientLight, DirectionalLight, Vec3, camera, color, window

from .config import Config, Palette


def setup_scene(config: Config) -> None:
    """Camera, lights and background. Runs once; these persist across rounds."""
    window.color = color.hex(Palette.background)
    center_x, center_z = (config.width - 1) / 2, (config.height - 1) / 2
    camera.position = (center_x, 17, -5.5)
    camera.look_at(Vec3(center_x, 0, center_z - .5))
    sun = DirectionalLight(shadows=False)
    sun.look_at(Vec3(.6, -1, .8))
    AmbientLight(color=color.hex('#8a8a8a'))
