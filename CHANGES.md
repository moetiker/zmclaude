# Changes

## [Unreleased]

### New
- `zmclaude fixhtml ID` repairs a mail that the Zimbra web client shows as an empty page and imports the repaired copy next to the original. `--trash` moves the original to the trash.

### Changed

### Fixed

## 0.0.1 - 2026-10-22
### New
- First release. `zmclaude` finds mail in a Zimbra mailbox, prints threads and attachments, and saves replies, forwards and new mails as drafts. It never sends mail.
- `zmclaude init URL USER` writes `config.toml` and a starter `rules.toml`.
