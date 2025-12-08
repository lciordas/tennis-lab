"""Tests for the SetScore class."""

import pytest
from src.core.set_score import SetScore
from src.core.game_score import GameScore
from src.core.tiebreak_score import TiebreakScore
from src.core.match_format import MatchFormat, SetEnding

# Default match formats for tests
DEFAULT_FORMAT     = MatchFormat(bestOfSets=3)
NO_AD_FORMAT       = MatchFormat(bestOfSets=3, noAdRule=True)
CAP_FORMAT         = MatchFormat(bestOfSets=3, capPoints=True)
NO_TIEBREAK_FORMAT = MatchFormat(bestOfSets=3, setEnding=SetEnding.ADVANTAGE)
SHORT_SET_FORMAT   = MatchFormat(bestOfSets=3, setLength=4)

# Formats with different final set rules
FINAL_SET_ADVANTAGE = MatchFormat(bestOfSets=3, setEnding=SetEnding.TIEBREAK, finalSetEnding=SetEnding.ADVANTAGE)
FINAL_SET_SUPERTIEBREAK = MatchFormat(bestOfSets=3, setEnding=SetEnding.TIEBREAK, finalSetEnding=SetEnding.SUPERTIEBREAK)


class TestSetScoreInit:
    """Tests for SetScore initialization."""

    def test_init_blank_score(self):
        score = SetScore(0, 0, False, DEFAULT_FORMAT)
        assert score.gamesPlayer1 == 0
        assert score.gamesPlayer2 == 0
        assert score.isBlank

    def test_init_with_games(self):
        score = SetScore(3, 2, False, DEFAULT_FORMAT)
        assert score.gamesPlayer1 == 3
        assert score.gamesPlayer2 == 2
        assert score.currGameScore is not None
        assert score.currGameScore.isBlank

    def test_init_with_game_score(self):
        game_score = GameScore(2, 1, DEFAULT_FORMAT)
        score = SetScore(3, 2, False, DEFAULT_FORMAT, gameScore=game_score)
        assert score.gamesPlayer1 == 3
        assert score.gamesPlayer2 == 2
        assert score.currGameScore.asPoints(1) == (2, 1)

    def test_init_at_tiebreak(self):
        score = SetScore(6, 6, False, DEFAULT_FORMAT)
        assert score.isTied
        assert score.currGameScore is None
        assert score.tiebreakScore is not None
        assert score.tiebreakScore.isBlank

    def test_init_with_tiebreak_score(self):
        tb_score = TiebreakScore(3, 2, isSuper=False, matchFormat=DEFAULT_FORMAT)
        score = SetScore(6, 6, False, DEFAULT_FORMAT, tiebreakScore=tb_score)
        assert score.tiebreakScore.asPoints(1) == (3, 2)

    def test_init_invalid_non_integer_games(self):
        with pytest.raises(ValueError):
            SetScore(3.5, 2, False, DEFAULT_FORMAT)
        with pytest.raises(ValueError):
            SetScore(3, "2", False, DEFAULT_FORMAT)

    def test_init_invalid_negative_games(self):
        with pytest.raises(ValueError):
            SetScore(-1, 0, False, DEFAULT_FORMAT)
        with pytest.raises(ValueError):
            SetScore(0, -1, False, DEFAULT_FORMAT)

    def test_init_invalid_isFinalSet_type(self):
        with pytest.raises(ValueError):
            SetScore(0, 0, "not a bool", DEFAULT_FORMAT)

    def test_init_invalid_matchFormat_type(self):
        with pytest.raises(ValueError):
            SetScore(0, 0, False, "not a MatchFormat")

    def test_init_invalid_game_score_type(self):
        with pytest.raises(ValueError):
            SetScore(3, 2, False, DEFAULT_FORMAT, gameScore="not a GameScore")

    def test_init_invalid_final_game_score(self):
        final_game = GameScore(4, 0, DEFAULT_FORMAT)  # This is a final score
        with pytest.raises(ValueError):
            SetScore(3, 2, False, DEFAULT_FORMAT, gameScore=final_game)

    def test_init_invalid_tiebreak_score_type(self):
        with pytest.raises(ValueError):
            SetScore(6, 6, False, DEFAULT_FORMAT, tiebreakScore="not a TiebreakScore")

    def test_init_invalid_final_tiebreak_score(self):
        final_tb = TiebreakScore(7, 3, isSuper=False, matchFormat=DEFAULT_FORMAT)  # This is a final score
        with pytest.raises(ValueError):
            SetScore(6, 6, False, DEFAULT_FORMAT, tiebreakScore=final_tb)

    def test_init_tiebreak_score_without_tiebreak_set(self):
        tb_score = TiebreakScore(1, 0, isSuper=False, matchFormat=NO_TIEBREAK_FORMAT)
        with pytest.raises(ValueError):
            SetScore(6, 6, False, NO_TIEBREAK_FORMAT, tiebreakScore=tb_score)

    def test_init_game_score_matchFormat_mismatch(self):
        game_score = GameScore(2, 1, NO_AD_FORMAT)
        with pytest.raises(ValueError):
            SetScore(3, 2, False, DEFAULT_FORMAT, gameScore=game_score)

    def test_init_tiebreak_score_matchFormat_mismatch(self):
        tb_score = TiebreakScore(2, 1, isSuper=False, matchFormat=CAP_FORMAT)
        with pytest.raises(ValueError):
            SetScore(6, 6, False, DEFAULT_FORMAT, tiebreakScore=tb_score)

    def test_init_custom_set_length(self):
        # 4-game set (like some junior formats)
        score = SetScore(4, 2, False, SHORT_SET_FORMAT)
        assert score.isFinal
        assert score.winner == 1

    def test_init_no_tiebreak_set(self):
        # At 6-6 without tiebreak, game continues
        score = SetScore(6, 6, False, NO_TIEBREAK_FORMAT)
        assert not score.isFinal
        assert score.currGameScore is not None
        assert score.tiebreakScore is None


