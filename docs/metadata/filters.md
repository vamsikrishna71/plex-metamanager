# Filters

Filters allow for you to filter every item added to the collection/overlay/playlist from every builder using the `filters` attribute. 

## Using Filters

Filters cannot do anything alone they require the use of at least one [Builder](builders) to function.

You can have multiple filters in each set but an item must match at least one value from **each** filter to not be ignored. The values for each must match what Plex has including special characters in order to match.

```yaml
filters:
  genre: Action
  country: Germany
```

Anything that doesn't have both the Genre `Action` and the Country `Germany` will be ignored.

Multiple Filter Sets can be given as a list. With multiple sets only one of the sets must pass for the item to not be ignored. 

```yaml
filters:
  - genre: Action
    country: Germany
  - genre: Comedy
    country: France
```

Anything that doesn't have either both the Genre `Action` and the Country `Germany` or the Genre `Comedy` and the Country `France` will be ignored.

All filter options are listed below. To display items filtered out add `show_filtered: true` to the definition.

You can use the `plex_all: true` builder to filter from your entire library.

**Filters can be very slow. Try to build or narrow your items using [Plex Search](builders/plex.md#plex-search) or another [Builder](builders) if possible.** 

## String Filters

String filters can be used with either no modifier or with `.not`, `.is`, `.isnot`, `.begins`, `.ends`, or `.regex`.

String filters can take multiple values **only as a list**.

### Modifier

| String Modifier | Description                                                                    |
|:----------------|:-------------------------------------------------------------------------------|
| No Modifier     | Matches every item where the attribute contains the given string               |
| `.not`          | Matches every item where the attribute does not contain the given string       |
| `.is`           | Matches every item where the attribute exactly matches the given string        |
| `.isnot`        | Matches every item where the attribute does not exactly match the given string |
| `.begins`       | Matches every item where the attribute begins with the given string            |
| `.ends`         | Matches every item where the attribute ends with the given string              |
| `.regex`        | Matches every item where the attribute matches the regex given                 |

### Attribute

| String Filter            | Description                              |  Movies  |        Shows        |       Seasons       | Episodes |       Artists       |       Albums        |  Track   |
|:-------------------------|:-----------------------------------------|:--------:|:-------------------:|:-------------------:|:--------:|:-------------------:|:-------------------:|:--------:|
| `title`                  | Uses the title attribute to match        | &#9989;  |       &#9989;       |       &#9989;       | &#9989;  |       &#9989;       |       &#9989;       | &#9989;  |
| `tmdb_title`<sup>2</sup> | Uses the title from TMDb to match        | &#9989;  |       &#9989;       |      &#10060;       | &#10060; |      &#10060;       |      &#10060;       | &#10060; |
| `summary`                | Uses the summary attribute to match      | &#9989;  |       &#9989;       |       &#9989;       | &#9989;  |       &#9989;       |       &#9989;       | &#9989;  |
| `studio`                 | Uses the studio attribute to match       | &#9989;  |       &#9989;       |      &#10060;       | &#10060; |      &#10060;       |      &#10060;       | &#10060; |
| `edition`                | Uses the edition attribute to match      | &#9989;  |      &#10060;       |      &#10060;       | &#10060; |      &#10060;       |      &#10060;       | &#10060; |
| `record_label`           | Uses the record label attribute to match | &#10060; |      &#10060;       |      &#10060;       | &#10060; |      &#10060;       |       &#9989;       | &#10060; |
| `folder`                 | Uses the item's folder to match          | &#10060; |       &#9989;       |      &#10060;       | &#10060; |       &#9989;       |      &#10060;       | &#10060; |
| `filepath`               | Uses the item's filepath to match        | &#9989;  | &#9989;<sup>1</sup> | &#9989;<sup>1</sup> | &#9989;  | &#9989;<sup>1</sup> | &#9989;<sup>1</sup> | &#9989;  |
| `audio_track_title`      | Uses the audio track titles to match     | &#9989;  | &#9989;<sup>1</sup> | &#9989;<sup>1</sup> | &#9989;  | &#9989;<sup>1</sup> | &#9989;<sup>1</sup> | &#9989;  |
| `video_codec`            | Uses the video codec tags to match       | &#9989;  | &#9989;<sup>1</sup> | &#9989;<sup>1</sup> | &#9989;  |      &#10060;       |      &#10060;       | &#10060; |
| `video_profile`          | Uses the video profile tags to match     | &#9989;  | &#9989;<sup>1</sup> | &#9989;<sup>1</sup> | &#9989;  |      &#10060;       |      &#10060;       | &#10060; |
| `audio_codec`            | Uses the audio codec tags to match       | &#9989;  | &#9989;<sup>1</sup> | &#9989;<sup>1</sup> | &#9989;  |      &#10060;       |      &#10060;       | &#10060; |
| `audio_profile`          | Uses the audio profile tags to match     | &#9989;  | &#9989;<sup>1</sup> | &#9989;<sup>1</sup> | &#9989;  |      &#10060;       |      &#10060;       | &#10060; |

<sup>1</sup> Filters using the special `episodes`/`tracks` [filter](#special-filters) with the [default percent](details/definition).

<sup>2</sup> Also filters out missing movies/shows from being added to Radarr/Sonarr. These Values also cannot use the `count` modifiers.

## Tag Filters

Tag filters can be used with either no modifier or with `.not`.

Tag filters can take multiple values as a **list or a comma-separated string**.

### Modifier

| Tag Modifier | Description                                                                               |
|:-------------|:------------------------------------------------------------------------------------------|
| No Modifier  | Matches every item where the attribute matches the given string                           |
| `.not`       | Matches every item where the attribute does not match the given string                    |
| `.regex`     | Matches every item where one value of this attribute matches the regex.                   |
| `.count_lt`  | Matches every item where the attribute count is less than the given number                |
| `.count_lte` | Matches every item where the attribute count is less than the given number                |
| `.count_gt`  | Matches every item where the attribute count is greater than the given number             |
| `.count_gte` | Matches every item where the attribute count is greater than or equal to the given number |

### Attribute

| Tag Filters                  | Description                                                                                                                                     |  Movies  |        Shows        |       Seasons       | Episodes | Artists  |  Albums  |  Track   |
|:-----------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------|:--------:|:-------------------:|:-------------------:|:--------:|:--------:|:--------:|:--------:|
| `actor`                      | Uses the actor tags to match                                                                                                                    | &#9989;  |       &#9989;       |      &#10060;       | &#9989;  | &#10060; | &#10060; | &#10060; |
| `collection`                 | Uses the collection tags to match                                                                                                               | &#9989;  |       &#9989;       |       &#9989;       | &#9989;  | &#9989;  | &#9989;  | &#9989;  |
| `content_rating`             | Uses the content rating tags to match                                                                                                           | &#9989;  |       &#9989;       |      &#10060;       | &#9989;  | &#10060; | &#10060; | &#10060; |
| `network`                    | Uses the network tags to match                                                                                                                  | &#10060; |       &#9989;       |      &#10060;       | &#10060; | &#10060; | &#10060; | &#10060; |
| `country`                    | Uses the country tags to match                                                                                                                  | &#9989;  |      &#10060;       |      &#10060;       | &#10060; | &#9989;  | &#10060; | &#10060; |
| `director`                   | Uses the director tags to match                                                                                                                 | &#9989;  |      &#10060;       |      &#10060;       | &#9989;  | &#10060; | &#10060; | &#10060; |
| `genre`                      | Uses the genre tags to match                                                                                                                    | &#9989;  |       &#9989;       |      &#10060;       | &#10060; | &#9989;  | &#9989;  | &#10060; |
| `label`                      | Uses the label tags to match                                                                                                                    | &#9989;  |       &#9989;       |       &#9989;       | &#9989;  | &#9989;  | &#9989;  | &#9989;  |
| `producer`                   | Uses the actor tags to match                                                                                                                    | &#9989;  |      &#10060;       |      &#10060;       | &#9989;  | &#10060; | &#10060; | &#10060; |
| `year`<sup>3</sup>           | Uses the year tag to match                                                                                                                      | &#9989;  |       &#9989;       |       &#9989;       | &#9989;  | &#10060; | &#9989;  | &#9989;  |
| `writer`                     | Uses the writer tags to match                                                                                                                   | &#9989;  |      &#10060;       |      &#10060;       | &#9989;  | &#10060; | &#10060; | &#10060; |
| `resolution`                 | Uses the resolution tag to match                                                                                                                | &#9989;  | &#9989;<sup>1</sup> | &#9989;<sup>1</sup> | &#9989;  | &#10060; | &#10060; | &#10060; |
| `audio_language`             | Uses the audio language tags to match                                                                                                           | &#9989;  | &#9989;<sup>1</sup> | &#9989;<sup>1</sup> | &#9989;  | &#10060; | &#10060; | &#10060; |
| `subtitle_language`          | Uses the subtitle language tags to match                                                                                                        | &#9989;  | &#9989;<sup>1</sup> | &#9989;<sup>1</sup> | &#9989;  | &#10060; | &#10060; | &#10060; |
| `tmdb_genre`<sup>2</sup>     | Uses the genres from TMDb to match                                                                                                              | &#9989;  |       &#9989;       |      &#10060;       | &#10060; | &#10060; | &#10060; | &#10060; |
| `tmdb_keyword`<sup>2</sup>   | Uses the keywords from TMDb to match                                                                                                            | &#9989;  |       &#9989;       |      &#10060;       | &#10060; | &#10060; | &#10060; | &#10060; |
| `origin_country`<sup>2</sup> | Uses TMDb origin country [ISO 3166-1 alpha-2 codes](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) to match<br>Example: `origin_country: us` | &#10060; |       &#9989;       |      &#10060;       | &#10060; | &#10060; | &#10060; | &#10060; |
| `imdb_keyword`<sup>2</sup>   | Uses the keywords from IMDb to match See [Special](#special-filters) for more attributes                                                        | &#9989;  |       &#9989;       |      &#10060;       | &#10060; | &#10060; | &#10060; | &#10060; |

<sup>1</sup> Filters using the special `episodes` [filter](#special-filters) with the [default percent](details/definition).

<sup>2</sup> Also filters out missing movies/shows from being added to Radarr/Sonarr. These Values also cannot use the `count` modifiers.

<sup>3</sup> You can use `current_year` to have PMM use the current years value. This can be combined with a `-#` at the end to subtract that number of years. i.e. `current-2`

## Boolean Filters

Boolean Filters have no modifiers.

### Attribute

| Boolean Filters    | Description                                                                                              | Movies  |        Shows        |       Seasons       | Episodes | Artists  |  Albums  |  Track   |
|:-------------------|:---------------------------------------------------------------------------------------------------------|:-------:|:-------------------:|:-------------------:|:--------:|:--------:|:--------:|:--------:|
| `has_collection`   | Matches every item that has or does not have a collection                                                | &#9989; |       &#9989;       |       &#9989;       | &#9989;  | &#9989;  | &#9989;  | &#9989;  |
| `has_edition`      | Matches every item that has or does not have an edition                                                  | &#9989; |      &#10060;       |      &#10060;       | &#10060; | &#10060; | &#10060; | &#10060; |
| `has_stinger`      | Matches every item that has a [media stinger](http://www.mediastinger.com/) (After/During Credits Scene) | &#9989; |      &#10060;       |      &#10060;       | &#10060; | &#10060; | &#10060; | &#10060; |
| `has_dolby_vision` | Matches every item that has or does not have a dolby vision                                              | &#9989; | &#9989;<sup>1</sup> | &#9989;<sup>1</sup> | &#9989;  | &#10060; | &#10060; | &#10060; |
| `has_overlay`      | Matches every item that has or does not have an overlay                                                  | &#9989; |       &#9989;       |       &#9989;       | &#9989;  | &#9989;  | &#9989;  | &#10060; |

<sup>1</sup> Filters using the special `episodes` [filter](#special-filters) with the [default percent](details/definition).

## Date Filters

Date filters can be used with either no modifier or with `.not`, `.before`, `.after`, or `.regex`.

Date filters can **NOT** take multiple values.

### Modifier

| Date Modifier | Description                                                           |                                   Format                                   |
|:--------------|:----------------------------------------------------------------------|:--------------------------------------------------------------------------:|
| No Modifier   | Matches every item where the date attribute is in the last X days     |                  **Format:** number of days<br>e.g. `30`                   |
| `.not`        | Matches every item where the date attribute is not in the last X days |                  **Format:** number of days<br>e.g. `30`                   |
| `.before`     | Matches every item where the date attribute is before the given date  | **Format:** MM/DD/YYYY or `today` for the current day<br>e.g. `01/01/2000` |
| `.after`      | Matches every item where the date attribute is after the given date   | **Format:** MM/DD/YYYY or `today` for the current day<br>e.g. `01/01/2000` |
| `.regex`      | Matches every item where the attribute matches the regex given        |                                    N/A                                     |

### Attribute

| Date Filters                              | Description                                                                    |  Movies  |  Shows  | Seasons  | Episodes | Artists  |  Albums  |  Track   |
|:------------------------------------------|:-------------------------------------------------------------------------------|:--------:|:-------:|:--------:|:--------:|:--------:|:--------:|:--------:|
| `release`                                 | Uses the release date attribute (originally available) to match                | &#9989;  | &#9989; | &#10060; | &#9989;  | &#10060; | &#9989;  | &#10060; |
| `added`                                   | Uses the date added attribute to match                                         | &#9989;  | &#9989; | &#9989;  | &#9989;  | &#9989;  | &#9989;  | &#9989;  |
| `last_played`                             | Uses the date last played attribute to match                                   | &#9989;  | &#9989; | &#9989;  | &#9989;  | &#9989;  | &#9989;  | &#9989;  |
| `first_episode_aired`<sup>1</sup>         | Uses the first episode aired date to match                                     | &#10060; | &#9989; | &#10060; | &#10060; | &#10060; | &#10060; | &#10060; |
| `last_episode_aired`<sup>1</sup>          | Uses the last episode aired date to match                                      | &#10060; | &#9989; | &#10060; | &#10060; | &#10060; | &#10060; | &#10060; |
| `last_episode_aired_or_never`<sup>1</sup> | Similar to `last_episode_aired` but also includes those that haven't aired yet | &#10060; | &#9989; | &#10060; | &#10060; | &#10060; | &#10060; | &#10060; |

<sup>1</sup> Also filters out missing movies/shows from being added to Radarr/Sonarr.

## Number Filters

Number filters must use `.gt`, `.gte`, `.lt`, or `.lte` as a modifier.

Number filters can **NOT** take multiple values.

### Modifier

| Number Modifier | Description                                                                                |                      Format                       |
|:----------------|:-------------------------------------------------------------------------------------------|:-------------------------------------------------:|
| No Modifier     | Matches every item where the number attribute is equal to the given number                 | **Format:** number<br>e.g. `30`, `1995`, or `7.5` |
| `.not`          | Matches every item where the number attribute is not equal to the given number             | **Format:** number<br>e.g. `30`, `1995`, or `7.5` |
| `.gt`           | Matches every item where the number attribute is greater than the given number             | **Format:** number<br>e.g. `30`, `1995`, or `7.5` |
| `.gte`          | Matches every item where the number attribute is greater than or equal to the given number | **Format:** number<br>e.g. `30`, `1995`, or `7.5` |
| `.lt`           | Matches every item where the number attribute is less than the given number                | **Format:** number<br>e.g. `30`, `1995`, or `7.5` |
| `.lte`          | Matches every item where the number attribute is less than or equal to the given number    | **Format:** number<br>e.g. `30`, `1995`, or `7.5` |

### Attribute

| Number Filters                      | Description                                                                                                                                                                 | Movies  |        Shows        |       Seasons       | Episodes |       Artists       |       Albums        |  Track   |
|:------------------------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-------:|:-------------------:|:-------------------:|:--------:|:-------------------:|:-------------------:|:--------:|
| `year`<sup>3</sup>                  | Uses the year attribute to match<br>minimum: `1`                                                                                                                            | &#9989; |       &#9989;       |       &#9989;       | &#9989;  |      &#10060;       |       &#9989;       | &#9989;  |
| `tmdb_year`<sup>2</sup><sup>3</sup> | Uses the year on TMDb to match<br>minimum: `1`                                                                                                                              | &#9989; |       &#9989;       |      &#10060;       | &#10060; |      &#10060;       |      &#10060;       | &#10060; |
| `critic_rating`                     | Uses the critic rating attribute to match<br>`0.0` - `10.0`                                                                                                                 | &#9989; |       &#9989;       |      &#10060;       | &#9989;  |      &#10060;       |       &#9989;       | &#10060; |
| `audience_rating`                   | Uses the audience rating attribute to match<br> `0.0` - `10.0`                                                                                                              | &#9989; |       &#9989;       |      &#10060;       | &#9989;  |      &#10060;       |      &#10060;       | &#10060; |
| `user_rating`                       | Uses the user rating attribute to match<br>`0.0` - `10.0`                                                                                                                   | &#9989; |       &#9989;       |       &#9989;       | &#9989;  |       &#9989;       |       &#9989;       | &#9989;  |
| `tmdb_vote_count`<sup>2</sup>       | Uses the tmdb vote count to match<br>minimum: `1`                                                                                                                           | &#9989; |       &#9989;       |      &#10060;       | &#10060; |      &#10060;       |      &#10060;       | &#10060; |
| `plays`                             | Uses the plays attribute to match<br>minimum: `1`                                                                                                                           | &#9989; |       &#9989;       |       &#9989;       | &#9989;  |       &#9989;       |       &#9989;       | &#9989;  |
| `duration`                          | Uses the duration attribute to match using minutes<br>minimum: `0.0`                                                                                                        | &#9989; |       &#9989;       |      &#10060;       | &#9989;  |      &#10060;       |      &#10060;       | &#9989;  |
| `channels`                          | Uses the audio channels attribute to match<br>minimum: `0`                                                                                                                  | &#9989; | &#9989;<sup>1</sup> | &#9989;<sup>1</sup> | &#9989;  |      &#10060;       |      &#10060;       | &#10060; |
| `height`                            | Uses the height attribute to match<br>minimum: `0`                                                                                                                          | &#9989; | &#9989;<sup>1</sup> | &#9989;<sup>1</sup> | &#9989;  |      &#10060;       |      &#10060;       | &#10060; |
| `width`                             | Uses the width attribute to match<br>minimum: `0`                                                                                                                           | &#9989; | &#9989;<sup>1</sup> | &#9989;<sup>1</sup> | &#9989;  |      &#10060;       |      &#10060;       | &#10060; |
| `aspect`                            | Uses the aspect attribute to match<br>minimum: `0.0`                                                                                                                        | &#9989; | &#9989;<sup>1</sup> | &#9989;<sup>1</sup> | &#9989;  |      &#10060;       |      &#10060;       | &#10060; |
| `versions`                          | Uses the number of versions found to match<br>minimum: `0`                                                                                                                  | &#9989; | &#9989;<sup>1</sup> | &#9989;<sup>1</sup> | &#9989;  | &#9989;<sup>1</sup> | &#9989;<sup>1</sup> | &#9989;  |
| `stinger_rating`<sup>4</sup>        | Uses the [media stinger](http://www.mediastinger.com/) rating to match. The media stinger rating is if the after/during credits scene is worth staying for.<br>minimum: `0` | &#9989; |      &#10060;       |      &#10060;       | &#10060; |      &#10060;       |      &#10060;       | &#10060; | 

<sup>1</sup> Filters using the special `episodes` [filter](#special-filters) with the [default percent](details/definition).

<sup>2</sup> Also filters out missing movies/shows from being added to Radarr/Sonarr.

<sup>3</sup> You can use `current_year` to have PMM use the current years value. This can be combined with a `-#` at the end to subtract that number of years. i.e. `current-2`

<sup>4</sup> The actual numbers are pulled from the [PMM-Mediastingers](https://github.com/meisnate12/PMM-Mediastingers) Repo.

## Special Filters

Special Filters each have their own set of rules for how they're used.

### Attribute

| Special Filters                                                        | Description                                                                                                                                                                                                                                                                                              |  Movies  |  Shows   | Seasons  | Episodes | Artists  |  Albums  |  Track   |
|:-----------------------------------------------------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------:|:--------:|:--------:|:--------:|:--------:|:--------:|:--------:|
| `history`                                                              | Uses the release date attribute (originally available) to match dates throughout history<br>`day`: Match the Day and Month to Today's Date<br>`month`: Match the Month to Today's Date<br>`1-30`: Match the Day and Month to Today's Date or `1-30` days before Today's Date                             | &#9989;  | &#9989;  | &#10060; | &#9989;  | &#10060; | &#9989;  | &#10060; |
| `episodes`                                                             | Uses the item's episodes attributes to match <br> Use the `percentage` attribute given a number between 0-100 to determine the percentage of an items episodes that must match the sub-filter.                                                                                                           | &#10060; | &#9989;  | &#9989;  | &#10060; | &#10060; | &#10060; | &#10060; |
| `seasons`                                                              | Uses the item's seasons attributes to match <br> Use the `percentage` attribute given a number between 0-100 to determine the percentage of an items seasons that must match the sub-filter.                                                                                                             | &#10060; | &#9989;  | &#10060; | &#10060; | &#10060; | &#10060; | &#10060; |
| `tracks`                                                               | Uses the item's tracks attributes to match <br> Use the `percentage` attribute given a number between 0-100 to determine the percentage of an items tracks that must match the sub-filter.                                                                                                               | &#10060; | &#10060; | &#10060; | &#10060; | &#9989;  | &#9989;  | &#10060; |
| `albums`                                                               | Uses the item's albums attributes to match <br> Use the `percentage` attribute given a number between 0-100 to determine the percentage of an items albums that must match the sub-filter.                                                                                                               | &#10060; | &#10060; | &#10060; | &#10060; | &#9989;  | &#10060; | &#10060; |
| `original_language`<sup>1</sup><br>`original_language.not`<sup>1</sup> | Uses TMDb original language [ISO 639-1 codes](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) to match<br>Example: `original_language: en, ko`                                                                                                                                                    | &#9989;  | &#9989;  | &#10060; | &#10060; | &#10060; | &#10060; | &#10060; |
| `tmdb_status`<sup>1</sup><br>`tmdb_status.not`<sup>1</sup>             | Uses TMDb Status to match<br>**Values:** `returning`, `planned`, `production`, `ended`, `canceled`, `pilot`                                                                                                                                                                                              | &#10060; | &#9989;  | &#10060; | &#10060; | &#10060; | &#10060; | &#10060; |
| `tmdb_type`<sup>1</sup><br>`tmdb_type.not`<sup>1</sup>                 | Uses TMDb Type to match<br>**Values:** `documentary`, `news`, `production`, `miniseries`, `reality`, `scripted`, `talk_show`, `video`                                                                                                                                                                    | &#10060; | &#9989;  | &#10060; | &#10060; | &#10060; | &#10060; | &#10060; |
| `imdb_keyword`<sup>1</sup><sup>2</sup>                                 | Uses the keywords from IMDb to match<br>`keywords`: list of keywords to match<br>`minimum_votes`: minimum number of votes keywords must have<br>`minimum_relevant`: minimum number of relevant votes keywords must have<br>`minimum_percentage`: minimum percentage of relevant votes keywords must have | &#9989;  | &#9989;  | &#10060; | &#10060; | &#10060; | &#10060; | &#10060; |

<sup>1</sup> Also filters out missing movies/shows from being added to Radarr/Sonarr.

<sup>2</sup> Also is a Tag Filter and can use all of those modifiers.

## Collection Filter Examples

A few examples are listed below:

```yaml
collections:
  1080p Documentaries:
    plex_search:
      all:
        genre: Documentary
    summary: A collection of 1080p Documentaries
    filters:
      resolution: 1080
```
```yaml
collections:
  Daniel Craig only James Bonds:
    imdb_list: https://www.imdb.com/list/ls006405458/
    filters:
      actor: Daniel Craig
```
```yaml
collections:
  French Romance:
    plex_search:
      all:
        genre: Romance
    filters:
      audio_language: Français
```
```yaml
collections:
  Romantic Comedies:
    plex_search:
      all:
        genre: Romance
    filters:
      genre: Comedy
```
```yaml
collections:
  9.0 Movies:
    plex_all: true
    filters:
      rating.gte: 9
```
```yaml
collections:
  Summer 2020 Movies:
    plex_all: true
    filters:
      release.after: 5/1/2020
      release.before: 8/31/2020
```
```yaml
collections:
  Movies Released in the Last 180 Days:
    plex_all: true
    filters:
      release: 180
```
```yaml
collections:
  Good Adam Sandler Romantic Comedies:
    plex_search:
      all:
        genre: Romance
        actor: Adam Sandler
    filters:
      genre: Comedy
      rating.gte: 7
```
```yaml
collections:
  Movies with Commentary:
    plex_all: true
    filters:
      audio_track_title: Commentary
```
