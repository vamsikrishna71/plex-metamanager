# Overlay Files

Overlay files are used to create and maintain overlays within the Plex libraries on the server.

Overlays and templates are defined within one or more Overlay files, which are linked to libraries in the [Libraries Attribute](../config/libraries.md#overlay-path) within the [Configuration File](../config/configuration.md).

All overlay coordinates assume 1000 x 1500 for Posters and 1920 x 1080 for Backgrounds and Title Cards.

**To remove all overlays add `remove_overlays: true` to the `overlay_path` [Libraries Attribute](../config/libraries.md#remove-overlays).**

**IMPORTANT NOTE ON OVERLAYS:** Once you have applied overlays to your posters in PLex, it is highly recommennded that you never change artwork on a thing directly in Plex again.  PMM uses labels on the items in Plex to decide if an overlays has been applied, so if you change artwork behind PMM's back things can become confused and items can end up with double-overlaid posters.  It's recommended to set new artwork using the asset directory, which will ensure that this doesn't happen. 

**To change a single overlay original image either remove the `Overlay` shared label and update the Image in Plex or replace the image in the assets folder and then PMM will overlay the new image**

These are the attributes which can be used within the Overlay File:

| Attribute                                               | Description                                                                                                        |
|:--------------------------------------------------------|:-------------------------------------------------------------------------------------------------------------------|
| [`templates`](templates)                                | contains definitions of templates that can be leveraged by multiple overlays                                       |
| [`external_templates`](templates.md#external-templates) | contains [path types](../config/paths) that point to external templates that can be leveraged by multiple overlays |
| [`queues`](#overlay-queues)                             | contains the positional attributes of queues                                                                       |
| [`overlays`](#overlays-attributes)                      | contains definitions of overlays you wish to add                                                                   |

* `overlays` is required in order to run the Overlay File.
* Example Overlay Files can be found in the [Plex Meta Manager Configs Repository](https://github.com/meisnate12/Plex-Meta-Manager-Configs/tree/master/PMM)

## Overlays Attributes

Each overlay definition requires its own section within the `overlays` attribute.

```yaml
overlays:
  IMDb Top 250:
    # ... builders, details, and filters for this overlay
  4K:
    # ... builders, details, and filters for this overlay
  etc:
    # ... builders, details, and filters for this overlay
```

There are multiple types of attributes that can be utilized within an overlay:

* [Builders](builders)
* [Settings/Updates](update)
* [Filters](filters)

## Overlay

Each overlay definition needs to specify what overlay to use. This can happen in 3 ways.

1. If there is no `overlay` attribute PMM will look in your `config/overlays` folder for a `.png` file named the same as the mapping name of the overlay definition. This example below would look for `IMDb Top 250.png`.
    ```yaml
    overlays:
      IMDb Top 250:
        imdb_chart: top_movies
    ```
   
2. If the `overlay` attribute is given a string PMM will look in your `config/overlays` folder for a `.png` file named the same as the string given. This example below would look for `IMDbTop.png`.
    ```yaml
    overlays:
      overlay: IMDbTop
      IMDb Top 250:
        imdb_chart: top_movies
    ```
   
3. Using a dictionary for more overlay location options.

```yaml
overlays:
  IMDb Top 250:
    overlay:
      name: IMDb Top 250
    imdb_chart: top_movies
```

There are many attributes available when using overlays to edit how they work.

| Attribute                  | Description                                                                                                                                                                                                                                                                         | Required |
|:---------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------:|
| `name`                     | Name of the overlay.                                                                                                                                                                                                                                                                | &#9989;  |
| `file`                     | Local location of the Overlay Image.                                                                                                                                                                                                                                                | &#10060; |
| `url`                      | URL of Overlay Image Online.                                                                                                                                                                                                                                                        | &#10060; |
| `git`                      | Location in the [Configs Repo](https://github.com/meisnate12/Plex-Meta-Manager-Configs) of the Overlay Image.                                                                                                                                                                       | &#10060; |
| `repo`                     | Location in the [Custom Repo](../config/settings.md#custom-repo) of the Overlay Image.                                                                                                                                                                                              | &#10060; |
| [`group`](#overlay-groups) | Name of the Grouping for this overlay. Only one overlay with the highest weight per group will be applied.<br>**`weight` is required when using `group`**<br>**Values:** group name                                                                                                 | &#10060; |
| [`queue`](#overlay-queues) | Name of the Queue for this overlay. Define `queue` positions using the `queues` attribute at the top level of an Overlay File. Overlay with the highest weight is applied to the first position and so on.<br>**`weight` is required when using `queue`**<br>**Values:** queue name | &#10060; |
| `weight`                   | Weight of this overlay in its group or queue.<br>**`group` or `queue` is required when using `weight`**<br>**Values:** Integer 0 or greater                                                                                                                                         | &#10060; |
| `horizontal_offset`        | Horizontal Offset of this overlay. Can be a %.<br>**`vertical_offset` is required when using `horizontal_offset`**<br>**Value:** Integer 0 or greater or 0%-100%                                                                                                                    | &#10060; |
| `horizontal_align`         | Horizontal Alignment of the overlay.<br>**Values:** `left`, `center`, `right`                                                                                                                                                                                                       | &#10060; |
| `vertical_offset`          | Vertical Offset of this overlay. Can be a %.<br>**`horizontal_offset` is required when using `vertical_offset`**<br>**Value:** Integer 0 or greater or 0%-100%                                                                                                                      | &#10060; |
| `vertical_align`           | Vertical Alignment of the overlay.<br>**Values:** `top`, `center`, `bottom`                                                                                                                                                                                                         | &#10060; |
| `font`                     | System Font Filename or path to font file for the Text Overlay.<br>**Value:** System Font Filename or path to font file                                                                                                                                                             | &#10060; |
| `font_style`               | Font style for Variable Fonts. Only needed when using a Variable Font.<br>**Value:** Variable Font Style                                                                                                                                                                            | &#10060; |
| `font_size`                | Font Size for the Text Overlay.<br>**Value:** Integer greater than 0                                                                                                                                                                                                                | &#10060; |
| `font_color`               | Font Color for the Text Overlay.<br>**Value:** Color Hex Code in format `#RGB`, `#RGBA`, `#RRGGBB` or `#RRGGBBAA`.                                                                                                                                                                  | &#10060; |
| `stroke_width`             | Font Stroke Width for the Text Overlay.<br>**Value:** Integer greater than 0                                                                                                                                                                                                        | &#10060; |
| `stroke_color`             | Font Stroke Color for the Text Overlay.<br>**Value:** Color Hex Code in format `#RGB`, `#RGBA`, `#RRGGBB` or `#RRGGBBAA`.                                                                                                                                                           | &#10060; |
| `back_color`               | Backdrop Color for the Text Overlay.<br>**Value:** Color Hex Code in format `#RGB`, `#RGBA`, `#RRGGBB` or `#RRGGBBAA`.                                                                                                                                                              | &#10060; |
| `back_width`               | Backdrop Width for the Text Overlay. If `back_width` is not specified the Backdrop Sizes to the text<br>**`back_height` is required when using `back_width`**<br>**Value:** Integer greater than 0                                                                                  | &#10060; |
| `back_height`              | Backdrop Height for the Text Overlay. If `back_height` is not specified the Backdrop Sizes to the text<br>**`back_width` is required when using `back_height`**<br>**Value:** Integer greater than 0                                                                                | &#10060; |
| `back_align`               | Alignment for the Text Overlay inside the backdrop. If `back_align` is not specified the Backdrop Centers the text<br>**`back_width` and `back_height` are required when using `back_align`**<br>**Values:** `left`, `right`, `center`, `top`, `bottom`                             | &#10060; |
| `back_padding`             | Backdrop Padding for the Text Overlay.<br>**Value:** Integer greater than 0                                                                                                                                                                                                         | &#10060; |
| `back_radius`              | Backdrop Radius for the Text Overlay.<br>**Value:** Integer greater than 0                                                                                                                                                                                                          | &#10060; |
| `back_line_color`          | Backdrop Line Color for the Text Overlay.<br>**Value:** Color Hex Code in format `#RGB`, `#RGBA`, `#RRGGBB` or `#RRGGBBAA`.                                                                                                                                                         | &#10060; |
| `back_line_width`          | Backdrop Line Width for the Text Overlay.<br>**Value:** Integer greater than 0                                                                                                                                                                                                      | &#10060; |
| `addon_offset`             | Text Addon Image Offset from the text.<br>**`addon_offset` Only works with text overlays**<br>**Value:** Integer 0 or greater                                                                                                                                                       | &#10060; |
| `addon_position`           | Text Addon Image Alignment in relation to the text.<br>**`addon_position` Only works with text overlays**<br>**Values:** `left`, `right`, `top`, `bottom`                                                                                                                           | &#10060; |

* If `url`, `git`, and `repo` are all not defined then PMM will look in your `config/overlays` folder for a `.png` file named the same as the `name` attribute.

### Non-Positional Image Overlay

Non-Positional overlays are images that are either 1000 x 1500 for Posters or 1920 x 1080 for Backgrounds and Title Cards.

These Overlays should be mostly transparent and will just be completely merged with the base image.

### Positional Image Overlay

Positional overlays can be of any size and use `horizontal_offset`, `horizontal_align`, `vertical_offset`, and `vertical_align` to position the overlay on the image. 

```yaml
overlays:
  IMDB-Top-250:
    imdb_chart: top_movies
    overlay:
      name: IMDB-Top-250
      pmm: images/IMDB-Top-250
      horizontal_offset: 0
      horizontal_align: right
      vertical_offset: 0
      vertical_align: bottom
```

### Blurring Overlay

There is a special overlay named `blur` that when given as the overlay name will instead of finding the image will just blur the image instead.

You can control the level of the blur by providing a number with the attribute like so `blur(##)`.

```yaml
overlays:
  blur:
    overlay:
      name: blur(50)
    builder_level: episode
    plex_search:
      all:
        resolution: 4K
```

   ![](blur.png)

### Backdrop Overlay

There is a special overlay named `backdrop` that when given as the overlay name will instead of finding the image will just apply the background instead.

You can set the size of the backdrop with `back_width` and `back_height`. By Default, they will extend the length of the Image.

```yaml
overlays:
  blur:
    overlay:
      name: backdrop
      back_color: "#00000099"
    builder_level: episode
    plex_all: true
```

### Text Overlay

You can add text as an overlay using the special `text()` overlay name. Anything inside the parentheses will be added as an overlay onto the image. Ex `text(4K)` adds `4K` to the image.

You can control the font, font size and font color using the `font`, `font_size`, and `font_color` overlay attributes.

You can control the backdrop of the text using the various `back_*` attributes.

The `horizontal_offset` and `vertical_offset` overlay attributes are required when using Text Overlays.

PMM includes multiple fonts in the [`fonts` folder](https://github.com/meisnate12/Plex-Meta-Manager/tree/master/fonts) which can be called using `fonts/fontname.ttf`

```yaml
overlays:
  audience_rating:
    overlay:
      name: text(Direct Play)
      horizontal_offset: 0
      horizontal_align: center
      vertical_offset: 150
      vertical_align: bottom
      font: fonts/Inter-Medium.ttf
      font_size: 63
      font_color: "#FFFFFF"
      back_color: "#00000099"
      back_radius: 30
```

#### Special Text Variables

You can use the item's metadata to determine the text by adding Special Text Variables to your text Overlay.

There are multiple Special Text Variables that can be used when formatting the text. The variables are defined like so `<<name>>` and some can have modifiers like so `<<name$>>` where `$` is the modifier. The available options are:

| Special Text Variables & Mods                                                                                                                                                                                                                                                                 |  Movies  |  Shows   | Seasons  | Episodes |
|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------:|:--------:|:--------:|:--------:|
| `<<audience_rating>>`: audience rating (`8.7`, `9.0`)<br>`<<audience_rating%>>`: audience rating out of 100 (`87`, `90`)<br>`<<audience_rating#>>`: audience rating removing `.0` as needed (`8.7`, `9`)<br>`<<audience_rating/>>`: audience rating on a 5 point scale (`8.6` shows as `4.3`) | &#9989;  | &#9989;  | &#10060; | &#9989;  |
| `<<critic_rating>>`: critic rating (`8.7`, `9.0`)<br>`<<critic_rating%>>`: critic rating out of 100 (`87`, `90`)<br>`<<critic_rating#>>`: critic rating removing `.0` as needed (`8.7`, `9`)<br>`<<critic_rating/>>`: critic rating on a 5 point scale (`8.6` shows as `4.3`)                 | &#9989;  | &#9989;  | &#10060; | &#9989;  |
| `<<user_rating>>`: user rating (`8.7`, `9.0`)<br>`<<user_rating%>>`: user rating out of 100 (`87`, `90`)<br>`<<user_rating#>>`: user rating removing `.0` as needed (`8.7`, `9`)<br>`<<user_rating/>>`: user rating on a 5 point scale (`8.6` shows as `4.3`)                                 | &#9989;  | &#9989;  | &#9989;  | &#9989;  |
| `<<title>>`: Title of the Item<br>`<<titleU>>`: Uppercase Title of the Item<br>`<<titleL>>`Lowercase Title of the Item<br>`<<titleP>>`Proper Title of the Item                                                                                                                                | &#9989;  | &#9989;  | &#9989;  | &#9989;  |
| `<<show_title>>`: Title of the Item's Show<br>`<<show_itleU>>`: Uppercase Title of the Item's Show<br>`<<show_titleL>>`Lowercase Title of the Item's Show<br>`<<show_titleP>>`Proper Title of the Item's Show                                                                                 | &#10060; | &#10060; | &#9989;  | &#9989;  |
| `<<season_title>>`: Title of the Item's Season<br>`<<season_titleU>>`: Uppercase Title of the Item's Season<br>`<<season_titleL>>`Lowercase title of the Item's Season<br>`<<season_titleP>>`Proper title of the Item's Season                                                                | &#10060; | &#10060; | &#10060; | &#9989;  |
| `<<original_title>>`: Original Title of the Item<br>`<<original_titleU>>`: Original Title of the Item<br>`<<original_titleL>>`Lowercase Original Title of the Item<br>`<<original_titleP>>`Proper Original Title of the Item                                                                  | &#9989;  | &#9989;  | &#10060; | &#10060; |
| `<<edition>>`: Edition of the Item<br>`<<editionU>>`: Uppercase Edition of the Item<br>`<<editionL>>`Lowercase Edition of the Item<br>`<<editionP>>`Proper Edition of the Item                                                                                                                | &#9989;  | &#10060; | &#10060; | &#10060; |
| `<<content_rating>>`: Content Rating of the Item<br>`<<content_ratingU>>`: Uppercase Content Rating of the Item<br>`<<content_ratingL>>`Lowercase Content Rating of the Item<br>`<<content_ratingP>>`Proper Content Rating of the Item                                                        | &#9989;  | &#9989;  | &#10060; | &#9989;  |
| `<<episode_count>>`: Number of Episodes (`1`)<br>`<<episode_countW>>`: Number of Episodes As Words (`One`)<br>`<<episode_count0>>`: Number of Episodes With 10s Padding (`01`)<br>`<<episode_count00>>`: Number of Episodes With 100s Padding (`001`)                                         | &#10060; | &#9989;  | &#9989;  | &#10060; |
| `<<season_number>>`: Season Number (`1`)<br>`<<season_numberW>>`: Season Number As Words (`One`)<br>`<<season_number0>>`: Season Number With 10s Padding (`01`)<br>`<<season_number00>>`: Season Number With 100s Padding (`001`)                                                             | &#10060; | &#10060; | &#9989;  | &#9989;  |
| `<<episode_number>>`: Episode Number (`1`)<br>`<<episode_numberW>>`: Episode Number As Words (`One`)<br>`<<episode_number0>>`: Episode Number With 10s Padding (`01`)<br>`<<episode_number00>>`: Episode Number With 100s Padding (`001`)                                                     | &#10060; | &#10060; | &#10060; | &#9989;  |
| `<<versions>>`: Number of Versions of the Item (`1`)<br>`<<versionsW>>`: Number of Versions of the Item As Words (`One`)<br>`<<versions0>>`: Number of Versions of the Item With 10s Padding (`01`)<br>`<<versions00>>`: Number of Versions of the Item With 100s Padding (`001`)             | &#9989;  | &#10060; | &#10060; | &#9989;  |
| `<<runtime>>`: Complete Runtime of the Item in minutes (`150`)<br>`<<runtimeH>>`: Hours in runtime of the Item (`2`)<br>`<<runtimeM>>`: Minutes remaining in the hour in the runtime of the Item (`30`)                                                                                       | &#9989;  | &#10060; | &#10060; | &#9989;  |
| `<<bitrate>>`: Bitrate of the first media file for an item.<br>`<<bitrateH>>`: Bitrate of the media file with the highest bitrate<br>`<<bitrateL>>`: Bitrate of the media file with the lowest bitrate                                                                                        | &#9989;  | &#10060; | &#10060; | &#9989;  |
| `<<originally_available>>`: Original Available Date of the Item<br>`<<originally_available[FORMAT]>>`: Original Available Date of the Item in the given format. [Format Options](https://strftime.org/)                                                                                       | &#9989;  | &#9989;  | &#10060; | &#9989;  |

Note: You can use the `mass_audience_rating_update` or `mass_critic_rating_update` [Library Operation](../config/operations) to update your plex ratings to various services like `tmdb`, `imdb`, `mdb`, `metacritic`, `letterboxd` and many more.

##### Example

I want to have the audience_rating display with a `%` out of 100 vs 0.0-10.0.
```yaml
overlays:
  audience_rating:
    overlay:
      name: text(<<audience_rating%>>%)
      horizontal_offset: 225
      horizontal_align: center
      vertical_offset: 15
      vertical_align: top
      font: fonts/Inter-Medium.ttf
      font_size: 63
      font_color: "#FFFFFF"
      back_color: "#00000099"
      back_radius: 30
      back_width: 300
      back_height: 105
```

I want to add `S##E##` to all my episode images.
```yaml
overlays:
  text_content_rating:
    builder_level: episode
    overlay:
      name: text(S<<season_number0>>E<<episode_number0>>)
      horizontal_align: center
      vertical_offset: 15
      vertical_align: top
      font: fonts/Inter-Medium.ttf
      font_size: 63
      font_color: "#FFFFFF"
      back_color: "#00000099"
      back_radius: 30
      back_width: 300
      back_height: 105
    plex_all: true
```

##### Common Special Text Uses

These are some commonly-used examples of Special Text overlays:

| Special Text                                                      | Example Output     |
|:------------------------------------------------------------------|--------------------|
| `name: text(S<<season_number0>>E<<episode_number0>>)`             | S01E01             |
| `name: text(Season <<season_number>> Episode <<episode_number>>)` | Season 1 Episode 1 |
| `name: text(Season <<season_number>>)`                            | Season 1           |
| `name: text(Episode <<episode_number>>)`                          | Episode 1          |
| `name: "text(Runtime: <<runtime>>m)"`                             | Runtime: 90m       |
| `name: "text(Runtime: <<runtimeH>>h <<runtimeM>>m)"`              | Runtime: 1h 30m    |

#### Text Addon Images

You can add an image to accompany the text by specifying the image location using `file`, `url`, `git`, or `repo`.

Use `addon_offset` to control the space between the text and the image.

Use `addon_position` to control which side of the text the image will be located on. 

```yaml
overlays:
  audience_rating:
    overlay:
      name: text(audience_rating)
      horizontal_offset: 225
      horizontal_align: center
      vertical_offset: 15
      vertical_align: top
      font: fonts/Inter-Medium.ttf
      font_size: 63
      font_color: "#FFFFFF"
      back_color: "#00000099"
      back_radius: 30
      back_width: 300
      back_height: 105
      pmm: images/raw/IMDB_Rating
      addon_position: left
      addon_offset: 25
```

### Overlay Groups

Overlay groups are defined by the name given to the `group` attribute. Only one overlay with the highest weight per group will be applied.

This is an example where the Multi-Audio overlay will be applied over the Dual-Audio overlay for every item found by both. 

```yaml
overlays:
  Dual-Audio:
    overlay:
      name: Dual-Audio
      pmm: images/Dual-Audio
      group: audio_language
      weight: 10
      horizontal_offset: 0
      horizontal_align: center
      vertical_offset: 15
      vertical_align: bottom
    plex_all: true
    filters:
      audio_language.count_gt: 1
  Multi-Audio:
    overlay:
      name: Multi-Audio
      pmm: images/Multi-Audio
      group: audio_language
      weight: 20
      horizontal_offset: 0
      horizontal_align: center
      vertical_offset: 15
      vertical_align: bottom
    plex_all: true
    filters:
      audio_language.count_gt: 2
```

### Overlay Queues

Overlay queues are defined by the name given to the `queue` attribute. The overlay with the highest weight is put into the first queue position, then the second highest is placed in the second queue position and so on. 

You can define the queue positions by using the `queues` attribute at the top level of an Overlay File. You can define as many positions as you want. 

```yaml
queues:
  custom_queue_name:
    - horizontal_offset: 300        # This is the first position
      horizontal_align: center
      vertical_offset: 1375
      vertical_align: top
    - horizontal_offset: 300        # This is the second position
      horizontal_align: center
      vertical_offset: 1250
      vertical_align: top
      
overlays:
  IMDb:
    imdb_chart: popular_movies
    overlay:
      name: text(IMDb Popular)
      queue: custom_queue_name
      weight: 20
      font: fonts/Inter-Medium.ttf
      font_size: 65
      font_color: "#FFFFFF"
      back_color: "#00000099"
      back_radius: 30
      back_width: 380
      back_height: 105
  TMDb:
    tmdb_popular: 100
    overlay:
      name: text(TMDb Popular)
      queue: custom_queue_name
      weight: 10
      font: fonts/Inter-Medium.ttf
      font_size: 65
      font_color: "#FFFFFF"
      back_color: "#00000099"
      back_radius: 30
      back_width: 400
      back_height: 105
```

## Suppress Overlays

You can add `suppress_overlays` to an overlay definition and give it a list or comma separated string of overlay names you want suppressed from this item if this overlay is attached to the item.

So in this example if the `4K-HDR` overlay matches an item then the `4K` and `HDR` overlays will also match. The `suppress_overlays` attribute on `4K-HDR` will stop the overlays specified (`4K` and `HDR`) from also being applied. 

```yaml
overlays:
  4K:
    plex_search:
      all:
        resolution: 4K
  HDR:
    plex_search:
      all:
        hdr: true
  4K-HDR:
    suppress_overlays:
      - 4K
      - HDR
    plex_search:
      all:
        resolution: 4K
        hdr: true
```

## Examples

### Example Overlay File

```yaml
overlays:
  4K:
    overlay:
      name: 4K    # This will look for a local overlays/4K.png in your config folder
    plex_search:
      all:
        resolution: 4K
  HDR:
    overlay:
      name: HDR
      pmm: HDR
    plex_search:
      all:
        hdr: true
  Dolby:
    overlay:
      name: Dolby
      url: https://somewebsite.com/dolby_overlay.png
    plex_all: true
    filters:
      has_dolby_vision: true
```

### Example Folder Structure

```
config
├── config.yml
├── Movies.yml
├── TV Shows.yml
├── Overlays.yml
├── overlays
│   ├── 4K.png
│   ├── Dolby.png
│   ├── HDR.png
```
