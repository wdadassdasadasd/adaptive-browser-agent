"""Protocol invariants, fake dispatch, and no-secret attempt persistence."""

import json
import subprocess
from types import SimpleNamespace

import pytest

from adaptive_agent.state import ToolResult
from benchmark.adaptive import run_adaptive
from benchmark.baseline import run_baseline
from benchmark.cases import CASES
from benchmark.metrics import duplicate_url_count, score_answer
from benchmark.runner import (
    ARMS,
    _git_revision,
    _run_live,
    _safe_url,
    _summarize_directory,
    _working_tree_fingerprint,
    attempt,
    redact,
    save_record,
    schedule,
    summarize,
)


def test_gitlink_and_checked_out_head_are_recorded_separately(monkeypatch):
    commands = []

    def fake_run(command, **_kwargs):
        commands.append(command)
        output = (
            "160000 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 0\tbrowser-use\n"
            if command[:2] == ["git", "ls-files"]
            else "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\n"
        )
        return subprocess.CompletedProcess(command, 0, stdout=output)

    monkeypatch.setattr("benchmark.runner.subprocess.run", fake_run)
    assert _git_revision("browser-use", gitlink=True) == "a" * 40
    assert _git_revision("browser-use") == "b" * 40
    assert commands[1] == ["git", "-C", "browser-use", "rev-parse", "HEAD"]


def test_working_tree_fingerprint_changes_with_tracked_bytes(monkeypatch):
    tracked = {"bytes": b"first patch"}

    def fake_run(command, **_kwargs):
        output = tracked["bytes"] if "diff" in command else b""
        return subprocess.CompletedProcess(command, 0, stdout=output)

    monkeypatch.setattr("benchmark.runner.subprocess.run", fake_run)
    first_dirty, first_hash = _working_tree_fingerprint()
    tracked["bytes"] = b"second patch"
    second_dirty, second_hash = _working_tree_fingerprint()
    assert first_dirty and second_dirty
    assert first_hash != second_hash


def test_working_tree_fingerprint_includes_upstream_dirty_bytes(monkeypatch):
    upstream = {"bytes": b"first upstream patch"}

    def fake_run(command, **kwargs):
        is_upstream = kwargs["cwd"].name == "browser-use"
        output = upstream["bytes"] if is_upstream and "diff" in command else b""
        return subprocess.CompletedProcess(command, 0, stdout=output)

    monkeypatch.setattr("benchmark.runner.subprocess.run", fake_run)
    first_dirty, first_hash = _working_tree_fingerprint()
    upstream["bytes"] = b"second upstream patch"
    second_dirty, second_hash = _working_tree_fingerprint()
    assert first_dirty and second_dirty
    assert first_hash != second_hash


def test_malformed_observed_url_is_redacted_without_losing_attempt():
    assert _safe_url("https://example.org:bad/path?token=secret") == "[REDACTED_URL]"


def test_standalone_provider_credentials_are_redacted_from_answer():
    cleaned = redact("The page showed sk-abc123UNKNOWN and ghp_abc123UNKNOWN")
    assert "sk-abc123UNKNOWN" not in cleaned
    assert "ghp_abc123UNKNOWN" not in cleaned


@pytest.mark.asyncio
async def test_attempt_records_working_tree_fingerprint():
    async def baseline(_task):
        return {"status": "failed", "steps": 0}

    record = await attempt("B01", "baseline", 1, baseline=baseline)
    assert record["git_revisions"]["project_worktree_sha256"] is not None


