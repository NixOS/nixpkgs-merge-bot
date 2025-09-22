# nixpkgs-merge-bot

## Introduction

Developed by Lassulus and Mic92 during #Oceansprint, we proudly introduce the
`nixpkgs-merge-bot`. Celebrating the milestone of 5000 concurrent open pull
requests on nixpkgs, we're enhancing the merging process with this bot! 🎉

[Mergebot RFC](https://github.com/NixOS/rfcs/pull/172)

See also [approving changes](#approving-changes) below, for how the mergebot can
evolve beyond the RFC.

## Features

This bot empowers package maintainers by granting them the capability to merge
PRs related to their own packages. It serves as a bridge for maintainers to
quickly respond to user feedback, facilitating a more self-reliant approach.
Especially when considering the scale of 3030 maintainers compared to just 203
committers, this bot is a game-changer.

To merge a PR, maintainers simply need to comment:

```
@NixOS/nixpkgs-merge-bot merge
```

Upon invocation, the bot will verify if the conditions are suitable. If
everything is in order, it merges the PR. Otherwise, it provides feedback
through a comment detailing the discrepancies.

## Contact

We can be found on the
[nixpkgs-ci matrix channel](https://matrix.to/#/#nixpkgs-ci:nixos.org).

## Constraints

To ensure security and a focused utility, the bot adheres to specific
limitations:

- Only compatible with packages located under `pkgs/by-name/*`.

- For now we only allow pull requests done by r-ryantm or committers to be
  merged

- Supports merging only into the `master`, `staging`, and `staging-next`
  branches.

## Approving changes

As with any project, fixes, improvements, and other changes are expected.

Usually, such changes can be approved internally by the @NixOS/nixpkgs-ci team
and other repository collaborators. However, changes that increase the scope of
**what** the mergebot will merge or **who** can trigger merging will typically
require additional acknowledgement from a "higher power".

Such "higher powers" include anyone responsible for deciding who can merge
things into nixpkgs, principally:

- The @NixOS/commit-bit-delegation
- The @NixOS/steering committee

A ping for approval not responded to within a week will usually be interpreted
as a silent acknowledgement.

---

<img src="https://qr.helsinki-systems.de/logo/github" height="200">

Supported by [Helsinki Systems](https://helsinki-systems.de/) Systems and
[lassulus](https://github.com/Lassulus). From package maintenance to
comprehensive support, we ensure your infrastructure is efficient, up-to-date,
and secure. Whether it's in our data center or on your premises, we tailor our
services to fit your needs.

[Contact us to learn more.](https://helsinki-systems.de/kontakt)
