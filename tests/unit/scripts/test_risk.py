import pytest

from scripts import risk
from scripts.risk import RiskLabelError, RiskLevel


class TestLabels:
    @pytest.mark.parametrize(
        ("labels", "problem"),
        [
            (["risk:low"], None),
            (["risk:medium"], None),
            (["risk:high"], None),
            (["bug", "risk:critical"], None),
            ([], "expected exactly one risk label"),
            (["bug"], "expected exactly one risk label"),
            (["risk:low", "risk:high"], "expected exactly one risk label"),
            (["risk:urgent"], "unknown risk label risk:urgent"),
        ],
    )
    def test_should_require_exactly_one_known_label(
        self, labels: list[str], problem: str | None
    ) -> None:
        result = risk.label_problem(labels)

        if problem is None:
            assert result is None
        else:
            assert result is not None
            assert problem in result

    def test_should_list_the_valid_labels_in_the_problem(self) -> None:
        result = risk.label_problem([])

        assert result == (
            "expected exactly one risk label (risk:low, risk:medium, risk:high, risk:critical), "
            "found: none"
        )

    def test_should_build_the_label_of_each_level(self) -> None:
        assert [level.label for level in RiskLevel] == [
            "risk:low",
            "risk:medium",
            "risk:high",
            "risk:critical",
        ]

    def test_should_parse_the_labels(self) -> None:
        assert risk.parse_labels('["risk:low", "bug"]') == ["risk:low", "bug"]
        assert risk.parse_labels("") == []

    @pytest.mark.parametrize("labels_json", ['{"a": 1}', "[1]"])
    def test_should_reject_labels_that_are_not_a_list_of_strings(self, labels_json: str) -> None:
        with pytest.raises(RiskLabelError, match="JSON list of strings"):
            risk.parse_labels(labels_json)


class TestCommands:
    def test_should_pass_with_one_known_label(self, caplog: pytest.LogCaptureFixture) -> None:
        with caplog.at_level("INFO"):
            assert risk.main(["check", "--labels-json", '["risk:low", "dependencies"]']) == 0
        assert "exactly one known risk label" in caplog.text

    @pytest.mark.parametrize(
        ("labels_json", "message"),
        [
            ('["risk:low", "risk:medium"]', "expected exactly one risk label"),
            ("[]", "found: none"),
            ('["risk:urgent"]', "unknown risk label"),
        ],
    )
    def test_should_fail_without_exactly_one_known_label(
        self, caplog: pytest.LogCaptureFixture, labels_json: str, message: str
    ) -> None:
        assert risk.main(["check", "--labels-json", labels_json]) == 1
        assert message in caplog.text

    @pytest.mark.parametrize("labels_json", ["not json", '{"a": 1}'])
    def test_should_fail_loudly_on_unreadable_labels(
        self, caplog: pytest.LogCaptureFixture, labels_json: str
    ) -> None:
        assert risk.main(["check", "--labels-json", labels_json]) == 1
        assert "Risk label check failed" in caplog.text
