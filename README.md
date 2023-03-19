# <img src="https://metamanager.wiki/en/latest/_static/logo-full.png" alt="PMM">

[![GitHub release (latest by date)](https://img.shields.io/github/v/release/meisnate12/Plex-Meta-Manager?style=plastic)](https://github.com/meisnate12/Plex-Meta-Manager/releases)
[![Docker Image Version (latest semver)](https://img.shields.io/docker/v/meisnate12/plex-meta-manager?label=docker&sort=semver&style=plastic)](https://hub.docker.com/r/meisnate12/plex-meta-manager)
[![Docker Pulls](https://img.shields.io/docker/pulls/meisnate12/plex-meta-manager?style=plastic)](https://hub.docker.com/r/meisnate12/plex-meta-manager)
[![Develop GitHub commits since latest stable release (by SemVer)](https://img.shields.io/github/commits-since/meisnate12/plex-meta-manager/latest/develop?label=Commits%20in%20Develop&style=plastic)](https://github.com/meisnate12/Plex-Meta-Manager/tree/develop)
[![Nightly GitHub commits since latest stable release (by SemVer)](https://img.shields.io/github/commits-since/meisnate12/plex-meta-manager/latest/nightly?label=Commits%20in%20Nightly&style=plastic)](https://github.com/meisnate12/Plex-Meta-Manager/tree/nightly)

[![Discord](https://img.shields.io/discord/822460010649878528?color=%2300bc8c&label=Discord&style=plastic)](https://discord.gg/NfH6mGFuAB)
[![Reddit](https://img.shields.io/reddit/subreddit-subscribers/PlexMetaManager?color=%2300bc8c&label=r%2FPlexMetaManager&style=plastic)](https://www.reddit.com/r/PlexMetaManager/)
[![Wiki](https://img.shields.io/readthedocs/plex-meta-manager?color=%2300bc8c&style=plastic)](https://metamanager.wiki)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/meisnate12?color=%238a2be2&style=plastic)](https://github.com/sponsors/meisnate12)
[![Sponsor or Donate](https://img.shields.io/badge/-Sponsor%2FDonate-blueviolet?style=plastic)](https://github.com/sponsors/meisnate12)
[![Feature Requests](https://img.shields.io/badge/Feature%20Requests-blueviolet?style=plastic)](https://features.metamanager.wiki/)

Plex Meta Manager is an open source Python 3 project that has been designed to ease the creation and maintenance of metadata, collections, and playlists within a Plex Media Server. The script is designed to be run continuously and be able to update information based on sources outside your plex environment. Plex Meta Manager supports Movie/TV/Music libraries and Playlists.

## What Can Plex-Meta-Manager Do?

Plex Meta Manager can

1. Create and maintain collections in Plex libraries using external lists, Plex searches, or filters.

2. Create, maintain, and share playlists on Plex servers using the same or similar criteria.

3. Manage metadata [artwork, titles, summaries, release year, etc.] for anything on your Plex server.

4. Add overlays to item artwork to display various details [ratings, resolution, edition, etc.].

5. Send missing items from external lists [for example the IMDB 250] to Radarr or Sonarr for download.

6. and more.

## Getting Started

These are the high-level steps you must take to get Plex Meta Manager up and running:

1. Install Plex Meta Manager; this process is described [here](https://metamanager.wiki/en/latest/home/installation.html).

2. Once installed, you have to create a [Configuration File](https://metamanager.wiki/en/latest/config/configuration.html), which contains URLs and credentials and the like which are used to connect to services like Plex and TMDb.

3. After that you can start updating Metadata and building automatic Collections by creating a [Metadata File](https://metamanager.wiki/en/latest/metadata/metadata.html) for each Library you want to interact with.

4. After that, explore the [Wiki](https://metamanager.wiki/) to see all the different Collection Builders that can be used to create collections.

## Walkthroughs

If you find steps 1-3 above daunting, there are some walkthroughs available that will take you through those three steps: getting Plex Meta Manager installed, creating a config file, and creating a couple collections to show how the process works.

   1. The [Local Walkthrough](https://metamanager.wiki/en/latest/home/guides/local.html) covers installing the script natively [not in docker] on your local computer or a remote server.
   2. The [Docker Walkthrough](https://metamanager.wiki/en/latest/home/guides/docker.html) covers the same thing, running the script via Docker.
   3. The [unRAID Walkthrough](https://metamanager.wiki/en/latest/home/guides/unraid.html) gets you started configuring the script in UNRaid.  It doesn't go through the same steps with regard to creating the config file and metadata file, so you may want to go through the [Docker Walkthrough](https://metamanager.wiki/en/latest/home/guides/docker.html) first on your computer to gain that understanding.

## Development & Nightly Builds

Development and Nightly builds are deemed as "beta" builds which are updated far more frequently than the master branch. Bug fixes, new features and and any other code added to Plex Meta Manager first goes to the nightly branch, followed by the develop branch, before finally being released to the master branch.

The development builds (particularly the nightly branch) is only recommended for those who have a technical knowledge of Plex Meta Manager, and are happy with having to frequently update to receive the latest changes.

### Development

[![Develop GitHub commits since latest stable release (by SemVer)](https://img.shields.io/github/commits-since/meisnate12/plex-meta-manager/latest/develop?label=Commits%20in%20Develop&style=plastic)](https://github.com/meisnate12/Plex-Meta-Manager/tree/develop)

The [develop](https://github.com/meisnate12/Plex-Meta-Manager/tree/develop) branch has the most updated **documented** fixes and enhancements to Plex Meta Manager.  This version is tested and documented to some degree, but it is still an active development branch, so there may be rough edges.

If switching to the develop build, it is recommended to also use the [develop branch of the wiki](https://metamanager.wiki/en/develop/), which documents any changes made from the Master build.

### Nightly

[![Nightly GitHub commits since latest stable release (by SemVer)](https://img.shields.io/github/commits-since/meisnate12/plex-meta-manager/latest/nightly?label=Commits%20in%20Nightly&style=plastic)](https://github.com/meisnate12/Plex-Meta-Manager/tree/nightly)

There is also a [nightly](https://github.com/meisnate12/Plex-Meta-Manager/tree/nightly) build which will have the absolute latest version of the script, but it could easily break, there is no guarantee that it even works, and any new features will not be documented.

**This branch will have squashed commits which can cause `git pull`/`git fetch` to error you can use `git reset origin/nightly --hard` to fix the branch.**

As this build is subject to extreme change, there is no promise of the feature being documented in the [nightly](https://metamanager.wiki/en/nightly/) branch of the wiki and all discussions relating to changes made in the nightly build will be held within the [Plex Meta Manager Discord Server](https://discord.gg/NfH6mGFuAB).

## Example Usage

Plex Meta Manager gives the user the power to curate a set of Collections to make discovering and organizing media easy. They can be built either using plex-based searches/filters, or by using popular builders such as TMDb, IMDb, Trakt, MDBList, MyAnimeList and many more.

Some example collections that can be created are:
  * Trending/Popular (based on TMDb, IMDb, Trakt, etc.)
  * Streaming Service (such as Netflix, Disney+, etc.)
  * Networks
  * Studios
  * Genres
  * Actors
  * Decades

Below are some user-curated collections which have been created by Plex Meta Manager.

![Movie Collection Preview](https://metamanager.wiki/en/latest/_images/movie-collection-preview.png)

![Movie Library Preview](https://metamanager.wiki/en/latest/_images/movie-library-preview.png)

![Show Collection Preview](https://metamanager.wiki/en/latest/_images/show-collection-preview.png)

![Show Library Preview](https://metamanager.wiki/en/latest/_images/show-collection-preview.png)

## Default and User Submitted Metadata/Overlay Files

The overlays and collection built in the images above can be easily added to any plex by using the [PMM Defaults](https://metamanager.wiki/en/latest/defaults/guide.html). These Files were created by the PMM team to make it easier than ever to have customized collections and overlays.

To see user submitted Metadata configuration files, and you to even add your own, go to the [Plex Meta Manager Configs](https://github.com/meisnate12/Plex-Meta-Manager-Configs).

## Discord Support Server
Before posting on GitHub about an enhancement, error, or configuration question please visit the [Plex Meta Manager Discord Server](https://discord.gg/NfH6mGFuAB). we have a dedicated support thread system so that your query can be dealt with efficiently by our team and community.

## Feature Requests
If you have an idea for how to enhance Plex Meta Manager or just want to vote on what should be added next please visit the [Feature Request](https://features.metamanager.wiki/features) Page.

## Errors and Configuration Questions
If you are unable to use the [Plex Meta Manager Discord Server](https://discord.gg/NfH6mGFuAB), please follow this guidance:
* If you have an idea for how to enhance Plex Meta Manager please open a new [Feature Request](https://github.com/meisnate12/Plex-Meta-Manager/issues/new?assignees=meisnate12&labels=status%3Anot-yet-viewed%2C+enhancement&2.feature_request.yml&title=%5BFeature%5D%3A+).
* If you're getting an Error please update to the latest version and then open a [Bug Report](https://github.com/meisnate12/Plex-Meta-Manager/issues/new?assignees=meisnate12&labels=status%3Anot-yet-viewed%2C+bug&template=1.bug_report.yml&title=%5BBug%5D%3A++) if the error persists.
* If you see a mistake/typo with the [Plex Meta Manager Wiki](https://metamanager.wiki/) or have an idea of how we can improve it please open a [Wiki Request](https://github.com/meisnate12/Plex-Meta-Manager/issues/new?assignees=meisnate12&labels=status%3Anot-yet-viewed%2C+documentation&template=3.docs_request.yml&title=%5BDocs%5D%3A+)
* If you have a metadata configuration query please post in the [Discussions](https://github.com/meisnate12/Plex-Meta-Manager/discussions).

## Contributing
* Pull Requests are greatly encouraged, please submit all Pull Requests to the nightly branch.
