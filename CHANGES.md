# Changes

## [Unreleased]

### New
- `zmclaude login --gui` asks for the password and the 2FA code in dialog windows, so a login works where no terminal is available.
- `zmclaude fixhtml ID` repairs a mail that the Zimbra web client shows as an empty page and imports the repaired copy next to the original. `--trash` moves the original to the trash.

- `zmclaude draft --subject TEXT` sets the subject of a reply.
- `draft`, `forward` and `new` with `--update` save the old draft to `~/.cache/zmclaude/backup/` and refuse to drop images or attachments the new version does not carry, unless `--drop-images` is given. `fixhtml` saves the original there as well. Backups older than seven days are removed.

### Changed
- A reply has one blank line between the text and the signature, however many the body file ends with.
- The reply subject is built as in the web client: `Re:`, `Fw:` and `Fwd:` are removed and `Re: ` is put in front, so `AW: x` becomes `Re: AW: x`.

### Fixed
- `draft --all` no longer drops recipients whose address belongs to another identity of the account, such as a colleague one may send as.
- `zmclaude login` without a terminal stops when standard input is empty instead of sending an empty password.

## 0.0.1 - 2026-10-22
### New
- First release. `zmclaude` finds mail in a Zimbra mailbox, prints threads and attachments, and saves replies, forwards and new mails as drafts. It never sends mail.
- `zmclaude init URL USER` writes `config.toml` and a starter `rules.toml`.
