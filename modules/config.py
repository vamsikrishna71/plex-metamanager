import base64, os, re, requests
from datetime import datetime
from lxml import html
from modules import util, radarr, sonarr, operations
from modules.anidb import AniDB
from modules.anilist import AniList
from modules.cache import Cache
from modules.convert import Convert
from modules.ergast import Ergast
from modules.flixpatrol import FlixPatrol
from modules.icheckmovies import ICheckMovies
from modules.imdb import IMDb
from modules.github import GitHub
from modules.letterboxd import Letterboxd
from modules.mal import MyAnimeList
from modules.meta import PlaylistFile
from modules.notifiarr import Notifiarr
from modules.omdb import OMDb
from modules.overlays import Overlays
from modules.plex import Plex
from modules.radarr import Radarr
from modules.sonarr import Sonarr
from modules.reciperr import Reciperr
from modules.mdblist import Mdblist
from modules.tautulli import Tautulli
from modules.tmdb import TMDb
from modules.trakt import Trakt
from modules.tvdb import TVDb
from modules.util import Failed, NotScheduled, NotScheduledRange, YAML
from modules.webhooks import Webhooks
from retrying import retry

logger = util.logger

mediastingers_url = "https://raw.githubusercontent.com/meisnate12/PMM-Mediastingers/master/stingers.yml"
sync_modes = {"append": "Only Add Items to the Collection or Playlist", "sync": "Add & Remove Items from the Collection or Playlist"}
imdb_label_options = {
    "none": "Add IMDb Parental Labels for None, Mild, Moderate, or Severe",
    "mild": "Add IMDb Parental Labels for Mild, Moderate, or Severe",
    "moderate": "Add IMDb Parental Labels for Moderate or Severe",
    "severe": "Add IMDb Parental Labels for Severe"
}
mass_genre_options = {
    "lock": "Unlock Genre", "unlock": "Unlock Genre", "remove": "Remove and Lock Genre", "reset": "Remove and Unlock Genre",
    "tmdb": "Use TMDb Genres", "imdb": "Use IMDb Genres", "omdb": "Use IMDb Genres through OMDb", "tvdb": "Use TVDb Genres",
    "anidb": "Use AniDB Main Tags", "anidb_all": "Use All AniDB Tags", "mal": "Use MyAnimeList Genres"
}
mass_content_options = {
    "lock": "Unlock Rating", "unlock": "Unlock Rating", "remove": "Remove and Lock Rating", "reset": "Remove and Unlock Rating",
    "omdb": "Use IMDb Rating through OMDb", "mdb": "Use MdbList Rating", "mdb_commonsense": "Use Commonsense Rating through MDbList",
    "mdb_commonsense0": "Use Commonsense Rating with Zero Padding through MDbList", "mal": "Use MyAnimeList Rating"
}
mass_studio_options = {
    "lock": "Unlock Rating", "unlock": "Unlock Rating", "remove": "Remove and Lock Rating", "reset": "Remove and Unlock Rating",
    "tmdb": "Use TMDb Studio", "anidb": "Use AniDB Animation Work", "mal": "Use MyAnimeList Studio"
}
mass_original_title_options = {
    "lock": "Unlock Original Title", "unlock": "Unlock Original Title", "remove": "Remove and Lock Original Title", "reset": "Remove and Unlock Original Title",
    "anidb": "Use AniDB Main Title", "anidb_official": "Use AniDB Official Title based on the language attribute in the config file",
    "mal": "Use MyAnimeList Main Title", "mal_english": "Use MyAnimeList English Title", "mal_japanese": "Use MyAnimeList Japanese Title",
}
mass_available_options = {
    "lock": "Unlock Originally Available", "unlock": "Unlock Originally Available", "remove": "Remove and Lock Originally Available", "reset": "Remove and Unlock Originally Available",
    "tmdb": "Use TMDb Release", "omdb": "Use IMDb Release through OMDb", "mdb": "Use MdbList Release", "tvdb": "Use TVDb Release",
    "anidb": "Use AniDB Release", "mal": "Use MyAnimeList Release"
}
mass_image_options = {
    "plex": "Use Plex Images", "tmdb": "Use TMDb Images"
}
mass_episode_rating_options = {
    "lock": "Unlock Rating", "unlock": "Unlock Rating", "remove": "Remove and Lock Rating", "reset": "Remove and Unlock Rating",
    "tmdb": "Use TMDb Rating", "imdb": "Use IMDb Rating"
}
mass_rating_options = {
    "lock": "Lock Rating",
    "unlock": "Unlock Rating",
    "remove": "Remove and Lock Rating",
    "reset": "Remove and Unlock Rating",
    "tmdb": "Use TMDb Rating",
    "imdb": "Use IMDb Rating",
    "trakt_user": "Use Trakt User Rating",
    "omdb": "Use IMDb Rating through OMDb",
    "mdb": "Use MdbList Score",
    "mdb_average": "Use MdbList Average Score",
    "mdb_imdb": "Use IMDb Rating through MDbList",
    "mdb_metacritic": "Use Metacritic Rating through MDbList",
    "mdb_metacriticuser": "Use Metacritic User Rating through MDbList",
    "mdb_trakt": "Use Trakt Rating through MDbList",
    "mdb_tomatoes": "Use Rotten Tomatoes Rating through MDbList",
    "mdb_tomatoesaudience": "Use Rotten Tomatoes Audience Rating through MDbList",
    "mdb_tmdb": "Use TMDb Rating through MDbList",
    "mdb_letterboxd": "Use Letterboxd Rating through MDbList",
    "mdb_myanimelist": "Use MyAnimeList Rating through MDbList",
    "anidb_rating": "Use AniDB Rating",
    "anidb_average": "Use AniDB Average",
    "anidb_score": "Use AniDB Review Dcore",
    "mal": "Use MyAnimeList Rating"
}
reset_overlay_options = {"tmdb": "Reset to TMDb poster", "plex": "Reset to Plex Poster"}
library_operations = {
    "assets_for_all": "bool", "split_duplicates": "bool", "update_blank_track_titles": "bool", "remove_title_parentheses": "bool",
    "radarr_add_all_existing": "bool", "radarr_remove_by_tag": "bool", "sonarr_add_all_existing": "bool", "sonarr_remove_by_tag": "bool",
    "mass_genre_update": mass_genre_options, "mass_content_rating_update": mass_content_options, "mass_studio_update": mass_studio_options,
    "mass_audience_rating_update": mass_rating_options, "mass_episode_audience_rating_update": mass_episode_rating_options,
    "mass_critic_rating_update": mass_rating_options, "mass_episode_critic_rating_update": mass_episode_rating_options,
    "mass_user_rating_update": mass_rating_options, "mass_episode_user_rating_update": mass_episode_rating_options,
    "mass_original_title_update": mass_original_title_options, "mass_originally_available_update": mass_available_options,
    "mass_imdb_parental_labels": imdb_label_options, "mass_episode_imdb_parental_labels": imdb_label_options,
    "mass_poster_update": mass_image_options, "mass_background_update": mass_image_options,
    "mass_collection_mode": "mass_collection_mode", "metadata_backup": "metadata_backup", "delete_collections": "delete_collections",
    "genre_mapper": "mapper", "content_rating_mapper": "mapper",
}

