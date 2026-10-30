# AI Notes

Built with Claude Code from the written build plan. Each entry below is a place where the AI got something wrong or needed correction: what went wrong, how it was noticed, and what changed.

1. **Font too large after restyling.** Pico CSS scales the root font up on wide screens, so the text grew compared with the original UI.
   *Noticed:* reviewing the UI after the restyle.
   *Changed:* pinned the base font to 16px.

2. **Wrong nav label.** The first nav tab was labelled "New case".
   *Noticed:* reviewing the UI.
   *Changed:* renamed it to "Alerts".