class TestSetScoreProperties:
    """Tests for SetScore properties."""

    def test_is_blank(self):
        assert SetScore(0, 0, False, DEFAULT_FORMAT).isBlank
        # Not blank if games have been played
        assert not SetScore(1, 0, False, DEFAULT_FORMAT).isBlank
        # Not blank if current game has points
        score = SetScore(0, 0, False, DEFAULT_FORMAT)
        score.recordPoint(1)
        assert not score.isBlank

    def test_is_tied(self):
        assert not SetScore(5, 5, False, DEFAULT_FORMAT).isTied
        assert SetScore(6, 6, False, DEFAULT_FORMAT).isTied
        assert not SetScore(6, 5, False, DEFAULT_FORMAT).isTied
        # Custom set length
        assert SetScore(4, 4, False, SHORT_SET_FORMAT).isTied

    def test_is_final_win_by_two(self):
        assert SetScore(6, 0, False, DEFAULT_FORMAT).isFinal
        assert SetScore(6, 4, False, DEFAULT_FORMAT).isFinal
        assert SetScore(0, 6, False, DEFAULT_FORMAT).isFinal
        assert SetScore(4, 6, False, DEFAULT_FORMAT).isFinal
        assert not SetScore(6, 5, False, DEFAULT_FORMAT).isFinal
        assert not SetScore(5, 6, False, DEFAULT_FORMAT).isFinal

    def test_is_final_tiebreak_win(self):
        assert SetScore(7, 6, False, DEFAULT_FORMAT).isFinal
        assert SetScore(6, 7, False, DEFAULT_FORMAT).isFinal

    def test_winner(self):
        assert SetScore(6, 4, False, DEFAULT_FORMAT).winner == 1
        assert SetScore(4, 6, False, DEFAULT_FORMAT).winner == 2
        assert SetScore(7, 6, False, DEFAULT_FORMAT).winner == 1
        assert SetScore(6, 7, False, DEFAULT_FORMAT).winner == 2
        assert SetScore(5, 5, False, DEFAULT_FORMAT).winner is None
        assert SetScore(6, 6, False, DEFAULT_FORMAT).winner is None

    def test_next_point_is_game(self):
        # Regular game in progress
        assert SetScore(3, 2, False, DEFAULT_FORMAT).nextPointIsGame
        # At tiebreak, not a regular game
        assert not SetScore(6, 6, False, DEFAULT_FORMAT).nextPointIsGame
        # Set is over
        assert not SetScore(6, 4, False, DEFAULT_FORMAT).nextPointIsGame
        # No tiebreak set at 6-6: still playing games
        assert SetScore(6, 6, False, NO_TIEBREAK_FORMAT).nextPointIsGame

    def test_next_point_is_tiebreak(self):
        assert not SetScore(5, 5, False, DEFAULT_FORMAT).nextPointIsTiebreak
        assert SetScore(6, 6, False, DEFAULT_FORMAT).nextPointIsTiebreak
        # Set is over
        assert not SetScore(7, 6, False, DEFAULT_FORMAT).nextPointIsTiebreak
        # No tiebreak set
        assert not SetScore(6, 6, False, NO_TIEBREAK_FORMAT).nextPointIsTiebreak

    def test_game_in_progress(self):
        # At start of game, not in progress
        assert not SetScore(3, 2, False, DEFAULT_FORMAT).gameInProgress
        # After a point, game is in progress
        score = SetScore(3, 2, False, DEFAULT_FORMAT)
        score.recordPoint(1)
        assert score.gameInProgress

    def test_tiebreak_in_progress(self):
        # At start of tiebreak, not in progress
        assert not SetScore(6, 6, False, DEFAULT_FORMAT).tiebreakInProgress
        # After a point, tiebreak is in progress
        score = SetScore(6, 6, False, DEFAULT_FORMAT)
        score.recordPoint(1)
        assert score.tiebreakInProgress


