# Git-Recon: find interesting commits

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Takes a list of projects and keywords and looks for commits that have any of those keywords.

Inspired by [cryptodotis/code-peer-review](https://github.com/cryptodotis/code-peer-review).

### Usage

You can find my instance at [snkth.com/git-recon](https://snkth.com/git-recon). But you probably want to create your own instance.

#### Running Locally

1. clone the repo;
2. update the `config.toml` file to use your projects and keywords;
3. `pipenv install` to install deps;
4. `pipenv run python generate.py` to generate `docs/index.html`; and
5. look at `docs/index.html` in your favourite browser.

#### Using Github Pages

1. fork the repo;
2. update the `config.toml` file to use your projects and keywords;
3. ensure that github pages and github actions are working; and
4. look at your github pages url.
