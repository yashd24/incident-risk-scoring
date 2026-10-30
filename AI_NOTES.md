# AI Notes

Built with Claude Code from the written build plan. Each entry below is a place where the AI got something wrong or needed correction: what went wrong, how it was noticed, and what changed.

1. **Font too large after restyling.** Pico CSS scales the root font up on wide screens, so the text grew compared with the original UI.
   *Noticed:* reviewing the UI after the restyle.
   *Changed:* pinned the base font to 16px.

2. **Wrong nav label.** The first nav tab was labelled "New case".
   *Noticed:* reviewing the UI.
   *Changed:* renamed it to "Alerts".

3. **Submit button missing.** After being asked to create a case from a draft, the UI still had no button to submit it.
   *Noticed:* reviewing the UI ("still there is no submit button").
   *Changed:* added a required case name field and a *Create case* button below the final score, which creates the case in one request.

4. **Create-case validation missing.** The backend accepted a case with no alerts.
   *Noticed:* reviewing the API behaviour (prompts 9–10).
   *Changed:* `POST /cases` and `PUT /cases/{id}` return 422 when no alerts are given, and removing a case's last alert is rejected. The UI disables the button and shows the server's message. Renaming to the same name makes no API call.

5. **Updates sent several API calls.** Editing a case saved each alert and policy change with its own request.
   *Noticed:* reviewing the case page (prompt 8: "API should be fired once at last").
   *Changed:* the case page keeps edits as a local draft with a live preview, and *Update case* saves alerts and policies in a single `PUT /cases/{id}`. Rename stays separate, confirmed with a tick.