class TestEndsInTiebreak:
    """Tests for endsInTiebreak property."""

    def test_ends_in_tiebreak_default(self):
        score = SetScore(0, 0, False, DEFAULT_FORMAT)
        assert score.endsInTiebreak

    def test_ends_in_tiebreak_advantage_set(self):
        score = SetScore(0, 0, False, NO_TIEBREAK_FORMAT)
        assert not score.endsInTiebreak

    def test_ends_in_tiebreak_non_final_set(self):
        # Non-final set uses setEnding
        score = SetScore(0, 0, False, FINAL_SET_ADVANTAGE)
        assert score.endsInTiebreak  # setEnding is TIEBREAK

    def test_ends_in_tiebreak_final_set_advantage(self):
        # Final set uses finalSetEnding
        score = SetScore(0, 0, True, FINAL_SET_ADVANTAGE)
        assert not score.endsInTiebreak  # finalSetEnding is ADVANTAGE

    def test_ends_in_tiebreak_final_set_supertiebreak(self):
        score = SetScore(0, 0, True, FINAL_SET_SUPERTIEBREAK)
        assert score.endsInTiebreak  # SUPERTIEBREAK still ends in tiebreak


class TestFinalSetBehavior:
    """Tests for final set specific behavior."""

    def test_final_set_advantage_no_tiebreak(self):
        # Final set with advantage rule - no tiebreak at 6-6
        score = SetScore(6, 6, True, FINAL_SET_ADVANTAGE)
        assert not score.isFinal
        assert score.nextPointIsGame
        assert not score.nextPointIsTiebreak
        assert score.currGameScore is not None
        assert score.tiebreakScore is None

    def test_final_set_advantage_win_by_two(self):
        score = SetScore(8, 6, True, FINAL_SET_ADVANTAGE)
        assert score.isFinal
        assert score.winner == 1

    def test_non_final_set_same_format_has_tiebreak(self):
        # Non-final set with same format still has tiebreak at 6-6
        score = SetScore(6, 6, False, FINAL_SET_ADVANTAGE)
        assert not score.isFinal
        assert score.nextPointIsTiebreak
        assert score.tiebreakScore is not None

    def test_final_set_supertiebreak(self):
        # Final set with super tiebreak
        score = SetScore(6, 6, True, FINAL_SET_SUPERTIEBREAK)
        assert score.nextPointIsTiebreak
        assert score.tiebreakScore is not None
        # Super tiebreak requires 10 points to win
        for _ in range(9):
            score.recordPoint(1)
        assert not score.isFinal
        score.recordPoint(1)  # 10th point
        assert score.isFinal
        assert score.winner == 1

    def test_non_final_set_regular_tiebreak(self):
        # Non-final set uses regular tiebreak (7 points)
        score = SetScore(6, 6, False, FINAL_SET_SUPERTIEBREAK)
        for _ in range(7):
            score.recordPoint(1)
        assert score.isFinal
        assert score.winner == 1


