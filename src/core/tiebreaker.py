"""Tiebreaker class representing a tiebreaker in a tennis match."""

from copy                      import deepcopy
from typing                    import List, Literal, Optional
from src.core.tiebreaker_score import TiebreakerScore

class Tiebreaker:
    """
    Represents a tiebreaker in a tennis match.

    The tiebreaker need not start at 0-0; any valid initial score may be specified via
    the 'initScore' parameter. Standard or super-tiebreaker rules are determined by
    the 'isSuper' parameter.

    Attributes:
    -----------
    server: Literal[1,2]
        Which player serves the next point
    score: TiebreakerScore
        The current score of the tiebreaker
    isOver: bool
        Whether the tiebreaker is over
    winner: Optional[Literal[1,2]]
        Which player won the tiebreaker (1 or 2, but 'None' if the tiebreaker is not over)
    scoreHistory: str
        Formatted string representation of the tiebreaker score history.
    pointHistory: list[Literal[1,2]]
        Which player won each point (following the initial score); ex: [1, 1, 2, 1, 1]

    Methods:
    --------
    __init__(playerToServe: Literal[1, 2], initScore: Optional[TiebreakerScore]=None, isSuper: bool=False)
        Initialize a tiebreaker - any valid initial score may be specified.
    recordPoint(pointWinner: Literal[1, 2])
        Updates the tiebreaker state with the result of the next point.
    recordPoints(self, pointWinners: List[Literal[1, 2]])
        Update the tiebreaker state with the result of multiple points.
    __str__() -> str
        Formatted string representation of the current tiebreaker state.
    __repr__() -> str
        Valid Python expression that can be used to recreate this Tiebreaker instance.
    """

    def __init__(self,
                 playerToServe : Literal[1, 2],
                 initScore     : Optional[TiebreakerScore] = None,
                 isSuper       : bool = False,
                _shareInitScore: bool = False):
        """
        Initialize a tiebreaker - any valid initial score may be specified.

        Parameters:
        -----------
        playerToServe   - which player serves the next point in the tiebreaker (1 or 2)
        initScore       - initial tiebreaker score; if None, the score is initialized to 0-0
        isSuper         - True if this is a super-tiebreaker (default: False)
        _shareInitScore - whether to share the initScore object (use default value unless
                          you know what you are doing)
        """
        if playerToServe not in (1, 2):
            raise ValueError(f"Invalid playerToServe: {playerToServe}. Must be 1 or 2.")
        if initScore is not None and not isinstance(initScore, TiebreakerScore):
            raise ValueError(f"Invalid initScore: must be None or a TiebreakerScore instance.")
        if not isinstance(isSuper, bool):
            raise ValueError(f"Invalid isSuper: {isSuper}. Must be a boolean.")
        if initScore is not None and initScore._isSuper != isSuper:
            raise ValueError(f"initScore.isSuper ({initScore._isSuper}) must match isSuper ({isSuper}).")

        # figure out the starting score
        if initScore: scoreStart = initScore if _shareInitScore else deepcopy(initScore)
        else:         scoreStart = TiebreakerScore(0, 0, isSuper=isSuper)

        self.score       : TiebreakerScore          = scoreStart        # keeps track of the current score
        self.pointHistory: List[Literal[1, 2]]      = []                # which player won each point following 'initScore'
        self.server      : Literal[1, 2]            = playerToServe     # which player serves next point
        self._servedFirst: Literal[1, 2]            = playerToServe     # remember which player served first

        # string representation of the score history
        pServ, pRecv = self.score.asPoints(playerToServe)
        self._scoreHistory: str = (f"P{playerToServe} serves 1st\n"
                                   f"P{playerToServe} score: {pServ}-{pRecv}, ")

    @property
    def isOver(self) -> bool:
        """Whether the tiebreaker is over."""
        return self.score.isFinal

    @property
    def winner(self) -> Optional[Literal[1, 2]]:
        """Which player won the tiebreaker (1 or 2), or None if the tiebreaker is not over."""
        return self.score.winner

    @property
    def scoreHistory(self) -> str:
        """Formatted string representation of the tiebreaker score history, server score is displayed first."""
        return self._scoreHistory[:-2]

    def recordPoint(self, pointWinner: Literal[1, 2]):
        """
        Update the tiebreaker state with the result of the next point.

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

        # update which player serves next 
        totalPoints = self.score.asPoints(1)[0] + self.score.asPoints(1)[1]
        if totalPoints == 1:                                  # after first point, switch server
            self.server = 3 - self._servedFirst
        elif totalPoints > 1 and (totalPoints - 1) % 2 == 0:  # after that, switch every 2 points
            self.server = 3 - self.server

        # incrementally build the string representation of the score history
        pServ, pRecv = self.score.asPoints(self._servedFirst)
        self._scoreHistory += f"{pServ}-{pRecv}, "
        if self.isOver:
            self._scoreHistory = self._scoreHistory[:-2] + "\n"
            self._scoreHistory += f"P{self.winner} wins tiebreaker  "

    def recordPoints(self, pointWinners: List[Literal[1, 2]]):
        """
        Update the tiebreaker state with the result of multiple points.
        pointWinners - which player won each point (1 or 2)
        """
        for pointWinner in pointWinners:
            self.recordPoint(pointWinner)

    def __repr__(self) -> str:
        """
        String representation for debugging.
        Note: eval(repr(tiebreaker)) recreates the tiebreaker at its current score, but not the full point history.
        """
        return f"Tiebreaker(playerToServe={self.server}, initScore={repr(self.score)}, isSuper={self.score._isSuper})"

    def __str__(self) -> str:
        """
        Formatted string representation of the current tiebreaker state.
        """
        if not self.isOver:
            pServ, pRecv = self.score.asPoints(self.server)
            return f"Player{self.server} to serve at {pServ}-{pRecv}"
        else:
            pWin, pLoss = self.score.asPoints(self.winner)
            return f"Player{self.winner} wins tiebreaker: {pWin}-{pLoss}"
