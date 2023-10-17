# nixpkgs-merge-bot

## Introduction

Developed by Lassulus and Mic92 during #Oceansprint, we proudly introduce the
`nixpkgs-merge-bot`. Celebrating the milestone of 5000 concurrent open pull
requests on nixpkgs, we're enhancing the merging process with this bot! 🎉

## Features

This bot empowers package maintainers by granting them the capability to merge
PRs related to their own packages. It serves as a bridge for maintainers to
quickly respond to user feedback, facilitating a more self-reliant approach.
Especially when considering the scale of 3030 maintainers compared to just 203
committers, this bot is a game-changer.

To merge a PR, maintainers simply need to comment:

```
@nixpkgs-merge-bot merge
```

Upon invocation, the bot will verify if the conditions are suitable. If
everything is in order, it merges the PR. Otherwise, it provides feedback
through a comment detailing the discrepancies.

## Constraints

To ensure security and a focused utility, the bot adheres to specific
limitations:

- For now we only allow pull requests done by r-ryantm to be merged

- Supports merging only into the `master`, `staging`, and `staging-next`
  branches.

- CI results validation is currently absent.
