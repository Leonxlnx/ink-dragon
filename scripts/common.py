"""Shared constants for the ink-dragon film. Pure Python/NumPy (no bpy). Units: meters, seconds.
World: Z up, glass axis = Z axis, table top at z=0. Camera 'front' looks along +Y (camera sits at -Y).
Sim time t: t = 0 is the instant the ink drop first touches the water surface.
"""
import math, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # project folder (parent of scripts/)
FPS = 30
N_FRAMES = 1350            # 45 s
RES = (1920, 1080)

# ---- glass tumbler (lathe around Z)
GLASS_H = 0.150            # total height
GLASS_RB = 0.0335          # outer radius at z=0
GLASS_RT = 0.0410          # outer radius at z=GLASS_H
GLASS_WALL = 0.0022        # wall thickness
GLASS_BASE = 0.016         # solid base thickness (inner floor at z=GLASS_BASE)
WATER_Z = 0.128            # rest water level (flat part of the surface)

def r_out(z):
    return GLASS_RB + (GLASS_RT - GLASS_RB) * (z / GLASS_H)

def r_in(z):
    """inner (cavity) radius at height z"""
    return r_out(z) - GLASS_WALL

# ---- ink drop
DROP_RADIUS = 0.0017       # 3.4 mm diameter drop
DROP_IMPACT_SPEED = 1.2    # m/s at t=0 (downwards)
DROP_XY = (0.004, -0.003)  # impact point (slightly off-axis looks more natural)
G = 9.81
