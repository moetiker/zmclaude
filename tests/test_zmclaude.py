import os
import subprocess
import sys
import time
import types

import pytest
from conftest import SCRIPT


@pytest.fixture
def zurich(monkeypatch):
    """Local time with DST changes, as on the machines zmclaude runs on."""
    monkeypatch.setenv("TZ", "Europe/Zurich")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


def free_days(z, capsys, start, days):
    z.call = lambda request, body, ns=None: {}
    z.cmd_free(types.SimpleNamespace(start=start, days=days, weekends=True,
                                     from_hour=8, to_hour=18, min=30))
    return [line.split()[1] for line in capsys.readouterr().out.splitlines()]


@pytest.mark.parametrize("start, days, expected", [
    # 2026-10-25 has 25 hours, 2027-03-28 has 23
    ("2026-10-24", 3, ["2026-10-24", "2026-10-25", "2026-10-26"]),
    ("2027-03-27", 3, ["2027-03-27", "2027-03-28", "2027-03-29"]),
])
def test_free_lists_each_day_once_across_dst(z, capsys, zurich, start, days, expected):
    assert free_days(z, capsys, start, days) == expected


def save(z, tmp_path, name, data=b"new"):
    z.get_msg = lambda msg_id: {}
    z.attachment_parts = lambda m: [("2", name)]
    z.fetch_rest = lambda path: data
    z.cmd_save(types.SimpleNamespace(id="1", part="2", dir=str(tmp_path / "out")))


@pytest.mark.parametrize("name, saved", [
    ("report.pdf", "report.pdf"),
    ("../../CLAUDE.md", "CLAUDE.md"),
    ("/etc/passwd", "passwd"),
    (".bashrc", "_.bashrc"),
    ("..", "_.."),
    ("", "part-2"),
    (None, "part-2"),
])
def test_save_keeps_attachment_names_inside_the_directory(z, tmp_path, name, saved):
    save(z, tmp_path, name)
    assert [p.name for p in (tmp_path / "out").iterdir()] == [saved]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["out"]


def test_save_never_overwrites(z, tmp_path):
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "a.pdf").write_bytes(b"old")
    save(z, tmp_path, "a.pdf")
    save(z, tmp_path, "a.pdf")
    out = tmp_path / "out"
    assert (out / "a.pdf").read_bytes() == b"old"
    assert sorted(p.name for p in out.iterdir()) == ["a-1.pdf", "a-2.pdf", "a.pdf"]


@pytest.mark.parametrize("url", [
    "https://mail.example.com/",
    "http://localhost:7070",
    "http://127.0.0.1:7070",
])
def test_check_url_accepts(z, url):
    assert z.check_url(url) == url.rstrip("/")


@pytest.mark.parametrize("url", [
    "http://mail.example.com",
    "ftp://mail.example.com",
    "mail.example.com",
])
def test_check_url_refuses(z, url):
    with pytest.raises(SystemExit, match="must start with https://"):
        z.check_url(url)


def test_write_private_tightens_existing_modes(z, tmp_path):
    folder = tmp_path / "cache"
    folder.mkdir(mode=0o755)
    folder.chmod(0o755)
    token = folder / "token"
    token.write_text("old")
    token.chmod(0o644)
    z.write_private(token, "new")
    assert token.read_text() == "new"
    assert folder.stat().st_mode & 0o777 == 0o700
    assert token.stat().st_mode & 0o777 == 0o600


def test_sync_keeps_signature_files_inside_signatures(z, tmp_path):
    answers = {
        "GetIdentitiesRequest": {"identity": []},
        "GetSignaturesRequest": {"signature": [
            {"id": "1", "name": "../../escape", "content": [{"type": "text/plain", "_content": "a"}]},
            {"id": "2", "name": ".hidden", "content": [{"type": "text/html", "_content": "b"}]},
            {"id": "3", "name": "Office", "content": [{"type": "text/plain", "_content": "c"}]},
        ]},
        "GetFilterRulesRequest": {},
    }
    z.call = lambda request, body, ns=None: answers[request]
    z.get_prefs = dict
    z.CONFIG_DIR = tmp_path / "config"
    z.RULES_FILE = z.CONFIG_DIR / "rules.toml"
    z.cmd_sync(None)
    names = sorted(p.name for p in (z.CONFIG_DIR / "signatures").iterdir())
    assert names == ["Office.txt", "_.._escape.txt", "hidden.html"]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["config"]


def run(tmp_path, url, *args):
    """Run the script as a user would, with a token and no config file."""
    token = tmp_path / ".cache" / "zmclaude" / "token"
    token.parent.mkdir(parents=True)
    token.write_text("token")
    env = dict(os.environ, HOME=str(tmp_path), ZMCLAUDE_CONFIG=str(tmp_path / "config"),
               ZIMBRA_URL=url, ZIMBRA_USER="jane@example.com")
    return subprocess.run([sys.executable, str(SCRIPT), *args], env=env, check=False,
                          capture_output=True, text=True, timeout=60)


def test_unreachable_server_is_a_message_not_a_traceback(tmp_path):
    # port 9 (discard) is closed on a CI runner and on a workstation
    result = run(tmp_path, "http://127.0.0.1:9", "search", "x")
    assert result.returncode == 1
    assert "cannot reach http://127.0.0.1:9" in result.stderr
    assert "Traceback" not in result.stderr


