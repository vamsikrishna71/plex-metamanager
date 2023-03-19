# Collection Defaults

There are many Default Metadata Files built into PMM itself which offer an easy-to-use and customizable set of Collections that the user can achieve without having to worry about creating the files that makes the collections possible.

This is the simplest way to create Collections using Plex Meta Manager.

```{include} collection_list.md
```

## Configurations

To run a default pmm Metadata file you can simply add it to your `metadata_path` using `pmm` like so:

```yaml
libraries:
  Movies:
    metadata_path:
      - pmm: actor
      - pmm: genre
```

## Separators

Most Metadata files use separators to denote different sections of collection like actor collections vs studio collections.

**Chart Separator and Award Separator each have their own file, while the other Separators are part of their respective files.**

<details>
  <summary>Click to expand to see an example of Separators.</summary>

   ![](images/separators.jpg)

</details>

### Library On/Off

Chart Separators are turned On by default (except `seasonal`), to turn the Separators On/Off on a per Library basis.

```yaml
libraries:
  LIBRARYNAME:
    template_variables:
      use_separator: false
    metadata_path:
      - pmm: actor
      - pmm: genre
```

## Collection Section Order

All Default Metadata Files have a `collection_section` attribute. These attributes determine the order of the various sections and can be set by [customizing your config](#customizing-configs).

For example: `collection_section: 01` translates to `sort_title: "!<<collection_section>><<pre>><<order_<<key>>>><<sort>>"` and so for `genre` if you have a `Fantasy` collection, plex is going to show `!06_Fantasy`

This is the default PMM collection ordering:

| Collection             | Collection Section |
|:-----------------------|:-------------------|
| `seasonal`             | `000`              |
| `basic`                | `010`              |
| `anilist`              | `020`              |
| `imdb`                 | `020`              |
| `flixpatrol`           | `020`              |
| `myanimelist`          | `020`              |
| `other_chart`          | `020`              |
| `tautulli`             | `020`              |
| `tmdb`                 | `020`              |
| `trakt`                | `020`              |
| `streaming`            | `030`              |
| `universe`             | `040`              |
| `network`              | `050`              |
| `genre`                | `060`              |
| `studio`               | `070`              |
| `studio_anime`         | `070`              |
| `country`              | `080`              |
| `based`                | `085`              |
| `audio_language`       | `090`              |
| `subtitle_language`    | `095`              |
| `decade`               | `100`              |
| `year`                 | `105`              |
| `content_rating_us`    | `110`              |
| `content_rating_uk`    | `110`              |
| `content_rating_cs`    | `110`              |
| `resolution`           | `120`              |
| `bafta`                | `130`              |
| `cannes`               | `130`              |
| `choice`               | `130`              |
| `emmy`                 | `130`              |
| `golden`               | `130`              |
| `oscars`               | `130`              |
| `other_award`          | `130`              |  
| `spirit`               | `130`              |
| `sundance`             | `130`              |
| `actor`                | `140`              |
| `director`             | `150`              |
| `producer`             | `160`              |
| `writer`               | `170`              |

## Customizing Configs

Configs can be customized using the `template_variables` attribute when calling the file. These `template_variables` will be given to every template call in the file which allows them to affect how that file runs.

This example changes the ratings overlay to work on episodes.

```yaml
libraries:
  TV Shows:
    metadata_path:
      - pmm: imdb
        template_variables:
          use_popular: false
          use_lowest: false
          visible_library_top: true
          visible_home_top: true
          visible_shared_top: true
```

Each file has a page on the wiki showing the available `template_variables` for each file. For example the default `pmm: genre` has a page [here](both/genre).

**In addition to the defined `template_variables` almost all default Metadata files have access to the [Shared Variables](collection_variables).**

### Examples

For example if you want yearly oscar collections that go back 10 years instead of 5 all of which gets sent to radarr use the `data` and `radarr_add_missing` template variables.

```yaml
libraries:
  Movies:
    metadata_path:
      - pmm: oscars
        template_variables:
          radarr_add_missing: true
          data:
            starting: current_year-10
            ending: current_year
```

Or maybe you want to change the number of actor collections made using pmm: actor.

```yaml
libraries:
  Movies:
    overlay_path:
      - pmm: actor
        template_variables:
          collection_mode: hide
          data:
            depth: 5
            limit: 50
```

Or maybe you want to change the collection sort order of the genre collections using pmm: genre.

```yaml
libraries:
  Movies:
    metadata_path:
      - pmm: genre
        template_variables:
          collection_section: 11
```

Or maybe you want to disable separators globally per library.

```yaml
libraries:
  LIBRARYNAME:
    template_variables:
      use_separator: false
    metadata_path:
      - ...
```

Alternatively it can be turned off individually per git file:

```yaml
libraries:
  LIBRARYNAME:
    metadata_path:
      - pmm: <file1>    # separator is disabled
        template_variables:
          use_separator: false
      - pmm: <file2>    # separator is enabled by default
      - pmm: <file3>    # separator is disabled
        template_variables:
          use_separator: false
```

```{include} example.md
```