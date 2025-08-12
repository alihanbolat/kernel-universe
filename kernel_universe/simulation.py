"""
Core simulation engine for Kernel Universe.
"""

import numpy as np
from typing import List, Tuple, Dict, Any
import time
from . import config


class Core:
    """Represents a core in the simulation that can bloom under specific conditions."""
    
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.temp_exposure_count = 0
        self.bloomed = False
        self.refractory_countdown = 0
        self.total_blooms = 0
        self.last_bloom_tick = -1
    
    def update(self, tick: int, temperature: float, catalyst: float, emit_mode: bool) -> bool:
        """
        Update core state based on current conditions.
        Returns True if the core blooms in this tick.
        """
        # Check if core is in refractory period
        if self.refractory_countdown > 0:
            self.refractory_countdown -= 1
            return False
        
        # Reset bloom state
        self.bloomed = False
        
        # Update temperature exposure counter
        if config.T_MIN <= temperature <= config.T_MAX:
            self.temp_exposure_count += 1
        else:
            self.temp_exposure_count = 0
        
        # Check bloom conditions
        if (emit_mode and 
            catalyst >= config.C_THRESH and 
            self.temp_exposure_count >= config.TAU_TEMP):
            
            # Core blooms!
            self.bloomed = True
            self.total_blooms += 1
            self.last_bloom_tick = tick
            self.refractory_countdown = config.TAU_REFRACT
            self.temp_exposure_count = 0
            
        return self.bloomed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert core to dictionary for serialization."""
        return {
            "x": self.x,
            "y": self.y,
            "temp_exposure_count": self.temp_exposure_count,
            "bloomed": self.bloomed,
            "refractory_countdown": self.refractory_countdown,
            "total_blooms": self.total_blooms,
            "last_bloom_tick": self.last_bloom_tick
        }


class KernelUniverseSimulation:
    """Main simulation class for Kernel Universe."""
    
    def __init__(self, seed=None):
        """Initialize the simulation with default parameters."""
        # Set random seed for reproducibility
        self.seed = seed if seed is not None else config.RNG_SEED
        self.rng = np.random.RandomState(self.seed)
        
        # Initialize simulation state
        self.reset()
    
    def reset(self):
        """Reset the simulation to initial state."""
        # Initialize tick counter
        self.tick = 0
        
        # Create temperature layer (lower)
        self.temperature = self.rng.random((config.GRID_SIZE, config.GRID_SIZE))
        
        # Create catalyst layer (upper)
        self.catalyst_upper = np.zeros((config.GRID_SIZE, config.GRID_SIZE))
        self.catalyst_lower = np.zeros((config.GRID_SIZE, config.GRID_SIZE))
        
        # Add initial catalyst to upper layer
        total_catalyst = config.GRID_SIZE * config.GRID_SIZE * 0.1  # 10% filled
        self.catalyst_upper = self.rng.random((config.GRID_SIZE, config.GRID_SIZE)) * 0.2
        
        # Initialize cores
        self.cores = []
        self.initialize_cores(config.INITIAL_CORES)
        
        # Statistics
        self.total_blooms = 0
        self.bloom_locations = []
        self.start_time = time.time()
    
    def initialize_cores(self, num_cores: int):
        """Initialize cores at random positions."""
        positions = set()
        for _ in range(num_cores):
            while True:
                x = self.rng.randint(0, config.GRID_SIZE)
                y = self.rng.randint(0, config.GRID_SIZE)
                if (x, y) not in positions:
                    positions.add((x, y))
                    self.cores.append(Core(x, y))
                    break
    
    def shift_temperature(self):
        """Shift temperature map to the right by one column."""
        # Shift right
        self.temperature = np.roll(self.temperature, 1, axis=1)
        
        # Generate new leftmost column
        self.temperature[:, 0] = self.rng.random(config.GRID_SIZE)
    
    def apply_convolution(self, input_array: np.ndarray, kernel: np.ndarray) -> np.ndarray:
        """Apply convolution with a given kernel."""
        output = np.zeros_like(input_array)
        pad_width = kernel.shape[0] // 2
        
        # Pad the input array
        padded = np.pad(input_array, pad_width, mode='wrap')
        
        # Apply convolution
        for i in range(config.GRID_SIZE):
            for j in range(config.GRID_SIZE):
                window = padded[i:i+kernel.shape[0], j:j+kernel.shape[1]]
                output[i, j] = np.sum(window * kernel)
        
        return output
    
    def advect_right(self, array: np.ndarray, alpha: float) -> np.ndarray:
        """Apply rightward advection to the array."""
        shifted = np.roll(array, 1, axis=1)
        return (1 - alpha) * array + alpha * shifted
    
    def step(self):
        """Execute one simulation step (tick)."""
        # Increment tick counter
        self.tick += 1
        
        # Determine mode: EMIT (even ticks) or COLLECT (odd ticks)
        emit_mode = (self.tick % 2 == 0)
        
        # Shift temperature map
        self.shift_temperature()
        
        # Execute catalyst mode logic
        if emit_mode:
            # EMIT mode: Move fraction of upper catalyst to lower
            transfer = self.catalyst_upper * config.EMIT_FRACTION
            self.catalyst_lower += transfer
            self.catalyst_upper -= transfer
        else:
            # COLLECT mode: Move all lower catalyst up, disperse with kernel, advect
            self.catalyst_upper += self.catalyst_lower
            self.catalyst_lower.fill(0)
            
            # Apply diffusion (3x3 kernel)
            self.catalyst_upper = self.apply_convolution(self.catalyst_upper, config.KERNEL_3x3)
            
            # Apply advection
            self.catalyst_upper = self.advect_right(self.catalyst_upper, config.ADVECT_ALPHA)
        
        # Bloom counter for this tick
        blooms_this_tick = 0
        
        # Update cores
        for core in self.cores:
            x, y = core.x, core.y
            temperature_at_core = self.temperature[y, x]
            catalyst_at_core = self.catalyst_upper[y, x]
            
            # Update core state
            did_bloom = core.update(
                self.tick, 
                temperature_at_core, 
                catalyst_at_core, 
                emit_mode
            )
            
            if did_bloom:
                blooms_this_tick += 1
                self.total_blooms += 1
                self.bloom_locations.append((x, y, self.tick))
                
                # Spawn new cores if configured
                if config.SPAWN_S > 0:
                    self.spawn_new_cores(x, y, config.SPAWN_S)
        
        # Check conservation of catalyst (debugging)
        total_catalyst = np.sum(self.catalyst_upper) + np.sum(self.catalyst_lower)
        
        # Return stats for this tick
        return {
            "tick": self.tick,
            "emit_mode": emit_mode,
            "blooms_this_tick": blooms_this_tick,
            "total_blooms": self.total_blooms,
            "total_catalyst": total_catalyst
        }
    
    def spawn_new_cores(self, parent_x: int, parent_y: int, count: int):
        """Spawn new cores near the parent core."""
        for _ in range(count):
            # Generate random position within 5 cells of parent
            dx = self.rng.randint(-5, 6)
            dy = self.rng.randint(-5, 6)
            
            new_x = (parent_x + dx) % config.GRID_SIZE
            new_y = (parent_y + dy) % config.GRID_SIZE
            
            # Add the new core
            self.cores.append(Core(new_x, new_y))
    
    def get_state(self) -> Dict[str, Any]:
        """Get the current state of the simulation."""
        return {
            "tick": self.tick,
            "temperature": self.temperature.tolist(),
            "catalyst_upper": self.catalyst_upper.tolist(),
            "catalyst_lower": self.catalyst_lower.tolist(),
            "cores": [core.to_dict() for core in self.cores],
            "total_blooms": self.total_blooms,
            "bloom_locations": self.bloom_locations,
            "runtime": time.time() - self.start_time
        }
    
    def set_parameter(self, param_name: str, value: Any) -> bool:
        """Update a configuration parameter."""
        if hasattr(config, param_name):
            setattr(config, param_name, value)
            return True
        return False