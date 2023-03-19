# Streaming Services Overlay

The `streaming` Default Overlay File is used to create an overlay based on the streaming service the file is found on for each item within your library.

![](images/streaming.png)

## Requirements & Recommendations

Supported Overlay Level: Movie, Show

## Supported Streaming Services


| Streaming Service | Key            | Weight |
|:------------------|:---------------|:-------|
| Netflix           | `netflix`      | `160`  |
| Prime Video       | `amazon`       | `150`  |
| Disney+           | `disney`       | `140`  |
| HBO Max           | `hbomax`       | `130`  |
| Crunchyroll       | `Crunchyroll`  | `120`  |
| YouTube           | `youtube`      | `110`  |
| Hulu              | `hulu`         | `100`  |
| Paramount+        | `paramount`    | `90`   |
| AppleTV           | `appletv`      | `80`   |
| Peacock           | `peacock`      | `70`   |
| Showtime          | `showtime`     | `60`   |
| discovery+        | `discovery`    | `58`   |
| Crave             | `crave`        | `55`   |
| NOW               | `now`          | `50`   |
| All 4             | `all4`         | `40`   |
| britbox           | `britbox`      | `30`   |
| BET+              | `bet`          | `20`   |
| hayu              | `hayu`         | `10`   |


## Config

The below YAML in your config.yml will create the overlays:

```yaml
libraries:
  Movies:
    overlay_path:
      - pmm: streaming
  TV Shows:
    overlay_path:
      - pmm: streaming
```

## Template Variables

Template Variables can be used to manipulate the file in various ways to slightly change how it works without having to make your own local copy.

Note that the `template_variables:` section only needs to be used if you do want to actually change how the defaults work. Any value not specified is its default value if it has one if not it's just ignored.

All [Shared Overlay Variables](../overlay_variables) are available with the default values below as well as the additional Variables below which can be used to customize the file.

| Variable            | Default     |
|:--------------------|:------------|
| `horizontal_offset` | `15`        |
| `horizontal_align`  | `left`      |
| `vertical_offset`   | `150`       |
| `vertical_align`    | `bottom`    |
| `back_color`        | `#00000099` |
| `back_radius`       | `30`        |
| `back_width`        | `305`       |
| `back_height`       | `105`       |

| Variable                     | Description & Values                                                                                         |
|:-----------------------------|:-------------------------------------------------------------------------------------------------------------|
| `weight_<<key>>`<sup>1</sup> | **Description:** Controls the weight of the Overlay. Higher numbers have priority.<br>**Values:** Any Number |

1. Each default overlay has a `key` that when calling to effect a specific collection you must replace `<<key>>` with when calling.

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
    overlay_path:
      - pmm: streaming
        template_variables:
          region: ca
          use_peacock: false
          use_youtube: false
          weight_youtube: 5
```
