# Deployment

How to publish `ClashRoyaleBuildABot` to PyPI.

## One-time setup

1. Sign in (2FA required) to [pypi.org](https://pypi.org) as an owner of
   [ClashRoyaleBuildABot](https://pypi.org/project/ClashRoyaleBuildABot/).
2. Under the project's **Settings → Publishing**, add a GitHub trusted
   publisher so the workflow can upload without a token:

   | Field | Value |
   |---|---|
   | Owner | `Pbatch` |
   | Repository name | `ClashRoyaleBuildABot` |
   | Workflow name | `release.yml` |
   | Environment name | `pypi` |

   Remove any API tokens left over from the old `pypi-package.yml` workflow.

3. In the GitHub repo, under **Settings → Environments**, create the
   environment `pypi` and add yourself as a required reviewer, so nothing
   reaches PyPI until you approve it.

## Releasing

### 1. Bump the version

Update `version` in `pyproject.toml`, then run `uv lock`. PyPI never accepts
the same version twice, even after deleting a release, and it must be higher
than the latest release on PyPI or `pip install` keeps picking that one.

### 2. Tag the release

Commit the version bump on `main`, then tag it to start the
[Release workflow](.github/workflows/release.yml):

```bash
git tag v<version> && git push origin v<version>
```

The workflow builds the sdist and wheel, checks the wheel loads the bot's
models and data when installed, and then, once you approve it, uploads them to
PyPI. The tag must be `v` plus the version exactly; otherwise nothing is
uploaded. So to try the build without releasing, push a tag like
`v<version>-test`, or run `gh workflow run release.yml`, which needs the
workflow on `main`.

The run's `clashroyalebuildabot` artifact should contain:

- `clashroyalebuildabot-<version>.tar.gz`: about 9 MB, mostly the models and
  `tests/data`. If it is much bigger, something gitignored, like
  `dev/synthetic`, has leaked in; check `tar -tzf dist/*.tar.gz`.
- `clashroyalebuildabot-<version>-py3-none-any.whl`: about 7 MB, mostly the
  ONNX models in `clashroyalebuildabot/models`.

To build locally instead:

```bash
uv build --out-dir dist
```

### 3. Approve the PyPI release

The workflow's `publish-pypi` job waits for your approval: open the run on
GitHub and choose **Review deployments → Approve and deploy**, or reject it if
the artifacts look wrong. The release then appears at
<https://pypi.org/project/ClashRoyaleBuildABot/>.

### 4. Check the release

Verify it installs and imports in a throwaway environment:

```bash
cd "$(mktemp -d)"
uv venv --python 3.12 && uv pip install ClashRoyaleBuildABot==<version>
uv run python -c "import clashroyalebuildabot"
```

## Troubleshooting

- **"Check the tag matches the version" failed**: the tag isn't `v` plus the
  version in `pyproject.toml`. Expected for test tags; for a release, fix the
  tag or the version.
- **"File already exists"**: that version is already uploaded; bump the
  version.
- **"invalid-publisher"**: the trusted publisher on PyPI doesn't match the
  repo, workflow or environment name; compare it with the table in step 2 of
  the one-time setup.
