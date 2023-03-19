# Defaults Usage Guide

Plex Meta Manager includes a pre-created set of Metadata Files and Overlay Files which can be found in the "defaults" folder in the root of your Plex Meta Manager installation directory.

These files offer an easy-to-use and customizable set of Collections and Overlays that the user can achieve without having to worry about creating the files that make the collections and overlays possible.

All Collections come with a matching poster to make a clean, consistent set of collections in your library. These files are stored in the [Plex Meta Manager Images](https://github.com/meisnate12/Plex-Meta-Manager-Images) Repository and each poster is downloaded straight to your Plex Collection when you run Plex Meta Manager.

Credits to Sohjiro, Bullmoose20, Yozora, Cpt Kuesel, and anon_fawkes for helping drive this entire Default Set of Configs through the concept, design and implementation.

Special thanks to Magic815 for the overlay image inspiration and base template.

Please consider [donating](https://github.com/sponsors/meisnate12) towards the project.

## Collection Defaults

See the [Collection Defaults](collections) Page for more information on the specifics of the Collection Defaults.

## Overlay Defaults

See the [Overlay Defaults](overlays.md) Page for more information on the specifics of the Overlay Defaults.

## Configurations

To run a default pmm Metadata or Overlay file you can simply add it to your `metadata_path` (For Metadata Files) or `overlay_path` (For Overlay Files) using `pmm` like so:

```yaml
libraries:
  Movies:
    metadata_path:
    - pmm: actor
    - pmm: genre
    overlay_path:
    - pmm: ribbon
    - pmm: ratings
```

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
    overlay_path:
      - pmm: ratings
        template_variables:
          overlay_level: episode
```

Each file has a page on the wiki showing the available `template_variables` for each file. For example the default `pmm: ratings` has a page [here](overlays/ratings).

**In addition to the defined `template_variables` almost all default Metadata and Overlay files have access to their respective [Metadata](collection_variables)/[Overlay](overlay_variables.md) Shared Variables.**

```{include} example.md
```