class TestGamesMethod:
    """Tests for games() method."""

    def test_games_pov1(self):
        score = SetScore(4, 2, False, DEFAULT_FORMAT)
        assert score.games(1) == (4, 2)

    def test_games_pov2(self):
        score = SetScore(4, 2, False, DEFAULT_FORMAT)
        assert score.games(2) == (2, 4)

    def test_games_invalid_pov(self):
        score = SetScore(3, 2, False, DEFAULT_FORMAT)
        with pytest.raises(ValueError):
            score.games(0)
        with pytest.raises(ValueError):
            score.games(3)


class TestRecordPoint:
    """Tests for recordPoint method."""

    def test_record_point_basic(self):
        score = SetScore(0, 0, False, DEFAULT_FORMAT)
        score.recordPoint(1)
        assert score.currGameScore.asPoints(1) == (1, 0)

    def test_record_point_invalid(self):
        score = SetScore(0, 0, False, DEFAULT_FORMAT)
        with pytest.raises(ValueError):
            score.recordPoint(0)
        with pytest.raises(ValueError):
            score.recordPoint(3)

    def test_record_point_set_over(self):
        score = SetScore(6, 4, False, DEFAULT_FORMAT)
        with pytest.raises(ValueError):
            score.recordPoint(1)

    def test_record_point_completes_game(self):
        score = SetScore(0, 0, False, DEFAULT_FORMAT)
        # P1 wins 4 points (game)
        for _ in range(4):
            score.recordPoint(1)
        assert score.gamesPlayer1 == 1
        assert score.gamesPlayer2 == 0
        assert score.currGameScore.isBlank

    def test_record_point_completes_set(self):
        score = SetScore(5, 0, False, DEFAULT_FORMAT)
        # P1 wins 4 points (game) to win set 6-0
        for _ in range(4):
            score.recordPoint(1)
        assert score.gamesPlayer1 == 6
        assert score.gamesPlayer2 == 0
        assert score.isFinal
        assert score.winner == 1

    def test_record_point_tiebreak(self):
        score = SetScore(6, 6, False, DEFAULT_FORMAT)
        score.recordPoint(1)
        assert score.tiebreakScore.asPoints(1) == (1, 0)

    def test_record_point_completes_tiebreak(self):
        score = SetScore(6, 6, False, DEFAULT_FORMAT)
        # P1 wins 7 points (tiebreak)
        for _ in range(7):
            score.recordPoint(1)
        assert score.gamesPlayer1 == 7
        assert score.gamesPlayer2 == 6
        assert score.isFinal
        assert score.winner == 1

    def test_record_point_game_transitions_to_tiebreak(self):
        score = SetScore(5, 5, False, DEFAULT_FORMAT)
        # P1 wins a game to make it 6-5
        for _ in range(4):
            score.recordPoint(1)
        assert score.gamesPlayer1 == 6
        assert score.gamesPlayer2 == 5
        assert score.currGameScore is not None
        # P2 wins a game to make it 6-6
        for _ in range(4):
            score.recordPoint(2)
        assert score.gamesPlayer1 == 6
        assert score.gamesPlayer2 == 6
        assert score.tiebreakScore is not None
        assert score.currGameScore is None


class TestNextGameScores:
    """Tests for nextGameScores method."""

    def test_next_game_scores_basic(self):
        score = SetScore(3, 2, False, DEFAULT_FORMAT)
        next_p1, next_p2 = score.nextGameScores()
        assert next_p1.gamesPlayer1 == 4
        assert next_p1.gamesPlayer2 == 2
        assert next_p2.gamesPlayer1 == 3
        assert next_p2.gamesPlayer2 == 3

    def test_next_game_scores_final(self):
        score = SetScore(6, 4, False, DEFAULT_FORMAT)
        assert score.nextGameScores() is None

    def test_next_game_scores_game_in_progress(self):
        score = SetScore(3, 2, False, DEFAULT_FORMAT)
        score.recordPoint(1)  # Now game is in progress
        with pytest.raises(ValueError):
            score.nextGameScores()

    def test_next_game_scores_tiebreak_in_progress(self):
        score = SetScore(6, 6, False, DEFAULT_FORMAT)
        score.recordPoint(1)  # Now tiebreak is in progress
        with pytest.raises(ValueError):
            score.nextGameScores()

    def test_next_game_scores_propagates_matchFormat(self):
        score = SetScore(3, 2, False, NO_AD_FORMAT)
        next_p1, next_p2 = score.nextGameScores()
        # Verify matchFormat is propagated
        assert next_p1._matchFormat == NO_AD_FORMAT
        assert next_p2._matchFormat == NO_AD_FORMAT

    def test_next_game_scores_propagates_isFinalSet(self):
        score = SetScore(3, 2, True, DEFAULT_FORMAT)
        next_p1, next_p2 = score.nextGameScores()
        assert next_p1._isFinalSet == True
        assert next_p2._isFinalSet == True


