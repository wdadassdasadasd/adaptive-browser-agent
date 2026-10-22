"""Explicit requested quantities count researched subjects, not pages or facts."""

import pytest

from adaptive_research.agent.goal_count import (
    parse_goal_targets,
    subject_in_evidence,
    targets_met,
    verified_subject_counts,
)
from adaptive_research.agent.state import ResearchFact


def fact(subject: str, kind: str, url: str) -> ResearchFact:
    return ResearchFact(
        content=f"{subject} is documented",
        source_url=url,
        source_title="Official documentation",
        evidence=f"{subject} is documented",
        subject=subject,
        subject_kind=kind,
    )


def test_common_english_and_chinese_counts_are_recognized() -> None:
    assert parse_goal_targets("Find two publicly documented Python projects") == {
        "project": 2
    }
    assert parse_goal_targets("找 3 个公开项目") == {"project": 3}
    assert parse_goal_targets("总结两项更新") == {"change": 2}
    assert parse_goal_targets("Find one repository") == {"project": 1}
    assert parse_goal_targets("Find me three projects") == {"project": 3}


def test_conflicting_or_ambiguous_numbers_do_not_trigger_count_stop() -> None:
    assert parse_goal_targets("Find 2 projects and 3 projects") == {}
    assert parse_goal_targets("Compare FastAPI 2.0 and Flask") == {}
    assert parse_goal_targets("Compare Python 3 projects") == {}


def test_only_distinct_matching_sourced_subjects_count() -> None:
    targets = {"project": 2}
    facts = [
        fact("FastAPI", "project", "https://example.com/one"),
        fact(" fastapi ", "project", "https://example.com/two"),
        fact("Release note", "change", "https://example.com/three"),
    ]
    assert not targets_met(targets, facts)
    assert targets_met(
        targets,
        facts + [fact("Flask", "project", "https://example.com/four")],
    )


def test_subject_prefix_inside_different_name_does_not_count() -> None:
    target = {"project": 1}
    renamed = ResearchFact(
        content="FastAPI2 is documented",
        source_url="https://example.com/fastapi2",
        source_title="Official documentation",
        evidence="FastAPI2 is documented",
        subject="FastAPI",
        subject_kind="project",
    )

    assert not targets_met(target, [renamed])


def test_chinese_subject_name_can_appear_inside_sentence() -> None:
    assert subject_in_evidence("快速工具", "这个快速工具支持搜索")


def test_exact_official_repository_url_counts_project_identity() -> None:
    anchored = ResearchFact(
        content="Python version of the Playwright testing and automation library",
        source_url="https://api.github.com/repos/microsoft/playwright-python",
        source_title="Official GitHub repository metadata",
        evidence="Python version of the Playwright testing and automation library",
        subject="microsoft/playwright-python",
        subject_kind="project",
    )
    assert verified_subject_counts([anchored]) == {"project": 1}
    assert targets_met({"project": 1}, [anchored])
    assert not targets_met(
        {"project": 1},
        [
            anchored.model_copy(
                update={"source_url": "https://api.github.com/search/repositories"}
            )
        ],
    )


def test_github_topic_page_does_not_anchor_repository_identity() -> None:
    topic = ResearchFact(
        content="Python topic page",
        source_url="https://github.com/topics/python",
        source_title="GitHub topics",
        evidence="Discover repositories related to Python",
        subject="topics/python",
        subject_kind="project",
    )
    assert verified_subject_counts([topic]) == {}
    assert not targets_met({"project": 1}, [topic])


@pytest.mark.parametrize("route", ["sponsors", "apps", "issues", "pulls"])
def test_other_github_site_routes_do_not_anchor_repository_identity(
    route: str,
) -> None:
    page = ResearchFact(
        content="GitHub site page",
        source_url=f"https://github.com/{route}/python",
        source_title="GitHub",
        evidence="Generic site content",
        subject=f"{route}/python",
        subject_kind="project",
    )
    assert verified_subject_counts([page]) == {}
