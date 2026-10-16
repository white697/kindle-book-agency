# Fonts for themed NLC books

Drop commercial-use fonts here (SIL Open Font License, e.g. from Google Fonts) and name them in the spec's
`theme.fonts`. The builder falls back to built-in Helvetica if a file is missing, so builds never fail on fonts.

Suggested pairing for kids' books: **Fredoka** (display, `Fredoka-Bold.ttf`) + **Nunito** (body:
`Nunito-Regular.ttf`, `Nunito-Bold.ttf`, `Nunito-Italic.ttf`). Use static TTFs (not variable fonts) so ReportLab can embed them.
Keep each font's license file next to it.
