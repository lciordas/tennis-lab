"""Match class representing an entire tennis match."""

from copy   import deepcopy
from typing import List, Literal, Optional

from tennis_lab.core.match_format import MatchFormat
from tennis_lab.core.match_score  import MatchScore
from tennis_lab.core.set          import Set

class Match:
    """
    Represents an entire tennis match.

    The match need not start at 0-0; any valid initial score may be specified.
    Its state is updated incrementally, one point at a time. Based on these
    updates, the Match instance updates the current score, keeping track of
    games, tiebreaks, sets, and the match itself. The current score, as well
    as the score history, can be queried at any time.

    Attributes:
    -----------
    score: MatchScore
        The current score of the match.
    servesNext: Literal[1, 2]
        Which player serves the next point.
    isOver: bool
        Whether the match is over.
    winner: Optional[Literal[1,2]]
        Which player won the match (1 or 2, but 'None' if the match is not over).
    currentSet: Optional[Set]
        The set in progress (if any).
    totalPoints: tuple[int, int]
        Current total # points won in this match by each player.
    setHistory: list[Set]
        The sets that have been completed so far in this match.
    pointHistory: list[Literal[1,2]]
        Which player won each point ex: [1, 1, 2, ...]
    matchFormat: MatchFormat
        The match format for this match.

    Methods:
    --------
    recordPoint(pointWinner: Literal[1, 2])
        Updates the match state with the result of the next point.
    recordPoints(pointWinners: list[Literal[1, 2]])
        Update the match state with the result of multiple points.
    scoreHistory() -> str
        Formatted string representation of the match score history.
    __str__() -> str
        Formatted string representation of the current match state.
    __repr__() -> str
        Valid Python expression that can be used to recreate this Match instance.
    """

    def __init__(self,
                 playerServing : Literal[1, 2],
                 matchFormat   : Optional[MatchFormat] = None,
                 initScore     : Optional[MatchScore]  = None,
                _shareInitScore: bool                  = False):
        """
        Initialize a match - any valid initial score may be specified.

        Parameters:
        -----------
        playerServing  - which player serves first in this match (1 or 2)
        matchFormat    - describes the match format; required if 'initScore' is None
        initScore      - initial match score; if None, the score is initialized to 0-0
       _shareInitScore - whether to share the initScore object (use default value unless
                         you know what you are doing)

        Raises:
        -------
        ValueError - if any of the inputs are invalid or mismatched
        """
        if playerServing not in (1, 2):
            raise ValueError(f"Invalid playerServing: {playerServing}. Must be 1 or 2.")
        if matchFormat is not None and not isinstance(matchFormat, MatchFormat):
            raise ValueError(f"Invalid matchFormat: must be None or a MatchFormat instance.")
        if initScore is not None and not isinstance(initScore, MatchScore):
            raise ValueError(f"Invalid initScore: must be None or a MatchScore instance.")
        if initScore is None and matchFormat is None:
            raise ValueError("matchFormat is required when initScore is None.")
        if initScore is not None and matchFormat is not None:
            if initScore._matchFormat != matchFormat:
                raise ValueError("initScore.matchFormat must match matchFormat.")

        self._matchFormat: MatchFormat = matchFormat if matchFormat else initScore._matchFormat

        # figure out the starting score
        if initScore: scoreStart = initScore if _shareInitScore else deepcopy(initScore)
        else:         scoreStart = MatchScore(0, 0, matchFormat)

        self.score     : MatchScore = scoreStart             # keeps track of the current score
        self._initScore: MatchScore = deepcopy(initScore)    # remember the initial score

        # object that represents the set being played next (if any)
        # Note the '_shareInitScore=True' argument.        
        self.currentSet: Optional[Set] = None
        if not self.score.isFinal:
            self.currentSet = Set(playerServing, self.score._isFinalSet(), self.score.currSetScore,
                                  self._matchFormat, _shareInitScore=True)

        self.setHistory: List[Set] = []  # completed Set instances

    @property
    def servesNext(self) -> Literal[1, 2]:
        """Which player serves the next point."""
        if self.isOver:
            # match is over, return who would serve next set, if another 
            # one would be played (flip the last server from the last set)
            lastSet = self.setHistory[-1]
            return 3 - lastSet.servesNext
        return self.currentSet.servesNext

    @property
    def isOver(self) -> bool:
        """Predicate which indicates whether the match is over."""
        return self.score.isFinal

    @property
    def winner(self) -> Optional[Literal[1, 2]]:
        """Which player won the match (1 or 2), or None if the match is not over."""
        return self.score.winner

    @property
    def pointHistory(self) -> list[Literal[1, 2]]:
        """
        Which player won each point ex: [1, 1, 2, ...]
        """
        points = [myset.pointHistory for myset in self.setHistory]
        if self.currentSet is not None:
            points.append(self.currentSet.pointHistory)
        return sum(points, [])

    @property
    def totalPoints(self) -> tuple[int, int]:
        """
        Current total # points won in this match by each player.
        """
        points = [myset.totalPoints for myset in self.setHistory]
        if self.currentSet is not None:
            points.append(self.currentSet.totalPoints)
        return sum([p[0] for p in points]), sum([p[1] for p in points])

    @property
    def matchFormat(self) -> MatchFormat:
        """The match format for this match."""
        return self._matchFormat

    def recordPoint(self, pointWinner: Literal[1, 2]):
        """
        Updates the match state with the result of the next point.
        pointWinner - which player won the point (1 or 2)
        """
        if pointWinner not in (1, 2):
            raise ValueError(f"Invalid pointWinner: {pointWinner}. Must be 1 or 2.")
        if self.isOver:
            return

        self.currentSet.recordPoint(pointWinner)

        # handle set completion
        if self.currentSet.isOver:

            # archive the completed set and determine next server
            self.setHistory.append(self.currentSet)
            servingNext = 3 - self.currentSet.servesNext

            # update the match score at the set granularity level
            # NOTE: at the point/game level, it has been updated via the shared SetScore object
            self.score._recordSet(self.currentSet.winner)

            if self.isOver:
                self.currentSet = None
            else:
                self.currentSet = Set(servingNext, self.score._isFinalSet(), self.score.currSetScore,
                                      self._matchFormat, _shareInitScore=True)

    def recordPoints(self, pointWinners: list[Literal[1, 2]]):
        """
        Update the match state with the result of multiple points.
        pointWinners - which player won each point (1 or 2)
        """
        for pointWinner in pointWinners:
            self.recordPoint(pointWinner)

    def scoreHistory(self) -> str:
        """
        Formatted string representation of the match score history.
        """
        s = ""
        sets1, sets2 = self._initScore.sets(pov=1) if self._initScore else (0, 0)
        setOffset = sets1 + sets2

        for idx, tennisSet in enumerate(self.setHistory):
            if tennisSet.winner == 1:
                sets1 += 1
            else:
                sets2 += 1
            s += f"Set #{setOffset + idx + 1}: \n\n"
            s += tennisSet.scoreHistory()
            s += f" #{setOffset + idx + 1}, score {sets1}-{sets2} for P1.\n\n"

        if self.currentSet is not None:
            s += f"Set #{self.score.setsPlayer1 + self.score.setsPlayer2 + 1}: \n\n"
            s += self.currentSet.scoreHistory()
        return s

    def __str__(self) -> str:
        """
        Formatted string representation of the current match state.
        """
        pov = self.servesNext

        s = f"Player{self.winner} wins match: " if self.isOver else \
            f"Player{pov} to serve at "

        # get the set score
        setsFirst, setsSecond = self.score.sets(pov)
        s += f"{setsFirst}-{setsSecond}"

        # if in the middle of a set, get the game score
        if self.currentSet is not None:
            gamesFirst, gamesSecond = self.currentSet.score.games(pov)
            s += f", {gamesFirst}-{gamesSecond}"

            # if in the middle of a game, get the point score
            if self.currentSet.currentGame is not None:
                s += f", " + self.currentSet.currentGame.score.asTraditional(pov)

            # if in the middle of a tiebreak, get the point score
            if self.currentSet.tiebreaker is not None:
                pointsFirst, pointsSecond = self.currentSet.tiebreaker.score.asPoints(pov)
                s += f", {pointsFirst}-{pointsSecond}"

        return s

    def __repr__(self) -> str:
        """
        Valid Python expression that can be used to recreate this Match instance.
        """
        return f"Match(playerServing={self.servesNext}, " \
               f"matchFormat={repr(self._matchFormat)}, initScore={repr(self.score)})"