class TestNoTiebreakSet:
    """Tests for sets without tiebreak."""

    def test_no_tiebreak_at_6_6(self):
        score = SetScore(6, 6, False, NO_TIEBREAK_FORMAT)
        assert not score.isFinal
        assert score.currGameScore is not None
        assert score.tiebreakScore is None

    def test_no_tiebreak_win_by_two(self):
        score = SetScore(8, 6, False, NO_TIEBREAK_FORMAT)
        assert score.isFinal
        assert score.winner == 1

    def test_no_tiebreak_not_final_at_7_6(self):
        score = SetScore(7, 6, False, NO_TIEBREAK_FORMAT)
        assert not score.isFinal

    def test_no_tiebreak_continues_past_6_6(self):
        score = SetScore(6, 6, False, NO_TIEBREAK_FORMAT)
        # P1 wins a game
        for _ in range(4):
            score.recordPoint(1)
        assert score.gamesPlayer1 == 7
        assert score.gamesPlayer2 == 6
        assert not score.isFinal
        # P2 wins a game
        for _ in range(4):
            score.recordPoint(2)
        assert score.gamesPlayer1 == 7
        assert score.gamesPlayer2 == 7
        assert not score.isFinal


class TestEquality:
    """Tests for __eq__ and __hash__."""

    def test_equal_scores(self):
        assert SetScore(3, 2, False, DEFAULT_FORMAT) == SetScore(3, 2, False, DEFAULT_FORMAT)

    def test_unequal_games(self):
        assert SetScore(3, 2, False, DEFAULT_FORMAT) != SetScore(2, 3, False, DEFAULT_FORMAT)

    def test_equal_with_game_score(self):
        gs1 = GameScore(2, 1, DEFAULT_FORMAT)
        gs2 = GameScore(2, 1, DEFAULT_FORMAT)
        assert SetScore(3, 2, False, DEFAULT_FORMAT, gameScore=gs1) == SetScore(3, 2, False, DEFAULT_FORMAT, gameScore=gs2)

    def test_unequal_game_score(self):
        gs1 = GameScore(2, 1, DEFAULT_FORMAT)
        gs2 = GameScore(1, 2, DEFAULT_FORMAT)
        assert SetScore(3, 2, False, DEFAULT_FORMAT, gameScore=gs1) != SetScore(3, 2, False, DEFAULT_FORMAT, gameScore=gs2)

    def test_hash_consistency(self):
        s1 = SetScore(3, 2, False, DEFAULT_FORMAT)
        s2 = SetScore(3, 2, False, DEFAULT_FORMAT)
        assert hash(s1) == hash(s2)

        # Can use in sets/dicts
        score_set = {s1, s2}
        assert len(score_set) == 1


class TestReprAndStr:
    """Tests for __repr__ and __str__."""

    def test_repr(self):
        score = SetScore(3, 2, False, NO_AD_FORMAT)
        repr_str = repr(score)
        assert "SetScore" in repr_str
        assert "gamesP1=3" in repr_str
        assert "gamesP2=2" in repr_str
        assert "isFinalSet=False" in repr_str
        assert "matchFormat=" in repr_str

    def test_repr_eval(self):
        # repr should produce valid Python
        score = SetScore(3, 2, False, DEFAULT_FORMAT)
        recreated = eval(repr(score))
        assert recreated.gamesPlayer1 == 3
        assert recreated.gamesPlayer2 == 2

    def test_str_basic(self):
        assert str(SetScore(3, 2, False, DEFAULT_FORMAT)) == "3-2, 0-0"
        assert str(SetScore(6, 4, False, DEFAULT_FORMAT)) == "6-4"

    def test_str_with_game_score(self):
        score = SetScore(3, 2, False, DEFAULT_FORMAT)
        score.recordPoint(1)
        score.recordPoint(1)
        assert str(score) == "3-2, 30-0"

    def test_str_with_tiebreak_score(self):
        score = SetScore(6, 6, False, DEFAULT_FORMAT)
        score.recordPoint(1)
        score.recordPoint(2)
        assert str(score) == "6-6, 1-1"


