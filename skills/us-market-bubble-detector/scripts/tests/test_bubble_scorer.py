"""
Tests for bubble_scorer.py
"""

from bubble_scorer import BubbleScorer

ALL_KEYS = [
    "mass_penetration",
    "media_saturation",
    "new_accounts",
    "new_issuance",
    "leverage",
    "price_acceleration",
    "valuation_disconnect",
    "breadth_expansion",
]


def make_scores(value: int) -> dict[str, int]:
    return {key: value for key in ALL_KEYS}


class TestCalculateScore:
    """Tests for BubbleScorer.calculate_score phase boundaries."""

    def test_normal_phase(self):
        result = BubbleScorer().calculate_score(make_scores(0))
        assert result["total_score"] == 0
        assert result["max_score"] == 16
        assert result["phase"] == "正常域"
        assert result["risk_level"] == "低"

    def test_caution_phase_upper_boundary(self):
        scores = make_scores(0)
        scores["mass_penetration"] = 2
        scores["media_saturation"] = 2
        scores["new_accounts"] = 2
        scores["new_issuance"] = 2
        result = BubbleScorer().calculate_score(scores)
        assert result["total_score"] == 8
        assert result["phase"] == "警戒域"

    def test_euphoria_phase(self):
        result = BubbleScorer().calculate_score(make_scores(2))
        assert result["total_score"] == 16
        assert result["phase"] == "臨界域"
        assert result["risk_level"] == "極めて高"

    def test_percentage_rounding(self):
        scores = make_scores(0)
        scores["mass_penetration"] = 1
        result = BubbleScorer().calculate_score(scores)
        assert result["percentage"] == round(1 / 16 * 100, 1)


class TestEstimateMinskyPhase:
    """Tests for BubbleScorer._estimate_minsky_phase."""

    def test_low_score_is_displacement(self):
        scorer = BubbleScorer()
        phase = scorer._estimate_minsky_phase(make_scores(0), total=0)
        assert phase == "Displacement/Early Boom (きっかけ・初期拡張)"

    def test_high_score_with_mass_and_media_is_peak_euphoria(self):
        scorer = BubbleScorer()
        scores = make_scores(2)
        phase = scorer._estimate_minsky_phase(scores, total=16)
        assert "Peak Euphoria" in phase

    def test_high_score_without_mass_penetration_is_euphoria(self):
        scorer = BubbleScorer()
        scores = make_scores(2)
        scores["mass_penetration"] = 0
        phase = scorer._estimate_minsky_phase(scores, total=14)
        assert phase == "Euphoria (熱狂期)"


class TestFormatOutput:
    """Tests for BubbleScorer.format_output."""

    def test_format_output_includes_total_score(self):
        scorer = BubbleScorer()
        result = scorer.calculate_score(make_scores(1))
        output = scorer.format_output(result)
        assert f"{result['total_score']}/{result['max_score']}" in output
