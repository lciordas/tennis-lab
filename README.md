# Tennis Lab

A Python library for tennis analytics, quantitative models, and Monte Carlo simulations.

## Features

- **Core tennis scoring**: Classes for tracking game, tiebreak, set, and match scores
- **Match simulation**: Monte Carlo simulation of tennis matches
- **Probability calculations**: Compute win probabilities at any scoring state (game, tiebreak, set, match)
- **Path analysis**: Enumerate and analyze possible score progressions

## Installation

```bash
pip install git+https://github.com/lciordas/tennis-lab.git
```

For development:

```bash
git clone https://github.com/lciordas/tennis-lab.git
cd tennis-lab
pip install -e ".[dev,notebooks]"
```

## Usage

```python
from tennis_lab.core import GameScore, Match, MatchFormat
from tennis_lab.paths import probabilityServerWinsGame, probabilityP1WinsMatch
```

## Examples

See the [examples/](examples/) directory for Jupyter notebooks demonstrating the library:

| Notebook | Description |
|----------|-------------|
| [0 - Tennis Lab Core Components](examples/0%20-%20Tennis%20Lab%20Core%20Components.ipynb) | Introduction to core scoring classes |
| [1 - Game Win Probability](examples/1%20-%20Game%20Win%20Probability.ipynb) | Probability calculations within a game |
| [2 - Tiebreak Win Probability](examples/2%20-%20Tiebreak%20Win%20Probability.ipynb) | Probability calculations for tiebreaks |
| [3 - Set Win Probability](examples/3%20-%20Set%20Win%20Probability.ipynb) | Probability calculations for sets |
| [4 - Match Win Probability](examples/4%20-%20Match%20Win%20Probability.ipynb) | Probability calculations for full matches |
| [Serve & Height](examples/Serve%20%26%20Height.ipynb) | Analysis of serve performance and player height |

## Development

Run tests:

```bash
pytest
```

## License

MIT
