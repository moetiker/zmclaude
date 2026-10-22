# zmclaude

Find mails in a Zimbra mailbox, read them and save reply drafts through the
Zimbra SOAP API. zmclaude never sends mail: replies land in the Drafts folder
and you send them from Zimbra yourself.

It is meant to be driven by an AI coding assistant working in a terminal: the
assistant searches and reads mail with zmclaude, writes the reply text, and
zmclaude stores it as a draft that looks like a reply from the Zimbra web
client.

## Requirements

Python 3.11 or later, standard library only. A Zimbra account with access to
the SOAP API; two-factor authentication is supported.

## Install

Run it from a checkout as `./zmclaude`, or install the `zmclaude` command
(on Windows this is the only way to get a command):

```sh
uv tool install git+https://github.com/moetiker/zmclaude
pipx install git+https://github.com/moetiker/zmclaude
```

The examples below use `./zmclaude`; with an installed command, drop the `./`.

## Setup

```sh
./zmclaude init https://mail.example.com jane@example.com
./zmclaude login
./zmclaude sync
```

`init` writes `config.toml` and a `rules.toml` with a Default rule and
commented examples; it never overwrites an existing file.

## Usage

The full reference is the manual, [`docs/manual.md`](docs/manual.md).

```sh
./zmclaude login                      # password and 2FA code, caches the auth token
./zmclaude search 'in:inbox' -n 20    # Zimbra search syntax
./zmclaude show ID                    # headers and plain-text body
./zmclaude raw ID [--headers]         # stored MIME message
./zmclaude sync                       # copy identities, signatures, filter rules to the config directory
./zmclaude rule ID                    # identity and reply rule for a message
./zmclaude todo [--days N] [--all]    # inbox mails still waiting for a reply
./zmclaude thread ID [--full]         # the whole conversation, quoted text cut
./zmclaude attachments ID             # list attachments
./zmclaude save ID PART [DIR]         # save an attachment
./zmclaude contacts QUERY             # addresses from contacts and the global address list
./zmclaude free [--start YYYY-MM-DD] [--days N]   # free times from the calendar
./zmclaude draft ID reply.html [options]
./zmclaude forward ID body.html --to ADDR [options]
./zmclaude new body.html --to ADDR --subject TEXT [options]
```

`todo` skips mails you sent, mails answered from Zimbra, conversations with a
later sent reply and newsletters or automatic mail (`List-Unsubscribe`,
`List-Id`, `Precedence`, `Auto-Submitted`). Mail from a ticketing system and
mail an explicit reply rule matches is always listed. For each mail it names
the reply rule, an existing draft, logged answers to the same sender and,
listed apart, answers to other people at the same domain (not for free mail
domains such as gmail.com).
It checks at most the newest 200 inbox mails of the period and says so on
standard error when there are more.

`forward` and `new` take `--cc`, `--attach`, `--identity`, `--signature` and
`--update` like `draft`. `forward` attaches the attachments of the original.

`draft` options:

- `--all`, `--no-all`: Reply to all recipients of the original, or only to the sender. Defaults to `reply_all` of the reply rule.
- `--cc ADDR`: Add a Cc recipient, in addition to `cc` of the reply rule. Repeatable.
- `--attach FILE`: Attach a file. Repeatable.
- `--identity NAME`: Reply as this Zimbra identity. Defaults to `identity` of the reply rule, else the identity whose "when sent to" addresses match a To or Cc address of the original, else `DEFAULT`.
- `--signature NAME`: Use this Zimbra signature, `none` for none. Defaults to the reply signature of the identity.
- `--update DRAFTID`: Replace an existing draft instead of creating a new one.

The reply body is an HTML fragment if the file name ends in `.html`, plain
text otherwise.

## Configuration

`~/.config/zmclaude/` (or `ZMCLAUDE_CONFIG`) holds:

- `config.toml`: `url`, `user` and optionally `from_name`, `ticket_systems` (addresses of ticketing systems such as RT, whose mail `todo` always lists) `answers_dir` (a folder of Markdown files with earlier answers that `todo` searches by sender and domain) and `freemail_domains` (more domains such as gmail.com where `todo` does not search by domain).
- `rules.toml`: Reply rules: tone, greeting, closing and fixed facts per recipient address, sender or subject. `init` writes a first version with commented examples; `sync` never touches it.
- `identities.json`, `signatures/`, `filters.json`, `prefs.json`: Copies from Zimbra, rewritten by `sync`.

Environment variables override `config.toml`:

- `ZIMBRA_URL`: Server.
- `ZIMBRA_USER`: Account.
- `ZIMBRA_FROM_NAME`: Sender name when the identity sets none.
- `ZIMBRA_PASSWORD`: Password for `login` when no terminal is available.

The auth token is stored in `~/.cache/zmclaude/token` with mode 600; the
password is not stored.

## Reply drafts

A draft is built like a reply from the Zimbra web client: the identity
chosen by the "when sent to" rule, its reply signature including images from
the Briefcase, the user's editor font, the quoted original with its header
block in the user's locale, and the inline images of the original. `origid`
and `In-Reply-To` make it a real reply; Zimbra adds `References` when the
draft is sent.

## License

MIT, see `LICENSE`.
