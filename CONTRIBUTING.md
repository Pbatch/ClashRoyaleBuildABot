# Contributing

Welcome all!
Thank you for your eagerness in contributing to the project,
hopefully we can build something really special together.

If you have ideas for the project,
or are interested in a task in the roadmap (see the README),
then kick off proceedings by saying something in Issues.
Make sure you check that your idea isn't already being discussed!

If we can agree that the idea is right for the project,
I'll assign you the issue,
and you can get started.

## Setting up

Follow the [Bot Installation guide](https://pbatch.github.io/ClashRoyaleBuildABot/bot-installation/) to clone the repository, then install the dev dependencies and the pre-commit hooks:

```bash
uv sync --extra dev
uv run pre-commit install
```

The hooks run Ruff (linting and formatting) and ty (type checking) on each commit.

## Before you open a PR

Run the same checks as CI:

```bash
uv run ruff check .
uv run ruff format . --check
uv run ty check
uv run pytest
```

If you change how something works, update the matching page in [docs/](docs/README.md).
They're published as the [docs site](https://pbatch.github.io/ClashRoyaleBuildABot/) on every push to `main`, and built on every pull request, so a broken link fails the check.
To preview the site while you edit, run `uv run --only-group docs zensical serve` and open http://localhost:8000.
A new page also needs an entry in `nav` in [zensical.toml](zensical.toml).
Every error code raised in the code needs a section in [docs/troubleshooting.md](docs/troubleshooting.md); the tests check this.

## Review

Once your PR is finished,
I'll take a quick look,
ask any questions,
and merge it into the project.

I will try my best to use the all-contributors bot to give you credit,
if I forget please say something.

Have fun coding :)
