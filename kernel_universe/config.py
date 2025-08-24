"""
Configuration parameters for the Kernel Universe simulation.
"""

import numpy as np

# Grid dimensions
GRID_SIZE = 100

# Time parameters
DAY_TICKS = 100

# Catalyst parameters
C_THRESH = 0.2
EMIT_FRACTION = 0.6

# Diffusion kernel for catalyst dispersal
KERNEL_3x3 = np.array([
    [0.05, 0.10, 0.05],
    [0.10, 0.40, 0.10],
    [0.05, 0.10, 0.05]
])

# Advection coefficient (rightward flow)
ADVECT_ALPHA = 0.05

# Temperature range for core activation
T_MIN, T_MAX = 0.40, 0.55

# Activation thresholds
TAU_TEMP = 8        # Consecutive ticks in temperature range
TAU_CATALYST = 12   # Catalyst threshold for bloom
TAU_REFRACT = 12    # Refractory period after bloom

# Core spawning parameter
SPAWN_S = 2

# Random seed for reproducibility
RNG_SEED = 42

# Initial number of cores
INITIAL_CORES = 10

# Redis configuration
REDIS_URL = "redis://localhost:6379"
REDIS_STATE_KEY = "kernel_universe:state"

# API settings
API_HOST = "0.0.0.0"
API_PORT = 8000
STREAM_FPS = 5
