import os, re, time
from arrapi import ArrException
from datetime import datetime
from modules import anidb, anilist, flixpatrol, icheckmovies, imdb, letterboxd, mal, plex, radarr, reciperr, sonarr, tautulli, tmdb, trakt, tvdb, mdblist, util
from modules.util import Failed, FilterFailed, NonExisting, NotScheduled, NotScheduledRange, Deleted
from modules.overlay import Overlay
from plexapi.audio import Artist, Album, Track
from plexapi.exceptions import NotFound
from plexapi.video import Movie, Show, Season, Episode
from requests.exceptions import ConnectionError
from urllib.parse import quote

logger = util.logger

advance_new_agent = ["item_metadata_language", "item_use_original_title"]
advance_show = ["item_episode_sorting", "item_keep_episodes", "item_delete_episodes", "item_season_display", "item_episode_sorting"]
all_builders = anidb.builders + anilist.builders + flixpatrol.builders + icheckmovies.builders + imdb.builders + \
               letterboxd.builders + mal.builders + plex.builders + reciperr.builders + tautulli.builders + \
               tmdb.builders + trakt.builders + tvdb.builders + mdblist.builders + radarr.builders + sonarr.builders
show_only_builders = [
    "tmdb_network", "tmdb_show", "tmdb_show_details", "tvdb_show", "tvdb_show_details", "tmdb_airing_today",
    "tmdb_on_the_air", "builder_level", "item_tmdb_season_titles", "sonarr_all", "sonarr_taglist"
]
movie_only_builders = [
    "letterboxd_list", "letterboxd_list_details", "icheckmovies_list", "icheckmovies_list_details", "stevenlu_popular",
    "tmdb_collection", "tmdb_collection_details", "tmdb_movie", "tmdb_movie_details", "tmdb_now_playing", "item_edition",
    "tvdb_movie", "tvdb_movie_details", "tmdb_upcoming", "trakt_boxoffice", "reciperr_list", "radarr_all", "radarr_taglist"
]
music_only_builders = ["item_album_sorting"]
summary_details = [
    "summary", "tmdb_summary", "tmdb_description", "tmdb_biography", "tvdb_summary",
    "tvdb_description", "trakt_description", "letterboxd_description", "icheckmovies_description"
]
poster_details = ["url_poster", "tmdb_poster", "tmdb_profile", "tvdb_poster", "file_poster"]
background_details = ["url_background", "tmdb_background", "tvdb_background", "file_background"]
boolean_details = [
    "show_filtered", "show_missing", "save_report", "missing_only_released", "only_filter_missing",
    "delete_below_minimum", "asset_folders", "create_asset_folders"
]
scheduled_boolean = ["visible_library", "visible_home", "visible_shared"]
string_details = ["sort_title", "content_rating", "name_mapping"]
ignored_details = [
    "smart_filter", "smart_label", "smart_url", "run_again", "schedule", "sync_mode", "template", "variables", "test", "suppress_overlays",
    "delete_not_scheduled", "tmdb_person", "build_collection", "collection_order", "builder_level", "overlay",
    "validate_builders", "libraries", "sync_to_users", "exclude_users", "collection_name", "playlist_name", "name",
    "blank_collection", "allowed_library_types", "run_definition", "delete_playlist", "ignore_blank_results", "only_run_on_create",
    "delete_collections_named", "tmdb_person_offset", "append_label"
]
details = [
    "ignore_ids", "ignore_imdb_ids", "server_preroll", "changes_webhooks", "collection_filtering", "collection_mode", "limit", "url_theme",
    "file_theme", "minimum_items", "label", "album_sorting", "cache_builders", "tmdb_region", "default_percent"
] + boolean_details + scheduled_boolean + string_details
collectionless_details = ["collection_order", "plex_collectionless", "label", "label_sync_mode", "test", "item_label"] + \
                         poster_details + background_details + summary_details + string_details
item_false_details = ["item_lock_background", "item_lock_poster", "item_lock_title"]
item_bool_details = ["item_tmdb_season_titles", "revert_overlay", "item_assets", "item_refresh"] + item_false_details
item_details = ["non_item_remove_label", "item_label", "item_genre", "item_edition", "item_radarr_tag", "item_sonarr_tag", "item_refresh_delay"] + item_bool_details + list(plex.item_advance_keys.keys())
none_details = ["label.sync", "item_label.sync", "item_genre.sync", "radarr_taglist", "sonarr_taglist", "item_edition"]
radarr_details = [
    "radarr_add_missing", "radarr_add_existing", "radarr_upgrade_existing", "radarr_folder", "radarr_monitor",
    "radarr_search", "radarr_availability", "radarr_quality", "radarr_tag", "item_radarr_tag", "radarr_ignore_cache"
]
sonarr_details = [
    "sonarr_add_missing", "sonarr_add_existing", "sonarr_upgrade_existing", "sonarr_folder", "sonarr_monitor", "sonarr_language",
    "sonarr_series", "sonarr_quality", "sonarr_season", "sonarr_search", "sonarr_cutoff_search", "sonarr_tag", "item_sonarr_tag", "sonarr_ignore_cache"
]
album_details = ["non_item_remove_label", "item_label", "item_album_sorting"]
sub_filters = [
    "filepath", "audio_track_title", "resolution", "audio_language", "subtitle_language", "has_dolby_vision",
    "channels", "height", "width", "aspect", "audio_codec", "audio_profile", "video_codec", "video_profile", "versions"
]
filters_by_type = {
    "movie_show_season_episode_artist_album_track": ["title", "summary", "collection", "has_collection", "added", "last_played", "user_rating", "plays", "filepath", "label", "audio_track_title", "versions"],
    "movie_show_season_episode_album_track": ["year"],
    "movie_show_season_episode_artist_album": ["has_overlay"],
    "movie_show_season_episode": ["resolution", "audio_language", "subtitle_language", "has_dolby_vision", "channels", "height", "width", "aspect", "audio_codec", "audio_profile", "video_codec", "video_profile"],
    "movie_show_episode_album": ["release", "critic_rating", "history"],
    "movie_show_episode_track": ["duration"],
    "movie_show_artist_album": ["genre"],
    "movie_show_episode": ["actor", "content_rating", "audience_rating"],
    "movie_show": ["studio", "original_language", "tmdb_vote_count", "tmdb_year", "tmdb_genre", "tmdb_title", "tmdb_keyword", "imdb_keyword"],
    "movie_episode": ["director", "producer", "writer"],
    "movie_artist": ["country"],
    "show_artist": ["folder"],
    "show_season": ["episodes"],
    "artist_album": ["tracks"],
    "movie": ["edition", "has_edition", "stinger_rating", "has_stinger"],
    "show": ["seasons", "tmdb_status", "tmdb_type", "origin_country", "network", "first_episode_aired", "last_episode_aired", "last_episode_aired_or_never"],
    "artist": ["albums"],
    "album": ["record_label"]
}
filters = {
    "movie": [item for check, sub in filters_by_type.items() for item in sub if "movie" in check],
    "show": [item for check, sub in filters_by_type.items() for item in sub if "show" in check],
    "season": [item for check, sub in filters_by_type.items() for item in sub if "season" in check],
    "episode": [item for check, sub in filters_by_type.items() for item in sub if "episode" in check],
    "artist": [item for check, sub in filters_by_type.items() for item in sub if "artist" in check],
    "album": [item for check, sub in filters_by_type.items() for item in sub if "album" in check],
    "track": [item for check, sub in filters_by_type.items() for item in sub if "track" in check]
}
tmdb_filters = [
    "original_language", "origin_country", "tmdb_vote_count", "tmdb_year", "tmdb_keyword", "tmdb_genre",
    "first_episode_aired", "last_episode_aired", "last_episode_aired_or_never", "tmdb_status", "tmdb_type", "tmdb_title"
]
imdb_filters = ["imdb_keyword"]
string_filters = [
    "title", "summary", "studio", "edition", "record_label", "folder", "filepath", "audio_track_title", "tmdb_title",
    "audio_codec", "audio_profile", "video_codec", "video_profile"
]
string_modifiers = ["", ".not", ".is", ".isnot", ".begins", ".ends", ".regex"]
tag_filters = [
    "actor", "collection", "content_rating", "country", "director", "network", "genre", "label", "producer", "year",
    "origin_country", "writer", "resolution", "audio_language", "subtitle_language", "tmdb_keyword", "tmdb_genre", "imdb_keyword"
]
tag_modifiers = ["", ".not", ".regex", ".count_gt", ".count_gte", ".count_lt", ".count_lte"]
boolean_filters = ["has_collection", "has_edition", "has_overlay", "has_dolby_vision", "has_stinger"]
date_filters = ["release", "added", "last_played", "first_episode_aired", "last_episode_aired", "last_episode_aired_or_never"]
date_modifiers = ["", ".not", ".before", ".after", ".regex"]
number_filters = [
    "year", "tmdb_year", "critic_rating", "audience_rating", "user_rating", "tmdb_vote_count", "plays", "duration",
    "channels", "height", "width", "aspect", "versions", "stinger_rating"]
number_modifiers = ["", ".not", ".gt", ".gte", ".lt", ".lte"]
special_filters = [
    "history", "episodes", "seasons", "albums", "tracks", "original_language", "original_language.not",
    "tmdb_status", "tmdb_status.not", "tmdb_type", "tmdb_type.not"
]
all_filters = boolean_filters + special_filters + \
              [f"{f}{m}" for f in string_filters for m in string_modifiers] + \
              [f"{f}{m}" for f in tag_filters for m in tag_modifiers] + \
              [f"{f}{m}" for f in date_filters for m in date_modifiers] + \
              [f"{f}{m}" for f in number_filters for m in number_modifiers]
date_attributes = plex.date_attributes + ["first_episode_aired", "last_episode_aired", "last_episode_aired_or_never"]
year_attributes = plex.year_attributes + ["tmdb_year"]
number_attributes = plex.number_attributes + ["channels", "height", "width", "tmdb_vote_count"]
tag_attributes = plex.tag_attributes
string_attributes = plex.string_attributes + string_filters
float_attributes = plex.float_attributes + ["aspect"]
boolean_attributes = plex.boolean_attributes + boolean_filters
smart_invalid = ["collection_order", "builder_level"]
smart_only = ["collection_filtering"]
smart_url_invalid = ["filters", "run_again", "sync_mode", "show_filtered", "show_missing", "save_report", "smart_label"] + radarr_details + sonarr_details
custom_sort_builders = [
    "plex_search", "plex_watchlist", "plex_pilots", "tmdb_list", "tmdb_popular", "tmdb_now_playing", "tmdb_top_rated",
    "tmdb_trending_daily", "tmdb_trending_weekly", "tmdb_discover", "reciperr_list", "trakt_chart", "trakt_userlist",
    "tvdb_list", "imdb_chart", "imdb_list", "imdb_watchlist", "stevenlu_popular", "anidb_popular", "tmdb_upcoming", "tmdb_airing_today",
    "tmdb_on_the_air", "trakt_list", "trakt_watchlist", "trakt_collection", "trakt_trending", "trakt_popular", "trakt_boxoffice",
    "trakt_collected_daily", "trakt_collected_weekly", "trakt_collected_monthly", "trakt_collected_yearly", "trakt_collected_all",
    "flixpatrol_url", "flixpatrol_demographics", "flixpatrol_popular", "flixpatrol_top", "trakt_recommendations",
    "trakt_recommended_personal", "trakt_recommended_daily", "trakt_recommended_weekly", "trakt_recommended_monthly", "trakt_recommended_yearly", "trakt_recommended_all",
    "trakt_watched_daily", "trakt_watched_weekly", "trakt_watched_monthly", "trakt_watched_yearly", "trakt_watched_all",
    "tautulli_popular", "tautulli_watched", "mdblist_list", "letterboxd_list", "icheckmovies_list",
    "anilist_top_rated", "anilist_popular", "anilist_trending", "anilist_search", "anilist_userlist",
    "mal_all", "mal_airing", "mal_upcoming", "mal_tv", "mal_movie", "mal_ova", "mal_special", "mal_search",
    "mal_popular", "mal_favorite", "mal_suggested", "mal_userlist", "mal_season", "mal_genre", "mal_studio"
]
episode_parts_only = ["plex_pilots"]
overlay_only = ["overlay", "suppress_overlays"]
overlay_attributes = [
     "filters", "limit", "show_missing", "save_report", "missing_only_released", "minimum_items", "cache_builders", "tmdb_region", "default_percent"
] + all_builders + overlay_only
parts_collection_valid = [
     "filters", "plex_all", "plex_search", "trakt_list", "trakt_list_details", "collection_filtering", "collection_mode", "label", "visible_library", "limit",
     "visible_home", "visible_shared", "show_missing", "save_report", "missing_only_released", "server_preroll", "changes_webhooks",
     "item_lock_background", "item_lock_poster", "item_lock_title", "item_refresh", "item_refresh_delay", "imdb_list", "cache_builders",
     "url_theme", "file_theme", "item_label", "default_percent"
] + episode_parts_only + summary_details + poster_details + background_details + string_details
playlist_attributes = [
    "filters", "name_mapping", "show_filtered", "show_missing", "save_report", "allowed_library_types", "run_definition",
    "missing_only_released", "only_filter_missing", "delete_below_minimum", "ignore_ids", "ignore_imdb_ids",
    "server_preroll", "changes_webhooks", "minimum_items", "cache_builders", "default_percent"
] + custom_sort_builders + summary_details + poster_details + radarr_details + sonarr_details
music_attributes = [
   "non_item_remove_label", "item_label", "collection_filtering", "item_lock_background", "item_lock_poster", "item_lock_title",
   "item_assets", "item_refresh", "item_refresh_delay", "plex_search", "plex_all", "filters"
] + details + summary_details + poster_details + background_details

