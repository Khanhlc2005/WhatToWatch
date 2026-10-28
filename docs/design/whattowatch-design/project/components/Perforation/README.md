The torn-ticket divider: a dashed `line` with a half-round notch at each end. It is the system's signature mark.

- Place it as a direct child of a `surface-200` block with no side padding, so the notches sit on the block's edges. Inside a padded block, set `--perf-pad` to that padding and pass `inset`.
- Use it in three places only: between the head and body of the detail modal, between the stub and fields of the auth card, and above the picks in a chat reply. Use at most one per block.
- It is decorative (`aria-hidden`). Never use it as a list separator; use `line` hairlines for that.
