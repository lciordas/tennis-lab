"""MatchFormat class descriging the format for a given tennis match."""

from enum import Enum
from typing import Optional

# Points needed to win a tiebreak or super-tiebreak
POINTS_TO_WIN_TIEBREAK      =  7
POINTS_TO_WIN_SUPERTIEBREAK = 10

class SetEnding(Enum):
    """
    How a set ends when tied (example at 6-6 in a standard set).
    """
    ADVANTAGE     = "advantage"      # play until someone leads by 2 games
    TIEBREAK      = "tiebreak"       # standard tiebreak 
    SUPERTIEBREAK = "supertiebreak"  # super tiebreak

class MatchFormat:
    """
    All parameters needed to describe the format of a tennis match.

    Attributes:
    -----------
    bestOfSets: Optional[int]
        Maximum number of sets in the match (None if not specified).
    matchTiebreak: bool
        Whether a match tiebreak replaces the final set when tied at sets (default: False)
    setLength: int
        Number of games needed to win a set (default: 6)
    setEnding: SetEnding
        How a (non-final) set ends when tied (default: SetEnding.TIEBREAK)
    finalSetEnding: SetEnding
        How the final set ends when tied (default: SetEnding.TIEBREAK)
    noAdRule: bool
        Whether games use the 'no ad' rule (default: False)
    capPoints: bool
        Whether to represent all deuces as 3-3 and all adds as 3-4 or 4-3. (default: True)
    """

    def __init__(self,
                 bestOfSets    : Optional[int] = None,
                 matchTiebreak : bool          = False,
                 setLength     : int           = 6,
                 setEnding     : SetEnding     = SetEnding.TIEBREAK,
                 finalSetEnding: SetEnding     = SetEnding.TIEBREAK,
                 noAdRule      : bool          = False,
                 capPoints     : bool          = True):
        """
        Initialize match format with scoring rules.

        Parameters:
        -----------
        bestOfSets     - max number of sets in the match (usually 3 or 5), or None if not needed
        matchTiebreak  - whether a match tiebreak replaces the final set when tied at sets (default: False)
        setLength      - number of games needed to win a set (default: 6)
        setEnding      - how a (non-final) set ends when tied (default: SetEnding.TIEBREAK)
        finalSetEnding - how the final set ends when tied (default: SetEnding.TIEBREAK)
        noAdRule       - whether games use the 'no ad' rule (default: False)
        capPoints      - whether to represent all deuces as 3-3 and all adds as 3-4 or 4-3 (default: True)

        Raises:
        -------
        ValueError - if any of the inputs are invalid
        """
        if bestOfSets is not None and (not isinstance(bestOfSets, int) or bestOfSets < 1):
            raise ValueError(f"Invalid bestOfSets: {bestOfSets}. Must be None or a positive integer.")
        if not isinstance(matchTiebreak, bool):
            raise ValueError(f"Invalid matchTiebreak: {matchTiebreak}. Must be a boolean.")
        if not isinstance(setLength, int) or setLength < 1:
            raise ValueError(f"Invalid setLength: {setLength}. Must be a positive integer.")
        if not isinstance(setEnding, SetEnding):
            raise ValueError(f"Invalid setEnding: {setEnding}. Must be a SetEnding instance.")
        if not isinstance(finalSetEnding, SetEnding):
            raise ValueError(f"Invalid finalSetEnding: {finalSetEnding}. Must be a SetEnding instance.")
        if not isinstance(noAdRule, bool):
            raise ValueError(f"Invalid noAdRule: {noAdRule}. Must be a boolean.")
        if not isinstance(capPoints, bool):
            raise ValueError(f"Invalid capPoints: {capPoints}. Must be a boolean.")

        self.bestOfSets    : Optional[int] = bestOfSets
        self.matchTiebreak : bool          = matchTiebreak
        self.setLength     : int           = setLength
        self.setEnding     : SetEnding     = setEnding
        self.finalSetEnding: SetEnding     = finalSetEnding
        self.noAdRule      : bool          = noAdRule
        self.capPoints     : bool          = capPoints

    def __repr__(self) -> str:
        """Valid Python expression that can be used to recreate this MatchFormat instance."""
        return (f"MatchFormat(bestOfSets={self.bestOfSets}, matchTiebreak={self.matchTiebreak}, "
                f"setLength={self.setLength}, setEnding={self.setEnding}, finalSetEnding={self.finalSetEnding}, "
                f"noAdRule={self.noAdRule}, capPoints={self.capPoints})")

    def __str__(self) -> str:
        """Human-readable description of the match format."""
        return (f"Match Format:\n"
                f"  bestOfSets    : {self.bestOfSets}\n"
                f"  matchTiebreak : {self.matchTiebreak}\n"
                f"  setLength     : {self.setLength}\n"
                f"  setEnding     : {self.setEnding.value}\n"
                f"  finalSetEnding: {self.finalSetEnding.value}\n"
                f"  noAdRule      : {self.noAdRule}\n"
                f"  capPoints     : {self.capPoints}")

    def __eq__(self, other) -> bool:
        """Check equality between two MatchFormat instances."""
        if not isinstance(other, MatchFormat):
            return False
        return (self.bestOfSets     == other.bestOfSets     and
                self.matchTiebreak  == other.matchTiebreak  and
                self.setLength      == other.setLength      and
                self.setEnding      == other.setEnding      and
                self.finalSetEnding == other.finalSetEnding and
                self.noAdRule       == other.noAdRule       and
                self.capPoints      == other.capPoints)

    def __hash__(self) -> int:
        return hash((self.bestOfSets, self.matchTiebreak, self.setLength,
                     self.setEnding, self.finalSetEnding, self.noAdRule, self.capPoints))
