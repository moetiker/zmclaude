# Changes

## [Unreleased]

### New
- `zmclaude login --gui` asks for the password and the 2FA code in dialog windows, so a login works where no terminal is available.
- `zmclaude fixhtml ID` repairs a mail that the Zimbra web client shows as an empty page and imports the repaired copy next to the original. `--trash` moves the original to the trash.

### Changed

### Fixed
- `zmclaude login` without a terminal stops when standard input is empty instead of sending an empty password.

## 0.0.1 - 2026-10-22
### New
- First release. `zmclaude` finds mail in a Zimbra mailbox, prints threads and attachments, and saves replies, forwards and new mails as drafts. It never sends mail.
- `zmclaude init URL USER` writes `config.toml` and a starter `rules.toml`.
