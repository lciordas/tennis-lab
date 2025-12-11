"""Tests for the Match class."""

import pytest
from tennis_lab.core.match         import Match
from tennis_lab.core.match_score   import MatchScore
from tennis_lab.core.set_score     import SetScore
from tennis_lab.core.game_score    import GameScore
from tennis_lab.core.tiebreak_score import TiebreakScore
from tennis_lab.core.match_format  import MatchFormat, SetEnding

# Default match formats for tests
DEFAULT_FORMAT = MatchFormat(bestOfSets=3)
BEST_OF_5      = MatchFormat(bestOfSets=5)
NO_AD_FORMAT   = MatchFormat(bestOfSets=3, noAdRule=True)


# Helper function: points needed to win a game (player wins all points)
def win_game(m: Match, player: int):
    """Record 4 points for the given player to win a game."""
    m.recordPoints([player] * 4)


# Helper function: win a set 6-0
def win_set(m: Match, player: int):
    """Record points for the given player to win a set 6-0."""
    for _ in range(6):
        win_game(m, player)


# Helper function: get to 6-6 in current set (tiebreak)
def get_to_tiebreak(m: Match):
    """Play games until the current set reaches 6-6."""
    for game_num in range(12):
        if game_num % 2 == 0:
            win_game(m, 1)
        else:
            win_game(m, 2)