def test_observed_nonofficial_url_path_cannot_persist_page_secret():
    assert (
        _safe_url("https://example.org/private/opaque-credential")
        == "https://example.org"
    )
    assert (
        _safe_url("https://github.com/acme/browserx")
        == "https://github.com/acme/browserx"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("scheme", ["https", "HTTPS"])
async def test_attempt_record_redacts_secret_in_nonofficial_url_path(tmp_path, scheme):
    secret_url = f"{scheme}://example.org/private/opaque-credential"

    async def baseline(_task):
        return {
            "status": "failed",
            "answer": secret_url,
            "urls": [secret_url],
            "trace": [f"Visited {secret_url}"],
            "steps": 1,
            "prompt_tokens": None,
            "completion_tokens": None,
            "budget_parity": "mismatched",
        }

    record = await attempt("B01", "baseline", 1, baseline=baseline)
    payload = save_record(record, tmp_path).read_text(encoding="utf-8")
    assert "opaque-credential" not in payload
    assert record["source_urls"] == ["https://example.org"]


@pytest.mark.asyncio
async def test_attempt_record_redacts_secret_in_official_url_path(tmp_path):
    secret_url = "https://github.com/acme/repo/blob/main/api_key=my-secret"

    async def baseline(_task):
        return {
            "status": "failed",
            "answer": secret_url,
            "urls": [secret_url],
            "trace": [f"Visited {secret_url}"],
            "steps": 1,
            "prompt_tokens": None,
            "completion_tokens": None,
            "budget_parity": "mismatched",
        }

    record = await attempt("B01", "baseline", 1, baseline=baseline)
    payload = save_record(record, tmp_path).read_text(encoding="utf-8")
    assert "my-secret" not in payload
    assert "api_key" not in payload


@pytest.mark.asyncio
async def test_attempt_record_omits_extracted_page_secrets_from_trace(tmp_path):
    async def baseline(_task):
        return {
            "status": "completed",
            "answer": "Name: BrowserX; License: MIT; pip install browserx. https://github.com/acme/browserx",
            "trace": ["Result 1: sessionid=abc123 private_key=xyz987"],
            "steps": 1,
        }

    record = await attempt("B01", "baseline", 1, baseline=baseline)
    payload = save_record(record, tmp_path).read_text(encoding="utf-8")
    assert "abc123" not in payload
    assert "xyz987" not in payload
    assert record["trace"] == [{"step": 1, "content": "[REDACTED_PAGE_TEXT]"}]


def test_duplicate_url_normalization_preserves_path_query_case_and_slash():
    urls = [
        "https://example.org/Docs/Page?q=FastAPI",
        "HTTPS://EXAMPLE.ORG/docs/page?q=FastAPI",
        "https://example.org/Docs/Page?q=fastapi",
        "https://example.org/Docs/Page/?q=FastAPI",
    ]
    assert duplicate_url_count(urls) == 0
    assert duplicate_url_count([urls[0], urls[0] + "#fragment"]) == 1


def test_fixed_schedule_rotates_and_contains_18_unique_attempts():
    plan = schedule(tuple(CASES), ARMS, 2)
    assert len(plan) == len(set(plan)) == 18
    assert plan[:3] == [
        ("B01", "baseline", 1),
        ("B01", "adaptive-full", 1),
        ("B01", "adaptive-browser-only", 1),
    ]
    assert [arm for case, arm, repeat in plan if case == "B01" and repeat == 2] == [
        "adaptive-full",
        "adaptive-browser-only",
        "baseline",
    ]
    assert all(CASES[case] for case, _, _ in plan)


def test_scorer_requires_official_source_and_explicit_values():
    empty = score_answer("B02", "FastAPI and Flask are excellent. https://example.com")
    assert not any(empty.values())
    sourced = score_answer(
        "B02",
        "FastAPI: route @app.get; async def handler; pip install fastapi. https://fastapi.tiangolo.com/tutorial/first-steps/",
    )
    assert all(value for key, value in sourced.items() if key.startswith("fastapi_"))
    assert not any(value for key, value in sourced.items() if key.startswith("flask_"))
    release = score_answer(
        "B03",
        "v1.2.3 released 2026-01-02.\n- Added a feature\n- Fixed a bug\nhttps://github.com/browser-use/browser-use/releases/tag/v1.2.3",
    )
    assert all(release.values())
    bare = score_answer(
        "B03", "https://github.com/browser-use/browser-use/releases/tag/v1.2.3"
    )
    assert not any(bare.values())


def test_comparison_does_not_award_two_projects_from_one_ambiguous_evidence_block():
    answer = (
        "FastAPI and Flask: route @app.get; async def handler; "
        "pip install fastapi; pip install flask. "
        "https://fastapi.tiangolo.com/tutorial/first-steps/ "
        "https://flask.palletsprojects.com/en/stable/quickstart/"
    )
    assert not any(score_answer("B02", answer).values())


def test_separately_cited_rows_in_one_section_are_scored_per_project():
    candidates = (
        "| Project | License | Install | Source |\n"
        "| BrowserX | MIT | pip install browserx | https://github.com/acme/browserx |\n"
        "| BrowserY | Apache-2.0 | pip install browsery | https://github.com/acme/browsery |"
    )
    assert all(score_answer("B01", candidates).values())
    comparison = (
        "FastAPI: route @app.get; async def handler; pip install fastapi. "
        "https://fastapi.tiangolo.com/tutorial/first-steps/\n"
        "Flask: route @app.route; async view supported; pip install flask. "
        "https://flask.palletsprojects.com/en/stable/quickstart/"
    )
    assert all(score_answer("B02", comparison).values())


def test_comparison_heading_does_not_contaminate_separately_sourced_rows():
    answer = (
        "## FastAPI vs Flask\n"
        "FastAPI: route @app.get; async handler supported; pip install fastapi. "
        "https://fastapi.tiangolo.com/tutorial/first-steps/\n"
        "Flask: route @app.route; async view supported; pip install flask. "
        "https://flask.palletsprojects.com/en/stable/quickstart/"
    )
    assert all(score_answer("B02", answer).values())


def test_multiline_candidate_claims_keep_each_adjacent_source():
    answer = (
        "- Playwright: Apache-2.0; pip install playwright\n"
        "  Source: https://github.com/microsoft/playwright-python\n"
        "- Selenium: Apache-2.0; pip install selenium\n"
        "  Source: https://github.com/SeleniumHQ/selenium"
    )
    assert all(score_answer("B01", answer).values())


def test_release_version_must_match_cited_tag_and_changes_need_descriptions():
    answer = (
        "Version v9.9.9, published 2026-01-02. "
        "https://github.com/browser-use/browser-use/releases/tag/v1.2.3\n\n"
        "### Added\n### Fixed\n"
        "https://github.com/browser-use/browser-use/releases/tag/v1.2.3"
    )
    fields = score_answer("B03", answer)
    assert fields["official_release_source"]
    assert not fields["version"]
    assert not fields["change_1"]
    assert not fields["change_2"]


def test_release_claimed_latest_version_cannot_use_older_tag_as_support():
    answer = (
        "Latest release: v2.0.0, published 2026-01-02. "
        "The previous v1.0.0 release added tabs and fixed scrolling. "
        "https://github.com/browser-use/browser-use/releases/tag/v1.0.0"
    )
    assert not score_answer("B03", answer)["version"]


def test_release_later_latest_claim_cannot_use_earlier_release_citation():
    answer = (
        "Previous release v1.2.3, published 2026-01-02. Added tabs. Fixed scrolling. "
        "https://github.com/browser-use/browser-use/releases/tag/v1.2.3\n\n"
        "Latest release v2.0.0 is now available."
    )
    fields = score_answer("B03", answer)
    assert not fields["version"]
    assert not all(fields.values())


def test_release_latest_claim_can_follow_previous_version_on_same_line():
    answer = (
        "Previous release v1.2.3, latest release v2.0.0, published 2026-01-02. "
        "Added tabs. Fixed scrolling. "
        "https://github.com/browser-use/browser-use/releases/tag/v2.0.0"
    )
    assert score_answer("B03", answer)["version"]


def test_release_unfinished_section_does_not_supply_coverage():
    answer = (
        "## Findings\nNo verified findings.\n\n"
        "## Unknown or unfinished\n"
        "- Verify whether latest release v1.2.3 was published 2026-01-02.\n"
        "- Check if it added tabs and fixed scrolling.\n\n"
        "## Sources\n"
        "- https://github.com/browser-use/browser-use/releases/tag/v1.2.3"
    )
    assert not any(score_answer("B03", answer).values())


def test_candidate_score_rejects_nonrepository_and_shared_paragraph_claims():
    arbitrary = score_answer(
        "B01",
        "Name: BrowserX; License: MIT; pip install browserx. https://unrelated.example.org/page",
    )
    assert not any(arbitrary.values())
    shared = score_answer(
        "B01",
        "Name: BrowserX; License: MIT; pip install browserx. "
        "https://github.com/acme/browserx https://github.com/acme/browsery",
    )
    assert not any(
        value for key, value in shared.items() if key.startswith("project_2_")
    )


def test_candidate_score_accepts_two_separately_sourced_projects():
    answer = (
        "Name: BrowserX; License: MIT; pip install browserx. "
        "https://github.com/acme/browserx\n\n"
        "Name: BrowserY; License: Apache-2.0; pip install browsery. "
        "https://github.com/acme/browsery"
    )
    assert all(score_answer("B01", answer).values())


def test_candidate_accepts_github_api_evidence_but_still_requires_repository_url():
    answer = (
        "Name: BrowserX; License: MIT. https://api.github.com/repos/acme/browserx\n\n"
        "Install: pip install browserx. https://github.com/acme/browserx\n\n"
        "Name: BrowserY; License: MIT; pip install browsery. "
        "https://github.com/acme/browsery"
    )
    assert all(score_answer("B01", answer).values())
    api_only = score_answer(
        "B01",
        "Name: BrowserX; License: MIT; pip install browserx. "
        "https://api.github.com/repos/acme/browserx",
    )
    assert api_only["project_1_name"] and api_only["project_1_license"]
    assert not api_only["project_1_repository"]


def test_candidate_install_option_without_package_does_not_score():
    answer = (
        "Name: BrowserX; License: MIT; pip install -U. "
        "https://github.com/acme/browserx\n\n"
        "Name: BrowserY; License: MIT; pip install -U. "
        "https://github.com/acme/browsery"
    )
    fields = score_answer("B01", answer)
    assert not fields["project_1_install"]
    assert not fields["project_2_install"]


def test_candidate_install_must_name_the_sourced_project():
    answer = (
        "### Playwright\nPlaywright: License MIT; pip install flask. "
        "https://github.com/microsoft/playwright-python\n\n"
        "### Selenium\nSelenium: License Apache-2.0; pip install django. "
        "https://github.com/SeleniumHQ/selenium"
    )
    fields = score_answer("B01", answer)
    assert not fields["project_1_install"]
    assert not fields["project_2_install"]


def test_candidate_install_does_not_match_generic_repository_prefix():
    answer = (
        "Name: browser-use; License: MIT; pip install browser. "
        "https://github.com/browser-use/browser-use\n\n"
        "Name: Selenium; License: Apache-2.0; pip install selenium. "
        "https://github.com/SeleniumHQ/selenium"
    )
    fields = score_answer("B01", answer)
    assert sum(fields[f"project_{index}_install"] for index in (1, 2)) == 1


def test_candidate_score_selects_complete_projects_after_contextual_repository():
    answer = (
        "Background repository: https://github.com/acme/background\n\n"
        "Name: BrowserX; License: MIT; pip install browserx. "
        "https://github.com/acme/browserx\n\n"
        "Name: BrowserY; License: Apache-2.0; pip install browsery. "
        "https://github.com/acme/browsery"
    )
    assert all(score_answer("B01", answer).values())


def test_candidate_score_aggregates_separately_sourced_fields_per_repository():
    answer = (
        "### BrowserX\nLicense: MIT. https://github.com/acme/browserx\n\n"
        "Install with pip install browserx. https://github.com/acme/browserx\n\n"
        "### BrowserY\nLicense: Apache-2.0; pip install browsery. "
        "https://github.com/acme/browsery"
    )
    assert all(score_answer("B01", answer).values())


def test_candidate_issue_links_do_not_count_as_repository_urls():
    answer = (
        "Name: BrowserX; License: MIT; pip install browserx. "
        "https://github.com/acme/browserx/issues/123\n\n"
        "Name: BrowserY; License: MIT; pip install browsery. "
        "https://github.com/acme/browsery/issues/456"
    )
    fields = score_answer("B01", answer)
    assert not fields["project_1_repository"]
    assert not fields["project_2_repository"]


def test_release_listing_page_alone_cannot_support_release_fields():
    answer = (
        "Version v1.2.3, published 2026-01-02. "
        "Added tab support. Fixed scrolling. "
        "https://github.com/browser-use/browser-use/releases/"
    )
    assert not any(score_answer("B03", answer).values())


def test_release_rephrased_same_change_is_not_counted_twice():
    answer = (
        "Version v1.2.3, published 2026-01-02. "
        "Added tab support. Adds tab support. "
        "https://github.com/browser-use/browser-use/releases/tag/v1.2.3"
    )
    fields = score_answer("B03", answer)
    assert fields["change_1"]
    assert not fields["change_2"]


def test_release_vague_issue_and_docs_do_not_count_as_changes():
    answer = (
        "Version v1.2.3, published 2026-01-02. Fixed issue. Updated docs. "
        "https://github.com/browser-use/browser-use/releases/tag/v1.2.3"
    )
    fields = score_answer("B03", answer)
    assert not fields["change_1"]
    assert not fields["change_2"]


def test_release_changes_heading_is_not_a_second_change():
    answer = (
        "Version v1.2.3, published 2026-01-02.\n"
        "### Changes in this release\n- Added tab support\n"
        "https://github.com/browser-use/browser-use/releases/tag/v1.2.3"
    )
    fields = score_answer("B03", answer)
    assert fields["change_1"]
    assert not fields["change_2"]


def test_release_task_title_does_not_count_as_a_second_change():
    answer = (
        "## Find browser-use v1.2.3 release date and two changes from its release notes\n"
        "Version v1.2.3, published 2026-01-02.\n"
        "- Added tab support.\n"
        "https://github.com/browser-use/browser-use/releases/tag/v1.2.3"
    )
    fields = score_answer("B03", answer)
    assert fields["change_1"]
    assert not fields["change_2"]


def test_release_source_label_alone_scores_no_fields():
    answer = "- Source: https://github.com/browser-use/browser-use/releases/tag/v1.2.3"
    assert not any(score_answer("B03", answer).values())


def test_release_date_must_be_identified_as_publication_date():
    answer = (
        "Version v1.2.3. Research performed 2026-10-14. "
        "Added tab support. Fixed scrolling. "
        "https://github.com/browser-use/browser-use/releases/tag/v1.2.3"
    )
    fields = score_answer("B03", answer)
    assert fields["version"] and fields["change_1"] and fields["change_2"]
    assert not fields["publication_date"]


def test_release_inline_code_citation_is_recognized():
    answer = (
        "Version v1.2.3, published 2026-01-02. "
        "Added tab support. Fixed scrolling. "
        "`https://github.com/browser-use/browser-use/releases/tag/v1.2.3`"
    )
    assert all(score_answer("B03", answer).values())


def test_release_date_adjacent_to_version_counts_as_publication_date():
    answer = (
        "v1.2.3 (2026-01-02): Added tracing; Fixed timeout. "
        "https://github.com/browser-use/browser-use/releases/tag/v1.2.3"
    )
    assert score_answer("B03", answer)["publication_date"]


def test_comparison_plural_async_views_are_scored_with_flask_source():
    answer = (
        "Flask supports async views. "
        "https://flask.palletsprojects.com/en/stable/async-await/"
    )
    assert score_answer("B02", answer)["flask_async"]


def test_comparison_documentation_homepages_do_not_support_exact_fields():
    answer = (
        "FastAPI: route @app.get; async def handler; pip install fastapi. "
        "https://fastapi.tiangolo.com/\n\n"
        "Flask: route @app.route; async views supported; pip install flask. "
        "https://flask.palletsprojects.com/en/stable/"
    )
    assert not all(score_answer("B02", answer).values())


def test_comparison_allows_contrast_mention_with_one_official_source():
    answer = (
        "FastAPI uses @app.get, unlike Flask; async def is supported; "
        "pip install fastapi. "
        "https://fastapi.tiangolo.com/tutorial/first-steps/"
    )
    fields = score_answer("B02", answer)
    assert all(value for key, value in fields.items() if key.startswith("fastapi_"))
    assert not any(value for key, value in fields.items() if key.startswith("flask_"))


def test_comparison_does_not_attribute_other_framework_claim_to_cited_host():
    answer = (
        "Flask uses @app.route, unlike FastAPI; async views are supported; "
        "pip install flask. "
        "https://fastapi.tiangolo.com/tutorial/first-steps/"
    )
    fields = score_answer("B02", answer)
    assert not any(value for key, value in fields.items() if key.startswith("fastapi_"))


def test_comparison_quoted_fastapi_install_is_scored():
    answer = (
        'FastAPI: pip install "fastapi[standard]". '
        "https://fastapi.tiangolo.com/tutorial/first-steps/"
    )
    assert score_answer("B02", answer)["fastapi_install"]


def test_release_single_final_source_supports_separate_claim_sections():
    answer = (
        "### Version\nv1.2.3, published 2026-01-02.\n"
        "### Changes\n- Added tab support\n- Fixed scrolling\n"
        "### Sources\nhttps://github.com/browser-use/browser-use/releases/tag/v1.2.3"
    )
    assert all(score_answer("B03", answer).values())


def test_candidate_score_accepts_gitlab_official_repository():
    answer = (
        "Name: BrowserX; License: MIT; pip install browserx. "
        "https://gitlab.com/acme/browserx\n\n"
        "Name: BrowserY; License: MIT; pip install browsery. "
        "https://github.com/acme/browsery"
    )
    assert all(score_answer("B01", answer).values())


def test_candidate_score_distinguishes_nested_gitlab_repositories():
    answer = (
        "Name: BrowserX; License: MIT; pip install browserx. "
        "https://gitlab.com/group/subgroup/browserx\n\n"
        "Name: BrowserY; License: MIT; pip install browsery. "
        "https://gitlab.com/group/subgroup/browsery"
    )
    assert all(score_answer("B01", answer).values())


def test_gitlab_issue_link_cannot_create_a_second_candidate():
    answer = (
        "Name: browser-use; License: MIT; pip install browser-use. "
        "https://gitlab.com/team/browser-use\n\n"
        "Name: browser-use; License: MIT; pip install browser-use. "
        "https://gitlab.com/team/browser-use/issues/7"
    )
    assert not all(score_answer("B01", answer).values())


def test_candidate_score_accepts_project_name_in_report_heading():
    answer = (
        "## Findings\n### BrowserX\nLicense: MIT; pip install browserx\n"
        "- Source: https://github.com/acme/browserx\n"
        "### BrowserY\nLicense: Apache-2.0; pip install browsery\n"
        "- Source: https://github.com/acme/browsery"
    )
    assert all(score_answer("B01", answer).values())


def test_candidate_score_accepts_name_and_license_in_normal_prose():
    answer = (
        "### Playwright\nPlaywright is licensed under Apache-2.0; "
        "install with pip install playwright.\n"
        "- Source: https://github.com/microsoft/playwright-python\n"
        "### Selenium\nSelenium uses the Apache-2.0 license; "
        "pip install selenium.\n"
        "- Source: https://github.com/SeleniumHQ/selenium"
    )
    assert all(score_answer("B01", answer).values())


def test_release_score_does_not_count_unrelated_bullets_as_changes():
    answer = (
        "v1.2.3 released 2026-01-02.\n- License: MIT\n- Maintainer: Team\n"
        "https://github.com/browser-use/browser-use/releases/tag/v1.2.3"
    )
    fields = score_answer("B03", answer)
    assert fields["version"] and fields["publication_date"]
    assert not fields["change_1"] and not fields["change_2"]


def test_release_score_accepts_sourced_report_finding_headings():
    answer = (
        "## Findings\n### Added tab support\nVersion v1.2.3, published 2026-01-02.\n"
        "- Source: https://github.com/browser-use/browser-use/releases/tag/v1.2.3\n"
        "### Fixed scrolling\nScrolling now works.\n"
        "- Source: https://github.com/browser-use/browser-use/releases/tag/v1.2.3"
    )
    assert all(score_answer("B03", answer).values())


def test_release_score_accepts_two_sourced_changes_in_prose_and_inline_bullets():
    prose = (
        "Version v1.2.3 was published 2026-01-02. This release adds tab support "
        "and fixes scrolling. "
        "https://github.com/browser-use/browser-use/releases/tag/v1.2.3"
    )
    assert all(score_answer("B03", prose).values())
    inline = (
        "Version v1.2.3 was published 2026-01-02.\n"
        "- Added tab support https://github.com/browser-use/browser-use/releases/tag/v1.2.3\n"
        "- Fixed scrolling https://github.com/browser-use/browser-use/releases/tag/v1.2.3"
    )
    assert all(score_answer("B03", inline).values())


def test_redaction_removes_every_cookie_pair_from_headers():
    cleaned = redact(
        "Cookie: sessionid=abc123; csrftoken=xyz789\n"
        "Set-Cookie: auth=topsecret; Path=/; HttpOnly"
    )
    assert "abc123" not in cleaned
    assert "xyz789" not in cleaned
    assert "topsecret" not in cleaned


def test_redaction_removes_basic_authorization_and_named_access_tokens():
    cleaned = redact(
        "Authorization: Basic dXNlcjpwYXNz\naccess_token: abc123 refresh_token=def456"
    )
    assert "dXNlcjpwYXNz" not in cleaned
    assert "abc123" not in cleaned
    assert "def456" not in cleaned


def test_redaction_removes_credentials_from_quoted_json_text():
    cleaned = redact(
        '{"authorization": "Basic dXNlcjpwYXNz", '
        '"api_key": "sk-example", "access_token": "abc123"}'
    )
    assert "dXNlcjpwYXNz" not in cleaned
    assert "sk-example" not in cleaned
    assert "abc123" not in cleaned


def test_redaction_sanitizes_uppercase_url_scheme():
    cleaned = redact("HTTPS://example.org/private/opaque?auth=hidden-value")
    assert "opaque" not in cleaned
    assert "hidden-value" not in cleaned
    assert "https://example.org" in cleaned.lower()


@pytest.mark.asyncio
async def test_browser_version_probe_uses_and_closes_upstream_session():
    from benchmark.runner import _browser_version

    calls = []

    class FakeBrowser:
        cdp_client = SimpleNamespace(
            send=SimpleNamespace(
                Browser=SimpleNamespace(getVersion=lambda: get_version())
            )
        )

        async def start(self):
            calls.append("start")

        async def kill(self):
            calls.append("kill")

    async def get_version():
        calls.append("getVersion")
        return {"product": "Chrome/130.0.1"}

    assert await _browser_version(FakeBrowser) == "Chrome/130.0.1"
    assert calls == ["start", "getVersion", "kill"]


@pytest.mark.asyncio
async def test_live_run_populates_browser_version_in_every_attempt(
    tmp_path, monkeypatch
):
    from benchmark import runner

    observed = []

    async def fake_version():
        return "Chrome/130.0.1"

    async def fake_attempt(case, arm, repetition, *, environment=None):
        observed.append(environment)
        return {
            "case": case,
            "arm": arm,
            "repetition": repetition,
            "status": "failed",
            "coverage": 0.0,
            "steps": 0,
            "duplicate_urls": 0,
            "duration_seconds": 0.1,
            "prompt_tokens": None,
            "completion_tokens": None,
            "budget_parity": "mismatched",
            "manual_contradiction_note": None,
            "environment": environment,
        }

    monkeypatch.setattr(runner, "_browser_version", fake_version, raising=False)
    monkeypatch.setattr(runner, "attempt", fake_attempt)
    await _run_live(tmp_path, [("B01", "baseline", 1)], run_id="version-run")
    assert len(observed) == 1
    assert observed[0]["browser"] == "Chrome/130.0.1"
    assert observed[0]["network"] == "unverified"


@pytest.mark.asyncio
async def test_live_run_retains_attempt_if_browser_version_probe_fails(
    tmp_path, monkeypatch
):
    from benchmark import runner

    async def broken_version():
        raise RuntimeError("probe failed")

    async def fake_attempt(case, arm, repetition, *, environment=None):
        return {
            "case": case,
            "arm": arm,
            "repetition": repetition,
            "status": "failed",
            "coverage": 0.0,
            "steps": 0,
            "duplicate_urls": 0,
            "duration_seconds": 0.1,
            "prompt_tokens": None,
            "completion_tokens": None,
            "budget_parity": "mismatched",
            "manual_contradiction_note": None,
            "environment": environment,
        }

    monkeypatch.setattr(runner, "_browser_version", broken_version)
    monkeypatch.setattr(runner, "attempt", fake_attempt)
    await _run_live(tmp_path, [("B01", "baseline", 1)], run_id="probe-failed")
    record = json.loads(
        (tmp_path / "probe-failed" / "B01_baseline_r1.json").read_text()
    )
    assert record["environment"]["browser"] == "unverified"
    assert record["environment"]["browser_version_error"] == "RuntimeError"


def test_redaction_keeps_usage_fields_while_removing_credentials():
    cleaned = redact({"prompt_tokens": 42, "api_key": "secret-value"})
    assert cleaned == {"prompt_tokens": 42, "api_key": "[REDACTED]"}


@pytest.mark.asyncio
async def test_adaptive_counts_repeated_observed_urls_without_state_dedup_loss():
    events = [
        SimpleNamespace(
            event_type="step_evaluated",
            payload={
                "tool_result": {
                    "tool": "browser",
                    "success": True,
                    "source_url": "https://example.org/a",
                }
            },
            model_dump=lambda **_: {"event_type": "step_evaluated"},
        ),
        SimpleNamespace(
            event_type="step_evaluated",
            payload={
                "tool_result": {"tool": "browser", "success": False, "source_url": None}
            },
            model_dump=lambda **_: {"event_type": "step_evaluated"},
        ),
    ]

    class FakeLoop:
        async def run(self, _task):
            return SimpleNamespace(
                report=SimpleNamespace(markdown="answer"),
                state=SimpleNamespace(
                    visited_urls=["https://example.org/a"],
                    step=2,
                    prompt_tokens=10,
                    completion_tokens=5,
                    status="completed",
                    stop_reason=None,
                ),
                events=events,
            )

    result = await run_adaptive(CASES["B01"], loop_factory=lambda _: FakeLoop())
    assert result["urls"] == ["https://example.org/a"]
    assert result["source_urls"] == ["https://example.org/a"]
    record = await attempt(
        "B01",
        "adaptive-browser-only",
        1,
        adaptive=lambda _task, *, browser_only: run_adaptive(
            _task, browser_only=browser_only, loop_factory=lambda _: FakeLoop()
        ),
    )
    assert record["duplicate_urls"] == 0


@pytest.mark.asyncio
async def test_adaptive_preserves_completed_tool_at_time_limit():
    pending = ToolResult(
        tool="browser",
        action="navigate",
        success=True,
        content="Navigated",
        source_url="https://example.org/a",
    )

    class FakeLoop:
        async def run(self, _task):
            return SimpleNamespace(
                report=None,
                state=SimpleNamespace(
                    visited_urls=[],
                    step=0,
                    prompt_tokens=10,
                    completion_tokens=5,
                    status="failed",
                    stop_reason="time_limit",
                ),
                events=(),
                pending_tool_result=pending,
            )

    result = await run_adaptive(CASES["B01"], loop_factory=lambda _: FakeLoop())
    assert result["status"] == "failed"
    assert result["steps"] == 1
    assert result["urls"] == ["https://example.org/a"]
    assert result["trace"] == [
        {"tool": "browser", "action": "navigate", "success": True, "error_type": "none"}
    ]


@pytest.mark.asyncio
async def test_adaptive_counts_actual_browser_url_revisit():
    urls = [
        "https://example.org/a",
        "https://example.org/a",
        "https://example.org/b",
        "https://example.org/a",
    ]
    actions = ["navigate", "click", "navigate", "go_back"]
    events = [
        SimpleNamespace(
            event_type="step_evaluated",
            payload={
                "tool_result": {
                    "tool": "browser",
                    "action": action,
                    "success": True,
                    "source_url": url,
                }
            },
        )
        for action, url in zip(actions, urls, strict=True)
    ]

    class FakeLoop:
        async def run(self, _task):
            return SimpleNamespace(
                report=None,
                state=SimpleNamespace(
                    visited_urls=list(dict.fromkeys(urls)),
                    step=4,
                    prompt_tokens=0,
                    completion_tokens=0,
                    status="completed",
                    stop_reason=None,
                ),
                events=events,
            )

    result = await run_adaptive(CASES["B01"], loop_factory=lambda _: FakeLoop())
    assert result["urls"] == [urls[0], urls[2], urls[3]]
    assert duplicate_url_count(result["urls"]) == 1


@pytest.mark.asyncio
async def test_baseline_uses_upstream_history_and_marks_token_cap_mismatch():
    seen = {"closed": False}

    class FakeAgent:
        def __init__(self):
            self.history = SimpleNamespace(
                usage=None,
                history=[1],
                final_result=lambda: "answer",
                urls=lambda: [
                    "https://example.com",
                    "https://example.com",
                    "https://example.org",
                    "https://example.com",
                    None,
                ],
                agent_steps=lambda: ["step"],
                is_successful=lambda: True,
            )

        async def run(self, *, max_steps, on_step_end=None):
            seen["steps"] = max_steps
            return self.history

        async def close(self):
            seen["closed"] = True

    result = await run_baseline(CASES["B01"], agent_factory=lambda prompt: FakeAgent())
    assert seen["steps"] == 30
    assert result["status"] == "completed"
    assert result["prompt_tokens"] is None
    assert result["budget_parity"] == "mismatched"
    assert result["urls"] == [
        "https://example.com",
        "https://example.org",
        "https://example.com",
    ]
    assert seen["closed"] is True


@pytest.mark.asyncio
async def test_baseline_records_post_step_navigation_and_revisits():
    pre_urls = ["https://example.org/a", "https://example.org/b"]
    post_urls = ["https://example.org/b", "https://example.org/a"]

    class FakeAgent:
        def __init__(self):
            self.history = SimpleNamespace(
                usage=None,
                history=[
                    SimpleNamespace(model_output=None, result=[]) for _ in pre_urls
                ],
                final_result=lambda: "answer",
                urls=lambda: pre_urls,
                is_successful=lambda: True,
            )
            self.browser_session = SimpleNamespace(
                get_current_page_url=self.current_url
            )
            self.token_cost_service = SimpleNamespace(get_usage_summary=self.usage)
            self.index = 0

        async def current_url(self):
            return post_urls[self.index]

        async def usage(self):
            return SimpleNamespace(entry_count=0)

        async def run(self, *, max_steps, on_step_end):
            for index in range(len(post_urls)):
                self.index = index
                await on_step_end(self)
            return self.history

        async def close(self):
            pass

    result = await run_baseline(CASES["B01"], agent_factory=lambda _: FakeAgent())
    assert result["urls"] == [
        "https://example.org/a",
        "https://example.org/b",
        "https://example.org/a",
    ]


@pytest.mark.asyncio
async def test_baseline_keeps_url_order_when_timeout_has_no_history_item():
    pages = [
        "https://example.org/a",
        "https://example.org/b",
        "https://example.org/c",
        "https://example.org/d",
        "https://example.org/a",
    ]

    class FakeAgent:
        def __init__(self):
            self.history = SimpleNamespace(
                usage=None,
                history=[],
                final_result=lambda: "answer",
                urls=lambda: [item.state.url for item in self.history.history],
                is_successful=lambda: True,
            )
            self.browser_session = SimpleNamespace(
                get_current_page_url=self.current_url
            )
            self.token_cost_service = SimpleNamespace(get_usage_summary=self.usage)
            self.current = None

        async def current_url(self):
            return self.current

        async def usage(self):
            return SimpleNamespace(entry_count=0)

        async def run(self, *, max_steps, on_step_end):
            self.history.history.append(
                SimpleNamespace(
                    state=SimpleNamespace(url=pages[0]), model_output=None, result=[]
                )
            )
            self.current = pages[1]
            await on_step_end(self)
            self.current = pages[2]
            await on_step_end(self)  # timed-out step has no history entry
            self.history.history.append(
                SimpleNamespace(
                    state=SimpleNamespace(url=pages[3]), model_output=None, result=[]
                )
            )
            self.current = pages[4]
            await on_step_end(self)
            return self.history

        async def close(self):
            pass

    result = await run_baseline(CASES["B01"], agent_factory=lambda _: FakeAgent())
    assert result["urls"] == pages


@pytest.mark.asyncio
async def test_baseline_self_assessment_does_not_override_scored_completion():
    answer = (
        "Name: BrowserX; License: MIT; pip install browserx. "
        "https://github.com/acme/browserx\n\n"
        "Name: BrowserY; License: MIT; pip install browsery. "
        "https://github.com/acme/browsery"
    )

    class FakeAgent:
        history = SimpleNamespace(
            usage=None,
            history=[1],
            final_result=lambda: answer,
            urls=list,
            agent_steps=list,
            is_successful=lambda: False,
        )

        async def run(self, **_kwargs):
            return self.history

        async def close(self):
            pass

    result = await run_baseline(CASES["B01"], agent_factory=lambda _: FakeAgent())
    assert result["status"] == "completed"
    assert result["upstream_success"] is False

    async def baseline(_task):
        return result

    record = await attempt("B01", "baseline", 1, baseline=baseline)
    assert record["upstream_success"] is False
    assert record["coverage"] == 1
    record["manual_contradiction_note"] = "none"
    assert summarize([record])["arms"]["baseline"]["completion_rate"] == 1


@pytest.mark.asyncio
async def test_baseline_unfinished_upstream_run_is_a_failed_attempt():
    class FakeAgent:
        history = SimpleNamespace(
            usage=None,
            history=[1],
            final_result=lambda: "partial answer",
            urls=list,
            agent_steps=list,
            is_done=lambda: False,
            is_successful=lambda: False,
        )

        async def run(self, **_kwargs):
            return self.history

        async def close(self):
            pass

    result = await run_baseline(CASES["B01"], agent_factory=lambda _: FakeAgent())
    assert result["status"] == "failed"
    assert result["failure_reason"] == "upstream_unfinished"


@pytest.mark.asyncio
async def test_baseline_keeps_checked_out_agent_default_judge_setting(monkeypatch):
    import browser_use

    seen = {}

    class FakeAgent:
        def __init__(self, **kwargs):
            seen.update(kwargs)
            self.history = SimpleNamespace(
                usage=None,
                history=[],
                final_result=lambda: "",
                urls=list,
                agent_steps=list,
                is_successful=lambda: False,
            )

        async def run(self, **_kwargs):
            return self.history

        async def close(self):
            pass

    monkeypatch.setattr(browser_use, "Agent", FakeAgent)
    monkeypatch.setattr(browser_use, "ChatDeepSeek", lambda **kwargs: kwargs)
    await run_baseline(CASES["B01"])
    assert "use_judge" not in seen
    assert seen["llm"] == {"model": "deepseek-flash"}


@pytest.mark.asyncio
async def test_baseline_stops_after_observed_token_cap_and_records_breach():
    observed = SimpleNamespace(
        total_prompt_tokens=39_000,
        total_completion_tokens=1_001,
        total_tokens=40_001,
        entry_count=1,
    )

    class FakeAgent:
        def __init__(self):
            self.stopped = False
            self.token_cost_service = SimpleNamespace(get_usage_summary=self.usage)
            self.history = SimpleNamespace(
                usage=observed,
                history=[1],
                final_result=lambda: "answer",
                urls=list,
                agent_steps=lambda: ["step"],
                is_successful=lambda: True,
            )

        async def usage(self):
            return observed

        def stop(self):
            self.stopped = True

        async def run(self, *, max_steps, on_step_end):
            await on_step_end(self)
            return self.history

        async def close(self):
            pass

    agent = FakeAgent()
    result = await run_baseline(CASES["B01"], agent_factory=lambda _: agent)
    assert agent.stopped is True
    assert result["failure_reason"] == "token_budget_breach"


@pytest.mark.asyncio
async def test_baseline_preserves_success_at_exact_token_limit():
    observed = SimpleNamespace(
        total_prompt_tokens=39_000,
        total_completion_tokens=1_000,
        total_tokens=40_000,
        entry_count=1,
    )

    class FakeAgent:
        def __init__(self):
            self.stopped = False
            self.token_cost_service = SimpleNamespace(get_usage_summary=self.usage)
            self.history = SimpleNamespace(
                usage=observed,
                history=[1],
                final_result=lambda: "completed answer",
                urls=list,
                agent_steps=list,
                is_successful=lambda: True,
            )

        async def usage(self):
            return observed

        def stop(self):
            self.stopped = True

        async def run(self, *, max_steps, on_step_end):
            await on_step_end(self)
            return self.history

        async def close(self):
            pass

    agent = FakeAgent()
    result = await run_baseline(CASES["B01"], agent_factory=lambda _: agent)
    assert agent.stopped is True
    assert result["status"] == "completed"
    assert result["failure_reason"] is None


@pytest.mark.asyncio
async def test_baseline_token_cap_skips_upstream_judge_after_done_step():
    observed = SimpleNamespace(
        total_prompt_tokens=39_000,
        total_completion_tokens=1_000,
        total_tokens=40_000,
        entry_count=1,
    )

    class FakeAgent:
        def __init__(self):
            self.judge_calls = 0
            self.token_cost_service = SimpleNamespace(get_usage_summary=self.usage)
            self.history = SimpleNamespace(
                usage=None,
                history=[1],
                final_result=lambda: "complete answer",
                urls=list,
                agent_steps=list,
                is_successful=lambda: True,
            )

        async def usage(self):
            return observed

        def stop(self):
            pass

        async def run(self, *, max_steps, on_step_end):
            await on_step_end(self)
            self.judge_calls += 1
            return self.history

        async def close(self):
            pass

    agent = FakeAgent()
    result = await run_baseline(CASES["B01"], agent_factory=lambda _: agent)
    assert agent.judge_calls == 0
    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_interrupted_baseline_retains_observed_usage():
    observed = SimpleNamespace(
        total_prompt_tokens=39_500,
        total_completion_tokens=600,
        total_tokens=40_100,
        entry_count=1,
    )

    class FakeAgent:
        def __init__(self):
            self.token_cost_service = SimpleNamespace(get_usage_summary=self.usage)
            self.history = SimpleNamespace(
                usage=None,
                history=[1],
                final_result=lambda: "partial",
                urls=list,
                agent_steps=list,
                is_successful=lambda: False,
            )

        async def usage(self):
            return observed

        async def run(self, **_kwargs):
            raise TimeoutError

        async def close(self):
            pass

    result = await run_baseline(CASES["B01"], agent_factory=lambda _: FakeAgent())
    assert result["prompt_tokens"] == 39_500
    assert result["completion_tokens"] == 600
    assert result["failure_reason"] == "token_budget_breach"


@pytest.mark.asyncio
async def test_baseline_max_steps_sentinel_is_not_an_executed_step():
    sentinel = SimpleNamespace(
        model_output=None,
        result=[SimpleNamespace(error="Failed to complete task in maximum steps")],
        metadata=None,
        state=SimpleNamespace(url=""),
    )

    class FakeAgent:
        def __init__(self):
            self.history = SimpleNamespace(
                usage=None,
                history=[object()] * 30 + [sentinel],
                final_result=lambda: "",
                urls=list,
                agent_steps=list,
                is_successful=lambda: False,
            )

        async def run(self, **_kwargs):
            return self.history

        async def close(self):
            pass

    result = await run_baseline(CASES["B01"], agent_factory=lambda _: FakeAgent())
    assert result["steps"] == 30
    assert result["status"] == "failed"
    assert result["failure_reason"] == "step_budget_reached"


@pytest.mark.asyncio
async def test_citing_a_visited_url_does_not_count_as_repeated_navigation():
    async def baseline(_task):
        return {
            "status": "completed",
            "answer": "See https://github.com/acme/browserx",
            "urls": ["https://github.com/acme/browserx"],
            "trace": [],
            "steps": 1,
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "budget_parity": "mismatched",
        }

    record = await attempt("B01", "baseline", 1, baseline=baseline)
    assert record["duplicate_urls"] == 0
    assert record["source_urls"] == ["https://github.com/acme/browserx"]


@pytest.mark.asyncio
async def test_distinct_search_queries_are_not_counted_as_duplicate_visits():
    async def baseline(_task):
        return {
            "status": "completed",
            "answer": "",
            "urls": [
                "https://example.org/search?q=fastapi",
                "https://example.org/search?q=flask",
            ],
            "trace": [],
            "steps": 2,
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "budget_parity": "mismatched",
        }

    record = await attempt("B01", "baseline", 1, baseline=baseline)
    assert record["duplicate_urls"] == 0
    assert record["source_urls"] == ["https://example.org"]


@pytest.mark.asyncio
async def test_blank_browser_pages_are_not_duplicate_public_urls():
    async def baseline(_task):
        return {
            "status": "failed",
            "answer": "",
            "urls": ["about:blank", "about:blank"],
            "trace": [],
            "steps": 2,
            "prompt_tokens": None,
            "completion_tokens": None,
            "budget_parity": "mismatched",
        }

    record = await attempt("B01", "baseline", 1, baseline=baseline)
    assert record["duplicate_urls"] == 0
    assert record["source_urls"] == []


@pytest.mark.asyncio
async def test_three_arm_dispatch_redaction_and_failed_attempt(tmp_path, monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret-sentinel-123")
    calls = []

    async def baseline(task):
        calls.append(("baseline", task))
        return {
            "status": "completed",
            "answer": "token=secret-sentinel-123",
            "urls": ["https://example.com/path?key=secret-sentinel-123"],
            "trace": [
                "Authorization: Bearer secret-sentinel-123",
                "Authorization: Basic dXNlcjpwYXNz",
                "access_token: abc123 refresh_token=def456",
                '{"authorization": "Basic dXNlcjpwYXNz", "api_key": "sk-example"}',
            ],
            "steps": 1,
            "prompt_tokens": None,
            "completion_tokens": None,
            "budget_parity": "mismatched",
        }

    async def adaptive(task, *, browser_only):
        calls.append(("browser-only" if browser_only else "full", task))
        if browser_only:
            raise RuntimeError("secret-sentinel-123")
        return {
            "status": "completed",
            "answer": "ok",
            "urls": [],
            "trace": [],
            "steps": 2,
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "budget_parity": "verified",
        }

    records = [
        await attempt("B01", arm, 1, baseline=baseline, adaptive=adaptive)
        for arm in ARMS
    ]
    assert [name for name, _ in calls] == ["baseline", "full", "browser-only"]
    assert all(task == CASES["B01"] for _, task in calls)
    assert records[0]["prompt_tokens"] is None
    assert records[0]["budget_parity"] == "mismatched"
    assert records[1]["budget_parity"] == "verified"
    assert records[2]["status"] == "failed"
    assert records[2]["failure_reason"] == "RuntimeError"
    for record in records:
        saved = save_record(record, tmp_path)
        payload = saved.read_text(encoding="utf-8")
        assert "secret-sentinel-123" not in payload
        assert "dXNlcjpwYXNz" not in payload
        assert "abc123" not in payload
        assert "def456" not in payload
        assert "sk-example" not in payload
        assert "?key=" not in payload
        assert json.loads(payload)["case"] == "B01"
    summary = summarize(records)
    assert summary["arms"]["baseline"]["completion_rate"] is None
    assert summary["protocol_complete"] is False
    assert summary["controlled_advantage_claim_allowed"] is False
    assert (
        summary["comparisons"]["full_system_vs_baseline"]
        != summary["comparisons"]["browser_only_vs_baseline"]
    )


@pytest.mark.asyncio
async def test_adaptive_token_overshoot_is_recorded_as_budget_failure():
    async def adaptive(_task, *, browser_only):
        return {
            "status": "completed",
            "answer": "answer",
            "urls": [],
            "trace": [],
            "steps": 1,
            "prompt_tokens": 39_900,
            "completion_tokens": 200,
            "budget_parity": "verified",
        }

    record = await attempt("B01", "adaptive-full", 1, adaptive=adaptive)
    assert record["status"] == "failed"
    assert record["failure_reason"] == "token_budget_breach"
    assert record["budget_parity"] == "mismatched"


def test_manual_notes_recompute_completion_without_controlled_claim(tmp_path):
    for case, arm, repetition in schedule(tuple(CASES), ARMS, 2):
        save_record(
            {
                "case": case,
                "arm": arm,
                "repetition": repetition,
                "status": "completed",
                "coverage": 1.0,
                "steps": 1,
                "duplicate_urls": 0,
                "duration_seconds": 1.0,
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "budget_parity": "mismatched" if arm == "baseline" else "verified",
                "manual_contradiction_note": "none",
            },
            tmp_path,
        )
    _summarize_directory(tmp_path)
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert summary["protocol_complete"] is True
    assert all(summary["arms"][arm]["completion_rate"] == 1.0 for arm in ARMS)
    assert summary["arms"]["baseline"]["budget_parity"] == "mismatched"
    assert summary["controlled_advantage_claim_allowed"] is False


def test_duplicate_record_is_rejected(tmp_path):
    record = {"case": "B01", "arm": "baseline", "repetition": 1}
    save_record(record, tmp_path)
    with pytest.raises(FileExistsError):
        save_record(record, tmp_path)


@pytest.mark.asyncio
async def test_live_run_isolated_directory_links_each_raw_attempt(
    tmp_path, monkeypatch
):
    async def fake_version():
        return "Chrome/130.0.1"

    async def fake_attempt(case, arm, repetition, *, environment=None):
        return {
            "case": case,
            "arm": arm,
            "repetition": repetition,
            "status": "failed",
            "coverage": 0.0,
            "steps": 0,
            "duplicate_urls": 0,
            "duration_seconds": 0.1,
            "prompt_tokens": None,
            "completion_tokens": None,
            "budget_parity": "mismatched",
            "manual_contradiction_note": None,
        }

    monkeypatch.setattr("benchmark.runner.attempt", fake_attempt)
    monkeypatch.setattr("benchmark.runner._browser_version", fake_version)
    await _run_live(tmp_path, [("B01", "baseline", 1)], run_id="test-run")
    record = tmp_path / "test-run" / "B01_baseline_r1.json"
    summary = json.loads((tmp_path / "test-run" / "summary.json").read_text())
    assert record.exists()
    assert summary["raw_records"] == ["B01_baseline_r1.json"]
    assert summary["protocol_complete"] is False