class ConfigFile:
    def __init__(self, default_dir, attrs):
        logger.info("Locating config...")
        config_file = attrs["config_file"]
        if config_file and os.path.exists(config_file):                     self.config_path = os.path.abspath(config_file)
        elif config_file and not os.path.exists(config_file):               raise Failed(f"Config Error: config not found at {os.path.abspath(config_file)}")
        elif os.path.exists(os.path.join(default_dir, "config.yml")):       self.config_path = os.path.abspath(os.path.join(default_dir, "config.yml"))
        else:                                                               raise Failed(f"Config Error: config not found at {os.path.abspath(default_dir)}")
        logger.info(f"Using {self.config_path} as config")
        logger.clear_errors()

        self._mediastingers = None
        self.default_dir = default_dir
        self.read_only = attrs["read_only"] if "read_only" in attrs else False
        self.version = attrs["version"] if "version" in attrs else None
        self.branch = attrs["branch"] if "branch" in attrs else None
        self.no_missing = attrs["no_missing"] if "no_missing" in attrs else None
        self.no_report = attrs["no_report"] if "no_report" in attrs else None
        self.ignore_schedules = attrs["ignore_schedules"] if "ignore_schedules" in attrs else False
        self.start_time = attrs["time_obj"]
        self.run_hour = datetime.strptime(attrs["time"], "%H:%M").hour
        self.requested_collections = None
        if "collections" in attrs and attrs["collections"]:
            self.requested_collections = [s.strip() for s in attrs["collections"].split("|")]
        self.requested_libraries = None
        if "libraries" in attrs and attrs["libraries"]:
            self.requested_libraries = [s.strip() for s in attrs["libraries"].split("|")]
        self.requested_metadata_files = None
        if "metadata_files" in attrs and attrs["metadata_files"]:
            self.requested_metadata_files = []
            for s in attrs["metadata_files"].split("|"):
                s = s.stripe()
                if s:
                    if s.endswith(".yml"):
                        self.requested_metadata_files.append(s[:-4])
                    elif s.endswith(".yaml"):
                        self.requested_metadata_files.append(s[:-5])
                    else:
                        self.requested_metadata_files.append(s)
        self.collection_only = attrs["collection_only"] if "collection_only" in attrs else False
        self.operations_only = attrs["operations_only"] if "operations_only" in attrs else False
        self.overlays_only = attrs["overlays_only"] if "overlays_only" in attrs else False
        self.env_plex_url = attrs["plex_url"] if "plex_url" in attrs else ""
        self.env_plex_token = attrs["plex_token"] if "plex_token" in attrs else ""
        current_time = datetime.now()

        with open(self.config_path, encoding="utf-8") as fp:
            logger.separator("Redacted Config", space=False, border=False, debug=True)
            for line in fp.readlines():
                logger.debug(re.sub(r"(token|client.*|url|api_*key|secret|error|run_start|run_end|version|changes|username|password): .+", r"\1: (redacted)", line.strip("\r\n")))
            logger.debug("")

        self.data = YAML(self.config_path).data

        def replace_attr(all_data, attr, par):
            if "settings" not in all_data:
                all_data["settings"] = {}
            if par in all_data and all_data[par] and attr in all_data[par] and attr not in all_data["settings"]:
                all_data["settings"][attr] = all_data[par][attr]
                del all_data[par][attr]
        if "libraries" not in self.data:
            self.data["libraries"] = {}
        if "settings" not in self.data:
            self.data["settings"] = {}
        if "tmdb" not in self.data:
            self.data["tmdb"] = {}
        replace_attr(self.data, "cache", "cache")
        replace_attr(self.data, "cache_expiration", "cache")
        if "config" in self.data:
            del self.data["cache"]
        replace_attr(self.data, "asset_directory", "plex")
        replace_attr(self.data, "sync_mode", "plex")
        replace_attr(self.data, "show_unmanaged", "plex")
        replace_attr(self.data, "show_filtered", "plex")
        replace_attr(self.data, "show_missing", "plex")
        replace_attr(self.data, "save_missing", "plex")
        if self.data["libraries"]:
            for library in self.data["libraries"]:
                if not self.data["libraries"][library]:
                    continue
                if "radarr_add_all" in self.data["libraries"][library]:
                    self.data["libraries"][library]["radarr_add_all_existing"] = self.data["libraries"][library].pop("radarr_add_all")
                if "sonarr_add_all" in self.data["libraries"][library]:
                    self.data["libraries"][library]["sonarr_add_all_existing"] = self.data["libraries"][library].pop("sonarr_add_all")
                if "plex" in self.data["libraries"][library] and self.data["libraries"][library]["plex"]:
                    replace_attr(self.data["libraries"][library], "asset_directory", "plex")
                    replace_attr(self.data["libraries"][library], "sync_mode", "plex")
                    replace_attr(self.data["libraries"][library], "show_unmanaged", "plex")
                    replace_attr(self.data["libraries"][library], "show_filtered", "plex")
                    replace_attr(self.data["libraries"][library], "show_missing", "plex")
                    replace_attr(self.data["libraries"][library], "save_missing", "plex")
                if "settings" in self.data["libraries"][library] and self.data["libraries"][library]["settings"]:
                    if "collection_minimum" in self.data["libraries"][library]["settings"]:
                        self.data["libraries"][library]["settings"]["minimum_items"] = self.data["libraries"][library]["settings"].pop("collection_minimum")
                    if "save_missing" in self.data["libraries"][library]["settings"]:
                        self.data["libraries"][library]["settings"]["save_report"] = self.data["libraries"][library]["settings"].pop("save_missing")
                if "radarr" in self.data["libraries"][library] and self.data["libraries"][library]["radarr"]:
                    if "monitor" in self.data["libraries"][library]["radarr"] and isinstance(self.data["libraries"][library]["radarr"]["monitor"], bool):
                        self.data["libraries"][library]["radarr"]["monitor"] = True if self.data["libraries"][library]["radarr"]["monitor"] else False
                    if "add" in self.data["libraries"][library]["radarr"]:
                        self.data["libraries"][library]["radarr"]["add_missing"] = self.data["libraries"][library]["radarr"].pop("add")
                if "sonarr" in self.data["libraries"][library] and self.data["libraries"][library]["sonarr"]:
                    if "add" in self.data["libraries"][library]["sonarr"]:
                        self.data["libraries"][library]["sonarr"]["add_missing"] = self.data["libraries"][library]["sonarr"].pop("add")
                if "operations" in self.data["libraries"][library] and self.data["libraries"][library]["operations"]:
                    if "radarr_add_all" in self.data["libraries"][library]["operations"]:
                        self.data["libraries"][library]["operations"]["radarr_add_all_existing"] = self.data["libraries"][library]["operations"].pop("radarr_add_all")
                    if "sonarr_add_all" in self.data["libraries"][library]["operations"]:
                        self.data["libraries"][library]["operations"]["sonarr_add_all_existing"] = self.data["libraries"][library]["operations"].pop("sonarr_add_all")
                    if "mass_imdb_parental_labels" in self.data["libraries"][library]["operations"] and self.data["libraries"][library]["operations"]["mass_imdb_parental_labels"]:
                        if self.data["libraries"][library]["operations"]["mass_imdb_parental_labels"] == "with_none":
                            self.data["libraries"][library]["operations"]["mass_imdb_parental_labels"] = "none"
                        elif self.data["libraries"][library]["operations"]["mass_imdb_parental_labels"] == "without_none":
                            self.data["libraries"][library]["operations"]["mass_imdb_parental_labels"] = "mild"
                if "webhooks" in self.data["libraries"][library] and self.data["libraries"][library]["webhooks"] and "collection_changes" not in self.data["libraries"][library]["webhooks"]:
                    changes = []
                    def hooks(attr):
                        if attr in self.data["libraries"][library]["webhooks"]:
                            changes.extend([w for w in util.get_list(self.data["libraries"][library]["webhooks"].pop(attr), split=False) if w not in changes])
                    hooks("collection_creation")
                    hooks("collection_addition")
                    hooks("collection_removal")
                    hooks("collection_changes")
                    self.data["libraries"][library]["webhooks"]["changes"] = None if not changes else changes if len(changes) > 1 else changes[0]
        if "libraries" in self.data:                   self.data["libraries"] = self.data.pop("libraries")
        if "playlist_files" in self.data:              self.data["playlist_files"] = self.data.pop("playlist_files")
        if "settings" in self.data:
            temp = self.data.pop("settings")
            if "collection_minimum" in temp:
                temp["minimum_items"] = temp.pop("collection_minimum")
            if "playlist_sync_to_user" in temp:
                temp["playlist_sync_to_users"] = temp.pop("playlist_sync_to_user")
            if "save_missing" in temp:
                temp["save_report"] = temp.pop("save_missing")
            self.data["settings"] = temp
        if "webhooks" in self.data:
            temp = self.data.pop("webhooks")
            if "changes" not in temp:
                changes = []
                def hooks(attr):
                    if attr in temp:
                        items = util.get_list(temp.pop(attr), split=False)
                        if items:
                            changes.extend([w for w in items if w not in changes])
                hooks("collection_creation")
                hooks("collection_addition")
                hooks("collection_removal")
                hooks("collection_changes")
                temp["changes"] = None if not changes else changes if len(changes) > 1 else changes[0]
            self.data["webhooks"] = temp
        if "plex" in self.data:                        self.data["plex"] = self.data.pop("plex")
        if "tmdb" in self.data:                        self.data["tmdb"] = self.data.pop("tmdb")
        if "tautulli" in self.data:                    self.data["tautulli"] = self.data.pop("tautulli")
        if "omdb" in self.data:                        self.data["omdb"] = self.data.pop("omdb")
        if "mdblist" in self.data:                     self.data["mdblist"] = self.data.pop("mdblist")
        if "notifiarr" in self.data:                   self.data["notifiarr"] = self.data.pop("notifiarr")
        if "anidb" in self.data:                       self.data["anidb"] = self.data.pop("anidb")
        if "radarr" in self.data:
            if "monitor" in self.data["radarr"] and isinstance(self.data["radarr"]["monitor"], bool):
                self.data["radarr"]["monitor"] = True if self.data["radarr"]["monitor"] else False
            temp = self.data.pop("radarr")
            if temp and "add" in temp:
                temp["add_missing"] = temp.pop("add")
            self.data["radarr"] = temp
        if "sonarr" in self.data:
            temp = self.data.pop("sonarr")
            if temp and "add" in temp:
                temp["add_missing"] = temp.pop("add")
            self.data["sonarr"] = temp
        if "trakt" in self.data:                       self.data["trakt"] = self.data.pop("trakt")
        if "mal" in self.data:                         self.data["mal"] = self.data.pop("mal")

        def check_for_attribute(data, attribute, parent=None, test_list=None, default=None, do_print=True, default_is_none=False, req_default=False, var_type="str", throw=False, save=True, int_min=0):
            endline = ""
            if parent is not None:
                if data and parent in data:
                    data = data[parent]
                else:
                    data = None
                    do_print = False
                    save = False
            if self.read_only:
                save = False
            text = f"{attribute} attribute" if parent is None else f"{parent} sub-attribute {attribute}"
            if data is None or attribute not in data:
                message = f"{text} not found"
                if parent and save is True:
                    yaml = YAML(self.config_path)
                    endline = f"\n{parent} sub-attribute {attribute} added to config"
                    if parent not in yaml.data or not yaml.data[parent]:                yaml.data[parent] = {attribute: default}
                    elif attribute not in yaml.data[parent]:                            yaml.data[parent][attribute] = default
                    else:                                                               endline = ""
                    yaml.save()
                if default_is_none and var_type in ["list", "int_list", "comma_list"]: return default if default else []
            elif data[attribute] is None:
                if default_is_none and var_type in ["list", "int_list", "comma_list"]: return default if default else []
                elif default_is_none:                                               return None
                else:                                                               message = f"{text} is blank"
            elif var_type == "url":
                if data[attribute].endswith(("\\", "/")):                           return data[attribute][:-1]
                else:                                                               return data[attribute]
            elif var_type == "bool":
                if isinstance(data[attribute], bool):                               return data[attribute]
                else:                                                               message = f"{text} must be either true or false"
            elif var_type == "int":
                if isinstance(data[attribute], bool):                               message = f"{text} must an integer >= {int_min}"
                elif isinstance(data[attribute], int) and data[attribute] >= int_min: return data[attribute]
                else:                                                               message = f"{text} must an integer >= {int_min}"
            elif var_type == "path":
                if os.path.exists(os.path.abspath(data[attribute])):                return data[attribute]
                else:                                                               message = f"Path {os.path.abspath(data[attribute])} does not exist"
            elif var_type == "list":                                            return util.get_list(data[attribute], split=False)
            elif var_type == "comma_list":                                      return util.get_list(data[attribute])
            elif var_type == "int_list":                                        return util.get_list(data[attribute], int_list=True)
            elif var_type == "list_path":
                temp_list = []
                warning_message = ""
                for p in util.get_list(data[attribute], split=False):
                    if os.path.exists(os.path.abspath(p)):
                        temp_list.append(p)
                    else:
                        if len(warning_message) > 0:
                            warning_message += "\n"
                        warning_message += f"Config Warning: Path does not exist: {os.path.abspath(p)}"
                if do_print and warning_message:
                    logger.warning(warning_message)
                if len(temp_list) > 0:                                              return temp_list
                else:                                                               message = "No Paths exist"
            elif var_type == "lower_list":                                      return util.get_list(data[attribute], lower=True)
            elif test_list is None or data[attribute] in test_list:             return data[attribute]
            else:                                                               message = f"{text}: {data[attribute]} is an invalid input"
            if var_type == "path" and default and os.path.exists(os.path.abspath(default)):
                return default
            elif var_type == "path" and default:
                if data and attribute in data and data[attribute]:
                    message = f"neither {data[attribute]} or the default path {default} could be found"
                else:
                    message = f"no {text} found and the default path {default} could not be found"
                default = None
            if default is not None or default_is_none:
                message = message + f" using {default} as default"
            message = message + endline
            if req_default and default is None:
                raise Failed(f"Config Error: {attribute} attribute must be set under {parent} globally or under this specific Library")
            options = ""
            if test_list:
                for option, description in test_list.items():
                    if len(options) > 0:
                        options = f"{options}\n"
                    options = f"{options}    {option} ({description})"
            if (default is None and not default_is_none) or throw:
                if len(options) > 0:
                    message = message + "\n" + options
                raise Failed(f"Config Error: {message}")
            if do_print:
                logger.warning(f"Config Warning: {message}")
                if data and attribute in data and data[attribute] and test_list is not None and data[attribute] not in test_list:
                    logger.warning(options)
            return default

        self.general = {
            "cache": check_for_attribute(self.data, "cache", parent="settings", var_type="bool", default=True),
            "cache_expiration": check_for_attribute(self.data, "cache_expiration", parent="settings", var_type="int", default=60, int_min=1),
            "asset_directory": check_for_attribute(self.data, "asset_directory", parent="settings", var_type="list_path", default_is_none=True),
            "asset_folders": check_for_attribute(self.data, "asset_folders", parent="settings", var_type="bool", default=True),
            "asset_depth": check_for_attribute(self.data, "asset_depth", parent="settings", var_type="int", default=0),
            "create_asset_folders": check_for_attribute(self.data, "create_asset_folders", parent="settings", var_type="bool", default=False),
            "prioritize_assets": check_for_attribute(self.data, "prioritize_assets", parent="settings", var_type="bool", default=False),
            "dimensional_asset_rename": check_for_attribute(self.data, "dimensional_asset_rename", parent="settings", var_type="bool", default=False),
            "download_url_assets": check_for_attribute(self.data, "download_url_assets", parent="settings", var_type="bool", default=False),
            "show_missing_assets": check_for_attribute(self.data, "show_missing_assets", parent="settings", var_type="bool", default=True),
            "show_missing_season_assets": check_for_attribute(self.data, "show_missing_season_assets", parent="settings", var_type="bool", default=False),
            "show_missing_episode_assets": check_for_attribute(self.data, "show_missing_episode_assets", parent="settings", var_type="bool", default=False),
            "show_asset_not_needed": check_for_attribute(self.data, "show_asset_not_needed", parent="settings", var_type="bool", default=True),
            "sync_mode": check_for_attribute(self.data, "sync_mode", parent="settings", default="append", test_list=sync_modes),
            "default_collection_order": check_for_attribute(self.data, "default_collection_order", parent="settings", default_is_none=True),
            "minimum_items": check_for_attribute(self.data, "minimum_items", parent="settings", var_type="int", default=1),
            "item_refresh_delay": check_for_attribute(self.data, "item_refresh_delay", parent="settings", var_type="int", default=0),
            "delete_below_minimum": check_for_attribute(self.data, "delete_below_minimum", parent="settings", var_type="bool", default=False),
            "delete_not_scheduled": check_for_attribute(self.data, "delete_not_scheduled", parent="settings", var_type="bool", default=False),
            "run_again_delay": check_for_attribute(self.data, "run_again_delay", parent="settings", var_type="int", default=0),
            "missing_only_released": check_for_attribute(self.data, "missing_only_released", parent="settings", var_type="bool", default=False),
            "only_filter_missing": check_for_attribute(self.data, "only_filter_missing", parent="settings", var_type="bool", default=False),
            "show_unmanaged": check_for_attribute(self.data, "show_unmanaged", parent="settings", var_type="bool", default=True),
            "show_unconfigured": check_for_attribute(self.data, "show_unconfigured", parent="settings", var_type="bool", default=True),
            "show_filtered": check_for_attribute(self.data, "show_filtered", parent="settings", var_type="bool", default=False),
            "show_options": check_for_attribute(self.data, "show_options", parent="settings", var_type="bool", default=False),
            "show_missing": check_for_attribute(self.data, "show_missing", parent="settings", var_type="bool", default=True),
            "save_report": check_for_attribute(self.data, "save_report", parent="settings", var_type="bool", default=False),
            "tvdb_language": check_for_attribute(self.data, "tvdb_language", parent="settings", default="default"),
            "ignore_ids": check_for_attribute(self.data, "ignore_ids", parent="settings", var_type="int_list", default_is_none=True),
            "ignore_imdb_ids": check_for_attribute(self.data, "ignore_imdb_ids", parent="settings", var_type="list", default_is_none=True),
            "playlist_sync_to_users": check_for_attribute(self.data, "playlist_sync_to_users", parent="settings", default="all", default_is_none=True),
            "playlist_exclude_users": check_for_attribute(self.data, "playlist_exclude_users", parent="settings", default_is_none=True),
            "playlist_report": check_for_attribute(self.data, "playlist_report", parent="settings", var_type="bool", default=True),
            "verify_ssl": check_for_attribute(self.data, "verify_ssl", parent="settings", var_type="bool", default=True),
            "custom_repo": check_for_attribute(self.data, "custom_repo", parent="settings", default_is_none=True),
            "check_nightly": check_for_attribute(self.data, "check_nightly", parent="settings", var_type="bool", default=False),
            "assets_for_all": check_for_attribute(self.data, "assets_for_all", parent="settings", var_type="bool", default=False, save=False, do_print=False)
        }
        self.custom_repo = None
        if self.general["custom_repo"]:
            repo = self.general["custom_repo"]
            if "https://github.com/" in repo:
                repo = repo.replace("https://github.com/", "https://raw.githubusercontent.com/").replace("/tree/", "/")
            self.custom_repo = repo
        self.check_nightly = self.general["check_nightly"]
        self.latest_version = util.current_version(self.version, branch=self.branch, nightly=self.check_nightly)

        self.session = requests.Session()
        if not self.general["verify_ssl"]:
            self.session.verify = False
            if self.session.verify is False:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        if self.general["cache"]:
            logger.separator()
            self.Cache = Cache(self.config_path, self.general["cache_expiration"])
        else:
            self.Cache = None
        self.GitHub = GitHub(self)

        logger.separator()

        self.NotifiarrFactory = None
        if "notifiarr" in self.data:
            logger.info("Connecting to Notifiarr...")
            try:
                self.NotifiarrFactory = Notifiarr(self, {"apikey": check_for_attribute(self.data, "apikey", parent="notifiarr", throw=True)})
            except Failed as e:
                if str(e).endswith("is blank"):
                    logger.warning(e)
                else:
                    logger.stacktrace()
                    logger.error(e)
            logger.info(f"Notifiarr Connection {'Failed' if self.NotifiarrFactory is None else 'Successful'}")
        else:
            logger.warning("notifiarr attribute not found")

        self.webhooks = {
            "error": check_for_attribute(self.data, "error", parent="webhooks", var_type="list", default_is_none=True),
            "version": check_for_attribute(self.data, "version", parent="webhooks", var_type="list", default_is_none=True),
            "run_start": check_for_attribute(self.data, "run_start", parent="webhooks", var_type="list", default_is_none=True),
            "run_end": check_for_attribute(self.data, "run_end", parent="webhooks", var_type="list", default_is_none=True),
            "changes": check_for_attribute(self.data, "changes", parent="webhooks", var_type="list", default_is_none=True),
            "delete": check_for_attribute(self.data, "delete", parent="webhooks", var_type="list", default_is_none=True)
        }
        self.Webhooks = Webhooks(self, self.webhooks, notifiarr=self.NotifiarrFactory)
        try:
            self.Webhooks.start_time_hooks(self.start_time)
            if self.version[0] != "Unknown" and self.latest_version[0] != "Unknown" and self.version[1] != self.latest_version[1] or (self.version[2] and self.version[2] < self.latest_version[2]):
                self.Webhooks.version_hooks(self.version, self.latest_version)
        except Failed as e:
            logger.stacktrace()
            logger.error(f"Webhooks Error: {e}")

        logger.save_errors = True
        logger.separator()

        try:
            self.TMDb = None
            if "tmdb" in self.data:
                logger.info("Connecting to TMDb...")
                self.TMDb = TMDb(self, {
                    "apikey": check_for_attribute(self.data, "apikey", parent="tmdb", throw=True),
                    "language": check_for_attribute(self.data, "language", parent="tmdb", default="en"),
                    "expiration": check_for_attribute(self.data, "cache_expiration", parent="tmdb", var_type="int", default=60, int_min=1)
                })
                regions = {k.upper(): v for k, v in self.TMDb.iso_3166_1.items()}
                region = check_for_attribute(self.data, "region", parent="tmdb", test_list=regions, default_is_none=True)
                self.TMDb.region = str(region).upper() if region else region
                logger.info(f"TMDb Connection {'Failed' if self.TMDb is None else 'Successful'}")
            else:
                raise Failed("Config Error: tmdb attribute not found")

            logger.separator()

            self.OMDb = None
            if "omdb" in self.data:
                logger.info("Connecting to OMDb...")
                try:
                    self.OMDb = OMDb(self, {
                        "apikey": check_for_attribute(self.data, "apikey", parent="omdb", throw=True),
                        "expiration": check_for_attribute(self.data, "cache_expiration", parent="omdb", var_type="int", default=60, int_min=1)
                    })
                except Failed as e:
                    if str(e).endswith("is blank"):
                        logger.warning(e)
                    else:
                        logger.error(e)
                logger.info(f"OMDb Connection {'Failed' if self.OMDb is None else 'Successful'}")
            else:
                logger.warning("omdb attribute not found")

            logger.separator()

            self.Mdblist = Mdblist(self)
            if "mdblist" in self.data:
                logger.info("Connecting to Mdblist...")
                try:
                    self.Mdblist.add_key(
                        check_for_attribute(self.data, "apikey", parent="mdblist", throw=True),
                        check_for_attribute(self.data, "cache_expiration", parent="mdblist", var_type="int", default=60, int_min=1)
                    )
                    logger.info("Mdblist Connection Successful")
                except Failed as e:
                    if str(e).endswith("is blank"):
                        logger.warning(e)
                    else:
                        logger.error(e)
                    logger.info("Mdblist Connection Failed")
            else:
                logger.warning("mdblist attribute not found")

            logger.separator()

            self.Trakt = None
            if "trakt" in self.data:
                logger.info("Connecting to Trakt...")
                try:
                    self.Trakt = Trakt(self, {
                        "client_id": check_for_attribute(self.data, "client_id", parent="trakt", throw=True),
                        "client_secret": check_for_attribute(self.data, "client_secret", parent="trakt", throw=True),
                        "pin":  check_for_attribute(self.data, "pin", parent="trakt", default_is_none=True),
                        "config_path": self.config_path,
                        "authorization": self.data["trakt"]["authorization"] if "authorization" in self.data["trakt"] else None
                    })
                except Failed as e:
                    if str(e).endswith("is blank"):
                        logger.warning(e)
                    else:
                        logger.error(e)
                logger.info(f"Trakt Connection {'Failed' if self.Trakt is None else 'Successful'}")
            else:
                logger.warning("trakt attribute not found")

            logger.separator()

            self.MyAnimeList = None
            if "mal" in self.data:
                logger.info("Connecting to My Anime List...")
                try:
                    self.MyAnimeList = MyAnimeList(self, {
                        "client_id": check_for_attribute(self.data, "client_id", parent="mal", throw=True),
                        "client_secret": check_for_attribute(self.data, "client_secret", parent="mal", throw=True),
                        "localhost_url": check_for_attribute(self.data, "localhost_url", parent="mal", default_is_none=True),
                        "cache_expiration": check_for_attribute(self.data, "cache_expiration", parent="mal", var_type="int", default=60, int_min=1),
                        "config_path": self.config_path,
                        "authorization": self.data["mal"]["authorization"] if "authorization" in self.data["mal"] else None
                    })
                except Failed as e:
                    if str(e).endswith("is blank"):
                        logger.warning(e)
                    else:
                        logger.error(e)
                logger.info(f"My Anime List Connection {'Failed' if self.MyAnimeList is None else 'Successful'}")
            else:
                logger.warning("mal attribute not found")

            self.AniDB = AniDB(self, {"language": check_for_attribute(self.data, "language", parent="anidb", default="en")})
            if "anidb" in self.data:
                logger.separator()
                logger.info("Connecting to AniDB...")
                try:
                    self.AniDB.authorize(
                        check_for_attribute(self.data, "client", parent="anidb", throw=True),
                        check_for_attribute(self.data, "version", parent="anidb", var_type="int", throw=True),
                        check_for_attribute(self.data, "cache_expiration", parent="anidb", var_type="int", default=60, int_min=1)
                    )
                except Failed as e:
                    if str(e).endswith("is blank"):
                        logger.warning(e)
                    else:
                        logger.error(e)
                logger.info(f"AniDB API Connection {'Successful' if self.AniDB.is_authorized else 'Failed'}")
                try:
                    self.AniDB.login(
                        check_for_attribute(self.data, "username", parent="anidb", throw=True),
                        check_for_attribute(self.data, "password", parent="anidb", throw=True)
                    )
                except Failed as e:
                    if str(e).endswith("is blank"):
                        logger.warning(e)
                    else:
                        logger.error(e)
                logger.info(f"AniDB Login {'Successful' if self.AniDB.username else 'Failed Continuing as Guest'}")

            logger.separator()

            self.playlist_names = []
            self.playlist_files = []
            if "playlist_files" in self.data:
                logger.info("Reading in Playlist Files")
                if self.data["playlist_files"]:
                    paths_to_check = self.data["playlist_files"]
                else:
                    default_playlist_file = os.path.abspath(os.path.join(self.default_dir, "playlists.yml"))
                    logger.warning(f"Config Warning: playlist_files attribute is blank using default: {default_playlist_file}")
                    paths_to_check = [default_playlist_file]
                files = util.load_files(paths_to_check, "playlist_files", schedule=(current_time, self.run_hour, self.ignore_schedules))
                if not files:
                    raise Failed("Config Error: No Paths Found for playlist_files")
                for file_type, playlist_file, temp_vars, asset_directory in files:
                    try:
                        playlist_obj = PlaylistFile(self, file_type, playlist_file, temp_vars, asset_directory)
                        self.playlist_names.extend([p for p in playlist_obj.playlists])
                        self.playlist_files.append(playlist_obj)
                    except Failed as e:
                        logger.info(f"Playlist File Failed To Load")
                        logger.error(e)
            else:
                logger.warning("playlist_files attribute not found")

            self.TVDb = TVDb(self, self.general["tvdb_language"], self.general["cache_expiration"])
            self.IMDb = IMDb(self)
            self.Convert = Convert(self)
            self.AniList = AniList(self)
            self.FlixPatrol = FlixPatrol(self)
            self.ICheckMovies = ICheckMovies(self)
            self.Letterboxd = Letterboxd(self)
            self.Reciperr = Reciperr(self)
            self.Ergast = Ergast(self)

            logger.separator()

            logger.info("Connecting to Plex Libraries...")

            self.general["plex"] = {
                "url": check_for_attribute(self.data, "url", parent="plex", var_type="url", default_is_none=True),
                "token": check_for_attribute(self.data, "token", parent="plex", default_is_none=True),
                "timeout": check_for_attribute(self.data, "timeout", parent="plex", var_type="int", default=60),
                "clean_bundles": check_for_attribute(self.data, "clean_bundles", parent="plex", var_type="bool", default=False),
                "empty_trash": check_for_attribute(self.data, "empty_trash", parent="plex", var_type="bool", default=False),
                "optimize": check_for_attribute(self.data, "optimize", parent="plex", var_type="bool", default=False)
            }
            self.general["radarr"] = {
                "url": check_for_attribute(self.data, "url", parent="radarr", var_type="url", default_is_none=True),
                "token": check_for_attribute(self.data, "token", parent="radarr", default_is_none=True),
                "add_missing": check_for_attribute(self.data, "add_missing", parent="radarr", var_type="bool", default=False),
                "add_existing": check_for_attribute(self.data, "add_existing", parent="radarr", var_type="bool", default=False),
                "upgrade_existing": check_for_attribute(self.data, "upgrade_existing", parent="radarr", var_type="bool", default=False),
                "ignore_cache": check_for_attribute(self.data, "ignore_cache", parent="radarr", var_type="bool", default=False),
                "root_folder_path": check_for_attribute(self.data, "root_folder_path", parent="radarr", default_is_none=True),
                "monitor": check_for_attribute(self.data, "monitor", parent="radarr", var_type="bool", default=True),
                "availability": check_for_attribute(self.data, "availability", parent="radarr", test_list=radarr.availability_descriptions, default="announced"),
                "quality_profile": check_for_attribute(self.data, "quality_profile", parent="radarr", default_is_none=True),
                "tag": check_for_attribute(self.data, "tag", parent="radarr", var_type="lower_list", default_is_none=True),
                "search": check_for_attribute(self.data, "search", parent="radarr", var_type="bool", default=False),
                "radarr_path": check_for_attribute(self.data, "radarr_path", parent="radarr", default_is_none=True),
                "plex_path": check_for_attribute(self.data, "plex_path", parent="radarr", default_is_none=True)
            }
            self.general["sonarr"] = {
                "url": check_for_attribute(self.data, "url", parent="sonarr", var_type="url", default_is_none=True),
                "token": check_for_attribute(self.data, "token", parent="sonarr", default_is_none=True),
                "add_missing": check_for_attribute(self.data, "add_missing", parent="sonarr", var_type="bool", default=False),
                "add_existing": check_for_attribute(self.data, "add_existing", parent="sonarr", var_type="bool", default=False),
                "upgrade_existing": check_for_attribute(self.data, "upgrade_existing", parent="sonarr", var_type="bool", default=False),
                "ignore_cache": check_for_attribute(self.data, "ignore_cache", parent="sonarr", var_type="bool", default=False),
                "root_folder_path": check_for_attribute(self.data, "root_folder_path", parent="sonarr", default_is_none=True),
                "monitor": check_for_attribute(self.data, "monitor", parent="sonarr", test_list=sonarr.monitor_descriptions, default="all"),
                "quality_profile": check_for_attribute(self.data, "quality_profile", parent="sonarr", default_is_none=True),
                "language_profile": check_for_attribute(self.data, "language_profile", parent="sonarr", default_is_none=True),
                "series_type": check_for_attribute(self.data, "series_type", parent="sonarr", test_list=sonarr.series_type_descriptions, default="standard"),
                "season_folder": check_for_attribute(self.data, "season_folder", parent="sonarr", var_type="bool", default=True),
                "tag": check_for_attribute(self.data, "tag", parent="sonarr", var_type="lower_list", default_is_none=True),
                "search": check_for_attribute(self.data, "search", parent="sonarr", var_type="bool", default=False),
                "cutoff_search": check_for_attribute(self.data, "cutoff_search", parent="sonarr", var_type="bool", default=False),
                "sonarr_path": check_for_attribute(self.data, "sonarr_path", parent="sonarr", default_is_none=True),
                "plex_path": check_for_attribute(self.data, "plex_path", parent="sonarr", default_is_none=True)
            }
            self.general["tautulli"] = {
                "url": check_for_attribute(self.data, "url", parent="tautulli", var_type="url", default_is_none=True),
                "apikey": check_for_attribute(self.data, "apikey", parent="tautulli", default_is_none=True)
            }

            self.libraries = []
            libs = check_for_attribute(self.data, "libraries", throw=True)

            for library_name, lib in libs.items():
                if self.requested_libraries and library_name not in self.requested_libraries:
                    continue
                params = {o: None for o in library_operations}
                params["mapping_name"] = str(library_name)
                params["name"] = str(lib["library_name"]) if lib and "library_name" in lib and lib["library_name"] else str(library_name)
                display_name = f"{params['name']} ({params['mapping_name']})" if lib and "library_name" in lib and lib["library_name"] else params["mapping_name"]

                logger.separator(f"{display_name} Configuration")
                logger.info("")
                logger.info(f"Connecting to {display_name} Library...")

                params["asset_directory"] = check_for_attribute(lib, "asset_directory", parent="settings", var_type="list_path", default=self.general["asset_directory"], default_is_none=True, save=False)
                params["asset_folders"] = check_for_attribute(lib, "asset_folders", parent="settings", var_type="bool", default=self.general["asset_folders"], do_print=False, save=False)
                params["asset_depth"] = check_for_attribute(lib, "asset_depth", parent="settings", var_type="int", default=self.general["asset_depth"], do_print=False, save=False)
                params["sync_mode"] = check_for_attribute(lib, "sync_mode", parent="settings", test_list=sync_modes, default=self.general["sync_mode"], do_print=False, save=False)
                params["default_collection_order"] = check_for_attribute(lib, "default_collection_order", parent="settings", default=self.general["default_collection_order"], default_is_none=True, do_print=False, save=False)
                params["show_unmanaged"] = check_for_attribute(lib, "show_unmanaged", parent="settings", var_type="bool", default=self.general["show_unmanaged"], do_print=False, save=False)
                params["show_unconfigured"] = check_for_attribute(lib, "show_unconfigured", parent="settings", var_type="bool", default=self.general["show_unconfigured"], do_print=False, save=False)
                params["show_filtered"] = check_for_attribute(lib, "show_filtered", parent="settings", var_type="bool", default=self.general["show_filtered"], do_print=False, save=False)
                params["show_options"] = check_for_attribute(lib, "show_options", parent="settings", var_type="bool", default=self.general["show_options"], do_print=False, save=False)
                params["show_missing"] = check_for_attribute(lib, "show_missing", parent="settings", var_type="bool", default=self.general["show_missing"], do_print=False, save=False)
                params["show_missing_assets"] = check_for_attribute(lib, "show_missing_assets", parent="settings", var_type="bool", default=self.general["show_missing_assets"], do_print=False, save=False)
                params["save_report"] = check_for_attribute(lib, "save_report", parent="settings", var_type="bool", default=self.general["save_report"], do_print=False, save=False)
                params["missing_only_released"] = check_for_attribute(lib, "missing_only_released", parent="settings", var_type="bool", default=self.general["missing_only_released"], do_print=False, save=False)
                params["only_filter_missing"] = check_for_attribute(lib, "only_filter_missing", parent="settings", var_type="bool", default=self.general["only_filter_missing"], do_print=False, save=False)
                params["create_asset_folders"] = check_for_attribute(lib, "create_asset_folders", parent="settings", var_type="bool", default=self.general["create_asset_folders"], do_print=False, save=False)
                params["dimensional_asset_rename"] = check_for_attribute(lib, "dimensional_asset_rename", parent="settings", var_type="bool", default=self.general["dimensional_asset_rename"], do_print=False, save=False)
                params["prioritize_assets"] = check_for_attribute(lib, "prioritize_assets", parent="settings", var_type="bool", default=self.general["prioritize_assets"], do_print=False, save=False)
                params["download_url_assets"] = check_for_attribute(lib, "download_url_assets", parent="settings", var_type="bool", default=self.general["download_url_assets"], do_print=False, save=False)
                params["show_missing_season_assets"] = check_for_attribute(lib, "show_missing_season_assets", parent="settings", var_type="bool", default=self.general["show_missing_season_assets"], do_print=False, save=False)
                params["show_missing_episode_assets"] = check_for_attribute(lib, "show_missing_episode_assets", parent="settings", var_type="bool", default=self.general["show_missing_episode_assets"], do_print=False, save=False)
                params["show_asset_not_needed"] = check_for_attribute(lib, "show_asset_not_needed", parent="settings", var_type="bool", default=self.general["show_asset_not_needed"], do_print=False, save=False)
                params["minimum_items"] = check_for_attribute(lib, "minimum_items", parent="settings", var_type="int", default=self.general["minimum_items"], do_print=False, save=False)
                params["item_refresh_delay"] = check_for_attribute(lib, "item_refresh_delay", parent="settings", var_type="int", default=self.general["item_refresh_delay"], do_print=False, save=False)
                params["delete_below_minimum"] = check_for_attribute(lib, "delete_below_minimum", parent="settings", var_type="bool", default=self.general["delete_below_minimum"], do_print=False, save=False)
                params["delete_not_scheduled"] = check_for_attribute(lib, "delete_not_scheduled", parent="settings", var_type="bool", default=self.general["delete_not_scheduled"], do_print=False, save=False)
                params["ignore_ids"] = check_for_attribute(lib, "ignore_ids", parent="settings", var_type="int_list", default_is_none=True, do_print=False, save=False)
                params["ignore_ids"].extend([i for i in self.general["ignore_ids"] if i not in params["ignore_ids"]])
                params["ignore_imdb_ids"] = check_for_attribute(lib, "ignore_imdb_ids", parent="settings", var_type="list", default_is_none=True, do_print=False, save=False)
                params["ignore_imdb_ids"].extend([i for i in self.general["ignore_imdb_ids"] if i not in params["ignore_imdb_ids"]])
                params["changes_webhooks"] = check_for_attribute(lib, "changes", parent="webhooks", var_type="list", default=self.webhooks["changes"], do_print=False, save=False, default_is_none=True)
                params["report_path"] = None
                if lib and "report_path" in lib and lib["report_path"]:
                    if os.path.exists(os.path.dirname(os.path.abspath(lib["report_path"]))):
                        params["report_path"] = lib["report_path"]
                    else:
                        logger.error(f"Config Error: Folder {os.path.dirname(os.path.abspath(lib['report_path']))} does not exist")
                if lib and "operations" in lib and lib["operations"]:
                    if isinstance(lib["operations"], dict):
                        if "delete_collections" not in lib["operations"] and ("delete_unmanaged_collections" in lib["operations"] or "delete_collections_with_less" in lib["operations"]):
                            lib["operations"]["delete_collections"] = {}
                            if "delete_unmanaged_collections" in lib["operations"]:
                                lib["operations"]["delete_collections"]["unmanaged"] = check_for_attribute(lib["operations"], "delete_unmanaged_collections", var_type="bool", default=False, save=False)
                            if "delete_collections_with_less" in lib["operations"]:
                                lib["operations"]["delete_collections"]["less"] = check_for_attribute(lib["operations"], "delete_collections_with_less", var_type="int", default_is_none=True, save=False)
                        for op, data_type in library_operations.items():
                            if op not in lib["operations"]:
                                continue
                            elif isinstance(data_type, list):
                                params[op] = check_for_attribute(lib["operations"], op, test_list=data_type, default_is_none=True, save=False)
                            elif data_type == "mass_collection_mode":
                                params[op] = util.check_collection_mode(lib["operations"][op])
                            elif data_type in ["metadata_backup", "mapper", "delete_collections"]:
                                if not lib["operations"][op] or not isinstance(lib["operations"][op], dict):
                                    raise Failed(f"Config Error: {op} must be a dictionary")
                                if data_type == "metadata_backup":
                                    default_path = os.path.join(default_dir, f"{str(library_name)}_Metadata_Backup.yml")
                                    try:
                                        default_path = check_for_attribute(lib["operations"][op], "path", var_type="path", save=False)
                                    except Failed as e:
                                        logger.debug(f"{e} using default {default_path}")
                                    params[op] = {
                                        "path": default_path,
                                        "exclude": check_for_attribute(lib["operations"][op], "exclude", var_type="comma_list", default_is_none=True, save=False),
                                        "sync_tags": check_for_attribute(lib["operations"][op], "sync_tags", var_type="bool", default=False, save=False),
                                        "add_blank_entries": check_for_attribute(lib["operations"][op], "add_blank_entries", var_type="bool", default=True, save=False)
                                    }
                                if data_type == "mapper":
                                    params[op] = lib["operations"][op]
                                    for old_value, new_value in lib["operations"][op].items():
                                        if old_value == new_value:
                                            logger.warning(f"Config Warning: {op} value '{new_value}' ignored as it cannot be mapped to itself")
                                        else:
                                            params[op][old_value] = new_value if new_value else None
                                if data_type == "delete_collections":
                                    params[op] = {
                                        "managed": check_for_attribute(lib["operations"][op], "managed", var_type="bool", default_is_none=True, save=False),
                                        "configured": check_for_attribute(lib["operations"][op], "configured", var_type="bool", default_is_none=True, save=False),
                                        "less": check_for_attribute(lib["operations"][op], "less", var_type="int", default_is_none=True, save=False, int_min=1),
                                    }
                            else:
                                params[op] = check_for_attribute(lib["operations"], op, var_type=data_type, default=False, save=False)
                    else:
                        logger.error("Config Error: operations must be a dictionary")

                def error_check(err_attr, service):
                    logger.error(f"Config Error: Operation {err_attr} cannot be {params[err_attr]} without a successful {service} Connection")
                    params[err_attr] = None

                for mass_key in operations.meta_operations:
                    if params[mass_key] == "omdb" and self.OMDb is None:
                        error_check(mass_key, "OMDb")
                    if params[mass_key] and params[mass_key].startswith("mdb") and not self.Mdblist.has_key:
                        error_check(mass_key, "MdbList")
                    if params[mass_key] and params[mass_key].startswith("anidb") and not self.AniDB.is_authorized:
                        error_check(mass_key, "AniDB")
                    if params[mass_key] and params[mass_key].startswith("mal") and self.MyAnimeList is None:
                        error_check(mass_key, "MyAnimeList")
                    if params[mass_key] and params[mass_key].startswith("trakt") and self.Trakt is None:
                        error_check(mass_key, "Trakt")

                lib_vars = {}
                if lib and "template_variables" in lib and lib["template_variables"] and isinstance(lib["template_variables"], dict):
                    lib_vars = lib["template_variables"]

                params["metadata_path"] = []
                try:
                    if lib and "metadata_path" in lib:
                        if not lib["metadata_path"]:
                            raise Failed("Config Error: metadata_path attribute is blank")
                        files = util.load_files(lib["metadata_path"], "metadata_path", schedule=(current_time, self.run_hour, self.ignore_schedules), lib_vars=lib_vars)
                        if not files:
                            raise Failed("Config Error: No Paths Found for metadata_path")
                        params["metadata_path"] = files
                    elif os.path.exists(os.path.join(default_dir, f"{library_name}.yml")):
                        params["metadata_path"] = [("File", os.path.join(default_dir, f"{library_name}.yml"), lib_vars, None)]
                except Failed as e:
                    logger.error(e)
                params["default_dir"] = default_dir

                params["skip_library"] = False
                if lib and "schedule" in lib and not self.requested_libraries and not self.ignore_schedules:
                    if not lib["schedule"]:
                        logger.error(f"Config Error: schedule attribute is blank")
                    else:
                        logger.debug(f"Value: {lib['schedule']}")
                        try:
                            util.schedule_check("schedule", lib["schedule"], current_time, self.run_hour)
                        except NotScheduled:
                            params["skip_library"] = True

                params["overlay_path"] = []
                params["remove_overlays"] = False
                params["reapply_overlays"] = False
                params["reset_overlays"] = None
                if lib and "overlay_path" in lib:
                    try:
                        if not lib["overlay_path"]:
                            raise Failed("Config Error: overlay_path attribute is blank")
                        files = util.load_files(lib["overlay_path"], "overlay_path", lib_vars=lib_vars)
                        for file in util.get_list(lib["overlay_path"], split=False):
                            if isinstance(file, dict):
                                if ("remove_overlays" in file and file["remove_overlays"] is True) \
                                        or ("remove_overlay" in file and file["remove_overlay"] is True) \
                                        or ("revert_overlays" in file and file["revert_overlays"] is True):
                                    params["remove_overlays"] = True
                                if ("reapply_overlays" in file and file["reapply_overlays"] is True) \
                                        or ("reapply_overlay" in file and file["reapply_overlay"] is True):
                                    params["reapply_overlays"] = True
                                if "reset_overlays" in file or "reset_overlay" in file:
                                    attr = f"reset_overlay{'s' if 'reset_overlays' in file else ''}"
                                    if file[attr] and not isinstance(file[attr], list):
                                        test_list = [file[attr]]
                                    else:
                                        test_list = file[attr]
                                    final_list = []
                                    for test_item in test_list:
                                        if test_item and test_item in reset_overlay_options:
                                            final_list.append(test_item)
                                        else:
                                            final_text = f"Config Error: reset_overlays attribute {test_item} invalid. Options: "
                                            for option, description in reset_overlay_options.items():
                                                final_text = f"{final_text}\n    {option} ({description})"
                                            logger.error(final_text)
                                    if final_list:
                                        params["reset_overlays"] = final_list
                                    else:
                                        final_text = f"Config Error: No proper reset_overlays option found. {file[attr]}. Options: "
                                        for option, description in reset_overlay_options.items():
                                            final_text = f"{final_text}\n    {option} ({description})"
                                        logger.error(final_text)
                                if "schedule" in file and file["schedule"]:
                                    logger.debug(f"Value: {file['schedule']}")
                                    err = None
                                    try:
                                        util.schedule_check("schedule", file["schedule"], current_time, self.run_hour)
                                    except NotScheduledRange as e:
                                        err = e
                                    except NotScheduled as e:
                                        if not self.ignore_schedules:
                                            err = e
                                    if err:
                                        raise NotScheduled(f"Overlay Schedule:{err}\n\nOverlays not scheduled to run")
                        if not files and params["remove_overlays"] is False and params["reset_overlays"] is False:
                            raise Failed("Config Error: No Paths Found for overlay_path")
                        params["overlay_path"] = files
                    except NotScheduled as e:
                        logger.info("")
                        logger.info(e)
                        params["overlay_path"] = []
                        params["remove_overlays"] = False
                    except Failed as e:
                        logger.error(e)

                params["images_path"] = []
                try:
                    if lib and "images_path" in lib:
                        if not lib["images_path"]:
                            raise Failed("Config Error: images_path attribute is blank")
                        files = util.load_files(lib["images_path"], "images_path")
                        if not files:
                            raise Failed("Config Error: No Paths Found for images_path")
                        params["images_path"] = files
                except Failed as e:
                    logger.error(e)

                try:
                    logger.info("")
                    logger.separator("Plex Configuration", space=False, border=False)
                    params["plex"] = {
                        "url": check_for_attribute(lib, "url", parent="plex", var_type="url", default=self.general["plex"]["url"], req_default=True, save=False),
                        "token": check_for_attribute(lib, "token", parent="plex", default=self.general["plex"]["token"], req_default=True, save=False),
                        "timeout": check_for_attribute(lib, "timeout", parent="plex", var_type="int", default=self.general["plex"]["timeout"], save=False),
                        "clean_bundles": check_for_attribute(lib, "clean_bundles", parent="plex", var_type="bool", default=self.general["plex"]["clean_bundles"], save=False),
                        "empty_trash": check_for_attribute(lib, "empty_trash", parent="plex", var_type="bool", default=self.general["plex"]["empty_trash"], save=False),
                        "optimize": check_for_attribute(lib, "optimize", parent="plex", var_type="bool", default=self.general["plex"]["optimize"], save=False)
                    }
                    if params["plex"]["url"].lower() == "env":
                        params["plex"]["url"] = self.env_plex_url
                    if params["plex"]["token"].lower() == "env":
                        params["plex"]["token"] = self.env_plex_token
                    library = Plex(self, params)
                    logger.info("")
                    logger.info(f"{display_name} Library Connection Successful")
                    logger.info("")
                    logger.separator("Scanning Metadata and Overlay Files", space=False, border=False)
                    library.scan_files(self.operations_only, self.overlays_only, self.collection_only)
                    if not library.metadata_files and not library.overlay_files and not library.library_operation and not library.images_files and not self.playlist_files:
                        raise Failed("Config Error: No valid metadata files, overlay files, images files, playlist files, or library operations found")
                except Failed as e:
                    logger.stacktrace()
                    logger.error(e)
                    logger.info("")
                    logger.info(f"{display_name} Library Connection Failed")
                    continue

                if self.general["radarr"]["url"] or (lib and "radarr" in lib):
                    logger.info("")
                    logger.separator("Radarr Configuration", space=False, border=False)
                    logger.info("")
                    logger.info(f"Connecting to {display_name} library's Radarr...")
                    logger.info("")
                    try:
                        library.Radarr = Radarr(self, library, {
                            "url": check_for_attribute(lib, "url", parent="radarr", var_type="url", default=self.general["radarr"]["url"], req_default=True, save=False),
                            "token": check_for_attribute(lib, "token", parent="radarr", default=self.general["radarr"]["token"], req_default=True, save=False),
                            "add_missing": check_for_attribute(lib, "add_missing", parent="radarr", var_type="bool", default=self.general["radarr"]["add_missing"], save=False),
                            "add_existing": check_for_attribute(lib, "add_existing", parent="radarr", var_type="bool", default=self.general["radarr"]["add_existing"], save=False),
                            "upgrade_existing": check_for_attribute(lib, "upgrade_existing", parent="radarr", var_type="bool", default=self.general["radarr"]["upgrade_existing"], save=False),
                            "ignore_cache": check_for_attribute(lib, "ignore_cache", parent="radarr", var_type="bool", default=self.general["radarr"]["ignore_cache"], save=False),
                            "root_folder_path": check_for_attribute(lib, "root_folder_path", parent="radarr", default=self.general["radarr"]["root_folder_path"], req_default=True, save=False),
                            "monitor": check_for_attribute(lib, "monitor", parent="radarr", var_type="bool", default=self.general["radarr"]["monitor"], save=False),
                            "availability": check_for_attribute(lib, "availability", parent="radarr", test_list=radarr.availability_descriptions, default=self.general["radarr"]["availability"], save=False),
                            "quality_profile": check_for_attribute(lib, "quality_profile", parent="radarr", default=self.general["radarr"]["quality_profile"], req_default=True, save=False),
                            "tag": check_for_attribute(lib, "tag", parent="radarr", var_type="lower_list", default=self.general["radarr"]["tag"], default_is_none=True, save=False),
                            "search": check_for_attribute(lib, "search", parent="radarr", var_type="bool", default=self.general["radarr"]["search"], save=False),
                            "radarr_path": check_for_attribute(lib, "radarr_path", parent="radarr", default=self.general["radarr"]["radarr_path"], default_is_none=True, save=False),
                            "plex_path": check_for_attribute(lib, "plex_path", parent="radarr", default=self.general["radarr"]["plex_path"], default_is_none=True, save=False)
                        })
                    except Failed as e:
                        logger.stacktrace()
                        logger.error(e)
                        logger.info("")
                    logger.info(f"{display_name} library's Radarr Connection {'Failed' if library.Radarr is None else 'Successful'}")

                if self.general["sonarr"]["url"] or (lib and "sonarr" in lib):
                    logger.info("")
                    logger.separator("Sonarr Configuration", space=False, border=False)
                    logger.info("")
                    logger.info(f"Connecting to {display_name} library's Sonarr...")
                    logger.info("")
                    try:
                        library.Sonarr = Sonarr(self, library, {
                            "url": check_for_attribute(lib, "url", parent="sonarr", var_type="url", default=self.general["sonarr"]["url"], req_default=True, save=False),
                            "token": check_for_attribute(lib, "token", parent="sonarr", default=self.general["sonarr"]["token"], req_default=True, save=False),
                            "add_missing": check_for_attribute(lib, "add_missing", parent="sonarr", var_type="bool", default=self.general["sonarr"]["add_missing"], save=False),
                            "add_existing": check_for_attribute(lib, "add_existing", parent="sonarr", var_type="bool", default=self.general["sonarr"]["add_existing"], save=False),
                            "upgrade_existing": check_for_attribute(lib, "upgrade_existing", parent="sonarr", var_type="bool", default=self.general["sonarr"]["upgrade_existing"], save=False),
                            "ignore_cache": check_for_attribute(lib, "ignore_cache", parent="sonarr", var_type="bool", default=self.general["sonarr"]["ignore_cache"], save=False),
                            "root_folder_path": check_for_attribute(lib, "root_folder_path", parent="sonarr", default=self.general["sonarr"]["root_folder_path"], req_default=True, save=False),
                            "monitor": check_for_attribute(lib, "monitor", parent="sonarr", test_list=sonarr.monitor_descriptions, default=self.general["sonarr"]["monitor"], save=False),
                            "quality_profile": check_for_attribute(lib, "quality_profile", parent="sonarr", default=self.general["sonarr"]["quality_profile"], req_default=True, save=False),
                            "language_profile": check_for_attribute(lib, "language_profile", parent="sonarr", default=self.general["sonarr"]["language_profile"], save=False) if self.general["sonarr"]["language_profile"] else check_for_attribute(lib, "language_profile", parent="sonarr", default_is_none=True, save=False),
                            "series_type": check_for_attribute(lib, "series_type", parent="sonarr", test_list=sonarr.series_type_descriptions, default=self.general["sonarr"]["series_type"], save=False),
                            "season_folder": check_for_attribute(lib, "season_folder", parent="sonarr", var_type="bool", default=self.general["sonarr"]["season_folder"], save=False),
                            "tag": check_for_attribute(lib, "tag", parent="sonarr", var_type="lower_list", default=self.general["sonarr"]["tag"], default_is_none=True, save=False),
                            "search": check_for_attribute(lib, "search", parent="sonarr", var_type="bool", default=self.general["sonarr"]["search"], save=False),
                            "cutoff_search": check_for_attribute(lib, "cutoff_search", parent="sonarr", var_type="bool", default=self.general["sonarr"]["cutoff_search"], save=False),
                            "sonarr_path": check_for_attribute(lib, "sonarr_path", parent="sonarr", default=self.general["sonarr"]["sonarr_path"], default_is_none=True, save=False),
                            "plex_path": check_for_attribute(lib, "plex_path", parent="sonarr", default=self.general["sonarr"]["plex_path"], default_is_none=True, save=False)
                        })
                    except Failed as e:
                        logger.stacktrace()
                        logger.error(e)
                        logger.info("")
                    logger.info(f"{display_name} library's Sonarr Connection {'Failed' if library.Sonarr is None else 'Successful'}")

                if self.general["tautulli"]["url"] or (lib and "tautulli" in lib):
                    logger.info("")
                    logger.separator("Tautulli Configuration", space=False, border=False)
                    logger.info("")
                    logger.info(f"Connecting to {display_name} library's Tautulli...")
                    logger.info("")
                    try:
                        library.Tautulli = Tautulli(self, library, {
                            "url": check_for_attribute(lib, "url", parent="tautulli", var_type="url", default=self.general["tautulli"]["url"], req_default=True, save=False),
                            "apikey": check_for_attribute(lib, "apikey", parent="tautulli", default=self.general["tautulli"]["apikey"], req_default=True, save=False)
                        })
                    except Failed as e:
                        logger.stacktrace()
                        logger.error(e)
                        logger.info("")
                    logger.info(f"{display_name} library's Tautulli Connection {'Failed' if library.Tautulli is None else 'Successful'}")

                library.Webhooks = Webhooks(self, {}, library=library, notifiarr=self.NotifiarrFactory)
                library.Overlays = Overlays(self, library)

                logger.info("")
                self.libraries.append(library)

            logger.separator()

            self.library_map = {_l.original_mapping_name: _l for _l in self.libraries}

            if len(self.libraries) > 0:
                logger.info(f"{len(self.libraries)} Plex Library Connection{'s' if len(self.libraries) > 1 else ''} Successful")
            else:
                raise Failed("Config Error: No libraries were found in config")

            logger.separator()

            if logger.saved_errors:
                self.notify(logger.saved_errors)
        except Exception as e:
            logger.stacktrace()
            self.notify(logger.saved_errors + [e])
            logger.save_errors = False
            logger.clear_errors()
            raise

    def notify(self, text, server=None, library=None, collection=None, playlist=None, critical=True):
        for error in util.get_list(text, split=False):
            try:
                self.Webhooks.error_hooks(error, server=server, library=library, collection=collection, playlist=playlist, critical=critical)
            except Failed as e:
                logger.stacktrace()
                logger.error(f"Webhooks Error: {e}")

    def notify_delete(self, message, server=None, library=None):
        try:
            self.Webhooks.delete_hooks(message, server=server, library=library)
        except Failed as e:
            logger.stacktrace()
            logger.error(f"Webhooks Error: {e}")

    def get_html(self, url, headers=None, params=None):
        return html.fromstring(self.get(url, headers=headers, params=params).content)

    def get_json(self, url, json=None, headers=None, params=None):
        response = self.get(url, json=json, headers=headers, params=params)
        try:
            return response.json()
        except ValueError:
            logger.error(str(response.content))
            raise

    @retry(stop_max_attempt_number=6, wait_fixed=10000)
    def get(self, url, json=None, headers=None, params=None):
        return self.session.get(url, json=json, headers=headers, params=params)

    def get_image_encoded(self, url):
        return base64.b64encode(self.get(url).content).decode('utf-8')

    def post_html(self, url, data=None, json=None, headers=None):
        return html.fromstring(self.post(url, data=data, json=json, headers=headers).content)

    def post_json(self, url, data=None, json=None, headers=None):
        response = self.post(url, data=data, json=json, headers=headers)
        try:
            return response.json()
        except ValueError:
            logger.error(str(response.content))
            raise

    @retry(stop_max_attempt_number=6, wait_fixed=10000)
    def post(self, url, data=None, json=None, headers=None):
        return self.session.post(url, data=data, json=json, headers=headers)

    @property
    def mediastingers(self):
        if self._mediastingers is None:
            self._mediastingers = YAML(input_data=self.get(mediastingers_url).content).data
        return self._mediastingers