class TestMatchInit:
    """Tests for Match initialization."""

    def test_init_default_score(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        assert m.servesNext == 1
        assert m.score.sets(1) == (0, 0)
        assert m.setHistory == []
        assert not m.isOver
        assert m.winner is None
        assert m.currentSet is not None

    def test_init_player2_serves(self):
        m = Match(playerServing=2, matchFormat=DEFAULT_FORMAT)
        assert m.servesNext == 2

    def test_init_best_of_3(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        assert m._matchFormat.bestOfSets == 3

    def test_init_best_of_5(self):
        m = Match(playerServing=1, matchFormat=BEST_OF_5)
        assert m._matchFormat.bestOfSets == 5

    def test_init_with_custom_score(self):
        init_score = MatchScore(1, 0, DEFAULT_FORMAT)
        m = Match(playerServing=1, initScore=init_score)
        assert m.score.sets(1) == (1, 0)

    def test_init_invalid_server(self):
        with pytest.raises(ValueError):
            Match(playerServing=0, matchFormat=DEFAULT_FORMAT)
        with pytest.raises(ValueError):
            Match(playerServing=3, matchFormat=DEFAULT_FORMAT)

    def test_init_invalid_score_type(self):
        with pytest.raises(ValueError):
            Match(playerServing=1, initScore="invalid", matchFormat=DEFAULT_FORMAT)

    def test_init_missing_matchFormat(self):
        with pytest.raises(ValueError):
            Match(playerServing=1)

    def test_init_mismatched_matchFormat(self):
        init_score = MatchScore(1, 0, DEFAULT_FORMAT)
        with pytest.raises(ValueError):
            Match(playerServing=1, initScore=init_score, matchFormat=BEST_OF_5)

    def test_init_deep_copies_score(self):
        init_score = MatchScore(1, 0, DEFAULT_FORMAT)
        m = Match(playerServing=1, initScore=init_score)
        win_set(m, 1)  # Win another set
        # Original should be unchanged
        assert init_score.sets(1) == (1, 0)
        assert m.score.sets(1) == (2, 0)

    def test_init_with_final_match_score(self):
        """Match already won shouldn't have a current set."""
        init_score = MatchScore(2, 0, DEFAULT_FORMAT)
        m = Match(playerServing=1, initScore=init_score)
        assert m.isOver
        assert m.currentSet is None


class TestMatchRecordPoint:
    """Tests for recordPoint method."""

    def test_record_single_point(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        m.recordPoint(1)
        assert m.currentSet.currentGame.score.asPoints(1) == (1, 0)
        assert m.pointHistory == [1]

    def test_record_multiple_points(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        m.recordPoints([1, 2, 1])
        assert m.currentSet.currentGame.score.asPoints(1) == (2, 1)
        assert m.pointHistory == [1, 2, 1]

    def test_record_point_invalid(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        with pytest.raises(ValueError):
            m.recordPoint(0)
        with pytest.raises(ValueError):
            m.recordPoint(3)

    def test_record_point_after_match_over(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        # P1 wins 2-0
        win_set(m, 1)
        win_set(m, 1)
        assert m.isOver
        initial_history = m.pointHistory.copy()

        # Additional points should be ignored
        m.recordPoint(2)
        assert m.pointHistory == initial_history


class TestMatchRecordPoints:
    """Tests for recordPoints method."""

    def test_record_points_basic(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        m.recordPoints([1, 2, 1, 2])
        assert m.pointHistory == [1, 2, 1, 2]

    def test_record_points_win_game(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        m.recordPoints([1, 1, 1, 1])
        assert m.currentSet.score.games(1) == (1, 0)

    def test_record_points_win_set(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        for _ in range(6):
            m.recordPoints([1, 1, 1, 1])
        assert m.score.sets(1) == (1, 0)
        assert len(m.setHistory) == 1

    def test_record_points_win_match(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        # Win 2 sets
        for _ in range(12):  # 2 sets x 6 games
            m.recordPoints([1, 1, 1, 1])
        assert m.isOver
        assert m.winner == 1


class TestMatchProperties:
    """Tests for Match properties."""

    def test_is_over_not_over(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        assert not m.isOver
        win_set(m, 1)
        assert not m.isOver

    def test_is_over_best_of_3(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        win_set(m, 1)
        win_set(m, 1)
        assert m.isOver

    def test_is_over_best_of_5(self):
        m = Match(playerServing=1, matchFormat=BEST_OF_5)
        win_set(m, 1)
        win_set(m, 1)
        assert not m.isOver
        win_set(m, 1)
        assert m.isOver

    def test_winner_none_when_not_over(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        assert m.winner is None
        win_set(m, 1)
        assert m.winner is None

    def test_winner_player1(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        win_set(m, 1)
        win_set(m, 1)
        assert m.winner == 1

    def test_winner_player2(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        win_set(m, 2)
        win_set(m, 2)
        assert m.winner == 2


class TestMatchServerRotation:
    """Tests for server rotation in a match."""

    def test_server_alternates_after_game(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        assert m.servesNext == 1
        win_game(m, 1)
        assert m.servesNext == 2
        win_game(m, 2)
        assert m.servesNext == 1

    def test_server_after_set_ends(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        # P1 wins first set 6-0
        win_set(m, 1)
        # After a 6-0 set where P1 served first:
        # Game 1: P1 serves -> P2 serves next
        # Game 2: P2 serves -> P1 serves next
        # Game 3: P1 serves -> P2 serves next
        # Game 4: P2 serves -> P1 serves next
        # Game 5: P1 serves -> P2 serves next
        # Game 6: P2 serves -> P1 serves next set
        # But servesNext on the set returns who would serve next GAME in that set
        # which is P1 (since P2 served game 6). Then match flips it? No wait...
        # Let's check: after set, currentSet.servesNext = 1, then match does 3 - 1 = 2
        # Actually the Set.servesNext after the set is over returns who would serve next
        # which is the flip of who served last. P2 served game 6, so servesNext = 1.
        # Match.servesNext for a new set also uses currentSet.servesNext which is
        # the same player who starts the new set.
        # Actually looking at the code: after set over, Match creates new Set with
        # servingNext = 3 - self.currentSet.servesNext. If Set.servesNext = 1,
        # then new set starts with server 2.
        assert m.servesNext == 2

    def test_server_after_match_over(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        win_set(m, 1)
        win_set(m, 1)
        assert m.isOver
        # servesNext should still return a valid value
        assert m.servesNext in (1, 2)

    def test_server_rotation_player2_starts(self):
        m = Match(playerServing=2, matchFormat=DEFAULT_FORMAT)
        assert m.servesNext == 2
        win_game(m, 2)
        assert m.servesNext == 1


class TestMatchSetHistory:
    """Tests for set history tracking."""

    def test_set_history_empty_initially(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        assert m.setHistory == []

    def test_set_history_after_one_set(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        win_set(m, 1)
        assert len(m.setHistory) == 1
        assert m.setHistory[0].winner == 1

    def test_set_history_after_multiple_sets(self):
        m = Match(playerServing=1, matchFormat=BEST_OF_5)
        win_set(m, 1)
        win_set(m, 2)
        win_set(m, 1)
        assert len(m.setHistory) == 3
        assert m.setHistory[0].winner == 1
        assert m.setHistory[1].winner == 2
        assert m.setHistory[2].winner == 1

    def test_set_history_contains_complete_sets(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        win_set(m, 1)
        # The completed set should have full game history
        assert len(m.setHistory[0].gameHistory) == 6


class TestMatchPointHistory:
    """Tests for point history tracking."""

    def test_point_history_empty_initially(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        assert m.pointHistory == []

    def test_point_history_within_game(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        m.recordPoints([1, 2, 1])
        assert m.pointHistory == [1, 2, 1]

    def test_point_history_across_sets(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        win_set(m, 1)  # 24 points
        m.recordPoints([2, 2])  # 2 more points
        assert len(m.pointHistory) == 26
        assert m.pointHistory[-2:] == [2, 2]


class TestMatchTotalPoints:
    """Tests for total points tracking."""

    def test_total_points_initial(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        assert m.totalPoints == (0, 0)

    def test_total_points_after_game(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        win_game(m, 1)
        assert m.totalPoints == (4, 0)

    def test_total_points_after_set(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        win_set(m, 1)
        assert m.totalPoints == (24, 0)

    def test_total_points_mixed(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        m.recordPoints([1, 2, 1, 2, 1, 1])  # P1 wins 4-2
        assert m.totalPoints == (4, 2)


class TestMatchWinConditions:
    """Tests for various match win conditions."""

    def test_win_2_0_best_of_3(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        win_set(m, 1)
        win_set(m, 1)
        assert m.isOver
        assert m.winner == 1
        assert m.score.sets(1) == (2, 0)

    def test_win_2_1_best_of_3(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        win_set(m, 1)
        win_set(m, 2)
        win_set(m, 1)
        assert m.isOver
        assert m.winner == 1
        assert m.score.sets(1) == (2, 1)

    def test_win_3_0_best_of_5(self):
        m = Match(playerServing=1, matchFormat=BEST_OF_5)
        for _ in range(3):
            win_set(m, 1)
        assert m.isOver
        assert m.winner == 1
        assert m.score.sets(1) == (3, 0)

    def test_win_3_2_best_of_5(self):
        m = Match(playerServing=1, matchFormat=BEST_OF_5)
        win_set(m, 1)
        win_set(m, 2)
        win_set(m, 2)
        win_set(m, 1)
        win_set(m, 1)
        assert m.isOver
        assert m.winner == 1
        assert m.score.sets(1) == (3, 2)

    def test_p2_wins_2_0(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        win_set(m, 2)
        win_set(m, 2)
        assert m.isOver
        assert m.winner == 2
        assert m.score.sets(1) == (0, 2)


class TestMatchTiebreaks:
    """Tests for tiebreak handling in matches."""

    def test_tiebreak_in_set(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        get_to_tiebreak(m)
        assert m.currentSet.tiebreaker is not None

    def test_set_after_tiebreak(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        get_to_tiebreak(m)
        # P1 wins tiebreak 7-0
        m.recordPoints([1] * 7)
        assert m.score.sets(1) == (1, 0)
        assert not m.isOver
        # New set should start
        assert m.currentSet is not None
        assert m.currentSet.score.games(1) == (0, 0)

    def test_match_won_via_tiebreak(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        # Win first set via tiebreak
        get_to_tiebreak(m)
        m.recordPoints([1] * 7)
        # Win second set 6-0
        win_set(m, 1)
        assert m.isOver
        assert m.winner == 1


class TestMatchStr:
    """Tests for __str__ method."""

    def test_str_initial(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        result = str(m)
        assert "Player1 to serve at 0-0" in result

    def test_str_mid_game(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        m.recordPoints([1, 2])
        result = str(m)
        assert "0-0" in result  # sets
        assert "0-0" in result  # games
        assert "15-15" in result  # points

    def test_str_mid_set(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        win_game(m, 1)
        win_game(m, 2)
        result = str(m)
        assert "0-0" in result  # sets
        assert "1-1" in result  # games

    def test_str_between_sets(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        win_set(m, 1)
        result = str(m)
        # Score is shown from POV of server (P2 serves next set)
        # so sets show as "0-1" (server's sets - opponent's sets)
        assert "0-1" in result  # sets from P2's POV

    def test_str_match_over(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        win_set(m, 1)
        win_set(m, 1)
        result = str(m)
        assert "wins match" in result
        assert "2-0" in result


class TestMatchRepr:
    """Tests for __repr__ method."""

    def test_repr_contains_match(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        assert "Match" in repr(m)

    def test_repr_contains_server(self):
        m = Match(playerServing=2, matchFormat=DEFAULT_FORMAT)
        assert "playerServing=" in repr(m)

    def test_repr_contains_matchFormat(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        assert "matchFormat=" in repr(m)

    def test_repr_contains_score(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        win_set(m, 1)
        repr_str = repr(m)
        assert "initScore=" in repr_str
        assert "MatchScore" in repr_str

    def test_repr_recreates_match(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        win_game(m, 1)
        win_game(m, 2)
        recreated = eval(repr(m))
        assert recreated.score.sets(1) == m.score.sets(1)
        assert recreated.currentSet.score.games(1) == m.currentSet.score.games(1)


class TestMatchScoreHistory:
    """Tests for scoreHistory method."""

    def test_score_history_initial(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        history = m.scoreHistory()
        # Should have current set info
        assert "Set #1" in history

    def test_score_history_after_set(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        win_set(m, 1)
        history = m.scoreHistory()
        assert "Set #1" in history
        assert "Set #2" in history  # Current set

    def test_score_history_match_complete(self):
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        win_set(m, 1)
        win_set(m, 1)
        history = m.scoreHistory()
        assert "Set #1" in history
        assert "Set #2" in history


class TestMatchWithInitialScore:
    """Tests for matches starting at non-zero scores."""

    def test_start_at_1_0(self):
        init_score = MatchScore(1, 0, DEFAULT_FORMAT)
        m = Match(playerServing=1, initScore=init_score)
        assert m.score.sets(1) == (1, 0)
        assert m.setHistory == []

        # P1 wins one more set
        win_set(m, 1)
        assert m.isOver
        assert m.winner == 1
        assert m.score.sets(1) == (2, 0)

    def test_start_at_1_1(self):
        init_score = MatchScore(1, 1, DEFAULT_FORMAT)
        m = Match(playerServing=1, initScore=init_score)
        assert m.score.sets(1) == (1, 1)

        # P2 wins deciding set
        win_set(m, 2)
        assert m.isOver
        assert m.winner == 2
        assert m.score.sets(1) == (1, 2)

    def test_start_with_set_in_progress(self):
        # At 1-0 in best of 3, the next set could be the final set if P1 wins
        # But until P1 is at match point, it's not a "final set" yet
        # Actually, _isFinalSet returns True when one more set win decides the match
        # At 1-0, P1 winning would end the match, so it IS a final set
        set_score = SetScore(3, 2, isFinalSet=True, matchFormat=DEFAULT_FORMAT)
        init_score = MatchScore(1, 0, DEFAULT_FORMAT, setScore=set_score)
        m = Match(playerServing=1, initScore=init_score)

        assert m.score.sets(1) == (1, 0)
        assert m.currentSet.score.games(1) == (3, 2)

        # Win 3 more games to complete this set
        for _ in range(3):
            win_game(m, 1)
        assert m.score.sets(1) == (2, 0)
        assert m.isOver


class TestMatchNoAdRule:
    """Tests for matches with no-ad rule."""

    def test_no_ad_game_ends_at_deuce(self):
        m = Match(playerServing=1, matchFormat=NO_AD_FORMAT)
        # Get to deuce (40-40)
        m.recordPoints([1, 1, 1, 2, 2, 2])
        # Next point wins
        m.recordPoint(1)
        assert m.currentSet.score.games(1) == (1, 0)


class TestMatchFullPlaythrough:
    """Tests simulating full matches."""

    def test_straight_sets_win(self):
        """P1 wins 2-0 in straight sets."""
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        win_set(m, 1)
        win_set(m, 1)
        assert m.isOver
        assert m.winner == 1
        assert len(m.setHistory) == 2

    def test_three_set_match(self):
        """P1 wins 2-1 after losing first set."""
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        win_set(m, 2)  # P2 wins first
        win_set(m, 1)  # P1 wins second
        win_set(m, 1)  # P1 wins third
        assert m.isOver
        assert m.winner == 1
        assert m.score.sets(1) == (2, 1)

    def test_five_set_match(self):
        """P2 wins 3-2 in a full 5-setter."""
        m = Match(playerServing=1, matchFormat=BEST_OF_5)
        win_set(m, 1)  # P1 wins
        win_set(m, 2)  # P2 wins
        win_set(m, 1)  # P1 wins
        win_set(m, 2)  # P2 wins
        win_set(m, 2)  # P2 wins decider
        assert m.isOver
        assert m.winner == 2
        assert m.score.sets(1) == (2, 3)

    def test_tiebreak_set_then_regular(self):
        """Win first set via tiebreak, second set 6-4."""
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)

        # First set: tiebreak
        get_to_tiebreak(m)
        m.recordPoints([1] * 7)
        assert m.score.sets(1) == (1, 0)

        # Second set: 6-4
        for _ in range(4):
            win_game(m, 1)
            win_game(m, 2)
        win_game(m, 1)
        win_game(m, 1)
        assert m.isOver
        assert m.winner == 1

    def test_all_tiebreaks(self):
        """Both sets decided by tiebreaks."""
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)

        # First set tiebreak
        get_to_tiebreak(m)
        m.recordPoints([1] * 7)

        # Second set tiebreak
        get_to_tiebreak(m)
        m.recordPoints([1] * 7)

        assert m.isOver
        assert m.winner == 1


class TestMatchEquality:
    """Tests for match state consistency."""

    def test_point_count_matches_history(self):
        """Total points should equal sum of history."""
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        win_set(m, 1)
        win_game(m, 2)
        m.recordPoints([1, 2, 1])

        p1, p2 = m.totalPoints
        history = m.pointHistory
        assert p1 == history.count(1)
        assert p2 == history.count(2)

    def test_current_set_none_when_over(self):
        """currentSet should be None when match is over."""
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        win_set(m, 1)
        win_set(m, 1)
        assert m.isOver
        assert m.currentSet is None

    def test_set_history_plus_current_equals_total(self):
        """setHistory + currentSet should account for all sets played."""
        m = Match(playerServing=1, matchFormat=DEFAULT_FORMAT)
        win_set(m, 1)
        # One completed set in history, one in progress
        assert len(m.setHistory) == 1
        assert m.currentSet is not None
        assert m.score.setsPlayer1 + m.score.setsPlayer2 == 1
