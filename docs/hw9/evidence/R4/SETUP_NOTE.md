# R4 set-up differs from the protocol in two ways (disclosed)

1. **Target copied with `.git`** (`scripts/hw9_run.py setup ... --keep-git`). PROTOCOL.md step 2
   says the target is copied without `.git`; R1 was set up that way and its client could not
   find the commit the job template asks for. R4's `run.json` was written before the script
   recorded this flag, so it does not show it.
2. **Interface doc at commit 3697444**, the version with the fix under test. R3 got the same doc.

The prompt (P1) is unchanged, word for word. R4 is therefore a rerun of the same task with the
fix and one set-up correction, not an exact replica of R1.
