# Rollback plan — merge `fixture_merge`

> CANDIDATE WORKSPACE MERGE ONLY — STABLE UNTOUCHED — NOT PROMOTED

This merge created a NEW candidate merge workspace and copied proposed
changes into it. **No repo target file, active candidate, stable skill,
safety gate, or promotion policy was modified.** Rolling back is therefore
trivial and fully reversible:

1. Delete the merge workspace directory: `/tmp/tmp4pnbnnc_/fixture_merge`.
2. Nothing else needs to change — the live tree was never touched.

Source apply workspace (unchanged): `fixtures/repair/fake_approved_apply_workspace`.

Because no promotion or stable change occurred, there is no deployed state
to revert. A future staging/stable promotion phase must define its own,
stronger rollback before changing any active/stable artifact.
