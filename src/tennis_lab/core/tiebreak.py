"""Tiebreak class representing a tiebreak in a tennis match."""

from copy                    import deepcopy
from typing                  import List, Literal, Optional
from tennis_lab.core.match_format   import MatchFormat
from tennis_lab.core.tiebreak_score import TiebreakScore

class Tiebreak:
    """
    Represents a tiebreak in a tennis match.

    The tiebreak need not start at 0-0; any valid initial score may be specified via
    the 'initScore' parameter. Standard or super-tiebreak rules are determined by
    the 'isSuper' parameter.

    Attributes:
    -----------
    score: TiebreakScore
        The current score of the tiebreak
    servesNext: Literal[1,2]
        Which player serves the next point
    isOver: bool
        Whether the tiebreak is over
    winner: Optional[Literal[1,2]]
        Which player won the tiebreak (1 or 2, but 'None' if the tiebreak is not over)
    scoreHistory: str
        Formatted string representation of the tiebreak score history.
    pointHistory: list[Literal[1,2]]
        Which player won each point (following the initial score); ex: [1, 1, 2, 1, 1]

    Methods:
    --------
    __init__(playerToServe: Literal[1, 2], isSuper: bool, initScore: Optional[TiebreakScore]=None, matchFormat: Optional[MatchFormat]=None)
        Initialize a tiebreak - any valid initial score may be specified.
    recordPoint(pointWinner: Literal[1, 2])
        Updates the tiebreak state with the result of the next point.
    recordPoints(self, pointWinners: List[Literal[1, 2]])
        Update the tiebreak state with the result of multiple points.
    __str__() -> str
        Formatted string representation of the current tiebreak state.
    __repr__() -> str
        Valid Python expression that can be used to recreate this Tiebreak instance.
    """

    def __init__(self,
                 playerToServe : Literal[1, 2],
                 isSuper       : bool,
                 initScore     : Optional[TiebreakScore] = None,
                 matchFormat   : Optional[MatchFormat]   = None,
                _shareInitScore: bool                    = False):
        """
        Initialize a tiebreak - any valid initial score may be specified.

        Parameters:
        -----------
        playerToServe  - which player serves the next point in the tiebreak (1 or 2)
        isSuper        - True if this is a super-tiebreak
        initScore      - initial tiebreak score; if None, the score is initialized to 0-0
        matchFormat    - describes the match format; required if 'initScore' is None
       _shareInitScore - whether to share the initScore object (use default value unless
                         you know what you are doing)

        Raises:
        -------
        ValueError - if inputs are invalid or inconsistent
        """
        if playerToServe not in (1, 2):
            raise ValueError(f"Invalid playerToServe: {playerToServe}. Must be 1 or 2.")
        if initScore is not None and not isinstance(initScore, TiebreakScore):
            raise ValueError(f"Invalid initScore: must be None or a TiebreakScore instance.")
        if not isinstance(isSuper, bool):
            raise ValueError(f"Invalid isSuper: {isSuper}. Must be a boolean.")
        if matchFormat is not None and not isinstance(matchFormat, MatchFormat):
            raise ValueError(f"Invalid matchFormat: must be None or a MatchFormat instance.")
        if initScore is None and matchFormat is None:
            raise ValueError("matchFormat is required when initScore is None.")
        if initScore is not None and initScore._isSuper != isSuper:
            raise ValueError(f"initScore.isSuper ({initScore._isSuper}) must match isSuper ({isSuper}).")
        if initScore is not None and matchFormat is not None:
            if initScore._matchFormat != matchFormat:
                raise ValueError("initScore.matchFormat must match matchFormat.")

        # figure out the starting score
        if initScore: scoreStart = initScore if _shareInitScore else deepcopy(initScore)
        else:         scoreStart = TiebreakScore(0, 0, isSuper=isSuper, matchFormat=matchFormat)

        self.score       : TiebreakScore       = scoreStart        # keeps track of the current score
        self.pointHistory: List[Literal[1, 2]] = []                # which player won each point following 'initScore'
        self.servesNext  : Literal[1, 2]       = playerToServe     # which player serves next point
        self._servedFirst: Literal[1, 2]       = playerToServe     # remember which player served first

        # string representation of the score history
        pServ, pRecv = self.score.asPoints(playerToServe)
        self._scoreHistory: str = (f"P{playerToServe} serves 1st\n"
                                   f"P{playerToServe} score: {pServ}-{pRecv}, ")

    @property
    def isOver(self) -> bool:
        """Whether the tiebreak is over."""
        return self.score.isFinal

    @property
    def winner(self) -> Optional[Literal[1, 2]]:
        """Which player won the tiebreak (1 or 2), or None if the tiebreak is not over."""
        return self.score.winner

    @property
    def scoreHistory(self) -> str:
        """Formatted string representation of the tiebreak score history, server score is displayed first."""
        return self._scoreHistory[:-2]

    def recordPoint(self, pointWinner: Literal[1, 2]):
        """
        Update the tiebreak state with the result of the next point.

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
            self.servesNext = 3 - self._servedFirst
        elif totalPoints > 1 and (totalPoints - 1) % 2 == 0:  # after that, switch every 2 points
            self.servesNext = 3 - self.servesNext

        # incrementally build the string representation of the score history
        pServ, pRecv = self.score.asPoints(self._servedFirst)
        self._scoreHistory += f"{pServ}-{pRecv}, "
        if self.isOver:
            self._scoreHistory = self._scoreHistory[:-2] + "\n"
            self._scoreHistory += f"P{self.winner} wins tiebreak  "

    def recordPoints(self, pointWinners: List[Literal[1, 2]]):
        """
        Update the tiebreak state with the result of multiple points.
        pointWinners - which player won each point (1 or 2)
        """
        for pointWinner in pointWinners:
            self.recordPoint(pointWinner)

    def __repr__(self) -> str:
        """
        String representation for debugging.
        Note: eval(repr(tiebreak)) recreates the tiebreak at its current score, but not the full point history.
        """
        return f"Tiebreak(playerToServe={self.servesNext}, isSuper={self.score._isSuper}, initScore={repr(self.score)})"

    def __str__(self) -> str:
        """
        Formatted string representation of the current tiebreak state.
        """
        if not self.isOver:
            pServ, pRecv = self.score.asPoints(self.servesNext)
            return f"Player{self.servesNext} to serve at {pServ}-{pRecv}"
        else:
            pWin, pLoss = self.score.asPoints(self.winner)
            return f"Player{self.winner} wins tiebreak: {pWin}-{pLoss}"
