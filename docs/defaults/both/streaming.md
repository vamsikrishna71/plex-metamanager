# Streaming Collections

The `streaming` Default Metadata File is used to dynamically create collections based on the streaming Services that your media is available on.

![](../images/streaming.png)

## Requirements & Recommendations

Supported Library Types: Movie, Show

## Collections Section 030

| Collection                 | Key           | Description                                                                 |
|:---------------------------|:--------------|:----------------------------------------------------------------------------|
| `Streaming Collections`    | `separator`   | [Separator Collection](../separators) to denote the Section of Collections. |
| `All 4 Movies/Shows`       | `all4`        | Collection of Movies/Shows Streaming on All 4.                              |
| `Apple TV+ Movies/Shows`   | `appletv`     | Collection of Movies/Shows Streaming on Apple TV+.                          |
| `BET+ Movies/Shows`        | `bet`         | Collection of Movies/Shows Streaming on BET+.                               |
| `BritBox Movies/Shows`     | `britbox`     | Collection of Movies/Shows Streaming on BritBox.                            |
| `Crave Movies/Shows`       | `crave`       | Collection of Movies/Shows Streaming on Crave.                              |
| `Crunchyroll Shows`        | `crunchyroll` | Collection of Shows Streaming on Crunchyroll.                               |
| `discovery+ Shows`         | `discovery`   | Collection of Shows Streaming on discovery+.                                |
| `Disney+ Movies/Shows`     | `disney`      | Collection of Movies/Shows Streaming on Disney+.                            |
| `hayu Shows`               | `hayu`        | Collection of Shows Streaming on hayu.                                      |
| `HBO Max Movies/Shows`     | `hbomax`      | Collection of Movies/Shows Streaming on HBO Max.                            |
| `Hulu Movies/Shows`        | `hulu`        | Collection of Movies/Shows Streaming on Hulu.                               |
| `Netflix Movies/Shows`     | `netflix`     | Collection of Movies/Shows Streaming on Netflix.                            |
| `NOW Movies/Shows`         | `now`         | Collection of Movies/Shows Streaming on NOW.                                |
| `Paramount+ Movies/Shows`  | `paramount`   | Collection of Movies/Shows Streaming on Paramount+.                         |
| `Peacock Movies/Shows`     | `peacock`     | Collection of Movies/Shows Streaming on Peacock.                            |
| `Prime Video Movies/Shows` | `amazon`      | Collection of Movies/Shows Streaming on Prime Video.                        |
| `Showtime Movies/Shows`    | `showtime`    | Collection of Movies/Shows Streaming on Showtime.                           |

## Config

The below YAML in your config.yml will create the collections:

```yaml
libraries:
  Movies:
    metadata_path:
      - pmm: streaming
  TV Shows:
    metadata_path:
      - pmm: streaming
```

## Template Variables

Template Variables can be used to manipulate the file in various ways to slightly change how it works without having to make your own local copy.

Note that the `template_variables:` section only needs to be used if you do want to actually change how the defaults work. Any value not specified is its default value if it has one if not it's just ignored.

All [Shared Collection Variables](../collection_variables) are available as well as the additional Variables below which can be used to customize the file.

This file contains a [Separator](../separators) so all [Shared Separator Variables](../separators.md#shared-separator-variables) are available as well.

| Variable                        | Description & Values                                                                                                                                                                                                                                                                             |
|:--------------------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `limit`                         | **Description:** Changes the Builder Limit for all collections in a Defaults file.<br>**Values:** Number Greater then 0                                                                                                                                                                          |
| `limit_<<key>>`<sup>1</sup>     | **Description:** Changes the Builder Limit of the specified key's collection.<br>**Default:** `limit`<br>**Values:** Number Greater then 0                                                                                                                                                       |
| `sort_by`                       | **Description:** Changes the Smart Filter Sort for all collections in a Defaults file.<br>**Default:** `release.desc`<br>**Values:** [Any `smart_filter` Sort Option](../../metadata/builders/smart.md#sort-options)                                                                             |
| `sort_by_<<key>>`<sup>1</sup>   | **Description:** Changes the Smart Filter Sort of the specified key's collection.<br>**Default:** `sort_by`<br>**Values:** [Any `smart_filter` Sort Option](../../metadata/builders/smart.md#sort-options)                                                                                       |
| `sync_mode`                     | **Description:** Changes the Sync Mode for all collections in a Defaults file.<br>**Default:** `sync`<br>**Values:**<table class="clearTable"><tr><td>`sync`</td><td>Add and Remove Items based on Builders</td></tr><tr><td>`append`</td><td>Only Add Items based on Builders</td></tr></table> |
| `sync_mode_<<key>>`<sup>1</sup> | **Description:** Changes the Sync Mode of the specified key's collection.<br>**Default:** `sync_mode`<br>**Values:**<table class="clearTable"><tr><td>`sync`</td><td>Add and Remove Items based on Builders</td></tr><tr><td>`append`</td><td>Only Add Items based on Builders</td></tr></table> |
| `exclude`                       | **Description:** Exclude these Streaming Services from creating a Dynamic Collection.<br>**Values:** List of Streaming Service Keys                                                                                                                                                              |
| `region`                        | **Description:** Changes some Streaming Service lists to regional variants (see below table for more information.<br>**Default:** `us`<br>**Values:** `us,`uk`,`ca`, `da`, `de`, `es`, `fr`, `it`, `pt-br`                                                                                       |
| `streaming_name`                | **Description:** Changes the title format of the Dynamic Collections.<br>**Default:** `<<key_name>> <<library_translationU>>s`<br>**Values:** Any string with `<<key_name>>` in it.                                                                                                              |
| `streaming_summary`             | **Description:** Changes the summary format of the Dynamic Collections.<br>**Default:** `<<library_translationU>>s streaming on <<key_name>>.`<br>**Values:** Any string.                                                                                                                        |

1. Each default collection has a `key` that when calling to effect a specific collection you must replace `<<key>>` with when calling.

## Regional Variants

Some logic is applied to allow for regional streaming service lists to be available to users depending on where they are, as detailed below:

| Region           | Key                              | Description                                                                                                                               |
|:-----------------|:---------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| any besides `us` | `amazon`, `disney`, `netflix`    | These collections will use regional variant lists to ensure the lists populate with what is available in the region specified             |
| any besides `uk` | `all4`, `britbox`, `hayu`, `now` | These collections will not be created if the region is not `uk` as these streaming services are UK-focused                                |
| any besides `ca` | `crave`                          | These collections will not be created if the region is not `ca` as these streaming services are Canada-focused                            |
| `ca`             | `hbomax`, `showtime`             | These collections will not be created if the region is `ca` as these streaming services are part of the Crave streaming service in Canada |


The below is an example config.yml extract with some Template Variables added in to change how the file works.

```yaml
libraries:
  Movies:
    metadata_path:
      - pmm: streaming
        template_variables:
          region: fr
          use_separator: false
          sep_style: stb
          visible_library_disney: true
          visible_home_disney: true
          visible_shared_disney: true
          sonarr_add_missing_hulu: true
          radarr_add_missing_amazon: true
          sort_by: random
```