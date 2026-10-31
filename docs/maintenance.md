# Maintaining my profile

The profile uses Project Explorer cards, macOS-inspired window controls, Japanese/English titles and a simple orange cat drawn with SVG shapes. Light/dark assets are selected with `<picture>`. GitHub controls the body font; Shippori Mincho titles are vector paths, with the original font notice retained in `licenses/`.

## Content and appearance

- `data/projects.json`: project facts and learning focus. Generated overviews live in `docs/projects/`.
- `data/spoken-languages.json`: the self-assessed spoken-language levels.
- `assets/mascot-cat.svg`: the editable geometric mascot, reused in the scenes and contribution art.
- `tools/build_scene.py`: the scene palettes and layout.
- `tools/build_profile.py`: README composition, terminal, metric and music cards.
- `config/profile.json`: GitHub author, time window, repository scope and file exclusions.
- `design/lettering.json`: committed vector lettering. The normal workflow does not download a font.

After editing, use Python 3:

```powershell
py -3 tools/build_scene.py
py -3 tools/build_profile.py
py -3 -m unittest discover -s tests -v
```

The README is generated. Change its generator or data before rebuilding so later workflows keep the edit. Project cards and Japanese heading SVGs are committed artwork; if their text changes, update the matching SVGs as well.

## Updates

- **Refresh profile data** runs daily, on relevant source changes and manually. It uses GitHub's automatic `github.token`; no personal access token is needed for the configured public repositories.
- **Refresh music snapshot** runs only after a supported provider is set in repository Variables. It uses only the corresponding music credentials, and does not fetch GitHub statistics.
- Both workflows serialize their commits and use the GitHub Actions bot identity. They do not rewrite history or backdate commits.
- A failed data request leaves the previous committed data available with its existing timestamp.

No workflow changes the project repositories, their deployments or databases.

## Scope and verification

Project facts were reviewed against their repository READMEs on 30 October 2026. A linked deployment is not a claim that every live flow has passed acceptance testing. Project learning notes describe the technical concepts being practised, without invented performance results or proficiency claims.

The full bundle has local build and data-rule checks. GitHub-hosted workflow execution and Spotify/Last.fm authorization require upload and account setup, and are not represented as already completed.
