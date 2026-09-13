# Profile Checks

A read-only GitHub REST API integration for maintaining this public portfolio. It catches missing assets and repository links that visitors cannot access.

Run the profile checks from a clone with Python 3.12 or later:

```sh
python scripts/check_profile.py
```

The checker validates local linked files, SVG XML, HTML image alt text, and HTTPS links. It calls GitHub's REST API to verify that linked repositories exist and are public, so a repository visible only to the owner does not accidentally become a featured project. It does not request access to private repository contents or modify GitHub data.

An optional `GITHUB_TOKEN` raises the API rate limit. GitHub Actions supplies its built-in token with only `contents: read`; local checks can run without a token. Rate limits and network failures are reported as failures, not silently counted as successful checks. Non-GitHub external sites and specific files inside remote repositories are not checked for availability.

The workflow runs on main-branch pushes, pull requests, and manual dispatch. Repository badges in the profile link to their source workflows and show the default branch's current result. They are project status indicators, not GitHub achievement awards.

When editing the public profile:

- Keep claims supported by the public projects or personal websites.
- Link only to public work; preserve a clear demo/prototype label where relevant.
- Run the checks and preview the README in GitHub before merging.
- Keep the banner in `assets/` so its rendering does not depend on an external badge service.