class TestPlayFullSet:
    """Integration tests for playing a full set."""

    def test_p1_wins_set_6_0(self):
        score = SetScore(0, 0, False, DEFAULT_FORMAT)
        for game in range(6):
            for point in range(4):
                score.recordPoint(1)
        assert score.isFinal
        assert score.winner == 1
        assert score.gamesPlayer1 == 6
        assert score.gamesPlayer2 == 0

    def test_p2_wins_set_6_4(self):
        score = SetScore(0, 0, False, DEFAULT_FORMAT)
        # P1 wins 4 games
        for game in range(4):
            for point in range(4):
                score.recordPoint(1)
        # P2 wins 6 games
        for game in range(6):
            for point in range(4):
                score.recordPoint(2)
        assert score.isFinal
        assert score.winner == 2
        assert score.gamesPlayer1 == 4
        assert score.gamesPlayer2 == 6

    def test_tiebreak_7_6(self):
        score = SetScore(0, 0, False, DEFAULT_FORMAT)
        # Each player wins 6 games alternately
        for game in range(6):
            for point in range(4):
                score.recordPoint(1)
            for point in range(4):
                score.recordPoint(2)
        assert score.gamesPlayer1 == 6
        assert score.gamesPlayer2 == 6
        assert score.tiebreakScore is not None
        # P1 wins tiebreak 7-0
        for point in range(7):
            score.recordPoint(1)
        assert score.isFinal
        assert score.winner == 1
        assert score.gamesPlayer1 == 7
        assert score.gamesPlayer2 == 6

    def test_tiebreak_extended(self):
        score = SetScore(6, 6, False, DEFAULT_FORMAT)
        # Each player wins 6 points
        for _ in range(6):
            score.recordPoint(1)
            score.recordPoint(2)
        assert not score.isFinal
        assert score.tiebreakScore.asPoints(1) == (6, 6)
        # P1 wins 2 more to win 8-6
        score.recordPoint(1)
        score.recordPoint(1)
        assert score.isFinal
        assert score.winner == 1

    def test_final_set_with_advantage_rule(self):
        # Play a final set that goes beyond 6-6 with advantage rule
        score = SetScore(6, 6, True, FINAL_SET_ADVANTAGE)
        # P1 and P2 trade games until 10-10
        for _ in range(4):
            for _ in range(4):
                score.recordPoint(1)
            for _ in range(4):
                score.recordPoint(2)
        assert score.gamesPlayer1 == 10
        assert score.gamesPlayer2 == 10
        assert not score.isFinal
        # P1 wins two games to win 12-10
        for _ in range(4):
            score.recordPoint(1)
        assert score.gamesPlayer1 == 11
        assert not score.isFinal
        for _ in range(4):
            score.recordPoint(1)
        assert score.gamesPlayer1 == 12
        assert score.gamesPlayer2 == 10
        assert score.isFinal
        assert score.winner == 1

    def test_final_set_supertiebreak_full(self):
        # Play a final set with super tiebreak
        score = SetScore(6, 6, True, FINAL_SET_SUPERTIEBREAK)
        # Super tiebreak: first to 10 with 2 point lead
        # P1 and P2 trade points to 9-9
        for _ in range(9):
            score.recordPoint(1)
            score.recordPoint(2)
        assert score.tiebreakScore.asPoints(1) == (9, 9)
        assert not score.isFinal
        # P1 wins 2 more to win 11-9
        score.recordPoint(1)
        score.recordPoint(1)
        assert score.isFinal
        assert score.winner == 1
        assert score.gamesPlayer1 == 7
        assert score.gamesPlayer2 == 6
