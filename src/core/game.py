"""Game class representing a tennis game."""

from copy                import deepcopy
from typing              import List, Literal, Optional
from src.core.game_score import GameScore

class Game:
    """
    Represents a game in a tennis match.

    The game need not start at 0-0; any valid initial score may be specified via
    the 'initScore' parameter. Scoring rules (standard or 'no-ad') are determined by
    the 'initScore's settings; if no 'initScore' is provided, standard scoring is used.

    Attributes:
    -----------
    server: Literal[1,2]
        Which player serves this game
    score: GameScore
        The current score of the game
    isOver: bool
        Whether the game is over
    winner: Optional[Literal[1,2]]
        Which player won the game (1 or 2, but 'None' if the game is not over)
    scoreHistory: str
        Formatted string representation of the game score history.
    pointHistory: list[Literal[1,2]]
        Which player won each point (following the initial score); ex: [1, 1, 2, 1, 1]

    Methods:
    --------
    __init__(playerToServe: Literal[1, 2], initScore: Optional[GameScore]=None)
        Initialize a game - any valid initial score may be specified.
    recordPoint(pointWinner: Literal[1, 2])
        Updates the game state with the result of the next point.
    recordPoints(self, pointWinners: List[Literal[1, 2]])
        Update the game state with the result of multiple points.
    __str__() -> str
        Formatted string representation of the current game state.
    __repr__() -> str
        Valid Python expression that can be used to recreate this Game instance.
    """

    def __init__(self,
                 playerToServe : Literal[1, 2],
                 initScore     : Optional[GameScore]=None,
                _shareInitScore: bool = False):
        """
        Initialize a game - any valid initial score may be specified.

        By default we create a game where standard scoring rules apply. If you want 
        to customize it (for example - use the 'no ad' rule, you can do this via the 
        initial score object you pass to __init__).

        Parameters:
        -----------
        playerToServe   - which player serves this game (1 or 2)
        initScore       - initial game score; if None, the score is initialized to 0-0
        _shareInitScore - whether to share the initScore object (use default value unless
                          you know what you are doing)
        """
        if playerToServe not in (1, 2):
            raise ValueError(f"Invalid playerToServe: {playerToServe}. Must be 1 or 2.")
        if initScore is not None and not isinstance(initScore, GameScore):
            raise ValueError(f"Invalid initScore: must be None or a GameScore instance.")

        # figure out the starting score
        if initScore: scoreStart = initScore if _shareInitScore else deepcopy(initScore)
        else:         scoreStart = GameScore(0, 0, noAdRule=False)

        self.score       : GameScore              = scoreStart        # keeps track of the current score
        self.pointHistory: List[Literal[1,2]]     = []                # which player won each point following 'initScore'
        self.server      : Literal[1,2]           = playerToServe     # which player serves this game

        # string representation of the score history
        self._scoreHistory: str = (f"P{playerToServe} serves\nP{playerToServe} "
                                   f"score: {self.score.asTraditional(self.server)}, ")

    @property
    def isOver(self) -> bool:
        """Whether the game is over."""
        return self.score.isFinal

    @property
    def winner(self) -> Optional[Literal[1, 2]]:
        """Which player won the game (1 or 2), or None if the game is not over."""
        return self.score.winner

    @property
    def scoreHistory(self) -> str:
        """Formatted string representation of the game score history, server score is displayed first."""
        return self._scoreHistory[:-2]

    def recordPoint(self, pointWinner: Literal[1, 2]):
        """
        Update the game state with the result of the next point.

        Parameters:
        -----------
        pointWinner - which player won the point (1 or 2)
        """
        if pointWinner not in (1, 2):
            raise ValueError(f"Invalid pointWinner: {pointWinner}. Must be 1 or 2.")
        if self.isOver:
            return

        # update the current score and the point history
        self.score.recordPoint(pointWinner)
        self.pointHistory.append(pointWinner)

        # incrementally built the string representation of the score history
        self._scoreHistory += self.score.asTraditional(self.server) + ", "
        if self.isOver:
            self._scoreHistory  = self._scoreHistory[:-2] + "\n"
            self._scoreHistory += f"P{self.winner} wins game  "

    def recordPoints(self, pointWinners: list[Literal[1, 2]]):
        """
        Update the game state with the result of multiple points.
        pointWinners - which player won each point (1 or 2)
        """
        for pointWinner in pointWinners:
            self.recordPoint(pointWinner)

    def __repr__(self) -> str:
        """
        String representation for debugging. 
        Note: eval(repr(game)) recreates the game at its current score, but not the full point history.
        """
        return f"Game(playerToServe={self.server}, initScore={repr(self.score)})"

    def __str__(self) -> str:
        """
        Formatted string representation of the current game state.
        """
        if not self.isOver:
            return f"Player{self.server} to serve at {self.score.asTraditional(self.server)}"
        else:
            return f"Player{self.winner} wins game: {self.score.asTraditional(self.server)}"
