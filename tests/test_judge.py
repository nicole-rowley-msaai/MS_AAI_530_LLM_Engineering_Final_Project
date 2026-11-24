
from src.judge import quote_in_resume, verdicts_by_index
from src.schemas import BulletVerdict, JudgeResult


RESUME = """
Sales Associate, Campus Bookstore
- Helped build weekly sales reports in Excel
  for the store manager.
- Answered customer questions at the service desk.
"""


def test_quote_found_despite_line_breaks_and_case():
    quote = "helped build weekly sales reports in Excel for the store manager."
    assert quote_in_resume(quote, RESUME)


def test_quote_found_with_surrounding_quotation_marks():
    assert quote_in_resume('"Answered customer questions"', RESUME)


def test_quote_not_in_resume():
    assert not quote_in_resume("Designed Tableau dashboards", RESUME)


def test_empty_quote_is_not_evidence():
    assert not quote_in_resume("", RESUME)
    assert not quote_in_resume("   ", RESUME)


def _verdict(index: int) -> BulletVerdict:
    return BulletVerdict(
        index=index, label="supported", evidence="x", reason="y"
    )


def test_verdicts_by_index_maps_bullet_numbers():
    result = JudgeResult(verdicts=[_verdict(1), _verdict(0)])
    verdicts = verdicts_by_index(result, bullet_count=2)
    assert set(verdicts) == {0, 1}


def test_verdicts_by_index_drops_out_of_range_and_allows_missing():
    result = JudgeResult(verdicts=[_verdict(0), _verdict(7)])
    verdicts = verdicts_by_index(result, bullet_count=3)
    assert set(verdicts) == {0}