class CollectionBuilder:
    def __init__(self, config, metadata, name, data, library=None, overlay=None, extra=None):
        self.config = config
        self.metadata = metadata
        self.mapping_name = name
        self.data = data
        self.library = library
        self.libraries = []
        self.playlist = library is None
        self.overlay = overlay
        methods = {m.lower(): m for m in self.data}
        if self.playlist:
            self.type = "playlist"
        elif self.overlay:
            self.type = "overlay"
        else:
            self.type = "collection"
        self.Type = self.type.capitalize()

        logger.separator(f"{self.mapping_name} {self.Type}{f' in {self.library.name}' if self.library else ''}")
        logger.info("")
        if extra:
            logger.info(extra)
            logger.info("")

        if f"{self.type}_name" in methods:
            logger.warning(f"Config Warning: Running {self.type}_name as name")
            self.data["name"] = self.data[methods[f"{self.type}_name"]]
            methods["name"] = "name"

        if "template" in methods:
            logger.separator(f"Building Definition From Templates", space=False, border=False)
            logger.debug("")
            named_templates = []
            for original_variables in util.get_list(self.data[methods["template"]], split=False):
                if not isinstance(original_variables, dict):
                    raise Failed(f"{self.Type} Error: template attribute is not a dictionary")
                elif "name" not in original_variables:
                    raise Failed(f"{self.Type} Error: template sub-attribute name is required")
                elif not original_variables["name"]:
                    raise Failed(f"{self.Type} Error: template sub-attribute name cannot be blank")
                named_templates.append(original_variables["name"])
            logger.debug(f"Templates Called: {', '.join(named_templates)}")
            logger.debug("")
            new_variables = {}
            if "variables" in methods:
                logger.debug("")
                logger.debug("Validating Method: variables")
                if not isinstance(self.data[methods["variables"]], dict):
                    raise Failed(f"{self.Type} Error: variables must be a dictionary (key: value pairs)")
                logger.trace(self.data[methods["variables"]])
                new_variables = self.data[methods["variables"]]
            name = self.data[methods["name"]] if "name" in methods else None
            new_attributes = self.metadata.apply_template(name, self.mapping_name, self.data, self.data[methods["template"]], new_variables)
            for attr in new_attributes:
                if attr.lower() not in methods:
                    self.data[attr] = new_attributes[attr]
                    methods[attr.lower()] = attr

        logger.separator(f"Validating {self.mapping_name} Attributes", space=False, border=False)

        if "name" in methods:
            logger.debug("")
            logger.debug("Validating Method: name")
            if not self.data[methods["name"]]:
                raise Failed(f"{self.Type} Error: name attribute is blank")
            logger.debug(f"Value: {self.data[methods['name']]}")
            self.name = str(self.data[methods["name"]])
        else:
            self.name = self.mapping_name

        if self.playlist:
            if "libraries" not in methods:
                raise Failed("Playlist Error: libraries attribute is required")
            logger.debug("")
            logger.debug("Validating Method: libraries")
            if not self.data[methods["libraries"]]:
                raise Failed(f"{self.Type} Error: libraries attribute is blank")
            logger.debug(f"Value: {self.data[methods['libraries']]}")
            for pl_library in util.get_list(self.data[methods["libraries"]]):
                if str(pl_library) not in config.library_map:
                    raise Failed(f"Playlist Error: Library: {pl_library} not defined")
                self.libraries.append(config.library_map[pl_library])
            self.library = self.libraries[0]

        try:
            self.obj = self.library.get_playlist(self.name) if self.playlist else self.library.get_collection(self.name, force_search=True)
        except Failed:
            self.obj = None

        self.only_run_on_create = False
        if "only_run_on_create" in methods and not self.playlist:
            logger.debug("")
            logger.debug("Validating Method: only_run_on_create")
            logger.debug(f"Value: {data[methods['only_run_on_create']]}")
            self.only_run_on_create = util.parse(self.Type, "only_run_on_create", self.data, datatype="bool", methods=methods, default=False)
        if self.obj and self.only_run_on_create:
            raise NotScheduled("Skipped because only_run_on_create is True and the collection already exists")

        if "allowed_library_types" in methods and "run_definition" not in methods:
            logger.warning(f"{self.Type} Warning: allowed_library_types will run as run_definition")
            methods["run_definition"] = methods["allowed_library_types"]

        if "run_definition" in methods:
            logger.debug("")
            logger.debug("Validating Method: run_definition")
            if self.data[methods["run_definition"]] is None:
                raise NotScheduled("Skipped because run_definition has no value")
            logger.debug(f"Value: {self.data[methods['run_definition']]}")
            valid_options = ["true", "false"] + plex.library_types
            for library_type in util.get_list(self.data[methods["run_definition"]], lower=True):
                if library_type not in valid_options:
                    raise Failed(f"{self.Type} Error: {library_type} is invalid. Options: true, false, {', '.join(plex.library_types)}")
                elif library_type == "false":
                    raise NotScheduled(f"Skipped because run_definition is false")
                elif library_type != "true" and self.library and library_type != self.library.Plex.type:
                    raise NotScheduled(f"Skipped because run_definition library_type: {library_type} doesn't match")

        if self.playlist:               self.builder_level = "item"
        elif self.library.is_show:      self.builder_level = "show"
        elif self.library.is_music:     self.builder_level = "artist"
        else:                           self.builder_level = "movie"
        level = None
        for level_attr in ["builder_level", "collection_level", "overlay_level"]:
            if level_attr in methods:
                level = self.data[methods[level_attr]]
                if level_attr != "builder_level":
                    logger.warning(f"Collection Warning: {level_attr} attribute will run as builder_level")
                break

        if level and not self.playlist and not self.library.is_movie:
            logger.debug("")
            logger.debug("Validating Method: builder_level")
            if level is None:
                logger.error(f"{self.Type} Error: builder_level attribute is blank")
            else:
                logger.debug(f"Value: {level}")
                level = level.lower()
                if (self.library.is_show and level in plex.builder_level_show_options) or (self.library.is_music and level in plex.builder_level_music_options):
                    self.builder_level = level
                elif (self.library.is_show and level != "show") or (self.library.is_music and level != "artist"):
                    if self.library.is_show:
                        options = "\n\tseason (Collection at the Season Level)\n\tepisode (Collection at the Episode Level)"
                    else:
                        options = "\n\talbum (Collection at the Album Level)\n\ttrack (Collection at the Track Level)"
                    raise Failed(f"{self.Type} Error: {self.data[methods['builder_level']]} builder_level invalid{options}")
        self.parts_collection = self.builder_level in plex.builder_level_options

        if self.overlay:
            if "overlay" in methods:
                overlay_data = data[methods["overlay"]]
            else:
                overlay_data = str(self.mapping_name)
                logger.warning(f"{self.Type} Warning: No overlay attribute using mapping name {self.mapping_name} as the overlay name")
            suppress = []
            if "suppress_overlays" in methods:
                logger.debug("")
                logger.debug("Validating Method: suppress_overlays")
                logger.debug(f"Value: {data[methods['suppress_overlays']]}")
                if data[methods["suppress_overlays"]]:
                    suppress = util.get_list(data[methods["suppress_overlays"]])
                else:
                    logger.error(f"Overlay Error: suppress_overlays attribute is blank")
            self.overlay = Overlay(config, library, metadata, str(self.mapping_name), overlay_data, suppress, self.builder_level)

        self.sync_to_users = None
        self.exclude_users = None
        self.valid_users = []
        if self.playlist:
            if "sync_to_users" in methods or "sync_to_user" in methods:
                s_attr = f"sync_to_user{'s' if 'sync_to_users' in methods else ''}"
                logger.debug("")
                logger.debug(f"Validating Method: {s_attr}")
                logger.debug(f"Value: {self.data[methods[s_attr]]}")
                self.sync_to_users = self.data[methods[s_attr]]
            else:
                self.sync_to_users = config.general["playlist_sync_to_users"]
                logger.warning(f"Playlist Warning: sync_to_users attribute not found defaulting to playlist_sync_to_users: {self.sync_to_users}")

            if "exclude_users" in methods or "exclude_user" in methods:
                s_attr = f"exclude_user{'s' if 'exclude_users' in methods else ''}"
                logger.debug("")
                logger.debug(f"Validating Method: {s_attr}")
                logger.debug(f"Value: {self.data[methods[s_attr]]}")
                self.exclude_users = self.data[methods[s_attr]]
            elif config.general["playlist_exclude_users"]:
                self.exclude_users = config.general["playlist_exclude_users"]
                logger.warning(f"Playlist Warning: exclude_users attribute not found defaulting to playlist_exclude_users: {self.exclude_users}")

            plex_users = self.library.users

            self.exclude_users = util.get_list(self.exclude_users) if self.exclude_users else []
            for user in self.exclude_users:
                if user not in plex_users:
                    raise Failed(f"Playlist Error: User: {user} not found in plex\nOptions: {plex_users}")

            if self.sync_to_users:
                if str(self.sync_to_users) == "all":
                    self.valid_users = [p for p in plex_users if p not in self.exclude_users]
                else:
                    for user in util.get_list(self.sync_to_users):
                        if user not in plex_users:
                            raise Failed(f"Playlist Error: User: {user} not found in plex\nOptions: {plex_users}")
                        if user not in self.exclude_users:
                            self.valid_users.append(user)

            if "delete_playlist" in methods:
                logger.debug("")
                logger.debug("Validating Method: delete_playlist")
                logger.debug(f"Value: {data[methods['delete_playlist']]}")
                if util.parse(self.Type, "delete_playlist", self.data, datatype="bool", methods=methods, default=False):
                    try:
                        self.obj = self.library.get_playlist(self.name)
                    except Failed as e:
                        logger.error(e)
                    raise Deleted(self.delete())
        else:
            self.libraries.append(self.library)

        self.asset_directory = metadata.asset_directory if metadata.asset_directory else self.library.asset_directory

        self.language = self.library.Plex.language
        self.details = {
            "show_filtered": self.library.show_filtered,
            "show_options": self.library.show_options,
            "show_missing": self.library.show_missing,
            "save_report": self.library.save_report,
            "missing_only_released": self.library.missing_only_released,
            "only_filter_missing": False if self.overlay else self.library.only_filter_missing,
            "asset_folders": self.library.asset_folders,
            "create_asset_folders": self.library.create_asset_folders,
            "delete_below_minimum": self.library.delete_below_minimum,
            "delete_not_scheduled": self.library.delete_not_scheduled,
            "changes_webhooks": self.library.changes_webhooks,
            "cache_builders": 0
        }
        if self.library.mass_collection_mode:
            self.details["collection_mode"] = self.library.mass_collection_mode
        self.item_details = {}
        self.radarr_details = {}
        self.sonarr_details = {}
        self.missing_movies = []
        self.missing_shows = []
        self.missing_parts = []
        self.added_to_radarr = []
        self.added_to_sonarr = []
        self.builders = []
        self.filters = []
        self.has_tmdb_filters = False
        self.has_imdb_filters = False
        self.found_items = []
        self.filtered_items = []
        self.filtered_keys = {}
        self.run_again_movies = []
        self.run_again_shows = []
        self.notification_additions = []
        self.notification_removals = []
        self.items = []
        self.remove_item_map = {}
        self.posters = {}
        self.backgrounds = {}
        self.summaries = {}
        self.schedule = ""
        self.limit = 0
        self.beginning_count = 0
        self.default_percent = 50
        self.minimum = self.library.minimum_items
        self.tmdb_region = None
        self.ignore_ids = [i for i in self.library.ignore_ids]
        self.ignore_imdb_ids = [i for i in self.library.ignore_imdb_ids]
        self.server_preroll = None
        self.current_time = datetime.now()
        self.current_year = self.current_time.year
        self.url_theme = None
        self.file_theme = None
        self.sync_to_trakt_list = None
        self.sync_missing_to_trakt_list = False
        self.collection_poster = None
        self.collection_background = None
        self.exists = False
        self.non_existing = False
        self.created = False
        self.deleted = False

        if self.playlist:
            server_check = None
            for pl_library in self.libraries:
                if server_check:
                    if pl_library.PlexServer.machineIdentifier != server_check:
                        raise Failed("Playlist Error: All defined libraries must be on the same server")
                else:
                    server_check = pl_library.PlexServer.machineIdentifier

        self.ignore_blank_results = False
        if "ignore_blank_results" in methods and not self.playlist:
            logger.debug("")
            logger.debug("Validating Method: ignore_blank_results")
            logger.debug(f"Value: {data[methods['ignore_blank_results']]}")
            self.ignore_blank_results = util.parse(self.Type, "ignore_blank_results", self.data, datatype="bool", methods=methods, default=False)

        self.smart_filter_details = ""
        self.smart_label_url = None
        self.smart_label = {"sort_by": "random", "all": {"label": [self.name]}}
        self.smart_label_collection = False
        if "smart_label" in methods and not self.playlist and not self.overlay and not self.library.is_music:
            logger.debug("")
            logger.debug("Validating Method: smart_label")
            self.smart_label_collection = True
            if not self.data[methods["smart_label"]]:
                logger.warning(f"{self.Type} Error: smart_label attribute is blank defaulting to random")
            else:
                logger.debug(f"Value: {self.data[methods['smart_label']]}")
                if isinstance(self.data[methods["smart_label"]], dict):
                    _data, replaced = util.replace_label(self.name, self.data[methods["smart_label"]])
                    if not replaced:
                        raise Failed("Config Error: <<smart_label>> not found in the smart_label attribute data")
                    self.smart_label = _data
                elif (self.library.is_movie and str(self.data[methods["smart_label"]]).lower() in plex.movie_sorts) \
                        or (self.library.is_show and str(self.data[methods["smart_label"]]).lower() in plex.show_sorts):
                    self.smart_label["sort_by"] = str(self.data[methods["smart_label"]]).lower()
                else:
                    logger.warning(f"{self.Type} Error: smart_label attribute: {self.data[methods['smart_label']]} is invalid defaulting to random")
        if self.smart_label_collection and self.library.smart_label_check(self.name):
            try:
                _, self.smart_filter_details, self.smart_label_url = self.build_filter("smart_label", self.smart_label, default_sort="random")
            except FilterFailed as e:
                if self.ignore_blank_results:
                    raise
                else:
                    raise Failed(str(e))

        if "delete_not_scheduled" in methods and not self.overlay:
            logger.debug("")
            logger.debug("Validating Method: delete_not_scheduled")
            logger.debug(f"Value: {data[methods['delete_not_scheduled']]}")
            self.details["delete_not_scheduled"] = util.parse(self.Type, "delete_not_scheduled", self.data, datatype="bool", methods=methods, default=False)

        if "delete_collections_named" in methods and not self.overlay and not self.playlist:
            logger.debug("")
            logger.debug("Validating Method: delete_collections_named")
            logger.debug(f"Value: {data[methods['delete_collections_named']]}")
            for del_col in util.parse(self.Type, "delete_collections_named", self.data, datatype="strlist", methods=methods):
                try:
                    del_obj = self.library.get_collection(del_col, force_search=True)
                    self.library.delete(del_obj)
                    logger.info(f"Collection: {del_obj.title} deleted")
                except Failed as e:
                    if str(e).startswith("Plex Error: Failed to delete"):
                        logger.error(e)

        if "schedule" in methods and not self.config.requested_collections and not self.overlay:
            logger.debug("")
            logger.debug("Validating Method: schedule")
            if not self.data[methods["schedule"]]:
                raise Failed(f"{self.Type} Error: schedule attribute is blank")
            else:
                logger.debug(f"Value: {self.data[methods['schedule']]}")
                err = None
                try:
                    util.schedule_check("schedule", self.data[methods["schedule"]], self.current_time, self.config.run_hour)
                except NonExisting as e:
                    self.non_existing = str(e)
                except NotScheduledRange as e:
                    err = e
                except NotScheduled as e:
                    if not self.config.ignore_schedules:
                        err = e
                if err:
                    suffix = ""
                    if self.details["delete_not_scheduled"]:
                        try:
                            self.obj = self.library.get_playlist(self.name) if self.playlist else self.library.get_collection(self.name, force_search=True)
                            logger.info(self.delete())
                            self.deleted = True
                            suffix = f" and was deleted"
                        except Failed:
                            suffix = f" and could not be found to delete"
                    raise NotScheduled(f"{err}\n\n{self.Type} {self.name} not scheduled to run{suffix}")

        self.collectionless = "plex_collectionless" in methods and not self.playlist and not self.overlay

        self.validate_builders = True
        if "validate_builders" in methods and not self.overlay:
            logger.debug("")
            logger.debug("Validating Method: validate_builders")
            logger.debug(f"Value: {data[methods['validate_builders']]}")
            self.validate_builders = util.parse(self.Type, "validate_builders", self.data, datatype="bool", methods=methods, default=True)

        self.run_again = False
        if "run_again" in methods and not self.overlay:
            logger.debug("")
            logger.debug("Validating Method: run_again")
            logger.debug(f"Value: {data[methods['run_again']]}")
            self.run_again = util.parse(self.Type, "run_again", self.data, datatype="bool", methods=methods, default=False)

        self.build_collection = False if self.overlay else True
        if "build_collection" in methods and not self.playlist and not self.overlay:
            logger.debug("")
            logger.debug("Validating Method: build_collection")
            logger.debug(f"Value: {data[methods['build_collection']]}")
            self.build_collection = util.parse(self.Type, "build_collection", self.data, datatype="bool", methods=methods, default=True)

        self.blank_collection = False
        if "blank_collection" in methods and not self.playlist and not self.overlay:
            logger.debug("")
            logger.debug("Validating Method: blank_collection")
            logger.debug(f"Value: {data[methods['blank_collection']]}")
            self.blank_collection = util.parse(self.Type, "blank_collection", self.data, datatype="bool", methods=methods, default=False)

        self.sync = self.library.sync_mode == "sync"
        if "sync_mode" in methods and not self.overlay:
            logger.debug("")
            logger.debug("Validating Method: sync_mode")
            if not self.data[methods["sync_mode"]]:
                logger.warning(f"Collection Warning: sync_mode attribute is blank using general: {self.library.sync_mode}")
            else:
                logger.debug(f"Value: {self.data[methods['sync_mode']]}")
                if self.data[methods["sync_mode"]].lower() not in ["append", "sync"]:
                    logger.warning(f"Collection Warning: {self.data[methods['sync_mode']]} sync_mode invalid using general: {self.library.sync_mode}")
                else:
                    self.sync = self.data[methods["sync_mode"]].lower() == "sync"

        self.tmdb_person_offset = 0
        if "tmdb_person_offset" in methods:
            logger.debug("")
            logger.debug("Validating Method: tmdb_person_offset")
            logger.debug(f"Value: {data[methods['tmdb_person_offset']]}")
            self.tmdb_person_offset = util.parse(self.Type, "tmdb_person_offset", self.data, datatype="int", methods=methods, default=0, minimum=0)

        if "tmdb_person" in methods:
            logger.debug("")
            logger.debug("Validating Method: tmdb_person")
            if not self.data[methods["tmdb_person"]]:
                raise Failed(f"{self.Type} Error: tmdb_person attribute is blank")
            else:
                logger.debug(f"Value: {self.data[methods['tmdb_person']]}")
                valid_names = []
                for tmdb_person in util.get_list(self.data[methods["tmdb_person"]]):
                    try:
                        person = self.config.TMDb.get_person(util.regex_first_int(tmdb_person, "TMDb Person ID"))
                        valid_names.append(person.name)
                        if person.biography:
                            self.summaries["tmdb_person"] = person.biography
                        if person.profile_url:
                            self.posters["tmdb_person"] = person.profile_url
                    except Failed as e:
                        if str(e).startswith("TMDb Error"):
                            logger.error(e)
                        else:
                            try:
                                results = self.config.TMDb.search_people(tmdb_person)
                                if results:
                                    result_index = len(results) - 1 if self.tmdb_person_offset >= len(results) else self.tmdb_person_offset
                                    valid_names.append(tmdb_person)
                                    if results[result_index].biography:
                                        self.summaries["tmdb_person"] = results[result_index].biography
                                    if results[result_index].profile_url:
                                        self.posters["tmdb_person"] = results[result_index].profile_url
                            except Failed as ee:
                                logger.error(ee)
                if len(valid_names) > 0:
                    self.details["tmdb_person"] = valid_names
                else:
                    raise Failed(f"{self.Type} Error: No valid TMDb Person IDs in {self.data[methods['tmdb_person']]}")

        self.smart_url = None
        self.smart_type_key = None
        if "smart_url" in methods and not self.playlist and not self.overlay:
            logger.debug("")
            logger.debug("Validating Method: smart_url")
            if not self.data[methods["smart_url"]]:
                raise Failed(f"{self.Type} Error: smart_url attribute is blank")
            else:
                logger.debug(f"Value: {self.data[methods['smart_url']]}")
                try:
                    self.smart_url, self.smart_type_key = self.library.get_smart_filter_from_uri(self.data[methods["smart_url"]])
                except ValueError:
                    raise Failed(f"{self.Type} Error: smart_url is incorrectly formatted")

        if "smart_filter" in methods and not self.playlist and not self.overlay:
            try:
                self.smart_type_key, self.smart_filter_details, self.smart_url = self.build_filter("smart_filter", self.data[methods["smart_filter"]], display=True, default_sort="random")
            except FilterFailed as e:
                if self.ignore_blank_results:
                    raise
                else:
                    raise Failed(str(e))

        if self.collectionless:
            for x in ["smart_label", "smart_filter", "smart_url"]:
                if x in methods:
                    self.collectionless = False
                    logger.info("")
                    logger.warning(f"{self.Type} Error: {x} is not compatible with plex_collectionless removing plex_collectionless")

        if self.run_again and self.smart_url:
            self.run_again = False
            logger.info("")
            logger.warning(f"{self.Type} Error: smart_filter is not compatible with run_again removing run_again")

        if self.smart_url and self.smart_label_collection:
            raise Failed(f"{self.Type} Error: smart_filter is not compatible with smart_label")

        if self.parts_collection and "smart_url" in methods:
            raise Failed(f"{self.Type} Error: smart_url is not compatible with builder_level: {self.builder_level}")

        self.smart = self.smart_url or self.smart_label_collection

        test_sort = None
        if "collection_order" in methods and not self.playlist and self.build_collection:
            if self.data[methods["collection_order"]] is None:
                raise Failed(f"{self.Type} Warning: collection_order attribute is blank")
            else:
                test_sort = self.data[methods["collection_order"]]
        elif "collection_order" not in methods and not self.playlist and not self.blank_collection and self.build_collection and self.library.default_collection_order and not self.smart:
            test_sort = self.library.default_collection_order
            logger.warning("")
            logger.warning(f"{self.Type} Warning: collection_order not found using library default_collection_order: {test_sort}")
        self.custom_sort = "custom" if self.playlist else None
        if test_sort:
            if self.smart:
                raise Failed(f"{self.Type} Error: collection_order does not work with Smart Collections")
            logger.debug("")
            logger.debug("Validating Method: collection_order")
            logger.debug(f"Value: {test_sort}")
            if test_sort in plex.collection_order_options + ["custom.asc", "custom.desc"]:
                self.details["collection_order"] = test_sort.split(".")[0]
                if test_sort.startswith("custom") and self.build_collection:
                    self.custom_sort = test_sort
            else:
                sort_type = self.builder_level
                if sort_type == "item":
                    if self.library.is_show:
                        sort_type = "show"
                    elif self.library.is_music:
                        sort_type = "artist"
                    else:
                        sort_type = "movie"
                _, _, sorts = plex.sort_types[sort_type]
                if not isinstance(test_sort, list):
                    test_sort = [test_sort]
                self.custom_sort = []
                for ts in test_sort:
                    if ts not in sorts:
                        raise Failed(f"{self.Type} Error: collection_order: {ts} is invalid. Options: {', '.join(sorts)}")
                    self.custom_sort.append(ts)
            if test_sort not in plex.collection_order_options + ["custom.asc", "custom.desc"] and not self.custom_sort:
                raise Failed(f"{self.Type} Error: {test_sort} collection_order invalid\n\trelease (Order Collection by release dates)\n\talpha (Order Collection Alphabetically)\n\tcustom.asc/custom.desc (Custom Order Collection)\n\tOther sorting options can be found at https://github.com/meisnate12/Plex-Meta-Manager/wiki/Smart-Builders#sort-options")

        if self.smart:
            self.custom_sort = None

        for method_key, method_data in self.data.items():
            if method_key.lower() in ignored_details:
                continue
            logger.debug("")
            method_name, method_mod, method_final = self.library.split(method_key)
            if method_name in ignored_details:
                continue
            logger.debug(f"Validating Method: {method_key}")
            logger.debug(f"Value: {method_data}")
            try:
                if method_data is None and method_name in all_builders + plex.searches:
                    raise Failed(f"{self.Type} Error: {method_final} attribute is blank")
                elif method_data is None and method_final not in none_details:
                    logger.warning(f"Collection Warning: {method_final} attribute is blank")
                elif self.playlist and method_name not in playlist_attributes:
                    raise Failed(f"{self.Type} Error: {method_final} attribute not allowed when using playlists")
                elif not self.config.Trakt and "trakt" in method_name:
                    raise Failed(f"{self.Type} Error: {method_final} requires Trakt to be configured")
                elif not self.library.Radarr and "radarr" in method_name:
                    logger.error(f"{self.Type} Error: {method_final} requires Radarr to be configured")
                elif not self.library.Sonarr and "sonarr" in method_name:
                    logger.error(f"{self.Type} Error: {method_final} requires Sonarr to be configured")
                elif not self.library.Tautulli and "tautulli" in method_name:
                    raise Failed(f"{self.Type} Error: {method_final} requires Tautulli to be configured")
                elif not self.config.MyAnimeList and "mal" in method_name:
                    raise Failed(f"{self.Type} Error: {method_final} requires MyAnimeList to be configured")
                elif self.library.is_movie and method_name in show_only_builders:
                    raise Failed(f"{self.Type} Error: {method_final} attribute only allowed for show libraries")
                elif self.library.is_show and method_name in movie_only_builders:
                    raise Failed(f"{self.Type} Error: {method_final} attribute only allowed for movie libraries")
                elif self.library.is_show and method_name in plex.movie_only_searches:
                    raise Failed(f"{self.Type} Error: {method_final} plex search only allowed for movie libraries")
                elif self.library.is_movie and method_name in plex.show_only_searches:
                    raise Failed(f"{self.Type} Error: {method_final} plex search only allowed for show libraries")
                elif self.library.is_music and method_name not in music_attributes:
                    raise Failed(f"{self.Type} Error: {method_final} attribute not allowed for music libraries")
                elif self.library.is_music and method_name in album_details and self.builder_level != "album":
                    raise Failed(f"{self.Type} Error: {method_final} attribute only allowed for album collections")
                elif not self.library.is_music and method_name in music_only_builders:
                    raise Failed(f"{self.Type} Error: {method_final} attribute only allowed for music libraries")
                elif not self.playlist and self.builder_level != "episode" and method_name in episode_parts_only:
                    raise Failed(f"{self.Type} Error: {method_final} attribute only allowed with Collection Level: episode")
                elif self.parts_collection and method_name not in parts_collection_valid:
                    raise Failed(f"{self.Type} Error: {method_final} attribute not allowed with Collection Level: {self.builder_level.capitalize()}")
                elif self.smart and method_name in smart_invalid:
                    raise Failed(f"{self.Type} Error: {method_final} attribute only allowed with normal collections")
                elif not self.smart and method_name in smart_only:
                    raise Failed(f"{self.Type} Error: {method_final} attribute only allowed with smart collections")
                elif self.collectionless and method_name not in collectionless_details:
                    raise Failed(f"{self.Type} Error: {method_final} attribute not allowed for Collectionless collection")
                elif self.smart_url and method_name in all_builders + smart_url_invalid:
                    raise Failed(f"{self.Type} Error: {method_final} builder not allowed when using smart_filter")
                elif not self.overlay and method_name in overlay_only:
                    raise Failed(f"{self.Type} Error: {method_final} attribute only allowed in an overlay file")
                elif self.overlay and method_name not in overlay_attributes:
                    raise Failed(f"{self.Type} Error: {method_final} attribute not allowed in an overlay file")
                elif method_name in summary_details:
                    self._summary(method_name, method_data)
                elif method_name in poster_details:
                    self._poster(method_name, method_data)
                elif method_name in background_details:
                    self._background(method_name, method_data)
                elif method_name in details:
                    self._details(method_name, method_data, method_final, methods)
                elif method_name in item_details:
                    self._item_details(method_name, method_data, method_mod, method_final, methods)
                elif method_name in radarr_details or method_name in radarr.builders:
                    self._radarr(method_name, method_data)
                elif method_name in sonarr_details or method_name in sonarr.builders:
                    self._sonarr(method_name, method_data)
                elif method_name in anidb.builders:
                    self._anidb(method_name, method_data)
                elif method_name in anilist.builders:
                    self._anilist(method_name, method_data)
                elif method_name in flixpatrol.builders:
                    self._flixpatrol(method_name, method_data)
                elif method_name in icheckmovies.builders:
                    self._icheckmovies(method_name, method_data)
                elif method_name in letterboxd.builders:
                    self._letterboxd(method_name, method_data)
                elif method_name in imdb.builders:
                    self._imdb(method_name, method_data)
                elif method_name in mal.builders:
                    self._mal(method_name, method_data)
                elif method_name in plex.builders or method_final in plex.searches:
                    self._plex(method_name, method_data)
                elif method_name in reciperr.builders:
                    self._reciperr(method_name, method_data)
                elif method_name in tautulli.builders:
                    self._tautulli(method_name, method_data)
                elif method_name in tmdb.builders:
                    self._tmdb(method_name, method_data)
                elif method_name in trakt.builders or method_name in ["sync_to_trakt_list", "sync_missing_to_trakt_list"]:
                    self._trakt(method_name, method_data)
                elif method_name in tvdb.builders:
                    self._tvdb(method_name, method_data)
                elif method_name in mdblist.builders:
                    self._mdblist(method_name, method_data)
                elif method_name == "filters":
                    self._filters(method_name, method_data)
                else:
                    raise Failed(f"{self.Type} Error: {method_final} attribute not supported")
            except Failed as e:
                if self.validate_builders:
                    raise
                else:
                    logger.error(e)

        if "append_label" in methods and not self.playlist and not self.overlay:
            logger.debug("")
            logger.debug("Validating Method: append_label")
            logger.debug(f"Value: {data[methods['append_label']]}")
            append_labels = util.get_list(data[methods["append_label"]])
            if "label.sync" in self.details:
                self.details["label.sync"].extend(append_labels)
            elif "label" in self.details:
                self.details["label"].extend(append_labels)
            else:
                self.details["label"] = append_labels

        if not self.server_preroll and not self.smart_url and not self.blank_collection and len(self.builders) == 0:
            raise Failed(f"{self.Type} Error: No builders were found")

        if self.blank_collection and len(self.builders) > 0:
            raise Failed(f"{self.Type} Error: No builders allowed with blank_collection")

        if not isinstance(self.custom_sort, list) and self.custom_sort and (len(self.builders) > 1 or self.builders[0][0] not in custom_sort_builders):
            raise Failed(f"{self.Type} Error: " + ('Playlists' if self.playlist else 'collection_order: custom') +
                         (f" can only be used with a single builder per {self.type}" if len(self.builders) > 1 else f" cannot be used with {self.builders[0][0]}"))

        if "add_missing" not in self.radarr_details:
            self.radarr_details["add_missing"] = self.library.Radarr.add_missing if self.library.Radarr else False
        if "add_existing" not in self.radarr_details:
            self.radarr_details["add_existing"] = self.library.Radarr.add_existing if self.library.Radarr else False

        if "add_missing" not in self.sonarr_details:
            self.sonarr_details["add_missing"] = self.library.Sonarr.add_missing if self.library.Sonarr else False
        if "add_existing" not in self.sonarr_details:
            self.sonarr_details["add_existing"] = self.library.Sonarr.add_existing if self.library.Sonarr else False

        if self.smart_url or self.collectionless or self.library.is_music:
            self.radarr_details["add_missing"] = False
            self.radarr_details["add_existing"] = False
            self.sonarr_details["add_missing"] = False
            self.sonarr_details["add_existing"] = False

        if (self.radarr_details["add_existing"] or self.sonarr_details["add_existing"]) and not self.parts_collection:
            self.item_details["add_existing"] = True

        if self.collectionless:
            self.details["collection_mode"] = "hide"
            self.sync = True

        if self.smart_url:
            self.sync = False

        self.do_report = not self.config.no_report and (self.details["save_report"])
        self.do_missing = not self.config.no_missing and (self.details["show_missing"] or self.do_report
                                                          or (self.library.Radarr and self.radarr_details["add_missing"])
                                                          or (self.library.Sonarr and self.sonarr_details["add_missing"]))
        if self.build_collection:
            if self.obj and ((self.smart and not self.obj.smart) or (not self.smart and self.obj.smart)):
                logger.info("")
                logger.error(f"{self.Type} Error: Converting {self.obj.title} to a {'smart' if self.smart else 'normal'} collection")
                self.library.delete(self.obj)
                self.obj = None
            if self.smart:
                check_url = self.smart_url if self.smart_url else self.smart_label_url
                if self.obj and check_url != self.library.smart_filter(self.obj):
                    self.library.update_smart_collection(self.obj, check_url)
                    logger.info(f"Detail: Smart Collection updated to {check_url}")
                self.beginning_count = len(self.library.get_filter_items(check_url))
            if self.obj:
                self.exists = True
                if self.sync or self.playlist:
                    self.remove_item_map = {i.ratingKey: i for i in self.library.get_collection_items(self.obj, self.smart_label_collection)}
                if not self.smart:
                    self.beginning_count = len(self.remove_item_map) if self.playlist else self.obj.childCount
        else:
            self.obj = None
            self.sync = False
            self.run_again = False
        if self.non_existing is not False and self.obj:
            raise NotScheduled(self.non_existing)

        logger.info("")
        logger.info("Validation Successful")

    def _summary(self, method_name, method_data):
        if method_name == "summary":
            self.summaries[method_name] = method_data
        elif method_name == "tmdb_summary":
            self.summaries[method_name] = self.config.TMDb.get_movie_show_or_collection(util.regex_first_int(method_data, "TMDb ID"), self.library.is_movie).overview
        elif method_name == "tmdb_description":
            self.summaries[method_name] = self.config.TMDb.get_list(util.regex_first_int(method_data, "TMDb List ID")).description
        elif method_name == "tmdb_biography":
            self.summaries[method_name] = self.config.TMDb.get_person(util.regex_first_int(method_data, "TMDb Person ID")).biography
        elif method_name == "tvdb_summary":
            self.summaries[method_name] = self.config.TVDb.get_tvdb_obj(method_data, is_movie=self.library.is_movie).summary
        elif method_name == "tvdb_description":
            summary, _ = self.config.TVDb.get_list_description(method_data)
            if summary:
                self.summaries[method_name] = summary
        elif method_name == "trakt_description":
            self.summaries[method_name] = self.config.Trakt.list_description(self.config.Trakt.validate_list(method_data)[0])
        elif method_name == "letterboxd_description":
            self.summaries[method_name] = self.config.Letterboxd.get_list_description(method_data, self.language)
        elif method_name == "icheckmovies_description":
            self.summaries[method_name] = self.config.ICheckMovies.get_list_description(method_data, self.language)

    def _poster(self, method_name, method_data):
        if method_name == "url_poster":
            try:
                image_response = self.config.get(method_data, headers=util.header())
                if image_response.status_code >= 400 or image_response.headers["Content-Type"] not in ["image/jpeg", "image/png", "image/webp"]:
                    raise ConnectionError
                self.posters[method_name] = method_data
            except ConnectionError:
                logger.warning(f"{self.Type} Warning: No Poster Found at {method_data}")
        elif method_name == "tmdb_list_poster":
            self.posters[method_name] = self.config.TMDb.get_list(util.regex_first_int(method_data, "TMDb List ID")).poster_url
        elif method_name == "tvdb_list_poster":
            _, poster = self.config.TVDb.get_list_description(method_data)
            if poster:
                self.posters[method_name] = poster
        elif method_name == "tmdb_poster":
            self.posters[method_name] = self.config.TMDb.get_movie_show_or_collection(util.regex_first_int(method_data, 'TMDb ID'), self.library.is_movie).poster_url
        elif method_name == "tmdb_profile":
            self.posters[method_name] = self.config.TMDb.get_person(util.regex_first_int(method_data, 'TMDb Person ID')).profile_url
        elif method_name == "tvdb_poster":
            self.posters[method_name] = f"{self.config.TVDb.get_tvdb_obj(method_data, is_movie=self.library.is_movie).poster_url}"
        elif method_name == "file_poster":
            if os.path.exists(os.path.abspath(method_data)):
                self.posters[method_name] = os.path.abspath(method_data)
            else:
                logger.error(f"{self.Type} Error: Poster Path Does Not Exist: {os.path.abspath(method_data)}")

    def _background(self, method_name, method_data):
        if method_name == "url_background":
            try:
                image_response = self.config.get(method_data, headers=util.header())
                if image_response.status_code >= 400 or image_response.headers["Content-Type"] not in ["image/jpeg", "image/png", "image/webp"]:
                    raise ConnectionError
                self.backgrounds[method_name] = method_data
            except ConnectionError:
                logger.warning(f"{self.Type} Warning: No Background Found at {method_data}")
        elif method_name == "tmdb_background":
            self.backgrounds[method_name] = self.config.TMDb.get_movie_show_or_collection(util.regex_first_int(method_data, 'TMDb ID'), self.library.is_movie).backdrop_url
        elif method_name == "tvdb_background":
            self.posters[method_name] = f"{self.config.TVDb.get_tvdb_obj(method_data, is_movie=self.library.is_movie).background_url}"
        elif method_name == "file_background":
            if os.path.exists(os.path.abspath(method_data)):
                self.backgrounds[method_name] = os.path.abspath(method_data)
            else:
                logger.error(f"{self.Type} Error: Background Path Does Not Exist: {os.path.abspath(method_data)}")

    def _details(self, method_name, method_data, method_final, methods):
        if method_name == "url_theme":
            self.url_theme = method_data
        elif method_name == "file_theme":
            if os.path.exists(os.path.abspath(method_data)):
                self.file_theme = os.path.abspath(method_data)
            else:
                logger.error(f"{self.Type} Error: Theme Path Does Not Exist: {os.path.abspath(method_data)}")
        elif method_name == "tmdb_region":
            self.tmdb_region = util.parse(self.Type, method_name, method_data, options=self.config.TMDb.iso_3166_1)
        elif method_name == "collection_mode":
            try:
                self.details[method_name] = util.check_collection_mode(method_data)
            except Failed as e:
                logger.error(e)
        elif method_name == "collection_filtering":
            if method_data and str(method_data).lower() in plex.collection_filtering_options:
                self.details[method_name] = str(method_data).lower()
            else:
                logger.error(f"Config Error: {method_data} collection_filtering invalid\n\tadmin (Always the server admin user)\n\tuser (User currently viewing the content)")
        elif method_name == "minimum_items":
            self.minimum = util.parse(self.Type, method_name, method_data, datatype="int", minimum=1)
        elif method_name == "limit":
            self.limit = util.parse(self.Type, method_name, method_data, datatype="int", minimum=1)
        elif method_name == "cache_builders":
            self.details[method_name] = util.parse(self.Type, method_name, method_data, datatype="int", minimum=0)
        elif method_name == "default_percent":
            self.default_percent = util.parse(self.Type, method_name, method_data, datatype="int", minimum=1, maximum=100)
        elif method_name == "server_preroll":
            self.server_preroll = util.parse(self.Type, method_name, method_data)
        elif method_name == "ignore_ids":
            self.ignore_ids.extend(util.parse(self.Type, method_name, method_data, datatype="intlist"))
        elif method_name == "ignore_imdb_ids":
            self.ignore_imdb_ids.extend(util.parse(self.Type, method_name, method_data, datatype="list"))
        elif method_name == "label":
            if "label" in methods and "label.sync" in methods:
                raise Failed(f"{self.Type} Error: Cannot use label and label.sync together")
            if "label.remove" in methods and "label.sync" in methods:
                raise Failed(f"{self.Type} Error: Cannot use label.remove and label.sync together")
            if method_final == "label" and "label_sync_mode" in methods and self.data[methods["label_sync_mode"]] == "sync":
                self.details["label.sync"] = util.get_list(method_data) if method_data else []
            else:
                self.details[method_final] = util.get_list(method_data) if method_data else []
        elif method_name == "changes_webhooks":
            self.details[method_name] = util.parse(self.Type, method_name, method_data, datatype="list") if method_data else None
        elif method_name in scheduled_boolean:
            if isinstance(method_data, bool):
                self.details[method_name] = method_data
            elif isinstance(method_data, (int, float)):
                self.details[method_name] = method_data > 0
            elif str(method_data).lower() in ["t", "true"]:
                self.details[method_name] = True
            elif str(method_data).lower() in ["f", "false"]:
                self.details[method_name] = False
            else:
                try:
                    util.schedule_check(method_name, util.parse(self.Type, method_name, method_data), self.current_time, self.config.run_hour)
                    self.details[method_name] = True
                except NotScheduled:
                    self.details[method_name] = False
        elif method_name in boolean_details:
            default = self.details[method_name] if method_name in self.details else None
            self.details[method_name] = util.parse(self.Type, method_name, method_data, datatype="bool", default=default)
        elif method_name in string_details:
            self.details[method_name] = str(method_data)

    def _item_details(self, method_name, method_data, method_mod, method_final, methods):
        if method_name == "item_label":
            if "item_label" in methods and "item_label.sync" in methods:
                raise Failed(f"{self.Type} Error: Cannot use item_label and item_label.sync together")
            if "item_label.remove" in methods and "item_label.sync" in methods:
                raise Failed(f"{self.Type} Error: Cannot use item_label.remove and item_label.sync together")
            self.item_details[method_final] = util.get_list(method_data) if method_data else []
        if method_name == "item_genre":
            if "item_genre" in methods and "item_genre.sync" in methods:
                raise Failed(f"{self.Type} Error: Cannot use item_genre and item_genre.sync together")
            if "item_genre.remove" in methods and "item_genre.sync" in methods:
                raise Failed(f"{self.Type} Error: Cannot use item_genre.remove and item_genre.sync together")
            self.item_details[method_final] = util.get_list(method_data) if method_data else []
        elif method_name == "item_edition":
            self.item_details[method_final] = str(method_data) if method_data else ""
        elif method_name == "non_item_remove_label":
            if not method_data:
                raise Failed(f"{self.Type} Error: non_item_remove_label is blank")
            self.item_details[method_final] = util.get_list(method_data)
        elif method_name in ["item_radarr_tag", "item_sonarr_tag"]:
            if method_name in methods and f"{method_name}.sync" in methods:
                raise Failed(f"{self.Type} Error: Cannot use {method_name} and {method_name}.sync together")
            if f"{method_name}.remove" in methods and f"{method_name}.sync" in methods:
                raise Failed(f"{self.Type} Error: Cannot use {method_name}.remove and {method_name}.sync together")
            if method_name in methods and f"{method_name}.remove" in methods:
                raise Failed(f"{self.Type} Error: Cannot use {method_name} and {method_name}.remove together")
            self.item_details[method_name] = util.get_list(method_data, lower=True)
            self.item_details["apply_tags"] = method_mod[1:] if method_mod else ""
        elif method_name == "item_refresh_delay":
            self.item_details[method_name] = util.parse(self.Type, method_name, method_data, datatype="int", default=0, minimum=0)
        elif method_name in item_bool_details:
            if util.parse(self.Type, method_name, method_data, datatype="bool", default=False):
                self.item_details[method_name] = True
            elif method_name in item_false_details:
                self.item_details[method_name] = False
        elif method_name in plex.item_advance_keys:
            key, options = plex.item_advance_keys[method_name]
            if method_name in advance_new_agent and self.library.agent not in plex.new_plex_agents:
                logger.error(f"Metadata Error: {method_name} attribute only works for with the New Plex Movie Agent and New Plex TV Agent")
            elif method_name in advance_show and not self.library.is_show:
                logger.error(f"Metadata Error: {method_name} attribute only works for show libraries")
            elif str(method_data).lower() not in options:
                logger.error(f"Metadata Error: {method_data} {method_name} attribute invalid")
            else:
                self.item_details[method_name] = str(method_data).lower()

    def _radarr(self, method_name, method_data):
        if method_name in ["radarr_add_missing", "radarr_add_existing", "radarr_upgrade_existing", "radarr_search", "radarr_monitor", "radarr_ignore_cache"]:
            self.radarr_details[method_name[7:]] = util.parse(self.Type, method_name, method_data, datatype="bool")
        elif method_name == "radarr_folder":
            self.radarr_details["folder"] = method_data
        elif method_name == "radarr_availability":
            if str(method_data).lower() in radarr.availability_translation:
                self.radarr_details["availability"] = str(method_data).lower()
            else:
                raise Failed(f"{self.Type} Error: {method_name} attribute must be either announced, cinemas, released or db")
        elif method_name == "radarr_quality":
            self.radarr_details["quality"] = method_data
        elif method_name == "radarr_tag":
            self.radarr_details["tag"] = util.get_list(method_data, lower=True)
        elif method_name == "radarr_taglist":
            self.builders.append((method_name, util.get_list(method_data, lower=True)))
        elif method_name == "radarr_all":
            self.builders.append((method_name, True))

    def _sonarr(self, method_name, method_data):
        if method_name in ["sonarr_add_missing", "sonarr_add_existing", "sonarr_upgrade_existing", "sonarr_season", "sonarr_search", "sonarr_cutoff_search", "sonarr_ignore_cache"]:
            self.sonarr_details[method_name[7:]] = util.parse(self.Type, method_name, method_data, datatype="bool")
        elif method_name in ["sonarr_folder", "sonarr_quality", "sonarr_language"]:
            self.sonarr_details[method_name[7:]] = method_data
        elif method_name == "sonarr_monitor":
            if str(method_data).lower() in sonarr.monitor_translation:
                self.sonarr_details["monitor"] = str(method_data).lower()
            else:
                raise Failed(f"{self.Type} Error: {method_name} attribute must be either all, future, missing, existing, pilot, first, latest or none")
        elif method_name == "sonarr_series":
            if str(method_data).lower() in sonarr.series_types:
                self.sonarr_details["series"] = str(method_data).lower()
            else:
                raise Failed(f"{self.Type} Error: {method_name} attribute must be either standard, daily, or anime")
        elif method_name == "sonarr_tag":
            self.sonarr_details["tag"] = util.get_list(method_data, lower=True)
        elif method_name == "sonarr_taglist":
            self.builders.append((method_name, util.get_list(method_data, lower=True)))
        elif method_name == "sonarr_all":
            self.builders.append((method_name, True))

    def _anidb(self, method_name, method_data):
        if method_name == "anidb_popular":
            self.builders.append((method_name, util.parse(self.Type, method_name, method_data, datatype="int", default=30, maximum=30)))
        elif method_name in ["anidb_id", "anidb_relation"]:
            for anidb_id in self.config.AniDB.validate_anidb_ids(method_data):
                self.builders.append((method_name, anidb_id))
        elif method_name == "anidb_tag":
            for dict_data in util.parse(self.Type, method_name, method_data, datatype="listdict"):
                dict_methods = {dm.lower(): dm for dm in dict_data}
                new_dictionary = {}
                if "tag" not in dict_methods:
                    raise Failed(f"{self.Type} Error: anidb_tag tag attribute is required")
                elif not dict_data[dict_methods["tag"]]:
                    raise Failed(f"{self.Type} Error: anidb_tag tag attribute is blank")
                else:
                    new_dictionary["tag"] = util.regex_first_int(dict_data[dict_methods["tag"]], "AniDB Tag ID")
                new_dictionary["limit"] = util.parse(self.Type, "limit", dict_data, datatype="int", methods=dict_methods, default=0, parent=method_name, minimum=0)
                self.builders.append((method_name, new_dictionary))

    def _anilist(self, method_name, method_data):
        if method_name in ["anilist_id", "anilist_relations", "anilist_studio"]:
            for anilist_id in self.config.AniList.validate_anilist_ids(method_data, studio=method_name == "anilist_studio"):
                self.builders.append((method_name, anilist_id))
        elif method_name in ["anilist_popular", "anilist_trending", "anilist_top_rated"]:
            self.builders.append((method_name, util.parse(self.Type, method_name, method_data, datatype="int", default=10)))
        elif method_name == "anilist_userlist":
            for dict_data in util.parse(self.Type, method_name, method_data, datatype="listdict"):
                dict_methods = {dm.lower(): dm for dm in dict_data}
                self.builders.append((method_name, self.config.AniList.validate_userlist({
                    "username": util.parse(self.Type, "username", dict_data, methods=dict_methods, parent=method_name),
                    "list_name": util.parse(self.Type, "list_name", dict_data, methods=dict_methods, parent=method_name),
                    "sort_by": util.parse(self.Type, "sort_by", dict_data, methods=dict_methods, parent=method_name, default="score", options=anilist.userlist_sort_options),
                })))
        elif method_name == "anilist_search":
            if self.current_time.month in [12, 1, 2]:           current_season = "winter"
            elif self.current_time.month in [3, 4, 5]:          current_season = "spring"
            elif self.current_time.month in [6, 7, 8]:          current_season = "summer"
            else:                                               current_season = "fall"
            default_year = self.current_year + 1 if self.current_time.month == 12 else self.current_year
            for dict_data in util.parse(self.Type, method_name, method_data, datatype="listdict"):
                dict_methods = {dm.lower(): dm for dm in dict_data}
                new_dictionary = {}
                for search_method, search_data in dict_data.items():
                    search_attr, modifier = os.path.splitext(str(search_method).lower())
                    if search_method not in anilist.searches:
                        raise Failed(f"{self.Type} Error: {method_name} {search_method} attribute not supported")
                    elif search_attr == "season":
                        new_dictionary[search_attr] = util.parse(self.Type, search_attr, search_data, parent=method_name, default=current_season, options=util.seasons)
                        if new_dictionary[search_attr] == "current":
                            new_dictionary[search_attr] = current_season
                        if "year" not in dict_methods:
                            logger.warning(f"Collection Warning: {method_name} year attribute not found using this year: {default_year} by default")
                            new_dictionary["year"] = default_year
                    elif search_attr == "year":
                        new_dictionary[search_attr] = util.parse(self.Type, search_attr, search_data, datatype="int", parent=method_name, default=default_year, minimum=1917, maximum=default_year + 1)
                    elif search_data is None:
                        raise Failed(f"{self.Type} Error: {method_name} {search_method} attribute is blank")
                    elif search_attr == "adult":
                        new_dictionary[search_attr] = util.parse(self.Type, search_attr, search_data, datatype="bool", parent=method_name)
                    elif search_attr == "country":
                        new_dictionary[search_attr] = util.parse(self.Type, search_attr, search_data, options=anilist.country_codes, parent=method_name)
                    elif search_attr == "source":
                        new_dictionary[search_attr] = util.parse(self.Type, search_attr, search_data, options=anilist.media_source, parent=method_name)
                    elif search_attr in ["episodes", "duration", "score", "popularity"]:
                        new_dictionary[search_method] = util.parse(self.Type, search_method, search_data, datatype="int", parent=method_name)
                    elif search_attr in ["format", "status", "genre", "tag", "tag_category"]:
                        new_dictionary[search_method] = self.config.AniList.validate(search_attr.replace("_", " ").title(), util.parse(self.Type, search_method, search_data))
                    elif search_attr in ["start", "end"]:
                        new_dictionary[search_method] = util.validate_date(search_data, f"{method_name} {search_method} attribute", return_as="%m/%d/%Y")
                    elif search_attr == "min_tag_percent":
                        new_dictionary[search_attr] = util.parse(self.Type, search_attr, search_data, datatype="int", parent=method_name, minimum=0, maximum=100)
                    elif search_attr == "search":
                        new_dictionary[search_attr] = str(search_data)
                    elif search_method not in ["sort_by", "limit"]:
                        raise Failed(f"{self.Type} Error: {method_name} {search_method} attribute not supported")
                if len(new_dictionary) == 0:
                    raise Failed(f"{self.Type} Error: {method_name} must have at least one valid search option")
                new_dictionary["sort_by"] = util.parse(self.Type, "sort_by", dict_data, methods=dict_methods, parent=method_name, default="score", options=anilist.sort_options)
                new_dictionary["limit"] = util.parse(self.Type, "limit", dict_data, datatype="int", methods=dict_methods, default=0, parent=method_name)
                self.builders.append((method_name, new_dictionary))

    def _flixpatrol(self, method_name, method_data):
        if method_name.startswith("flixpatrol_url"):
            flixpatrol_lists = self.config.FlixPatrol.validate_flixpatrol_lists(method_data, self.language, self.library.is_movie)
            for flixpatrol_list in flixpatrol_lists:
                self.builders.append(("flixpatrol_url", flixpatrol_list))
        elif method_name in flixpatrol.builders:
            for dict_data in util.parse(self.Type, method_name, method_data, datatype="listdict"):
                dict_methods = {dm.lower(): dm for dm in dict_data}
                if method_name == "flixpatrol_demographics":
                    data = {
                        "generation": util.parse(self.Type, "generation", dict_data, methods=dict_methods, parent=method_name, options=flixpatrol.generations),
                        "gender": util.parse(self.Type, "gender", dict_data, methods=dict_methods, parent=method_name, default="all", options=flixpatrol.gender),
                        "location": util.parse(self.Type, "location", dict_data, methods=dict_methods, parent=method_name, default="world", options=flixpatrol.demo_locations),
                        "limit": util.parse(self.Type, "limit", dict_data, datatype="int", methods=dict_methods, parent=method_name, default=10)
                    }
                elif method_name == "flixpatrol_popular":
                    data = {
                        "source": util.parse(self.Type, "source", dict_data, methods=dict_methods, parent=method_name, options=flixpatrol.popular),
                        "time_window": util.parse(self.Type, "time_window", dict_data, methods=dict_methods, parent=method_name, default="today"),
                        "limit": util.parse(self.Type, "limit", dict_data, datatype="int", methods=dict_methods, parent=method_name, default=10)
                    }
                elif method_name == "flixpatrol_top":
                    data = {
                        "platform": util.parse(self.Type, "platform", dict_data, methods=dict_methods, parent=method_name, options=flixpatrol.platforms),
                        "location": util.parse(self.Type, "location", dict_data, methods=dict_methods, parent=method_name, default="world", options=flixpatrol.locations),
                        "time_window": util.parse(self.Type, "time_window", dict_data, methods=dict_methods, parent=method_name, default="today"),
                        "limit": util.parse(self.Type, "limit", dict_data, datatype="int", methods=dict_methods, parent=method_name, default=10)
                    }
                else:
                    continue
                if self.config.FlixPatrol.validate_flixpatrol_dict(method_name, data, self.language, self.library.is_movie):
                    self.builders.append((method_name, data))

    def _icheckmovies(self, method_name, method_data):
        if method_name.startswith("icheckmovies_list"):
            icheckmovies_lists = self.config.ICheckMovies.validate_icheckmovies_lists(method_data, self.language)
            for icheckmovies_list in icheckmovies_lists:
                self.builders.append(("icheckmovies_list", icheckmovies_list))
            if method_name.endswith("_details"):
                self.summaries[method_name] = self.config.ICheckMovies.get_list_description(icheckmovies_lists[0], self.language)

    def _imdb(self, method_name, method_data):
        if method_name == "imdb_id":
            for value in util.get_list(method_data):
                if str(value).startswith("tt"):
                    self.builders.append((method_name, value))
                else:
                    raise Failed(f"{self.Type} Error: imdb_id {value} must begin with tt")
        elif method_name == "imdb_list":
            for imdb_dict in self.config.IMDb.validate_imdb_lists(self.Type, method_data, self.language):
                self.builders.append((method_name, imdb_dict))
        elif method_name == "imdb_chart":
            for value in util.get_list(method_data):
                if value in imdb.movie_charts and not self.library.is_movie:
                    raise Failed(f"{self.Type} Error: chart: {value} does not work with show libraries")
                elif value in imdb.show_charts and self.library.is_movie:
                    raise Failed(f"{self.Type} Error: chart: {value} does not work with movie libraries")
                elif value in imdb.movie_charts or value in imdb.show_charts:
                    self.builders.append((method_name, value))
                else:
                    raise Failed(f"{self.Type} Error: chart: {value} is invalid options are {[i for i in imdb.charts]}")
        elif method_name == "imdb_watchlist":
            for imdb_user in self.config.IMDb.validate_imdb_watchlists(self.Type, method_data, self.language):
                self.builders.append((method_name, imdb_user))

    def _letterboxd(self, method_name, method_data):
        if method_name.startswith("letterboxd_list"):
            letterboxd_lists = self.config.Letterboxd.validate_letterboxd_lists(self.Type, method_data, self.language)
            for letterboxd_list in letterboxd_lists:
                self.builders.append(("letterboxd_list", letterboxd_list))
            if method_name.endswith("_details"):
                self.summaries[method_name] = self.config.Letterboxd.get_list_description(letterboxd_lists[0]["url"], self.language)

    def _mal(self, method_name, method_data):
        if method_name == "mal_id":
            for mal_id in util.get_int_list(method_data, "MyAnimeList ID"):
                self.builders.append((method_name, mal_id))
        elif method_name in ["mal_all", "mal_airing", "mal_upcoming", "mal_tv", "mal_ova", "mal_movie", "mal_special", "mal_popular", "mal_favorite", "mal_suggested"]:
            self.builders.append((method_name, util.parse(self.Type, method_name, method_data, datatype="int", default=10, maximum=100 if method_name == "mal_suggested" else 500)))
        elif method_name in ["mal_season", "mal_userlist", "mal_search"]:
            for dict_data in util.parse(self.Type, method_name, method_data, datatype="listdict"):
                dict_methods = {dm.lower(): dm for dm in dict_data}
                if method_name == "mal_season":
                    if self.current_time.month in [1, 2, 3]:            default_season = "winter"
                    elif self.current_time.month in [4, 5, 6]:          default_season = "spring"
                    elif self.current_time.month in [7, 8, 9]:          default_season = "summer"
                    else:                                               default_season = "fall"
                    season = util.parse(self.Type, "season", dict_data, methods=dict_methods, parent=method_name, default=default_season, options=util.seasons)
                    if season == "current":
                        season = default_season
                    self.builders.append((method_name, {
                        "season": season,
                        "sort_by": util.parse(self.Type, "sort_by", dict_data, methods=dict_methods, parent=method_name, default="members", options=mal.season_sort_options, translation=mal.season_sort_translation),
                        "year": util.parse(self.Type, "year", dict_data, datatype="int", methods=dict_methods, default=self.current_year, parent=method_name, minimum=1917, maximum=self.current_year + 1),
                        "limit": util.parse(self.Type, "limit", dict_data, datatype="int", methods=dict_methods, default=100, parent=method_name, maximum=500),
                        "starting_only": util.parse(self.Type, "starting_only", dict_data, datatype="bool", methods=dict_methods, default=False, parent=method_name)
                    }))
                elif method_name == "mal_userlist":
                    self.builders.append((method_name, {
                        "username": util.parse(self.Type, "username", dict_data, methods=dict_methods, parent=method_name),
                        "status": util.parse(self.Type, "status", dict_data, methods=dict_methods, parent=method_name, default="all", options=mal.userlist_status),
                        "sort_by": util.parse(self.Type, "sort_by", dict_data, methods=dict_methods, parent=method_name, default="score", options=mal.userlist_sort_options, translation=mal.userlist_sort_translation),
                        "limit": util.parse(self.Type, "limit", dict_data, datatype="int", methods=dict_methods, default=100, parent=method_name, maximum=1000)
                    }))
                elif method_name == "mal_search":
                    final_attributes = {}
                    final_text = "MyAnimeList Search"
                    if "sort_by" in dict_methods:
                        sort = util.parse(self.Type, "sort_by", dict_data, methods=dict_methods, parent=method_name, options=mal.search_combos)
                        sort_type, sort_direction = sort.split(".")
                        final_text += f"\nSorted By: {sort}"
                        final_attributes["order_by"] = sort_type
                        final_attributes["sort"] = sort_direction
                    limit = 0
                    if "limit" in dict_methods:
                        limit = util.parse(self.Type, "limit", dict_data, datatype="int", default=0, methods=dict_methods, parent=method_name)
                        final_text += f"\nLimit: {limit if limit else 'None'}"
                    if "query" in dict_methods:
                        final_attributes["q"] = util.parse(self.Type, "query", dict_data, methods=dict_methods, parent=method_name)
                        final_text += f"\nQuery: {final_attributes['q']}"
                    if "prefix" in dict_methods:
                        final_attributes["letter"] = util.parse(self.Type, "prefix", dict_data, methods=dict_methods, parent=method_name)
                        final_text += f"\nPrefix: {final_attributes['letter']}"
                    if "type" in dict_methods:
                        type_list = util.parse(self.Type, "type", dict_data, datatype="commalist", methods=dict_methods, parent=method_name, options=mal.search_types)
                        final_attributes["type"] = ",".join(type_list)
                        final_text += f"\nType: {' or '.join(type_list)}"
                    if "status" in dict_methods:
                        final_attributes["status"] = util.parse(self.Type, "status", dict_data, methods=dict_methods, parent=method_name, options=mal.search_status)
                        final_text += f"\nStatus: {final_attributes['status']}"
                    if "genre" in dict_methods:
                        genre_str = str(util.parse(self.Type, "genre", dict_data, methods=dict_methods, parent=method_name))
                        out_text, out_ints = util.parse_and_or(self.Type, 'Genre', genre_str, self.config.MyAnimeList.genres)
                        final_text += f"\nGenre: {out_text}"
                        final_attributes["genres"] = out_ints
                    if "genre.not" in dict_methods:
                        genre_str = str(util.parse(self.Type, "genre.not", dict_data, methods=dict_methods, parent=method_name))
                        out_text, out_ints = util.parse_and_or(self.Type, 'Genre', genre_str, self.config.MyAnimeList.genres)
                        final_text += f"\nNot Genre: {out_text}"
                        final_attributes["genres_exclude"] = out_ints
                    if "studio" in dict_methods:
                        studio_str = str(util.parse(self.Type, "studio", dict_data, methods=dict_methods, parent=method_name))
                        out_text, out_ints = util.parse_and_or(self.Type, 'Studio', studio_str, self.config.MyAnimeList.studios)
                        final_text += f"\nStudio: {out_text}"
                        final_attributes["producers"] = out_ints
                    if "content_rating" in dict_methods:
                        final_attributes["rating"] = util.parse(self.Type, "content_rating", dict_data, methods=dict_methods, parent=method_name, options=mal.search_ratings)
                        final_text += f"\nContent Rating: {final_attributes['rating']}"
                    if "score.gte" in dict_methods:
                        final_attributes["min_score"] = util.parse(self.Type, "score.gte", dict_data, datatype="float", methods=dict_methods, parent=method_name, minimum=0, maximum=10)
                        final_text += f"\nScore Greater Than or Equal: {final_attributes['min_score']}"
                    elif "score.gt" in dict_methods:
                        original_score = util.parse(self.Type, "score.gt", dict_data, datatype="float", methods=dict_methods, parent=method_name, minimum=0, maximum=10)
                        final_attributes["min_score"] = original_score + 0.01
                        final_text += f"\nScore Greater Than: {original_score}"
                    if "score.lte" in dict_methods:
                        final_attributes["max_score"] = util.parse(self.Type, "score.lte", dict_data, datatype="float", methods=dict_methods, parent=method_name, minimum=0, maximum=10)
                        final_text += f"\nScore Less Than or Equal: {final_attributes['max_score']}"
                    elif "score.lt" in dict_methods:
                        original_score = util.parse(self.Type, "score.lt", dict_data, datatype="float", methods=dict_methods, parent=method_name, minimum=0, maximum=10)
                        final_attributes["max_score"] = original_score - 0.01
                        final_text += f"\nScore Less Than: {original_score}"
                    if "min_score" in final_attributes and "max_score"  in final_attributes and final_attributes["max_score"] <= final_attributes["min_score"]:
                        raise Failed(f"{self.Type} Error: mal_search score.lte/score.lt attribute must be greater than score.gte/score.gt")
                    if "sfw" in dict_methods:
                        sfw = util.parse(self.Type, "sfw", dict_data, datatype="bool", methods=dict_methods, parent=method_name)
                        if sfw:
                            final_attributes["sfw"] = 1
                        final_text += f"\nSafe for Work: {final_attributes['sfw']}"
                    if not final_attributes:
                        raise Failed(f"{self.Type} Error: no mal_search attributes found")
                    self.builders.append((method_name, (final_attributes, final_text, limit)))
        elif method_name in ["mal_genre", "mal_studio"]:
            logger.warning(f"Config Warning: {method_name} will run as a mal_search")
            item_list = util.parse(self.Type, method_name[4:], method_data, datatype="commalist")
            all_items = self.config.MyAnimeList.genres if method_name == "mal_genre" else self.config.MyAnimeList.studios
            final_items = [str(all_items[i]) for i in item_list if i in all_items]
            final_text = f"MyAnimeList Search\n{method_name[4:].capitalize()}: {' or '.join([str(all_items[i]) for i in final_items])}"
            self.builders.append(("mal_search", ({"genres" if method_name == "mal_genre" else "producers": ",".join(final_items)}, final_text, 0)))

    def _plex(self, method_name, method_data):
        if method_name in ["plex_all", "plex_pilots"]:
            self.builders.append((method_name, self.builder_level))
        elif method_name == "plex_watchlist":
            if method_data not in plex.watchlist_sorts:
                logger.warning(f"{self.Type} Warning: Watchlist sort: {method_data} invalid defaulting to added.asc")
            self.builders.append((method_name, method_data if method_data in plex.watchlist_sorts else "added.asc"))
        elif method_name in ["plex_search", "plex_collectionless"]:
            for dict_data in util.parse(self.Type, method_name, method_data, datatype="listdict"):
                dict_methods = {dm.lower(): dm for dm in dict_data}
                if method_name == "plex_search":
                    try:
                        self.builders.append((method_name, self.build_filter("plex_search", dict_data)))
                    except FilterFailed as e:
                        if self.ignore_blank_results:
                            raise
                        else:
                            raise Failed(str(e))
                elif method_name == "plex_collectionless":
                    prefix_list = util.parse(self.Type, "exclude_prefix", dict_data, datatype="list", methods=dict_methods) if "exclude_prefix" in dict_methods else []
                    exact_list = util.parse(self.Type, "exclude", dict_data, datatype="list", methods=dict_methods) if "exclude" in dict_methods else []
                    if len(prefix_list) == 0 and len(exact_list) == 0:
                        raise Failed(f"{self.Type} Error: you must have at least one exclusion")
                    exact_list.append(self.name)
                    self.builders.append((method_name, {"exclude_prefix": prefix_list, "exclude": exact_list}))
        else:
            try:
                self.builders.append(("plex_search", self.build_filter("plex_search", {"any": {method_name: method_data}})))
            except FilterFailed as e:
                if self.ignore_blank_results:
                    raise
                else:
                    raise Failed(str(e))

    def _reciperr(self, method_name, method_data):
        if method_name == "reciperr_list":
            for reciperr_list in self.config.Reciperr.validate_list(method_data):
                self.builders.append((method_name, reciperr_list))
        elif method_name == "stevenlu_popular":
            self.builders.append((method_name, util.parse(self.Type, method_name, method_data, "bool")))

    def _mdblist(self, method_name, method_data):
        for mdb_dict in self.config.Mdblist.validate_mdblist_lists(self.Type, method_data):
            self.builders.append((method_name, mdb_dict))

    def _tautulli(self, method_name, method_data):
        for dict_data in util.parse(self.Type, method_name, method_data, datatype="listdict"):
            dict_methods = {dm.lower(): dm for dm in dict_data}
            self.builders.append((method_name, {
                "list_type": "popular" if method_name == "tautulli_popular" else "watched",
                "list_days": util.parse(self.Type, "list_days", dict_data, datatype="int", methods=dict_methods, default=30, parent=method_name),
                "list_size": util.parse(self.Type, "list_size", dict_data, datatype="int", methods=dict_methods, default=10, parent=method_name),
                "list_buffer": util.parse(self.Type, "list_buffer", dict_data, datatype="int", methods=dict_methods, default=20, parent=method_name),
                "list_minimum": util.parse(self.Type, "list_minimum", dict_data, datatype="int", methods=dict_methods, default=0, parent=method_name)
            }))

    def _tmdb(self, method_name, method_data):
        if method_name == "tmdb_discover":
            for dict_data in util.parse(self.Type, method_name, method_data, datatype="listdict"):
                dict_methods = {dm.lower(): dm for dm in dict_data}
                new_dictionary = {"limit": util.parse(self.Type, "limit", dict_data, datatype="int", methods=dict_methods, default=100, parent=method_name)}
                for discover_method, discover_data in dict_data.items():
                    discover_attr, modifier = os.path.splitext(str(discover_method).lower())
                    if discover_data is None:
                        raise Failed(f"{self.Type} Error: {method_name} {discover_method} attribute is blank")
                    elif discover_method not in tmdb.discover_all:
                        raise Failed(f"{self.Type} Error: {method_name} {discover_method} attribute not supported")
                    elif self.library.is_movie and discover_attr in tmdb.discover_tv_only:
                        raise Failed(f"{self.Type} Error: {method_name} {discover_method} attribute only works for show libraries")
                    elif self.library.is_show and discover_attr in tmdb.discover_movie_only:
                        raise Failed(f"{self.Type} Error: {method_name} {discover_method} attribute only works for movie libraries")
                    elif discover_attr == "region":
                        new_dictionary[discover_attr] = util.parse(self.Type, discover_attr, discover_data, parent=method_name, regex=("^[A-Z]{2}$", "US"))
                    elif discover_attr == "sort_by":
                        options = tmdb.discover_movie_sort if self.library.is_movie else tmdb.discover_tv_sort
                        new_dictionary[discover_method] = util.parse(self.Type, discover_attr, discover_data, parent=method_name, options=options)
                    elif discover_attr == "certification_country":
                        if "certification" in dict_data or "certification.lte" in dict_data or "certification.gte" in dict_data:
                            new_dictionary[discover_method] = discover_data
                        else:
                            raise Failed(f"{self.Type} Error: {method_name} {discover_attr} attribute: must be used with either certification, certification.lte, or certification.gte")
                    elif discover_attr == "certification":
                        if "certification_country" in dict_data:
                            new_dictionary[discover_method] = discover_data
                        else:
                            raise Failed(f"{self.Type} Error: {method_name} {discover_method} attribute: must be used with certification_country")
                    elif discover_attr == "watch_region":
                        if "with_watch_providers" in dict_data or "without_watch_providers" in dict_data or "with_watch_monetization_types" in dict_data:
                            new_dictionary[discover_method] = discover_data
                        else:
                            raise Failed(f"{self.Type} Error: {method_name} {discover_method} attribute: must be used with either with_watch_providers, without_watch_providers, or with_watch_monetization_types")
                    elif discover_attr == "with_watch_monetization_types":
                        if "watch_region" in dict_data:
                            new_dictionary[discover_method] = util.parse(self.Type, discover_attr, discover_data, parent=method_name, options=tmdb.discover_monetization_types)
                        else:
                            raise Failed(f"{self.Type} Error: {method_name} {discover_method} attribute: must be used with watch_region")
                    elif discover_attr in tmdb.discover_booleans:
                        new_dictionary[discover_method] = util.parse(self.Type, discover_attr, discover_data, datatype="bool", parent=method_name)
                    elif discover_attr == "vote_average":
                        new_dictionary[discover_method] = util.parse(self.Type, discover_method, discover_data, datatype="float", parent=method_name)
                    elif discover_attr == "with_status":
                        new_dictionary[discover_method] = util.parse(self.Type, discover_attr, discover_data, datatype="int", parent=method_name, minimum=0, maximum=5)
                    elif discover_attr == "with_type":
                        new_dictionary[discover_method] = util.parse(self.Type, discover_attr, discover_data, datatype="int", parent=method_name, minimum=0, maximum=6)
                    elif discover_attr in tmdb.discover_dates:
                        new_dictionary[discover_method] = util.validate_date(discover_data, f"{method_name} {discover_method} attribute", return_as="%m/%d/%Y")
                    elif discover_attr in tmdb.discover_years:
                        new_dictionary[discover_method] = util.parse(self.Type, discover_attr, discover_data, datatype="int", parent=method_name, minimum=1800, maximum=self.current_year + 1)
                    elif discover_attr in tmdb.discover_ints:
                        new_dictionary[discover_method] = util.parse(self.Type, discover_method, discover_data, datatype="int", parent=method_name)
                    elif discover_attr in tmdb.discover_strings:
                        new_dictionary[discover_method] = discover_data
                    elif discover_attr != "limit":
                        raise Failed(f"{self.Type} Error: {method_name} {discover_method} attribute not supported")
                if len(new_dictionary) > 1:
                    self.builders.append((method_name, new_dictionary))
                else:
                    raise Failed(f"{self.Type} Error: {method_name} had no valid fields")
        elif method_name in tmdb.int_builders:
            self.builders.append((method_name, util.parse(self.Type, method_name, method_data, datatype="int", default=10)))
        else:
            values = self.config.TMDb.validate_tmdb_ids(method_data, method_name)
            if method_name in tmdb.details_builders:
                if method_name.startswith(("tmdb_collection", "tmdb_movie", "tmdb_show")):
                    item = self.config.TMDb.get_movie_show_or_collection(values[0], self.library.is_movie)
                    if item.overview:
                        self.summaries[method_name] = item.overview
                    if item.backdrop_url:
                        self.backgrounds[method_name] = item.backdrop_url
                    if item.poster_url:
                        self.posters[method_name] = item.poster_url
                elif method_name.startswith(("tmdb_actor", "tmdb_crew", "tmdb_director", "tmdb_producer", "tmdb_writer")):
                    item = self.config.TMDb.get_person(values[0])
                    if item.biography:
                        self.summaries[method_name] = item.biography
                    if item.profile_path:
                        self.posters[method_name] = item.profile_url
                elif method_name.startswith("tmdb_list"):
                    item = self.config.TMDb.get_list(values[0])
                    if item.description:
                        self.summaries[method_name] = item.description
                    if item.poster_url:
                        self.posters[method_name] = item.poster_url
            for value in values:
                self.builders.append((method_name[:-8] if method_name in tmdb.details_builders else method_name, value))

    def _trakt(self, method_name, method_data):
        if method_name.startswith("trakt_list"):
            trakt_lists = self.config.Trakt.validate_list(method_data)
            for trakt_list in trakt_lists:
                self.builders.append(("trakt_list", trakt_list))
            if method_name.endswith("_details"):
                self.summaries[method_name] = self.config.Trakt.list_description(trakt_lists[0])
        elif method_name == "trakt_boxoffice":
            if util.parse(self.Type, method_name, method_data, datatype="bool", default=False):
                self.builders.append((method_name, 10))
            else:
                raise Failed(f"{self.Type} Error: {method_name} must be set to true")
        elif method_name == "trakt_recommendations":
            self.builders.append((method_name, util.parse(self.Type, method_name, method_data, datatype="int", default=10, maximum=100)))
        elif method_name == "sync_to_trakt_list":
            if method_data not in self.config.Trakt.slugs:
                raise Failed(f"{self.Type} Error: {method_data} invalid. Options {', '.join(self.config.Trakt.slugs)}")
            self.sync_to_trakt_list = method_data
        elif method_name == "sync_missing_to_trakt_list":
            self.sync_missing_to_trakt_list = util.parse(self.Type, method_name, method_data, datatype="bool", default=False)
        elif method_name in trakt.builders:
            if method_name in ["trakt_chart", "trakt_userlist"]:
                trakt_dicts = method_data
                final_method = method_name
            elif method_name in ["trakt_watchlist", "trakt_collection"]:
                trakt_dicts = []
                for trakt_user in util.get_list(method_data, split=False):
                    trakt_dicts.append({"userlist": "watchlist" if "trakt_watchlist" else "collected", "user": trakt_user})
                final_method = "trakt_userlist"
            else:
                terms = method_name.split("_")
                trakt_dicts = {
                    "chart": terms[1],
                    "limit": util.parse(self.Type, method_name, method_data, datatype="int", default=10),
                    "time_period": terms[2] if len(terms) > 2 else None
                }
                final_method = "trakt_chart"
            if method_name != final_method:
                logger.warning(f"{self.Type} Warning: {method_name} will run as {final_method}")
            for trakt_dict in self.config.Trakt.validate_chart(self.Type, final_method, trakt_dicts,  self.library.is_movie):
                self.builders.append((final_method, trakt_dict))

    def _tvdb(self, method_name, method_data):
        values = util.get_list(method_data)
        if method_name.endswith("_details"):
            if method_name.startswith(("tvdb_movie", "tvdb_show")):
                item = self.config.TVDb.get_tvdb_obj(values[0], is_movie=method_name.startswith("tvdb_movie"))
                if item.background_url:
                    self.backgrounds[method_name] = item.background_url
                if item.poster_url:
                    self.posters[method_name] = item.poster_url
            elif method_name.startswith("tvdb_list"):
                description, poster = self.config.TVDb.get_list_description(values[0])
                if description:
                    self.summaries[method_name] = description
                if poster:
                    self.posters[method_name] = poster
        for value in values:
            self.builders.append((method_name[:-8] if method_name.endswith("_details") else method_name, value))

    def _filters(self, method_name, method_data):
        for dict_data in util.parse(self.Type, method_name, method_data, datatype="listdict"):
            dict_methods = {dm.lower(): dm for dm in dict_data}
            current_filters = []
            validate = True
            if "validate" in dict_methods:
                if dict_data[dict_methods["validate"]] is None:
                    raise Failed(f"{self.Type} Error: validate filter attribute is blank")
                if not isinstance(dict_data[dict_methods["validate"]], bool):
                    raise Failed(f"{self.Type} Error: validate filter attribute must be either true or false")
                validate = dict_data.pop(dict_methods["validate"])
            for filter_method, filter_data in dict_data.items():
                filter_attr, modifier, filter_final = self.library.split(filter_method)
                message = None
                if filter_final not in all_filters:
                    message = f"{self.Type} Error: {filter_final} is not a valid filter attribute"
                elif self.builder_level in filters and filter_attr not in filters[self.builder_level]:
                    message = f"{self.Type} Error: {filter_final} is not a valid {self.builder_level} filter attribute"
                elif filter_final is None:
                    message = f"{self.Type} Error: {filter_final} filter attribute is blank"
                else:
                    try:
                        final_data = self.validate_attribute(filter_attr, modifier, f"{filter_final} filter", filter_data, validate)
                    except FilterFailed as e:
                        raise Failed(e)
                    if self.builder_level in ["show", "season", "artist", "album"] and filter_attr in sub_filters:
                        current_filters.append(("episodes" if self.builder_level in ["show", "season"] else "tracks", {filter_final: final_data, "percentage": self.default_percent}))
                    else:
                        current_filters.append((filter_final, final_data))
                if message:
                    if validate:
                        raise Failed(message)
                    else:
                        logger.error(message)
            if current_filters:
                self.filters.append(current_filters)
        self.has_tmdb_filters = any([k in tmdb_filters for f in self.filters for k, v in f])
        self.has_imdb_filters = any([k in imdb_filters for f in self.filters for k, v in f])

    def gather_ids(self, method, value):
        expired = None
        list_key = None
        if self.config.Cache and self.details["cache_builders"]:
            list_key, expired = self.config.Cache.query_list_cache(f"{self.library.type}:{method}", str(value), self.details["cache_builders"])
            if list_key and expired is False:
                logger.info(f"Builder: {method} loaded from Cache")
                return self.config.Cache.query_list_ids(list_key)
        if "plex" in method:
            ids = self.library.get_rating_keys(method, value, self.playlist)
        elif "tautulli" in method:
            ids = self.library.Tautulli.get_rating_keys(value, self.playlist)
        elif "anidb" in method:
            anidb_ids = self.config.AniDB.get_anidb_ids(method, value)
            ids = self.config.Convert.anidb_to_ids(anidb_ids, self.library)
        elif "anilist" in method:
            anilist_ids = self.config.AniList.get_anilist_ids(method, value)
            ids = self.config.Convert.anilist_to_ids(anilist_ids, self.library)
        elif "mal" in method:
            mal_ids = self.config.MyAnimeList.get_mal_ids(method, value)
            ids = self.config.Convert.myanimelist_to_ids(mal_ids, self.library)
        elif "tvdb" in method:
            ids = self.config.TVDb.get_tvdb_ids(method, value)
        elif "imdb" in method:
            ids = self.config.IMDb.get_imdb_ids(method, value, self.language)
        elif "flixpatrol" in method:
            ids = self.config.FlixPatrol.get_tmdb_ids(method, value, self.language, self.library.is_movie)
        elif "icheckmovies" in method:
            ids = self.config.ICheckMovies.get_imdb_ids(method, value, self.language)
        elif "letterboxd" in method:
            ids = self.config.Letterboxd.get_tmdb_ids(method, value, self.language)
        elif "reciperr" in method or "stevenlu" in method:
            ids = self.config.Reciperr.get_imdb_ids(method, value)
        elif "mdblist" in method:
            ids = self.config.Mdblist.get_tmdb_ids(method, value, self.library.is_movie if not self.playlist else None)
        elif "tmdb" in method:
            ids = self.config.TMDb.get_tmdb_ids(method, value, self.library.is_movie, self.tmdb_region)
        elif "trakt" in method:
            ids = self.config.Trakt.get_trakt_ids(method, value, self.library.is_movie)
        elif "radarr" in method:
            ids = self.library.Radarr.get_tmdb_ids(method, value)
        elif "sonarr" in method:
            ids = self.library.Sonarr.get_tvdb_ids(method, value)
        else:
            ids = []
            logger.error(f"{self.Type} Error: {method} method not supported")
        if self.config.Cache and self.details["cache_builders"] and ids:
            if list_key:
                self.config.Cache.delete_list_ids(list_key)
            list_key = self.config.Cache.update_list_cache(f"{self.library.type}:{method}", str(value), expired, self.details["cache_builders"])
            self.config.Cache.update_list_ids(list_key, ids)
        return ids

    def filter_and_save_items(self, ids):
        items = []
        if len(ids) > 0:
            total_ids = len(ids)
            logger.debug("")
            logger.debug(f"{total_ids} IDs Found")
            logger.trace(f"IDs: {ids}")
            logger.debug("")
            for i, input_data in enumerate(ids, 1):
                input_id, id_type = input_data
                logger.ghost(f"Parsing ID {i}/{total_ids}")
                rating_keys = []
                if id_type == "ratingKey":
                    rating_keys = int(input_id)
                elif id_type == "imdb":
                    if input_id not in self.ignore_imdb_ids:
                        found = False
                        for pl_library in self.libraries:
                            if input_id in pl_library.imdb_map:
                                found = True
                                rating_keys = pl_library.imdb_map[input_id]
                                break
                        if not found and (self.builder_level == "episode" or self.playlist or self.do_missing):
                            try:
                                _id, tmdb_type = self.config.Convert.imdb_to_tmdb(input_id, fail=True)
                                if tmdb_type == "episode" and (self.builder_level == "episode" or self.playlist):
                                    try:
                                        tmdb_id, season_num, episode_num = _id.split("_")
                                        tvdb_id = self.config.Convert.tmdb_to_tvdb(tmdb_id, fail=True)
                                        tvdb_id = int(tvdb_id)
                                    except Failed as e:
                                        try:
                                            if not self.config.OMDb:
                                                raise Failed("")
                                            if self.config.OMDb.limit:
                                                raise Failed(" and OMDb limit reached.")
                                            omdb_item = self.config.OMDb.get_omdb(input_id)
                                            tvdb_id = omdb_item.series_id
                                            season_num = omdb_item.season_num
                                            episode_num = omdb_item.episode_num
                                            if not tvdb_id or not season_num or not episode_num:
                                                raise Failed(f" and OMDb metadata lookup Failed for IMDb ID: {input_id}")
                                        except Failed as ee:
                                            logger.error(f"{e}{ee}")
                                            continue
                                    for pl_library in self.libraries:
                                        if tvdb_id in pl_library.show_map:
                                            found = True
                                            show_item = pl_library.fetch_item(pl_library.show_map[tvdb_id][0])
                                            try:
                                                items.append(show_item.episode(season=int(season_num), episode=int(episode_num)))
                                            except NotFound:
                                                self.missing_parts.append(f"{show_item.title} Season: {season_num} Episode: {episode_num} Missing")
                                            break
                                    if not found and tvdb_id not in self.missing_shows and self.do_missing:
                                        self.missing_shows.append(tvdb_id)
                                elif tmdb_type == "movie" and self.do_missing and _id not in self.missing_movies:
                                    self.missing_movies.append(_id)
                                elif tmdb_type in ["show", "episode"] and self.do_missing:
                                    if tmdb_type == "episode":
                                        tmdb_id, _, _ = _id.split("_")
                                    else:
                                        tmdb_id = _id
                                    tvdb_id = self.config.Convert.tmdb_to_tvdb(tmdb_id, fail=True)
                                    if tvdb_id not in self.missing_shows:
                                        self.missing_shows.append(tvdb_id)
                            except Failed as e:
                                logger.warning(e)
                                continue
                elif id_type == "tmdb" and not self.parts_collection:
                    input_id = int(input_id)
                    if input_id not in self.ignore_ids:
                        found = False
                        for pl_library in self.libraries:
                            if input_id in pl_library.movie_map:
                                found = True
                                rating_keys = pl_library.movie_map[input_id]
                                break
                        if not found and input_id not in self.missing_movies:
                            self.missing_movies.append(input_id)
                elif id_type == "tvdb_season" and (self.builder_level == "season" or self.playlist):
                    tvdb_id, season_num = input_id.split("_")
                    tvdb_id = int(tvdb_id)
                    found = False
                    for pl_library in self.libraries:
                        if tvdb_id in pl_library.show_map:
                            found = True
                            show_item = pl_library.fetch_item(pl_library.show_map[tvdb_id][0])
                            try:
                                season_obj = show_item.season(season=int(season_num))
                                if self.playlist:
                                    items.extend(season_obj.episodes())
                                else:
                                    items.append(season_obj)
                            except NotFound:
                                self.missing_parts.append(f"{show_item.title} Season: {season_num} Missing")
                            break
                    if not found and tvdb_id not in self.missing_shows:
                        self.missing_shows.append(tvdb_id)
                elif id_type == "tvdb_episode" and (self.builder_level == "episode" or self.playlist):
                    tvdb_id, season_num, episode_num = input_id.split("_")
                    tvdb_id = int(tvdb_id)
                    found = False
                    for pl_library in self.libraries:
                        if tvdb_id in pl_library.show_map:
                            found = True
                            show_item = pl_library.fetch_item(pl_library.show_map[tvdb_id][0])
                            try:
                                items.append(show_item.episode(season=int(season_num), episode=int(episode_num)))
                            except NotFound:
                                self.missing_parts.append(f"{show_item.title} Season: {season_num} Episode: {episode_num} Missing")
                    if not found and tvdb_id not in self.missing_shows and self.do_missing:
                        self.missing_shows.append(tvdb_id)
                elif id_type in ["tvdb", "tmdb_show", "tvdb_season", "tvdb_episode"]:
                    tvdb_season = None
                    if id_type == "tmdb_show":
                        try:
                            tvdb_id = self.config.Convert.tmdb_to_tvdb(input_id, fail=True)
                        except Failed as e:
                            logger.warning(e)
                            continue
                    elif id_type == "tvdb_season":
                        tvdb_id, tvdb_season = input_id.split("_")
                        tvdb_id = int(tvdb_id)
                        tvdb_season = int(tvdb_season)
                    elif id_type == "tvdb_episode":
                        tvdb_id, _, _ = input_id.split("_")
                        tvdb_id = int(tvdb_id)
                    else:
                        tvdb_id = int(input_id)
                    if tvdb_id not in self.ignore_ids:
                        found_keys = None
                        for pl_library in self.libraries:
                            if tvdb_id in pl_library.show_map:
                                found_keys = pl_library.show_map[tvdb_id]
                                break
                        if not found_keys and tvdb_id not in self.missing_shows:
                            self.missing_shows.append(tvdb_id)
                        if found_keys:
                            if self.parts_collection:
                                rating_keys = []
                                for rk in found_keys:
                                    try:
                                        item = self.library.fetch_item(rk)
                                        if self.builder_level == "episode" and isinstance(item, Show):
                                            if tvdb_season is not None:
                                                item = item.season(season=tvdb_season)
                                            rating_keys.extend([k.ratingKey for k in item.episodes()])
                                        elif self.builder_level == "season" and isinstance(item, Show):
                                            rating_keys.extend([k.ratingKey for k in item.seasons()])
                                    except Failed as e:
                                        logger.error(e)
                            else:
                                rating_keys = found_keys
                else:
                    continue

                if not isinstance(rating_keys, list):
                    rating_keys = [rating_keys]
                for rk in rating_keys:
                    try:
                        item = self.library.fetch_item(rk)
                        if self.playlist and isinstance(item, (Show, Season)):
                            items.extend(item.episodes())
                        elif self.builder_level == "movie" and not isinstance(item, Movie):
                            logger.info(f"Item: {item} is not an Movie")
                        elif self.builder_level == "show" and not isinstance(item, Show):
                            logger.info(f"Item: {item} is not an Show")
                        elif self.builder_level == "episode" and not isinstance(item, Episode):
                            logger.info(f"Item: {item} is not an Episode")
                        elif self.builder_level == "season" and not isinstance(item, Season):
                            logger.info(f"Item: {item} is not a Season")
                        elif self.builder_level == "artist" and not isinstance(item, Artist):
                            logger.info(f"Item: {item} is not an Artist")
                        elif self.builder_level == "album" and not isinstance(item, Album):
                            logger.info(f"Item: {item} is not an Album")
                        elif self.builder_level == "track" and not isinstance(item, Track):
                            logger.info(f"Item: {item} is not a Track")
                        else:
                            items.append(item)
                    except Failed as e:
                        logger.error(e)
            logger.exorcise()
        if not items:
            return None
        name = self.obj.title if self.obj else self.name
        total = len(items)
        max_length = len(str(total))
        if self.filters and self.details["show_filtered"] is True:
            logger.info("")
            logger.info("Filtering Builders:")
        filtered_items = []
        for i, item in enumerate(items, 1):
            if not isinstance(item, (Movie, Show, Season, Episode, Artist, Album, Track)):
                logger.error(f"{self.Type} Error: Item: {item} is an invalid type")
                continue
            if item not in self.found_items:
                if item.ratingKey in self.filtered_keys:
                    if self.details["show_filtered"] is True:
                        logger.info(f"{name} {self.Type} | X | {self.filtered_keys[item.ratingKey]}")
                else:
                    current_title = util.item_title(item)
                    if self.check_filters(item, f"{(' ' * (max_length - len(str(i))))}{i}/{total}"):
                        self.found_items.append(item)
                    else:
                        filtered_items.append(item)
                        self.filtered_keys[item.ratingKey] = current_title
                        if self.details["show_filtered"] is True:
                            logger.info(f"{name} {self.Type} | X | {current_title}")
        if self.do_report and filtered_items:
            self.library.add_filtered(self.name, [(i.title, self.library.get_id_from_maps(i.ratingKey)) for i in filtered_items], self.library.is_movie)

    def build_filter(self, method, plex_filter, display=False, default_sort=None):
        if display:
            logger.info("")
            logger.info(f"Validating Method: {method}")
        if plex_filter is None:
            raise Failed(f"{self.Type} Error: {method} attribute is blank")
        if not isinstance(plex_filter, dict):
            raise Failed(f"{self.Type} Error: {method} must be a dictionary: {plex_filter}")
        if display:
            logger.debug(f"Value: {plex_filter}")

        filter_alias = {m.lower(): m for m in plex_filter}

        if "any" in filter_alias and "all" in filter_alias:
            raise Failed(f"{self.Type} Error: Cannot have more then one base")

        if self.builder_level == "item":
            if "type" in filter_alias:
                if plex_filter[filter_alias["type"]] is None:
                    raise Failed(f"{self.Type} Error: type attribute is blank")
                if plex_filter[filter_alias["type"]] not in plex.sort_types:
                    raise Failed(f"{self.Type} Error: type: {plex_filter[filter_alias['type']]} is invalid. Options: {', '.join(plex.sort_types)}")
                sort_type = plex_filter[filter_alias["type"]]
            elif self.library.is_show:
                sort_type = "show"
            elif self.library.is_music:
                sort_type = "artist"
            else:
                sort_type = "movie"
        else:
            sort_type = self.builder_level

        ms = method.split("_")
        filter_details = f"{ms[0].capitalize()} {sort_type.capitalize()} {ms[1].capitalize()}\n"
        type_default_sort, type_key, sorts = plex.sort_types[sort_type]

        sort = []
        if "sort_by" in filter_alias:
            test_sorts = plex_filter[filter_alias["sort_by"]]
            if test_sorts is None:
                raise Failed(f"{self.Type} Error: sort_by attribute is blank")
            if not isinstance(test_sorts, list):
                test_sorts = [test_sorts]
            for test_sort in test_sorts:
                if test_sort not in sorts:
                    raise Failed(f"{self.Type} Error: sort_by: {test_sort} is invalid. Options: {', '.join(sorts)}")
                sort.append(test_sort)
        if not sort:
            sort.append(default_sort if default_sort else type_default_sort)
        filter_details += f"Sort By: {sort}\n"

        limit = None
        if "limit" in filter_alias:
            if plex_filter[filter_alias["limit"]] is None:
                raise Failed(f"{self.Type} Error: limit attribute is blank")
            elif str(plex_filter[filter_alias["limit"]]).lower() == "all":
                filter_details += "Limit: all\n"
            else:
                try:
                    if int(plex_filter[filter_alias["limit"]]) < 1:
                        raise ValueError
                    else:
                        limit = int(plex_filter[filter_alias["limit"]])
                        filter_details += f"Limit: {limit}\n"
                except ValueError:
                    raise Failed(f"{self.Type} Error: limit attribute must be an integer greater than 0")

        validate = True
        if "validate" in filter_alias:
            if plex_filter[filter_alias["validate"]] is None:
                raise Failed(f"{self.Type} Error: validate attribute is blank")
            if not isinstance(plex_filter[filter_alias["validate"]], bool):
                raise Failed(f"{self.Type} Error: validate attribute must be either true or false")
            validate = plex_filter[filter_alias["validate"]]
            filter_details += f"Validate: {validate}\n"

        def _filter(filter_dict, is_all=True, level=1):
            output = ""
            display_out = f"\n{'  ' * level}Match {'all' if is_all else 'any'} of the following:"
            level += 1
            indent = f"\n{'  ' * level}"
            conjunction = f"{'and' if is_all else 'or'}=1&"
            for _key, _data in filter_dict.items():
                attr, modifier, final_attr = self.library.split(_key)

                def build_url_arg(arg, mod=None, arg_s=None, mod_s=None):
                    arg_key = plex.search_translation[attr] if attr in plex.search_translation else attr
                    arg_key = plex.show_translation[arg_key] if self.library.is_show and arg_key in plex.show_translation else arg_key
                    if mod is None:
                        mod = plex.modifier_translation[modifier] if modifier in plex.modifier_translation else modifier
                    if arg_s is None:
                        arg_s = arg
                    if attr in plex.string_attributes and modifier in ["", ".not"]:
                        mod_s = "does not contain" if modifier == ".not" else "contains"
                    elif mod_s is None:
                        mod_s = util.mod_displays[modifier]
                    param_s = plex.search_display[attr] if attr in plex.search_display else attr.title().replace('_', ' ')
                    display_line = f"{indent}{param_s} {mod_s} {arg_s}"
                    return f"{arg_key}{mod}={arg}&", display_line

                error = None
                if final_attr not in plex.searches and not final_attr.startswith(("any", "all")):
                    error = f"{self.Type} Error: {final_attr} is not a valid {method} attribute"
                elif self.library.is_show and final_attr in plex.movie_only_searches:
                    error = f"{self.Type} Error: {final_attr} {method} attribute only works for movie libraries"
                elif self.library.is_movie and final_attr in plex.show_only_searches:
                    error = f"{self.Type} Error: {final_attr} {method} attribute only works for show libraries"
                elif self.library.is_music and final_attr not in plex.music_searches + ["all", "any"]:
                    error = f"{self.Type} Error: {final_attr} {method} attribute does not work for music libraries"
                elif not self.library.is_music and final_attr in plex.music_searches:
                    error = f"{self.Type} Error: {final_attr} {method} attribute only works for music libraries"
                elif _data is not False and _data != 0 and not _data:
                    error = f"{self.Type} Error: {final_attr} {method} attribute is blank"
                else:
                    if final_attr.startswith(("any", "all")):
                        dicts = util.get_list(_data)
                        results = ""
                        display_add = ""
                        for dict_data in dicts:
                            if not isinstance(dict_data, dict):
                                raise Failed(f"{self.Type} Error: {attr} must be either a dictionary or list of dictionaries")
                            inside_filter, inside_display = _filter(dict_data, is_all=attr == "all", level=level)
                            if len(inside_filter) > 0:
                                display_add += inside_display
                                results += f"{conjunction if len(results) > 0 else ''}push=1&{inside_filter}pop=1&"
                    else:
                        validation = self.validate_attribute(attr, modifier, final_attr, _data, validate, plex_search=True)
                        if validation is not False and validation != 0 and not validation:
                            continue
                        elif attr in plex.date_attributes and modifier in ["", ".not"]:
                            last_text = "is not in the last" if modifier == ".not" else "is in the last"
                            last_mod = "%3E%3E" if modifier == "" else "%3C%3C"
                            search_mod = validation[-1]
                            if search_mod == "o":
                                validation = f"{validation[:-1]}mon"
                            results, display_add = build_url_arg(f"-{validation}", mod=last_mod, arg_s=f"{validation} {plex.date_sub_mods[search_mod]}", mod_s=last_text)
                        elif attr == "duration" and modifier in [".gt", ".gte", ".lt", ".lte"]:
                            results, display_add = build_url_arg(validation * 60000)
                        elif modifier == ".rated":
                            results, display_add = build_url_arg(-1, mod="!" if validation else "", arg_s="Rated", mod_s="is" if validation else "is not")
                        elif attr in plex.boolean_attributes:
                            bool_mod = "" if validation else "!"
                            bool_arg = "true" if validation else "false"
                            results, display_add = build_url_arg(1, mod=bool_mod, arg_s=bool_arg, mod_s="is")
                        elif (attr in plex.tag_attributes + plex.string_attributes + plex.year_attributes) and modifier in ["", ".is", ".isnot", ".not", ".begins", ".ends", ".regex"]:
                            results = ""
                            display_add = ""
                            for og_value, result in validation:
                                built_arg = build_url_arg(quote(str(result)) if attr in plex.string_attributes else result, arg_s=og_value)
                                display_add += built_arg[1]
                                results += f"{conjunction if len(results) > 0 else ''}{built_arg[0]}"
                        else:
                            results, display_add = build_url_arg(validation)
                    display_out += display_add
                    output += f"{conjunction if len(output) > 0 else ''}{results}"
                if error:
                    if validate:
                        raise Failed(error)
                    else:
                        logger.error(error)
                        continue
            return output, display_out

        if "any" not in filter_alias and "all" not in filter_alias:
            base_dict = {}
            any_dicts = []
            for alias_key, alias_value in filter_alias.items():
                _, _, final = self.library.split(alias_key)
                if final in plex.and_searches:
                    base_dict[alias_value[:-4]] = plex_filter[alias_value]
                elif final in plex.or_searches:
                    any_dicts.append({alias_value: plex_filter[alias_value]})
                elif final in plex.searches:
                    base_dict[alias_value] = plex_filter[alias_value]
            if len(any_dicts) > 0:
                base_dict["any"] = any_dicts
            base_all = True
            if len(base_dict) == 0:
                raise Failed(f"{self.Type} Error: Must have either any or all as a base for {method}")
        else:
            base = "all" if "all" in filter_alias else "any"
            base_all = base == "all"
            if plex_filter[filter_alias[base]] is None:
                raise Failed(f"{self.Type} Error: {base} attribute is blank")
            if not isinstance(plex_filter[filter_alias[base]], dict):
                raise Failed(f"{self.Type} Error: {base} must be a dictionary: {plex_filter[filter_alias[base]]}")
            base_dict = plex_filter[filter_alias[base]]
        built_filter, filter_text = _filter(base_dict, is_all=base_all)
        filter_details = f"{filter_details}Filter:{filter_text}"
        if len(built_filter) > 0:
            final_filter = built_filter[:-1] if base_all else f"push=1&{built_filter}pop=1"
            filter_url = f"?type={type_key}&{f'limit={limit}&' if limit else ''}sort={'%2C'.join([sorts[s] for s in sort])}&{final_filter}"
        else:
            raise FilterFailed(f"{self.Type} Error: No Plex Filter Created")

        if display:
            logger.debug(f"Smart URL: {filter_url}")
        return type_key, filter_details, filter_url

    def validate_attribute(self, attribute, modifier, final, data, validate, plex_search=False):
        def smart_pair(list_to_pair):
            return [(t, t) for t in list_to_pair] if plex_search else list_to_pair
        if attribute in tag_attributes and modifier in [".regex"]:
            _, names = self.library.get_search_choices(attribute, title=not plex_search, name_pairs=True)
            valid_list = []
            used = []
            for reg in util.validate_regex(data, self.Type, validate=validate):
                for name, key in names:
                    if name not in used and re.compile(reg).search(name):
                        used.append(name)
                        valid_list.append((name, key) if plex_search else key)
            if not valid_list:
                error = f"Plex Error: {attribute}: No matches found with regex pattern {data}"
                if self.details["show_options"]:
                    error += f"\nOptions: {names}"
                if validate:
                    raise Failed(error)
                else:
                    logger.error(error)
            return valid_list
        elif modifier == ".regex":
            return util.validate_regex(data, self.Type, validate=validate)
        elif attribute in string_attributes and modifier in ["", ".not", ".is", ".isnot", ".begins", ".ends"]:
            return smart_pair(util.get_list(data, split=False))
        elif attribute in year_attributes and modifier in ["", ".not", ".gt", ".gte", ".lt", ".lte"]:
            if modifier in ["", ".not"]:
                final_years = []
                values = util.get_list(data)
                for value in values:
                    if str(value).startswith("current_year"):
                        year_values = str(value).split("-")
                        try:
                            final_years.append(datetime.now().year - (0 if len(year_values) == 1 else int(year_values[1].strip())))
                        except ValueError:
                            raise Failed(f"{self.Type} Error: {final} attribute modifier invalid '{year_values[1]}'")
                    else:
                        final_years.append(util.parse(self.Type, final, value, datatype="int"))
                return smart_pair(final_years)
            else:
                if str(data).startswith("current_year"):
                    year_values = str(data).split("-")
                    try:
                        return datetime.now().year - (0 if len(year_values) == 1 else int(year_values[1].strip()))
                    except ValueError:
                        raise Failed(f"{self.Type} Error: {final} attribute modifier invalid '{year_values[1]}'")
                return util.parse(self.Type, final, data, datatype="int", minimum=0)
        elif (attribute in number_attributes and modifier in ["", ".not", ".gt", ".gte", ".lt", ".lte"]) \
                or (attribute in tag_attributes and modifier in [".count_gt", ".count_gte", ".count_lt", ".count_lte"]):
            return util.parse(self.Type, final, data, datatype="int", minimum=0)
        elif attribute == "origin_country":
            return util.get_list(data, upper=True)
        elif attribute in ["original_language", "tmdb_keyword"]:
            return util.get_list(data, lower=True)
        elif attribute in ["tmdb_genre"]:
            return util.get_list(data)
        elif attribute == "history":
            try:
                return util.parse(self.Type, final, data, datatype="int", maximum=30)
            except Failed:
                if str(data).lower() in ["day", "month"]:
                    return data.lower()
                else:
                    raise Failed(f"{self.Type} Error: history attribute invalid: {data} must be a number between 1-30, day, or month")
        elif attribute == "tmdb_type":
            return util.parse(self.Type, final, data, datatype="commalist", options=[v for k, v in tmdb.discover_types.items()])
        elif attribute == "tmdb_status":
            return util.parse(self.Type, final, data, datatype="commalist", options=[v for k, v in tmdb.discover_status.items()])
        elif attribute == "imdb_keyword":
            new_dictionary = {"minimum_votes": 0, "minimum_relevant": 0, "minimum_percentage": 0}
            if isinstance(data, dict) and "keyword" not in data:
                raise Failed(f"{self.Type} Error: imdb_keyword requires the keyword attribute")
            elif isinstance(data, dict):
                dict_methods = {dm.lower(): dm for dm in data}
                new_dictionary["keywords"] = util.parse(self.Type, "keyword", data, methods=dict_methods, parent=attribute, datatype="lowerlist")
                new_dictionary["minimum_votes"] = util.parse(self.Type, "minimum_votes", data, methods=dict_methods, parent=attribute, datatype="int", minimum=0)
                new_dictionary["minimum_relevant"] = util.parse(self.Type, "minimum_relevant", data, methods=dict_methods, parent=attribute, datatype="int", minimum=0)
                new_dictionary["minimum_percentage"] = util.parse(self.Type, "minimum_percentage", data, methods=dict_methods, parent=attribute, datatype="int", minimum=0, maximum=100)
            else:
                new_dictionary["keywords"] = util.parse(self.Type, final, data, datatype="lowerlist")
            return new_dictionary
        elif attribute in tag_attributes and modifier in ["", ".not"]:
            if attribute in plex.tmdb_attributes:
                final_values = []
                for value in util.get_list(data):
                    if value.lower() == "tmdb" and "tmdb_person" in self.details:
                        for name in self.details["tmdb_person"]:
                            final_values.append(name)
                    else:
                        final_values.append(value)
            else:
                final_values = util.get_list(data, trim=False)
            search_choices, names = self.library.get_search_choices(attribute, title=not plex_search)
            valid_list = []
            for fvalue in final_values:
                if str(fvalue) in search_choices or str(fvalue).lower() in search_choices:
                    valid_value = search_choices[str(fvalue) if str(fvalue) in search_choices else str(fvalue).lower()]
                    valid_list.append((fvalue, valid_value) if plex_search else valid_value)
                else:
                    actor_id = None
                    if attribute in ["actor", "director", "producer", "writer"]:
                        actor_id = self.library.get_actor_id(fvalue)
                        if actor_id:
                            if plex_search:
                                valid_list.append((fvalue, actor_id))
                            else:
                                valid_list.append(actor_id)
                    if not actor_id:
                        error = f"Plex Error: {attribute}: {fvalue} not found"
                        if self.details["show_options"]:
                            error += f"\nOptions: {names}"
                        if validate:
                            raise FilterFailed(error)
                        elif not self.ignore_blank_results:
                            logger.error(error)
            return valid_list
        elif attribute in date_attributes and modifier in [".before", ".after"]:
            if data == "today":
                return datetime.strftime(datetime.now(), "%Y-%m-%d")
            else:
                return util.validate_date(data, final, return_as="%Y-%m-%d")
        elif attribute in date_attributes and modifier in ["", ".not"]:
            search_mod = "d"
            if plex_search and data and str(data)[-1] in ["s", "m", "h", "d", "w", "o", "y"]:
                search_mod = str(data)[-1]
                data = str(data)[:-1]
            search_data = util.parse(self.Type, final, data, datatype="int", minimum=0)
            return f"{search_data}{search_mod}" if plex_search else search_data
        elif attribute in float_attributes and modifier in ["", ".not", ".gt", ".gte", ".lt", ".lte"]:
            return util.parse(self.Type, final, data, datatype="float", minimum=0, maximum=None if attribute == "duration" else 10)
        elif attribute in boolean_attributes or (attribute in float_attributes and modifier in [".rated"]):
            return util.parse(self.Type, attribute, data, datatype="bool")
        elif attribute in ["seasons", "episodes", "albums", "tracks"]:
            if isinstance(data, dict) and data:
                percentage = self.default_percent
                if "percentage" in data:
                    if data["percentage"] is None:
                        logger.warning(f"{self.Type} Warning: percentage filter attribute is blank using {self.default_percent} as default")
                    else:
                        maybe = util.check_num(data["percentage"])
                        if maybe < 0 or maybe > 100:
                            logger.warning(f"{self.Type} Warning: percentage filter attribute must be a number 0-100 using {self.default_percent} as default")
                        else:
                            percentage = maybe
                final_filters = {"percentage": percentage}
                for filter_method, filter_data in data.items():
                    filter_attr, filter_modifier, filter_final = self.library.split(filter_method)
                    message = None
                    if filter_final == "percentage":
                        continue
                    if filter_final not in all_filters:
                        message = f"{self.Type} Error: {filter_final} is not a valid filter attribute"
                    elif filter_attr not in filters[attribute[:-1]] or filter_attr in ["seasons", "episodes", "albums", "tracks"]:
                        message = f"{self.Type} Error: {filter_final} is not a valid {attribute[:-1]} filter attribute"
                    elif filter_final is None:
                        message = f"{self.Type} Error: {filter_final} filter attribute is blank"
                    else:
                        final_filters[filter_final] = self.validate_attribute(filter_attr, filter_modifier, f"{attribute} {filter_final} filter", filter_data, validate)
                    if message:
                        if validate:
                            raise Failed(message)
                        else:
                            logger.error(message)
                if not final_filters:
                    raise Failed(f"{self.Type} Error: no filters found under {attribute}")
                return final_filters
            else:
                raise Failed(f"{self.Type} Error: {final} attribute must be a dictionary")
        else:
            raise Failed(f"{self.Type} Error: {final} attribute not supported")

    def add_to_collection(self):
        logger.info("")
        logger.separator(f"Adding to {self.name} {self.Type}", space=False, border=False)
        logger.info("")
        name, collection_items = self.library.get_collection_name_and_items(self.obj if self.obj else self.name, self.smart_label_collection)
        total = self.limit if self.limit and len(self.found_items) > self.limit else len(self.found_items)
        spacing = len(str(total)) * 2 + 1
        amount_added = 0
        amount_unchanged = 0
        items_added = []
        for i, item in enumerate(self.found_items, 1):
            if self.limit and amount_added + self.beginning_count - len([r for _, r in self.remove_item_map.items() if r is not None]) >= self.limit:
                logger.info(f"{self.Type} Limit reached")
                self.found_items = self.found_items[:i - 1]
                break
            current_operation = "=" if item in collection_items else "+"
            number_text = f"{i}/{total}"
            logger.info(f"{number_text:>{spacing}} | {name} {self.Type} | {current_operation} | {util.item_title(item)}")
            if item in collection_items:
                self.remove_item_map[item.ratingKey] = None
                amount_unchanged += 1
            else:
                items_added.append(item)
                if not self.playlist:
                    self.library.alter_collection(item, name, smart_label_collection=self.smart_label_collection)
                amount_added += 1
                if self.details["changes_webhooks"]:
                    self.notification_additions.append(util.item_set(item, self.library.get_id_from_maps(item.ratingKey)))
        if self.playlist and items_added and not self.obj:
            self.obj = self.library.create_playlist(self.name, items_added)
            logger.info("")
            logger.info(f"Playlist: {self.name} created")
        elif self.playlist and items_added:
            self.obj.addItems(items_added)
        if self.do_report and items_added:
            self.library.add_additions(self.name, [(i.title, self.library.get_id_from_maps(i.ratingKey)) for i in items_added], self.library.is_movie)
        logger.exorcise()
        logger.info("")
        item_label = f"{self.builder_level.capitalize()}{'s' if total > 1 else ''}"
        logger.info(f"{total} {item_label} Processed {amount_added} {item_label} Added")
        return amount_added, amount_unchanged

    def sync_collection(self):
        amount_removed = 0
        items_removed = []
        items = [item for _, item in self.remove_item_map.items() if item is not None]
        if items:
            logger.info("")
            logger.separator(f"Removed from {self.name} {self.Type}", space=False, border=False)
            logger.info("")
            total = len(items)
            spacing = len(str(total)) * 2 + 1
            for i, item in enumerate(items, 1):
                number_text = f"{i}/{total}"
                logger.info(f"{number_text:>{spacing}} | {self.name} {self.Type} | - | {util.item_title(item)}")
                items_removed.append(item)
                if not self.playlist:
                    self.library.alter_collection(item, self.name, smart_label_collection=self.smart_label_collection, add=False)
                amount_removed += 1
                if self.details["changes_webhooks"]:
                    self.notification_removals.append(util.item_set(item, self.library.get_id_from_maps(item.ratingKey)))
            if self.playlist and items_removed:
                self.obj.reload()
                self.obj.removeItems(items_removed)
            if self.do_report and items_removed:
                self.library.add_removed(self.name, [(i.title, self.library.get_id_from_maps(i.ratingKey)) for i in items_removed], self.library.is_movie)
            logger.info("")
            logger.info(f"{amount_removed} {self.builder_level.capitalize()}{'s' if amount_removed == 1 else ''} Removed")
        return amount_removed

    def check_tmdb_filters(self, tmdb_item, filters_in, is_movie):
        for filter_method, filter_data in filters_in:
            filter_attr, modifier, filter_final = self.library.split(filter_method)
            if self.config.TMDb.item_filter(tmdb_item, filter_attr, modifier, filter_final, filter_data, is_movie, self.current_time) is False:
                return False
        return True

    def check_imdb_filters(self, imdb_info, filters_in):
        for filter_method, filter_data in filters_in:
            filter_attr, modifier, filter_final = self.library.split(filter_method)
            if self.config.IMDb.item_filter(imdb_info, filter_attr, modifier, filter_final, filter_data) is False:
                return False
        return True

    def check_missing_filters(self, item_id, is_movie, tmdb_item=None, check_released=False):
        imdb_info = None
        if self.has_tmdb_filters or self.has_imdb_filters or check_released:
            try:
                if tmdb_item is None:
                    if is_movie:
                        tmdb_item = self.config.TMDb.get_movie(item_id, ignore_cache=True)
                    else:
                        tmdb_item = self.config.TMDb.get_show(self.config.Convert.tvdb_to_tmdb(item_id, fail=True), ignore_cache=True)
            except Failed:
                return False
            if self.has_imdb_filters and tmdb_item and tmdb_item.imdb_id:
                try:
                    imdb_info = self.config.IMDb.keywords(tmdb_item.imdb_id)
                except Failed as e:
                    logger.error(e)
                    return False
        if check_released:
            date_to_check = tmdb_item.release_date if is_movie else tmdb_item.first_air_date
            if not date_to_check or date_to_check > self.current_time:
                return False
        final_return = True
        if self.has_tmdb_filters or self.has_imdb_filters:
            final_return = False
            for filter_list in self.filters:
                tmdb_f = []
                imdb_f = []
                for k, v in filter_list:
                    if k.split(".")[0] in tmdb_filters:
                        tmdb_f.append((k, v))
                    elif k.split(".")[0] in imdb_filters:
                        imdb_f.append((k, v))
                or_result = True
                if tmdb_f:
                    if not tmdb_item or self.check_tmdb_filters(tmdb_item, tmdb_f, is_movie) is False:
                        or_result = False
                if imdb_f:
                    if not imdb_info and self.check_imdb_filters(imdb_info, imdb_f) is False:
                        or_result = False
                if or_result:
                    final_return = True
        return final_return

    def check_filters(self, item, display):
        final_return = True
        if self.filters and not self.details["only_filter_missing"]:
            logger.ghost(f"Filtering {display} {item.title}")
            item = self.library.reload(item)
            final_return = False
            tmdb_item = None
            imdb_info = None
            for filter_list in self.filters:
                tmdb_f = []
                imdb_f = []
                plex_f = []
                for k, v in filter_list:
                    if k.split(".")[0] in tmdb_filters:
                        tmdb_f.append((k, v))
                    elif k.split(".")[0] in imdb_filters:
                        imdb_f.append((k, v))
                    else:
                        plex_f.append((k, v))
                or_result = True
                if tmdb_f:
                    if not tmdb_item and isinstance(item, (Movie, Show)):
                        if item.ratingKey not in self.library.movie_rating_key_map and item.ratingKey not in self.library.show_rating_key_map:
                            logger.warning(f"Filter Error: No {'TMDb' if self.library.is_movie else 'TVDb'} ID found for {item.title}")
                            or_result = False
                        else:
                            try:
                                if item.ratingKey in self.library.movie_rating_key_map:
                                    tmdb_item = self.config.TMDb.get_movie(self.library.movie_rating_key_map[item.ratingKey], ignore_cache=True)
                                else:
                                    tmdb_item = self.config.TMDb.get_show(self.config.Convert.tvdb_to_tmdb(self.library.show_rating_key_map[item.ratingKey], fail=True), ignore_cache=True)
                            except Failed as e:
                                logger.error(e)
                                or_result = False
                    if not tmdb_item or self.check_tmdb_filters(tmdb_item, tmdb_f, item.ratingKey in self.library.movie_rating_key_map) is False:
                        or_result = False
                if imdb_f:
                    if not imdb_info and isinstance(item, (Movie, Show)):
                        if item.ratingKey not in self.library.imdb_rating_key_map:
                            logger.warning(f"Filter Error: No IMDb ID found for {item.title}")
                            or_result = False
                        else:
                            try:
                                imdb_info = self.config.IMDb.keywords(self.library.imdb_rating_key_map[item.ratingKey])
                            except Failed as e:
                                logger.error(e)
                                or_result = False
                    if not imdb_info or self.check_imdb_filters(imdb_info, imdb_f) is False:
                        or_result = False
                if plex_f and self.library.check_filters(item, plex_f, self.current_time) is False:
                    or_result = False
                if or_result:
                    final_return = True
        return final_return

    def display_filters(self):
        if self.filters:
            for filter_list in self.filters:
                logger.info("")
                for filter_key, filter_value in filter_list:
                    logger.info(f"Collection Filter {filter_key}: {filter_value}")

    def run_missing(self):
        added_to_radarr = 0
        added_to_sonarr = 0
        if len(self.missing_movies) > 0:
            if self.details["show_missing"] is True:
                logger.info("")
                logger.separator(f"Missing Movies from Library: {self.library.name}", space=False, border=False)
                logger.info("")
            missing_movies_with_names = []
            filtered_movies_with_names = []
            for missing_id in self.missing_movies:
                try:
                    movie = self.config.TMDb.get_movie(missing_id)
                except Failed as e:
                    logger.error(e)
                    continue
                current_title = f"{movie.title} ({movie.release_date.year})" if movie.release_date else movie.title
                if self.check_missing_filters(missing_id, True, tmdb_item=movie, check_released=self.details["missing_only_released"]):
                    missing_movies_with_names.append((current_title, missing_id))
                    if self.details["show_missing"] is True:
                        logger.info(f"{self.name} {self.Type} | ? | {current_title} (TMDb: {missing_id})")
                else:
                    filtered_movies_with_names.append((current_title, missing_id))
                    if self.details["show_filtered"] is True and self.details["show_missing"] is True:
                        logger.info(f"{self.name} {self.Type} | X | {current_title} (TMDb: {missing_id})")
            logger.info("")
            logger.info(f"{len(missing_movies_with_names)} Movie{'s' if len(missing_movies_with_names) > 1 else ''} Missing")
            if len(missing_movies_with_names) > 0:
                if self.do_report:
                    self.library.add_missing(self.name, missing_movies_with_names, True)
                if self.run_again or (self.library.Radarr and (self.radarr_details["add_missing"] or "item_radarr_tag" in self.item_details)):
                    missing_tmdb_ids = [missing_id for title, missing_id in missing_movies_with_names]
                    if self.library.Radarr:
                        if self.radarr_details["add_missing"]:
                            try:
                                added = self.library.Radarr.add_tmdb(missing_tmdb_ids, **self.radarr_details)
                                self.added_to_radarr.extend([{"title": movie.title, "id": movie.tmdbId} for movie in added])
                                added_to_radarr += len(added)
                            except Failed as e:
                                logger.error(e)
                            except ArrException as e:
                                logger.stacktrace()
                                logger.error(f"Arr Error: {e}")
                        if "item_radarr_tag" in self.item_details:
                            try:
                                self.library.Radarr.edit_tags(missing_tmdb_ids, self.item_details["item_radarr_tag"], self.item_details["apply_tags"])
                            except Failed as e:
                                logger.error(e)
                            except ArrException as e:
                                logger.stacktrace()
                                logger.error(f"Arr Error: {e}")
                    if self.run_again:
                        self.run_again_movies.extend(missing_tmdb_ids)
            if len(filtered_movies_with_names) > 0 and self.do_report:
                self.library.add_filtered(self.name, filtered_movies_with_names, True)
        if len(self.missing_shows) > 0 and self.library.is_show:
            if self.details["show_missing"] is True:
                logger.info("")
                logger.separator(f"Missing Shows from Library: {self.name}", space=False, border=False)
                logger.info("")
            missing_shows_with_names = []
            filtered_shows_with_names = []
            for missing_id in self.missing_shows:
                try:
                    title = self.config.TVDb.get_tvdb_obj(missing_id).title
                except Failed as e:
                    logger.error(e)
                    continue
                if self.check_missing_filters(missing_id, False, check_released=self.details["missing_only_released"]):
                    missing_shows_with_names.append((title, missing_id))
                    if self.details["show_missing"] is True:
                        logger.info(f"{self.name} {self.Type} | ? | {title} (TVDb: {missing_id})")
                else:
                    filtered_shows_with_names.append((title, missing_id))
                    if self.details["show_filtered"] is True and self.details["show_missing"] is True:
                        logger.info(f"{self.name} {self.Type} | X | {title} (TVDb: {missing_id})")
            logger.info("")
            logger.info(f"{len(missing_shows_with_names)} Show{'s' if len(missing_shows_with_names) > 1 else ''} Missing")
            if len(missing_shows_with_names) > 0:
                if self.do_report:
                    self.library.add_missing(self.name, missing_shows_with_names, False)
                if self.run_again or (self.library.Sonarr and (self.sonarr_details["add_missing"] or "item_sonarr_tag" in self.item_details)):
                    missing_tvdb_ids = [missing_id for title, missing_id in missing_shows_with_names]
                    if self.library.Sonarr:
                        if self.sonarr_details["add_missing"]:
                            try:
                                added = self.library.Sonarr.add_tvdb(missing_tvdb_ids, **self.sonarr_details)
                                self.added_to_sonarr.extend([{"title": show.title, "id": show.tvdbId} for show in added])
                                added_to_sonarr += len(added)
                            except Failed as e:
                                logger.error(e)
                            except ArrException as e:
                                logger.stacktrace()
                                logger.error(f"Arr Error: {e}")
                        if "item_sonarr_tag" in self.item_details:
                            try:
                                self.library.Sonarr.edit_tags(missing_tvdb_ids, self.item_details["item_sonarr_tag"], self.item_details["apply_tags"])
                            except Failed as e:
                                logger.error(e)
                            except ArrException as e:
                                logger.stacktrace()
                                logger.error(f"Arr Error: {e}")
                    if self.run_again:
                        self.run_again_shows.extend(missing_tvdb_ids)
            if len(filtered_shows_with_names) > 0 and self.do_report:
                self.library.add_filtered(self.name, filtered_shows_with_names, False)
        if len(self.missing_parts) > 0 and self.library.is_show:
            if self.details["show_missing"] is True:
                for missing in self.missing_parts:
                    logger.info(f"{self.name} {self.Type} | ? | {missing}")
            if self.do_report:
                self.library.add_missing(self.name, self.missing_parts, False)
        return added_to_radarr, added_to_sonarr

    def load_collection_items(self):
        if self.build_collection and self.obj:
            self.items = self.library.get_collection_items(self.obj, self.smart_label_collection)
        elif not self.build_collection:
            logger.info("")
            logger.separator(f"Items Found for {self.name} {self.Type}", space=False, border=False)
            logger.info("")
            self.items = self.found_items
        if not self.items:
            raise Failed(f"Plex Error: No {self.Type} items found")

    def update_item_details(self):
        logger.info("")
        logger.separator(f"Updating Details of the Items in {self.name} {self.Type}", space=False, border=False)
        logger.info("")

        add_tags = self.item_details["item_label"] if "item_label" in self.item_details else None
        remove_tags = self.item_details["item_label.remove"] if "item_label.remove" in self.item_details else None
        sync_tags = self.item_details["item_label.sync"] if "item_label.sync" in self.item_details else None

        add_genres = self.item_details["item_genre"] if "item_genre" in self.item_details else None
        remove_genres = self.item_details["item_genre.remove"] if "item_genre.remove" in self.item_details else None
        sync_genres = self.item_details["item_genre.sync"] if "item_genre.sync" in self.item_details else None

        if "non_item_remove_label" in self.item_details:
            rk_compare = [item.ratingKey for item in self.items]
            for non_item in self.library.search(label=self.item_details["non_item_remove_label"], libtype=self.builder_level):
                if non_item.ratingKey not in rk_compare:
                    self.library.edit_tags("label", non_item, remove_tags=self.item_details["non_item_remove_label"])

        tmdb_paths = []
        tvdb_paths = []
        for item in self.items:
            item = self.library.reload(item)
            current_labels = [la.tag for la in self.library.item_labels(item)]
            if "item_assets" in self.item_details and self.asset_directory and "Overlay" not in current_labels:
                self.library.find_and_upload_assets(item, current_labels, asset_directory=self.asset_directory)
            self.library.edit_tags("label", item, add_tags=add_tags, remove_tags=remove_tags, sync_tags=sync_tags)
            self.library.edit_tags("genre", item, add_tags=add_genres, remove_tags=remove_genres, sync_tags=sync_genres)
            if "item_edition" in self.item_details and item.editionTitle != self.item_details["item_edition"]:
                self.library.query_data(item.editEditionTitle, self.item_details["item_edition"])
                logger.info(f"{item.title[:25]:<25} | Edition | {self.item_details['item_edition']}")
            path = os.path.dirname(str(item.locations[0])) if self.library.is_movie else str(item.locations[0])
            if self.library.Radarr and item.ratingKey in self.library.movie_rating_key_map:
                path = path.replace(self.library.Radarr.plex_path, self.library.Radarr.radarr_path)
                path = path[:-1] if path.endswith(('/', '\\')) else path
                tmdb_paths.append((self.library.movie_rating_key_map[item.ratingKey], path))
            if self.library.Sonarr and item.ratingKey in self.library.show_rating_key_map:
                path = path.replace(self.library.Sonarr.plex_path, self.library.Sonarr.sonarr_path)
                path = path[:-1] if path.endswith(('/', '\\')) else path
                tvdb_paths.append((self.library.show_rating_key_map[item.ratingKey], path))
            if any([mn in plex.item_advance_keys for mn in self.item_details]) and hasattr(item, "preferences"):
                advance_edits = {}
                prefs = [p.id for p in item.preferences()]
                for method_name, method_data in self.item_details.items():
                    if method_name in plex.item_advance_keys:
                        key, options = plex.item_advance_keys[method_name]
                        if key in prefs and getattr(item, key) != options[method_data]:
                            advance_edits[key] = options[method_data]
                if advance_edits:
                    logger.debug(f"Details Update: {advance_edits}")
                    if self.library.edit_advance(item, advance_edits):
                        logger.info(f"{item.title} Advanced Details Update Successful")
                    else:
                        logger.error(f"{item.title} Advanced Details Update Failed")

            if "item_tmdb_season_titles" in self.item_details and item.ratingKey in self.library.show_rating_key_map:
                try:
                    tmdb_id = self.config.Convert.tvdb_to_tmdb(self.library.show_rating_key_map[item.ratingKey])
                    names = {s.season_number: s.name for s in self.config.TMDb.get_show(tmdb_id).seasons}
                    for season in self.library.query(item.seasons):
                        if season.index in names and season.title != names[season.index]:
                            season.editTitle(names[season.index])
                except Failed as e:
                    logger.error(e)

            # Locking should come before refreshing since refreshing can change metadata (i.e. if specified to both lock
            # background/poster and also refreshing, assume that the item background/poster should be kept)
            if "item_lock_background" in self.item_details:
                self.library.query(item.lockArt if self.item_details["item_lock_background"] else item.unlockArt)
            if "item_lock_poster" in self.item_details:
                self.library.query(item.lockPoster if self.item_details["item_lock_poster"] else item.unlockPoster)
            if "item_lock_title" in self.item_details:
                self.library.edit_query(item, {"title.locked": 1 if self.item_details["item_lock_title"] else 0})
            if "item_refresh" in self.item_details:
                delay = self.item_details["item_refresh_delay"] if "item_refresh_delay" in self.item_details else self.library.item_refresh_delay
                if delay > 0:
                    time.sleep(delay)
                self.library.query(item.refresh)

        if self.library.Radarr and tmdb_paths:
            if "item_radarr_tag" in self.item_details:
                self.library.Radarr.edit_tags([t[0] if isinstance(t, tuple) else t for t in tmdb_paths], self.item_details["item_radarr_tag"], self.item_details["apply_tags"])
            if self.radarr_details["add_existing"]:
                added = self.library.Radarr.add_tmdb(tmdb_paths, **self.radarr_details)
                self.added_to_radarr.extend([{"title": movie.title, "id": movie.tmdbId} for movie in added])

        if self.library.Sonarr and tvdb_paths:
            if "item_sonarr_tag" in self.item_details:
                self.library.Sonarr.edit_tags([t[0] if isinstance(t, tuple) else t for t in tvdb_paths], self.item_details["item_sonarr_tag"], self.item_details["apply_tags"])
            if self.sonarr_details["add_existing"]:
                added = self.library.Sonarr.add_tvdb(tvdb_paths, **self.sonarr_details)
                self.added_to_sonarr.extend([{"title": show.title, "id": show.tvdbId} for show in added])

    def load_collection(self):
        if self.obj is None and self.smart_url:
            self.library.create_smart_collection(self.name, self.smart_type_key, self.smart_url, self.ignore_blank_results)
            logger.debug(f"Smart Collection Created: {self.smart_url}")
        elif self.obj is None and self.blank_collection:
            self.library.create_blank_collection(self.name)
        elif self.smart_label_collection:
            try:
                if not self.library.smart_label_check(self.name):
                    raise Failed
                smart_type, _, self.smart_url = self.build_filter("smart_label", self.smart_label, default_sort="random")
                if not self.obj:
                    self.library.create_smart_collection(self.name, smart_type, self.smart_url, self.ignore_blank_results)
            except Failed:
                raise Failed(f"{self.Type} Error: Label: {self.name} was not added to any items in the Library")
        self.obj = self.library.get_playlist(self.name) if self.playlist else self.library.get_collection(self.name, force_search=True)
        if not self.exists:
            self.created = True

    def update_details(self):
        updated_details = []
        logger.info("")
        logger.separator(f"Updating Details of {self.name} {self.Type}", space=False, border=False)
        logger.info("")
        if "summary" in self.summaries:                     summary = ("summary", self.summaries["summary"])
        elif "tmdb_description" in self.summaries:          summary = ("tmdb_description", self.summaries["tmdb_description"])
        elif "tvdb_description" in self.summaries:          summary = ("tvdb_description", self.summaries["tvdb_description"])
        elif "letterboxd_description" in self.summaries:    summary = ("letterboxd_description", self.summaries["letterboxd_description"])
        elif "tmdb_summary" in self.summaries:              summary = ("tmdb_summary", self.summaries["tmdb_summary"])
        elif "tvdb_summary" in self.summaries:              summary = ("tvdb_summary", self.summaries["tvdb_summary"])
        elif "tmdb_biography" in self.summaries:            summary = ("tmdb_biography", self.summaries["tmdb_biography"])
        elif "tmdb_person" in self.summaries:               summary = ("tmdb_person", self.summaries["tmdb_person"])
        elif "tmdb_collection_details" in self.summaries:   summary = ("tmdb_collection_details", self.summaries["tmdb_collection_details"])
        elif "trakt_list_details" in self.summaries:        summary = ("trakt_list_details", self.summaries["trakt_list_details"])
        elif "tmdb_list_details" in self.summaries:         summary = ("tmdb_list_details", self.summaries["tmdb_list_details"])
        elif "tvdb_list_details" in self.summaries:         summary = ("tvdb_list_details", self.summaries["tvdb_list_details"])
        elif "letterboxd_list_details" in self.summaries:   summary = ("letterboxd_list_details", self.summaries["letterboxd_list_details"])
        elif "icheckmovies_list_details" in self.summaries: summary = ("icheckmovies_list_details", self.summaries["icheckmovies_list_details"])
        elif "tmdb_actor_details" in self.summaries:        summary = ("tmdb_actor_details", self.summaries["tmdb_actor_details"])
        elif "tmdb_crew_details" in self.summaries:         summary = ("tmdb_crew_details", self.summaries["tmdb_crew_details"])
        elif "tmdb_director_details" in self.summaries:     summary = ("tmdb_director_details", self.summaries["tmdb_director_details"])
        elif "tmdb_producer_details" in self.summaries:     summary = ("tmdb_producer_details", self.summaries["tmdb_producer_details"])
        elif "tmdb_writer_details" in self.summaries:       summary = ("tmdb_writer_details", self.summaries["tmdb_writer_details"])
        elif "tmdb_movie_details" in self.summaries:        summary = ("tmdb_movie_details", self.summaries["tmdb_movie_details"])
        elif "tvdb_movie_details" in self.summaries:        summary = ("tvdb_movie_details", self.summaries["tvdb_movie_details"])
        elif "tvdb_show_details" in self.summaries:         summary = ("tvdb_show_details", self.summaries["tvdb_show_details"])
        elif "tmdb_show_details" in self.summaries:         summary = ("tmdb_show_details", self.summaries["tmdb_show_details"])
        else:                                               summary = None

        if self.playlist:
            if summary:
                if str(summary[1]) != str(self.obj.summary):
                    try:
                        self.obj.edit(summary=str(summary[1]))
                        logger.info(f"Summary ({summary[0]}) | {summary[1]:<25}")
                        logger.info("Details: have been updated")
                        updated_details.append("Metadata")
                    except NotFound:
                        logger.error("Details: Failed to Update Please delete the collection and run again")
                    logger.info("")
        else:
            #self.obj.batchEdits()
            batch_display = "Collection Metadata Edits"
            if summary and str(summary[1]) != str(self.obj.summary):
                self.obj.editSummary(summary[1])
                batch_display += f"\nSummary ({summary[0]}) | {summary[1]:<25}"

            if "sort_title" in self.details and str(self.details["sort_title"]) != str(self.obj.titleSort):
                self.obj.editSortTitle(self.details["sort_title"])
                batch_display += f"\nSort Title | {self.details['sort_title']}"

            if "content_rating" in self.details and str(self.details["content_rating"]) != str(self.obj.contentRating):
                self.obj.editContentRating(self.details["content_rating"])
                batch_display += f"\nContent Rating | {self.details['content_rating']}"

            add_tags = self.details["label"] if "label" in self.details else []
            remove_tags = self.details["label.remove"] if "label.remove" in self.details else None
            sync_tags = self.details["label.sync"] if "label.sync" in self.details else None
            if sync_tags:
                sync_tags.append("PMM")
            else:
                add_tags.append("PMM")
            tag_results = self.library.edit_tags('label', self.obj, add_tags=add_tags, remove_tags=remove_tags, sync_tags=sync_tags, do_print=False)
            if tag_results:
                batch_display += f"\n{tag_results}"

            logger.info(batch_display)
            if len(batch_display) > 25:
                try:
                    #self.obj.saveEdits()
                    logger.info("Details: have been updated")
                    updated_details.append("Metadata")
                except NotFound:
                    logger.error("Details: Failed to Update Please delete the collection and run again")
                logger.info("")

            advance_update = False
            if "collection_mode" in self.details:
                if (self.blank_collection and self.created) or int(self.obj.collectionMode) not in plex.collection_mode_keys \
                        or plex.collection_mode_keys[int(self.obj.collectionMode)] != self.details["collection_mode"]:
                    if self.blank_collection and self.created:
                        self.library.collection_mode_query(self.obj, "hide")
                        logger.info(f"Collection Mode | hide")
                        self.library.collection_mode_query(self.obj, "default")
                        logger.info(f"Collection Mode | default")
                    self.library.collection_mode_query(self.obj, self.details["collection_mode"])
                    logger.info(f"Collection Mode | {self.details['collection_mode']}")
                    advance_update = True

            if "collection_filtering" in self.details:
                try:
                    self.library.edit_query(self.obj, {"collectionFilterBasedOnUser": 0 if self.details["collection_filtering"] == "admin" else 1}, advanced=True)
                    advance_update = True
                except NotFound:
                    logger.error("Collection Error: collection_filtering requires a more recent version of Plex Media Server")

            if "collection_order" in self.details:
                if int(self.obj.collectionSort) not in plex.collection_order_keys \
                        or plex.collection_order_keys[int(self.obj.collectionSort)] != self.details["collection_order"]:
                    self.library.collection_order_query(self.obj, self.details["collection_order"])
                    logger.info(f"Collection Order | {self.details['collection_order']}")
                    advance_update = True

            if "visible_library" in self.details or "visible_home" in self.details or "visible_shared" in self.details:
                visibility = self.library.collection_visibility(self.obj)
                visible_library = None
                visible_home = None
                visible_shared = None

                if "visible_library" in self.details and self.details["visible_library"] != visibility["library"]:
                    visible_library = self.details["visible_library"]

                if "visible_home" in self.details and self.details["visible_home"] != visibility["home"]:
                    visible_home = self.details["visible_home"]

                if "visible_shared" in self.details and self.details["visible_shared"] != visibility["shared"]:
                    visible_shared = self.details["visible_shared"]

                if visible_library is not None or visible_home is not None or visible_shared is not None:
                    self.library.collection_visibility_update(self.obj, visibility=visibility, library=visible_library, home=visible_home, shared=visible_shared)
                    advance_update = True
                    logger.info("Collection Visibility Updated")

            if advance_update and "Metadata" not in updated_details:
                updated_details.append("Metadata")

        asset_location = None
        if self.asset_directory:
            name_mapping = self.name
            if "name_mapping" in self.details:
                if self.details["name_mapping"]:                    name_mapping = self.details["name_mapping"]
                else:                                               logger.error(f"{self.Type} Error: name_mapping attribute is blank")
            try:
                asset_poster, asset_background, asset_location, _ = self.library.find_item_assets(name_mapping, asset_directory=self.asset_directory)
                if asset_poster:
                    self.posters["asset_directory"] = asset_poster
                if asset_background:
                    self.backgrounds["asset_directory"] = asset_background
            except Failed as e:
                if self.library.asset_folders and (self.library.show_missing_assets or self.library.create_asset_folders):
                    logger.warning(e)
        if self.mapping_name in self.library.collection_images or self.name in self.library.collection_images:
            image_set = self.library.collection_images[self.mapping_name if self.mapping_name in self.library.collection_images else self.name]
            if image_set and "url_poster" in image_set and image_set["url_poster"]:
                self.posters["image_set"] = image_set["url_poster"]
            elif image_set and "tpdb_poster" in image_set and image_set["tpdb_poster"]:
                self.posters["image_set"] = f"https://theposterdb.com/api/assets/{image_set['tpdb_poster']}"
            if image_set and "url_background" in image_set and image_set["url_background"]:
                self.backgrounds["image_set"] = image_set["url_background"]
            elif image_set and "tpdb_background" in image_set and image_set["tpdb_background"]:
                self.backgrounds["image_set"] = f"https://theposterdb.com/api/assets/{image_set['tpdb_background']}"

        self.collection_poster = util.pick_image(self.obj.title, self.posters, self.library.prioritize_assets, self.library.download_url_assets, asset_location)
        self.collection_background = util.pick_image(self.obj.title, self.backgrounds, self.library.prioritize_assets, self.library.download_url_assets, asset_location, is_poster=False)

        if self.collection_poster or self.collection_background:
            pu, bu = self.library.upload_images(self.obj, poster=self.collection_poster, background=self.collection_background)
            if pu or bu:
                updated_details.append("Image")

        if self.url_theme:  # TODO: cache theme path to not constantly upload
            self.library.upload_theme(self.obj, url=self.url_theme)
        elif self.file_theme:
            self.library.upload_theme(self.obj, filepath=self.file_theme)
        return updated_details

    def sort_collection(self):
        logger.info("")
        logger.separator(f"Sorting {self.name} {self.Type}", space=False, border=False)
        logger.info("")
        if not isinstance(self.custom_sort, list):
            items = self.found_items
            if self.custom_sort == "custom.desc":
                items = items[::-1]
        else:
            plex_search = {"sort_by": self.custom_sort}
            if self.builder_level in ["season", "episode"]:
                plex_search["type"] = f"{self.builder_level}s"
                plex_search["any"] = {f"{self.builder_level}_collection": self.name}
            else:
                plex_search["any"] = {"collection": self.name}
            try:
                search_data = self.build_filter("plex_search", plex_search)
            except FilterFailed as e:
                if self.ignore_blank_results:
                    raise
                else:
                    raise Failed(str(e))
            items = self.library.get_filter_items(search_data[2])
        previous = None
        sort_edit = False
        for i, item in enumerate(items, 0):
            try:
                if len(self.items) <= i or item.ratingKey != self.items[i].ratingKey:
                    text = f"after {util.item_title(previous)}" if previous else "to the beginning"
                    self.library.moveItem(self.obj, item, previous)
                    logger.info(f"Moving {util.item_title(item)} {text}")
                    sort_edit = True
                previous = item
            except Failed:
                logger.error(f"Failed to Move {util.item_title(item)}")
                sort_edit = True
        if not sort_edit:
            logger.info("No Sorting Required")

    def sync_trakt_list(self):
        logger.info("")
        logger.separator(f"Syncing {self.name} {self.Type} to Trakt List {self.sync_to_trakt_list}", space=False, border=False)
        logger.info("")
        if self.obj:
            self.obj.reload()
        self.load_collection_items()
        current_ids = []
        for item in self.items:
            for pl_library in self.libraries:
                new_id = None
                if isinstance(item, Movie) and item.ratingKey in pl_library.movie_rating_key_map:
                    new_id = (pl_library.movie_rating_key_map[item.ratingKey], "tmdb")
                elif isinstance(item, Show) and item.ratingKey in pl_library.show_rating_key_map:
                    new_id = (pl_library.show_rating_key_map[item.ratingKey], "tvdb")
                elif isinstance(item, Season) and item.parentRatingKey in pl_library.show_rating_key_map:
                    new_id = (f"{pl_library.show_rating_key_map[item.parentRatingKey]}_{item.seasonNumber}", "tvdb_season")
                elif isinstance(item, Episode) and item.grandparentRatingKey in pl_library.show_rating_key_map:
                    new_id = (f"{pl_library.show_rating_key_map[item.grandparentRatingKey]}_{item.seasonNumber}_{item.episodeNumber}", "tvdb_episode")
                if new_id:
                    current_ids.append(new_id)
                    break
        if self.sync_missing_to_trakt_list:
            current_ids.extend([(mm, "tmdb") for mm in self.missing_movies])
            current_ids.extend([(ms, "tvdb") for ms in self.missing_shows])
        self.config.Trakt.sync_list(self.sync_to_trakt_list, current_ids)

    def delete(self):
        title = self.obj.title if self.obj else self.name
        if self.playlist:
            output = f"Deleting {self.Type} {title}"
            output += f"\n{self.Type} {'deleted' if self.obj else 'not found'} on {self.library.account.username}"
        elif self.obj:
            output = f"{self.Type} {self.obj.title} deleted"
            if self.smart_label_collection:
                for item in self.library.search(label=self.name, libtype=self.builder_level):
                    self.library.edit_tags("label", item, remove_tags=self.name)
        else:
            output = ""
        if self.obj:
            self.library.delete(self.obj)

        if self.playlist and self.valid_users:
            for user in self.valid_users:
                try:
                    self.library.delete_user_playlist(title, user)
                    output += f"\nPlaylist deleted on User {user}"
                except Failed:
                    output += f"\nPlaylist not found on User {user}"
        return output

    def sync_playlist(self):
        if self.obj and self.valid_users:
            logger.info("")
            logger.separator(f"Syncing Playlist to Users", space=False, border=False)
            logger.info("")
            for user in self.valid_users:
                try:
                    self.library.delete_user_playlist(self.obj.title, user)
                except Failed:
                    pass
                self.obj.copyToUser(user)
                logger.info(f"Playlist: {self.name} synced to {user}")

    def send_notifications(self, playlist=False):
        if self.obj and self.details["changes_webhooks"] and \
                (self.created or len(self.notification_additions) > 0 or len(self.notification_removals) > 0):
            self.obj.reload()
            try:
                self.library.Webhooks.collection_hooks(
                    self.details["changes_webhooks"],
                    self.obj,
                    poster_url=self.collection_poster.location if self.collection_poster and self.collection_poster.is_url else None,
                    background_url=self.collection_background.location if self.collection_background and self.collection_background.is_url else None,
                    created=self.created,
                    additions=self.notification_additions,
                    removals=self.notification_removals,
                    radarr=self.added_to_radarr,
                    sonarr=self.added_to_sonarr,
                    playlist=playlist
                )
            except Failed as e:
                logger.stacktrace()
                logger.error(f"Webhooks Error: {e}")

    def run_collections_again(self):
        self.obj = self.library.get_collection(self.name, force_search=True)
        name, collection_items = self.library.get_collection_name_and_items(self.obj, self.smart_label_collection)
        self.created = False
        rating_keys = []
        amount_added = 0
        self.notification_additions = []
        self.added_to_radarr = []
        self.added_to_sonarr = []
        for mm in self.run_again_movies:
            if mm in self.library.movie_map:
                rating_keys.extend(self.library.movie_map[mm])
        if self.library.is_show:
            for sm in self.run_again_shows:
                if sm in self.library.show_map:
                    rating_keys.extend(self.library.show_map[sm])
        if len(rating_keys) > 0:
            for rating_key in rating_keys:
                try:
                    current = self.library.fetch_item(int(rating_key))
                except Failed as e:
                    logger.error(e)
                    continue
                if current in collection_items:
                    logger.info(f"{name} {self.Type} | = | {util.item_title(current)}")
                else:
                    self.library.alter_collection(current, name, smart_label_collection=self.smart_label_collection)
                    amount_added += 1
                    logger.info(f"{name} {self.Type} | + | {util.item_title(current)}")
                    if self.library.is_movie and current.ratingKey in self.library.movie_rating_key_map:
                        add_id = self.library.movie_rating_key_map[current.ratingKey]
                    elif self.library.is_show and current.ratingKey in self.library.show_rating_key_map:
                        add_id = self.library.show_rating_key_map[current.ratingKey]
                    else:
                        add_id = None
                    self.notification_additions.append(util.item_set(current, add_id))
            self.send_notifications()
            logger.info(f"{len(rating_keys)} {self.builder_level.capitalize()}{'s' if len(rating_keys) > 1 else ''} Processed")

        if len(self.run_again_movies) > 0:
            logger.info("")
            for missing_id in self.run_again_movies:
                if missing_id not in self.library.movie_map:
                    try:
                        movie = self.config.TMDb.get_movie(missing_id)
                    except Failed as e:
                        logger.error(e)
                        continue
                    if self.details["show_missing"] is True:
                        current_title = f"{movie.title} ({movie.release_date.year})" if movie.release_date else movie.title
                        logger.info(f"{name} {self.Type} | ? | {current_title} (TMDb: {missing_id})")
            logger.info("")
            logger.info(f"{len(self.run_again_movies)} Movie{'s' if len(self.run_again_movies) > 1 else ''} Missing")

        if len(self.run_again_shows) > 0 and self.library.is_show:
            logger.info("")
            for missing_id in self.run_again_shows:
                if missing_id not in self.library.show_map:
                    try:
                        title = self.config.TVDb.get_tvdb_obj(missing_id).title
                    except Failed as e:
                        logger.error(e)
                        continue
                    if self.details["show_missing"] is True:
                        logger.info(f"{name} {self.Type} | ? | {title} (TVDb: {missing_id})")
            logger.info(f"{len(self.run_again_shows)} Show{'s' if len(self.run_again_shows) > 1 else ''} Missing")

        return amount_added
