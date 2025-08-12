"""
Tests for the Kernel Universe simulation.
"""

import numpy as np
import pytest

from kernel_universe.simulation import KernelUniverseSimulation, Core
from kernel_universe import config


def test_simulation_initialization():
    """Test that the simulation initializes correctly."""
    sim = KernelUniverseSimulation(seed=42)
    
    # Check dimensions
    assert sim.temperature.shape == (config.GRID_SIZE, config.GRID_SIZE)
    assert sim.catalyst_upper.shape == (config.GRID_SIZE, config.GRID_SIZE)
    assert sim.catalyst_lower.shape == (config.GRID_SIZE, config.GRID_SIZE)
    
    # Check that cores were created
    assert len(sim.cores) == config.INITIAL_CORES


def test_temperature_shift():
    """Test temperature shifting works correctly."""
    sim = KernelUniverseSimulation(seed=42)
    
    # Save the original first and second columns
    original_first_column = sim.temperature[:, 0].copy()
    original_second_column = sim.temperature[:, 1].copy()
    
    # Shift temperature
    sim.shift_temperature()
    
    # Check that columns shifted (second column should now be in the first)
    # Note: The first column is randomized, so we can't check it directly
    np.testing.assert_array_equal(sim.temperature[:, 1], original_first_column)
    np.testing.assert_array_equal(sim.temperature[:, 2], original_second_column)


def test_catalyst_conservation():
    """Test that catalyst is conserved during simulation steps."""
    sim = KernelUniverseSimulation(seed=42)
    
    # Get initial total catalyst
    initial_total = np.sum(sim.catalyst_upper) + np.sum(sim.catalyst_lower)
    
    # Run several steps
    for _ in range(10):
        sim.step()
        
        # Check total catalyst after step
        current_total = np.sum(sim.catalyst_upper) + np.sum(sim.catalyst_lower)
        
        # Should be approximately equal (allowing for floating-point errors)
        np.testing.assert_almost_equal(current_total, initial_total, decimal=5)


def test_core_bloom_conditions():
    """Test that cores bloom under the right conditions."""
    # Create a core
    core = Core(0, 0)
    
    # Test that core doesn't bloom without meeting all conditions
    assert not core.update(tick=2, temperature=config.T_MIN + 0.01, catalyst=0, emit_mode=True)
    
    # Test temperature exposure counting
    for i in range(config.TAU_TEMP - 1):
        assert not core.update(
            tick=2*i, 
            temperature=config.T_MIN + 0.01, 
            catalyst=config.C_THRESH + 0.1, 
            emit_mode=True
        )
        assert core.temp_exposure_count == i + 1
    
    # Should bloom on the final exposure with sufficient catalyst
    assert core.update(
        tick=2*config.TAU_TEMP, 
        temperature=config.T_MIN + 0.01, 
        catalyst=config.C_THRESH + 0.1, 
        emit_mode=True
    )
    
    # Should be in refractory period
    assert core.refractory_countdown == config.TAU_REFRACT
    
    # Should not bloom while in refractory period
    assert not core.update(
        tick=2*config.TAU_TEMP + 2, 
        temperature=config.T_MIN + 0.01, 
        catalyst=config.C_THRESH + 0.1, 
        emit_mode=True
    )