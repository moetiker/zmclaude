---
title: ZMCLAUDE
section: 1
header: zmclaude manual
footer: zmclaude
date: 2026-10-22
---

# NAME

zmclaude - read Zimbra mail and save reply drafts through the SOAP API

# SYNOPSIS

**zmclaude** *command* [*options*] [*arguments*]

# CONFIGURATION

**zmclaude** reads its settings from `config.toml` in the configuration directory,
by default `~/.config/zmclaude`.
Environment variables override the file, see **ENVIRONMENT**.

- `url`: Zimbra server, for example `https://mail.example.com`. Required.
- `user`: Account name, for example `jane@example.com`. Required.
- `from_name`: Sender name used when an identity sets none.
- `ticket_systems`: List of addresses of ticketing systems such as RT. The **todo** command always lists mail from them.
- `answers_dir`: Folder of Markdown files with earlier answers. The **todo** command names the files that mention the sender of a mail.

Reply rules live in `rules.toml` in the same directory.
The first rule whose `match` fits a mail applies; a rule without `match` fits every mail.
The match keys are:

- `to`: Addresses the mail was sent to, in To or Cc.
- `from`: Sender addresses.
- `from_domain`: Sender domains.
- `subject`: Regular expression on the subject.

**draft** and **forward** apply three keys of the matching rule:

- `identity`: Name of the Zimbra identity to write as. `--identity` overrides it.
- `reply_all`: `true` replies to all recipients, as `--all` does. **draft** only; `--no-all` overrides it.
- `cc`: Addresses added as Cc. `--cc` adds further addresses.

The remaining keys describe how to answer:
`language`, `address` (`Sie`, `du` or `auto`), `greeting`, `closing`,
`facts` (fixed information a reply may use) and `notes` (hints for writing the reply).
**zmclaude** prints them with **rule** and does not apply them itself.
The repository carries a commented example, `rules.example.toml`.

Sender address, signature and signature images come from the Zimbra identity, not from `rules.toml`.

# DESCRIPTION

**zmclaude** finds mail in a Zimbra mailbox, prints it and saves drafts.
It never sends mail.
Drafts appear in the Drafts folder of the Zimbra web client and are sent from there.

A reply draft has the structure of a reply from the web client:
the identity whose "when sent to" addresses match the original,
its reply signature including images from the Briefcase,
the editor font from the user's preferences,
the quoted original with a header block in the user's locale,
and the inline images of the original.
`origid` and `In-Reply-To` link the draft to the original;
Zimbra adds `References` when the draft is sent.

The tool is meant to be run by an AI coding assistant in a terminal.
The assistant reads mail with **todo**, **thread** and **show**,
writes the reply text to a file,
and stores it with **draft**.

# COMMANDS

- `login`: Ask for the password and, if two-factor authentication is on, the code; store the auth token.
- `search [QUERY] [-n N]`: List messages matching a Zimbra search query, newest first. The default query is `in:inbox`, the default limit 20.
- `todo [--days N] [--all]`: List inbox mails of the last *N* days (default 14) that still wait for a reply. See **NOTES** for what it skips.
- `show ID`: Print the headers and the plain-text body of a message.
- `thread ID [--full]`: Print every message of the conversation of *ID*, oldest first, except those in the trash. Unless `--full` is given, each block of lines starting with `>` is shown as `> [...]`, and the text is cut at the first attribution or header line (`On ... wrote:`, `From:`, `-----Original Message-----`) that follows new text.
- `raw ID [--headers]`: Print the stored MIME message, or only its top-level headers.
- `attachments ID`: List the attachments of a message with part number, type, size and file name.
- `save ID PART [DIR]`: Save attachment *PART* of message *ID* into *DIR*, by default the current directory, and print the path.
- `contacts QUERY`: Look up addresses in the contacts and the global address list.
- `free [--start YYYY-MM-DD] [--days N]`: Print the free times from the calendar per working day, see **OPTIONS**.
- `rule ID`: Print the identity and the reply rule that apply to a message.
- `sync`: Copy identities, signatures, filter rules and compose preferences from Zimbra into the configuration directory.
- `draft ID BODYFILE`: Save a reply to message *ID*.
- `forward ID BODYFILE --to ADDR`: Save a forward of message *ID*, including its attachments.
- `new BODYFILE --to ADDR --subject TEXT`: Save a new mail.

*BODYFILE* holds the text above the signature.
A file name ending in `.html` is taken as an HTML fragment, any other file as plain text.

# OPTIONS

Options of **draft**, **forward** and **new**:

