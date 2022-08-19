from datetime import datetime
from json import load
from pathlib import Path

from pytest import fixture
from pytest import raises
from requests import Response

from faapi.connection import CloudflareScraper
from faapi.connection import join_url
from faapi.connection import make_session
from faapi.connection import root
from faapi.exceptions import DisabledAccount
from faapi.exceptions import NotFound
from faapi.parse import check_page_raise
from faapi.parse import clean_html
from faapi.parse import html_to_bbcode
from faapi.parse import parse_journal_page
from faapi.parse import parse_loggedin_user
from faapi.parse import parse_page
from faapi.parse import parse_submission_page
from faapi.parse import parse_user_page
from faapi.parse import username_url

__root__: Path = Path(__file__).resolve().parent


@fixture
def data() -> dict:
    return load((__root__ / "test_data.json").open())


@fixture
def session(data: dict) -> CloudflareScraper:
    sess = make_session(data["cookies"])
    sess.headers["User-Agent"] += " test"
    return sess


@fixture
def user_test_data() -> dict:
    return load((__root__ / "test_user.json").open())


@fixture
def submission_test_data() -> dict:
    return load((__root__ / "test_submission.json").open())


@fixture
def journal_test_data() -> dict:
    return load((__root__ / "test_journal.json").open())


def test_check_page_disabled_account(session: CloudflareScraper, data: dict):
    res: Response = session.get(join_url(root, "user", data["disabled"]["user"]))
    assert res.ok

    page = parse_page(res.text)

    with raises(DisabledAccount):
        check_page_raise(page)


def test_check_page_not_found(session: CloudflareScraper):
    res: Response = session.get(join_url(root, "user", "_"))
    assert res.ok

    page = parse_page(res.text)

    with raises(NotFound):
        check_page_raise(page)


def test_parse_loggedin_user(session: CloudflareScraper, data: dict):
    res: Response = session.get(join_url(root, "user", data["login"]["user"]))
    assert res.ok

    page = parse_page(res.text)

    assert username_url(parse_loggedin_user(page)) == username_url(data["login"]["user"])


def test_parse_user_page(session: CloudflareScraper, user_test_data: dict):
    res: Response = session.get(join_url(root, "user", username_url(user_test_data["name"])))
    assert res.ok

    page = parse_page(res.text)
    result = parse_user_page(page)

    assert result["name"] == user_test_data["name"]
    assert result["status"] == user_test_data["status"]
    assert result["title"] == user_test_data["title"]
    assert result["join_date"] == datetime.fromisoformat(user_test_data["join_date"])
    assert result["stats"][0] >= user_test_data["stats"]["views"]
    assert result["stats"][1] >= user_test_data["stats"]["submissions"]
    assert result["stats"][2] >= user_test_data["stats"]["favorites"]
    assert result["stats"][3] >= user_test_data["stats"]["comments_earned"]
    assert result["stats"][4] >= user_test_data["stats"]["comments_made"]
    assert result["stats"][5] >= user_test_data["stats"]["journals"]
    assert result["info"] == user_test_data["info"]
    assert result["contacts"] == user_test_data["contacts"]
    assert result["user_icon_url"] != ""
    assert clean_html(result["profile"]) == clean_html(user_test_data["profile"])
    assert html_to_bbcode(result["profile"], convert_special_characters=True) == user_test_data["profile_bbcode"]


def test_parse_submission_page(session: CloudflareScraper, submission_test_data: dict):
    res: Response = session.get(join_url(root, "view", submission_test_data["id"]))
    assert res.ok

    page = parse_page(res.text)
    result = parse_submission_page(page)

    assert result["id"] == submission_test_data["id"]
    assert result["title"] == submission_test_data["title"]
    assert result["author"] == submission_test_data["author"]["name"]
    assert result["author_icon_url"] != ""
    assert result["date"] == datetime.fromisoformat(submission_test_data["date"])
    assert result["tags"] == submission_test_data["tags"]
    assert result["category"] == submission_test_data["category"]
    assert result["species"] == submission_test_data["species"]
    assert result["gender"] == submission_test_data["gender"]
    assert result["rating"] == submission_test_data["rating"]
    assert result["views"] >= submission_test_data["stats"]["views"]
    assert result["comment_count"] >= submission_test_data["stats"]["comments"]
    assert result["favorites"] >= submission_test_data["stats"]["favorites"]
    assert result["type"] == submission_test_data["type"]
    assert result["mentions"] == submission_test_data["mentions"]
    assert result["folder"] == submission_test_data["folder"]
    assert [list(f) for f in result["user_folders"]] == submission_test_data["user_folders_tuples"]
    assert result["file_url"] != ""
    assert result["thumbnail_url"] != ""
    assert result["prev"] == submission_test_data["prev"]
    assert result["next"] == submission_test_data["next"]
    assert bool(result["unfav_link"]) == submission_test_data["favorite"]
    assert (("/fav/" in submission_test_data["favorite_toggle_link"]) and bool(result["fav_link"])) or \
           (("/unfav/" in submission_test_data["favorite_toggle_link"]) and bool(result["unfav_link"]))
    assert clean_html(result["description"]) == clean_html(submission_test_data["description"])
    assert html_to_bbcode(result["description"], convert_special_characters=True) \
           == submission_test_data["description_bbcode"]


def test_parse_journal_page(session: CloudflareScraper, journal_test_data: dict):
    res: Response = session.get(join_url(root, "journal", journal_test_data["id"]))
    assert res.ok

    page = parse_page(res.text)
    result = parse_journal_page(page)

    assert result["id"] == journal_test_data["id"]
    assert result["title"] == journal_test_data["title"]
    assert result["user_name"] == journal_test_data["author"]["name"]
    assert result["user_join_date"] == datetime.fromisoformat(journal_test_data["author"]["join_date"])
    assert result["user_icon_url"] != ""
    assert result["date"] == datetime.fromisoformat(journal_test_data["date"])
    assert result["comments"] >= journal_test_data["stats"]["comments"]
    assert result["mentions"] == journal_test_data["mentions"]
    assert clean_html(result["content"]) == clean_html(journal_test_data["content"])
    assert html_to_bbcode(result["content"], convert_special_characters=True) == journal_test_data["content_bbcode"]
