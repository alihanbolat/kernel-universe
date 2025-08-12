"""
Command-line interface for Kernel Universe.
"""

import argparse
import asyncio
import os
import time
from typing import Dict, Any

from . import config
from .simulation import KernelUniverseSimulation


def run_headless(steps: int, output_file: str = None):
    """Run the simulation in headless mode for a specified number of steps."""
    print(f"Running simulation for {steps} steps...")
    
    # Initialize simulation
    sim = KernelUniverseSimulation()
    
    # Run steps
    stats = []
    for i in range(steps):
        if i % 100 == 0:
            print(f"Step {i}/{steps}")
        
        # Run step and collect stats
        step_stats = sim.step()
        stats.append(step_stats)
    
    # Output results
    print(f"Simulation completed: {steps} steps")
    print(f"Total blooms: {sim.total_blooms}")
    
    # Save stats if requested
    if output_file:
        import json
        with open(output_file, 'w') as f:
            json.dump(stats, f)
        print(f"Statistics saved to {output_file}")


def run_server():
    """Run the FastAPI server."""
    import uvicorn
    print("Starting Kernel Universe server...")
    uvicorn.run("kernel_universe.server:app", host=config.API_HOST, port=config.API_PORT)


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Kernel Universe Simulation")
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Headless command
    headless_parser = subparsers.add_parser("headless", help="Run simulation in headless mode")
    headless_parser.add_argument("--steps", type=int, default=1000, help="Number of steps to run")
    headless_parser.add_argument("--output", type=str, help="Output file for statistics")
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Run the API server")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    if args.command == "headless":
        run_headless(args.steps, args.output)
    elif args.command == "server":
        run_server()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()