def test_missing_file_is_a_message(z, monkeypatch):
    def cmd_raw(args):
        raise FileNotFoundError(2, "No such file or directory", "/x/body.html")
    monkeypatch.setattr(z, "cmd_raw", cmd_raw)
    monkeypatch.setenv("ZIMBRA_URL", "https://mail.example.com")
    monkeypatch.setenv("ZIMBRA_USER", "jane@example.com")
    monkeypatch.setattr(sys, "argv", ["zmclaude", "raw", "1"])
    with pytest.raises(SystemExit) as exit_info:
        z.main()
    assert exit_info.value.code == "/x/body.html: No such file or directory"


def test_config_is_not_written_by_a_failing_init(tmp_path):
    env = dict(os.environ, ZMCLAUDE_CONFIG=str(tmp_path / "config"))
    result = subprocess.run([sys.executable, str(SCRIPT), "init", "http://mail.example.com",
                             "jane@example.com"], env=env, check=False,
                            capture_output=True, text=True)
    assert result.returncode == 1
    assert "must start with https://" in result.stderr
    assert not (tmp_path / "config").exists()


STRAY_STYLE = ('<html><head><style type="text/css">\r\n  .a { color: red; }\r\n'
               '    <![endif]-->\r\n  </style></head><body><p>Grüezi</p>'
               '<!--[if mso]><table><![endif]--></body></html>')


def test_fix_style_comments_removes_a_stray_endif(z):
    fixed, n = z.fix_style_comments(STRAY_STYLE)
    assert n == 1
    assert "<![endif]-->\r\n  </style>" not in fixed
    # conditional comments outside <style> are not touched
    assert fixed.endswith("<!--[if mso]><table><![endif]--></body></html>")


def test_fix_style_comments_keeps_paired_conditionals(z):
    paired = "<style><!--[if mso]>.a { color: red; }<![endif]--></style>"
    assert z.fix_style_comments(paired) == (paired, 0)


def mail(html_part, cte):
    return ("From: shop@example.com\r\nTo: jane@example.com\r\n"
            "Subject: =?UTF-8?Q?Das_iPhone_ist_erh=C3=A4ltlich?=\r\n"
            "MIME-Version: 1.0\r\nContent-Type: multipart/alternative; boundary=\"b\"\r\n\r\n"
            "--b\r\nContent-Type: text/plain; charset=\"utf-8\"\r\n"
            "Content-Transfer-Encoding: 8bit\r\n\r\nGrüezi\r\n"
            f"--b\r\nContent-Type: text/html; charset=\"utf-8\"\r\n"
            f"Content-Transfer-Encoding: {cte}\r\n\r\n{html_part}\r\n--b--\r\n").encode()


@pytest.mark.parametrize("cte", ["8bit", "quoted-printable", "base64"])
def test_fix_message_repairs_the_html_part(z, cte):
    import base64
    import email
    import quopri
    body = STRAY_STYLE.encode()
    encoded = {"8bit": body,
               "quoted-printable": quopri.encodestring(body),
               "base64": base64.encodebytes(body)}[cte].decode()
    fixed, n = z.fix_message(mail(encoded, cte))
    assert n == 1
    msg = email.message_from_bytes(fixed)
    plain, html_part = msg.get_payload()
    assert plain.get_payload(decode=True).decode() == "Grüezi"
    assert html_part["Content-Transfer-Encoding"] == cte
    text = html_part.get_payload(decode=True).decode()
    assert "<![endif]-->\r\n  </style>" not in text and "Grüezi" in text
    assert b"Subject: =?UTF-8?Q?Das_iPhone_ist_erh=C3=A4ltlich?=\r\n" in fixed


def test_fix_message_without_stray_endif_changes_nothing(z):
    raw = mail("<html><body><p>ok</p></body></html>", "8bit")
    assert z.fix_message(raw) == (raw, 0)


def fixhtml(z, raw, trash=False):
    calls = []
    def call(request, body, ns=None):
        calls.append((request, body))
        if request == "GetMsgRequest" and body["m"]["id"] == "7":
            return {"m": [{"id": "7", "l": "2", "f": "u", "d": 1792733962000, "tn": "shop"}]}
        if request == "AddMsgRequest":
            return {"m": [{"id": "8"}]}
        return {"m": [{"mp": [{"ct": "text/html", "body": True, "content": "<p>ok</p>"}]}]}
    z.call = call
    z.fetch_rest = lambda path: raw
    z.upload_data = lambda data, name, ctype: "aid-1"
    z.cmd_fixhtml(types.SimpleNamespace(id="7", trash=trash))
    return calls


def test_fixhtml_imports_the_copy_like_the_original(z, capsys):
    calls = fixhtml(z, mail(STRAY_STYLE, "8bit"))
    add = next(body for request, body in calls if request == "AddMsgRequest")
    assert add == {"m": {"l": "2", "f": "u", "d": 1792733962000, "tn": "shop", "aid": "aid-1"}}
    assert not any(request == "MsgActionRequest" for request, _ in calls)
    assert "8" in capsys.readouterr().out


def test_fixhtml_trash_moves_the_original(z):
    calls = fixhtml(z, mail(STRAY_STYLE, "8bit"), trash=True)
    assert ("MsgActionRequest", {"action": {"op": "trash", "id": "7"}}) in calls


def test_fixhtml_with_nothing_to_fix_imports_nothing(z):
    with pytest.raises(SystemExit, match="nothing to fix"):
        fixhtml(z, mail("<html><body>ok</body></html>", "8bit"))
