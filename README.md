# Kernel Universe

A continuous 2D simulation of a simplified universe where cores can bloom into energy under specific conditions. This project serves as a testbed for studying self-organizing systems and potentially emergent behavior (a "kernel" of artificial consciousness).

## Project Overview

### Core Concepts

* **Two 2D layers** (100×100 grids):
  1. **Lower layer** — temperature map (float ∈ [0,1]), shifts right each tick.
  2. **Upper layer** — catalyst concentration (float ≥ 0), alternates between:
     * **EMIT mode** (even ticks): sends a fraction of its catalyst to the lower layer.
     * **COLLECT mode** (odd ticks): collects free catalyst from the lower layer, disperses it to neighbors (via 3×3 kernel), optional advection to the right.

* **Cores**:
  * Fixed positions in the lower layer.
  * **Bloom** into energy if:
    * Current tick is EMIT.
    * Catalyst above ≥ threshold.
    * Temperature within a range for N consecutive ticks.
  * After blooming: refractory cooldown before they can catalyze again.

* **Catalyst conservation**:
  * Strict mass conservation between upper/lower layers.
  * Catalyst values are floats, not binary.

## Tech Stack

* **Python** (simulation engine)
* **Numpy** — array updates
* **FastAPI** — REST + WebSocket API for real-time streaming
* **Redis** — store latest simulation state
* **Frontend** — React/Next.js with canvas (Pixi.js) for smooth rendering
* **Docker** — for cloud deployment

## Getting Started

### Prerequisites

- Python 3.9+
- Docker and Docker Compose (for deployment)
- Node.js 16+ (for frontend development)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/alihanbolat/kernel-universe.git
   cd kernel-universe
   ```

2. Set up a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Run the simulation locally:
   ```bash
   python -m kernel_universe.server
   ```

4. Access the API at `http://localhost:8000`

### Docker Deployment

```bash
docker-compose up -d
```

## API Endpoints

- `GET /snapshot` — Get the latest simulation state
- `WS /stream` — WebSocket for streaming frame updates
- `POST /control` — Update simulation parameters

## Configuration

Default simulation parameters are defined in `kernel_universe/config.py`. These can be modified either by editing the file or through the API.

## License

[MIT](LICENSE)