- `--to ADDR`: Add a recipient. Repeatable. Required for **forward** and **new**.
- `--cc ADDR`: Add a Cc recipient. Repeatable.
- `--all`, `--no-all`: Reply to all recipients of the original, except the user's own addresses, or only to the sender. The default is `reply_all` of the reply rule, else only the sender. **draft** only.
- `--subject TEXT`: Subject. Required for **new**.
- `--attach FILE`: Attach a file. Repeatable.
- `--identity NAME`: Write as this Zimbra identity. The default is `identity` of the reply rule, else the identity whose "when sent to" addresses match the original, else `DEFAULT`.
- `--signature NAME`: Use this signature, `none` for none. The default is the reply signature of the identity, for **new** its default signature.
- `--update DRAFTID`: Replace an existing draft instead of creating a new one.

Options of **free**:

- `--start YYYY-MM-DD`: First day, by default today.
- `--days N`: Number of days, default 7.
- `--from-hour H`: Start of the working day, default 8.
- `--to-hour H`: End of the working day, default 18.
- `--min M`: Shortest free slot in minutes, default 30.
- `--weekends`: Include Saturday and Sunday.

# EXIT STATUS

**zmclaude** exits 0 on success, 1 on an error with a message on standard error,
and 2 on invalid command-line arguments.
An expired auth token ends with the message `auth token expired, run: zmclaude login`.

# ENVIRONMENT

- `ZIMBRA_URL`: Server, overrides `url`.
- `ZIMBRA_USER`: Account, overrides `user`.
- `ZIMBRA_FROM_NAME`: Sender name, overrides `from_name`.
- `ZIMBRA_PASSWORD`: Password for **login** when no terminal is available.
- `ZMCLAUDE_CONFIG`: Configuration directory, default `~/.config/zmclaude`.

# FILES

- `~/.config/zmclaude/config.toml`: Server, account and options, see **CONFIGURATION**.
- `~/.config/zmclaude/rules.toml`: Reply rules.
- `~/.config/zmclaude/identities.json`: Identities, written by **sync**.
- `~/.config/zmclaude/signatures/`: Signatures as `.html` and `.txt`, written by **sync**.
- `~/.config/zmclaude/filters.json`: Incoming mail filter rules, written by **sync**.
- `~/.config/zmclaude/prefs.json`: Compose preferences, written by **sync**.
- `~/.cache/zmclaude/token`: Auth token, mode 600. The password is not stored.

# NOTES

The **todo** command leaves out
mail sent from one of the user's addresses,
mail marked as answered in Zimbra,
mail whose conversation holds a later sent message,
and newsletters or automatic mail, recognised by the headers
`List-Unsubscribe`, `List-Id`, `Precedence` and `Auto-Submitted`.
Mail from an address in `ticket_systems`, mail with an `RT-Ticket` header
and mail an explicit reply rule matches is always listed.
`--all` lists newsletters and automatic mail as well.
**todo** checks at most the newest 200 inbox mails of the period and prints a note on standard error when there are more.

When a draft is edited in the web client, Zimbra saves it under a new ID.
`--update` needs the current ID, which **search in:drafts** shows.

**draft** reads identities, signatures and preferences from Zimbra on every call.
The copies written by **sync** are for looking things up.

# EXAMPLES

First setup:

```sh
mkdir -p ~/.config/zmclaude
printf 'url = "https://mail.example.com"\nuser = "jane@example.com"\n' \
  > ~/.config/zmclaude/config.toml
zmclaude login
zmclaude sync
cp rules.example.toml ~/.config/zmclaude/rules.toml
```

Find the mails that wait for an answer and read one with its conversation:

```sh
zmclaude todo
zmclaude thread 81234
zmclaude attachments 81199
zmclaude save 81199 2 /tmp/mail
```

Check which identity and rule apply, then save a reply:

```sh
zmclaude rule 81234
cat > reply.html <<'EOF'
<div>Hallo Alex</div>
<div><br></div>
<div>Der Termin am Montag um 10 Uhr passt.</div>
<div><br></div>
<div>Gruess<br>Jane</div>
EOF
zmclaude draft 81234 reply.html
```

Change the text and replace the same draft:

```sh
zmclaude draft 81234 reply.html --update 81240
```

Forward a mail with its attachments, and start a new mail:

```sh
zmclaude forward 81199 note.html --to colleague@example.com
zmclaude contacts smith
zmclaude free --start 2026-10-26 --days 5
zmclaude new invite.html --to alex@example.com --subject "Meeting next week"
```

A session with an AI assistant usually runs:
**todo** to pick a mail,
**thread** and **attachments** to read it,
**rule** to see the identity and rules,
then **draft** with the text the assistant wrote,
and **draft --update** for each change the user asks for.

# SEE ALSO

The Zimbra SOAP API reference, <https://files.zimbra.com/docs/soap_api/>.
