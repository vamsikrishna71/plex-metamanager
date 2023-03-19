import glob, os, re, requests, ruamel.yaml, signal, sys, time
from datetime import datetime, timedelta
from modules.logs import MyLogger
from num2words import num2words
from pathvalidate import is_valid_filename, sanitize_filename
from plexapi.audio import Album, Track
from plexapi.exceptions import BadRequest, NotFound, Unauthorized
from plexapi.video import Season, Episode, Movie

try:
    import msvcrt
    windows = True
except ModuleNotFoundError:
    windows = False


logger: MyLogger = None

class TimeoutExpired(Exception):
    pass

class LimitReached(Exception):
    pass

class Failed(Exception):
    pass

class FilterFailed(Failed):
    pass

class Continue(Exception):
    pass

class Deleted(Exception):
    pass

class NonExisting(Exception):
    pass

class NotScheduled(Exception):
    pass

class NotScheduledRange(NotScheduled):
    pass

class ImageData:
    def __init__(self, attribute, location, prefix="", is_poster=True, is_url=True):
        self.attribute = attribute
        self.location = location
        self.prefix = prefix
        self.is_poster = is_poster
        self.is_url = is_url
        self.compare = location if is_url else os.stat(location).st_size
        self.message = f"{prefix}{'poster' if is_poster else 'background'} to [{'URL' if is_url else 'File'}] {location}"

    def __str__(self):
        return str(self.__dict__)

def retry_if_not_failed(exception):
    return not isinstance(exception, Failed)

def retry_if_not_plex(exception):
    return not isinstance(exception, (BadRequest, NotFound, Unauthorized, Failed))

days_alias = {
    "monday": 0, "mon": 0, "m": 0,
    "tuesday": 1, "tues": 1, "tue": 1, "tu": 1, "t": 1,
    "wednesday": 2, "wed": 2, "w": 2,
    "thursday": 3, "thurs": 3, "thur": 3, "thu": 3, "th": 3, "r": 3,
    "friday": 4, "fri": 4, "f": 4,
    "saturday": 5, "sat": 5, "s": 5,
    "sunday": 6, "sun": 6, "su": 6, "u": 6
}
mod_displays = {
    "": "is", ".not": "is not", ".is": "is", ".isnot": "is not", ".begins": "begins with", ".ends": "ends with", ".before": "is before", ".after": "is after",
    ".gt": "is greater than", ".gte": "is greater than or equal", ".lt": "is less than", ".lte": "is less than or equal", ".regex": "is"
}
pretty_days = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"}
pretty_months = {
    1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
    7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"
}
seasons = ["current", "winter", "spring", "summer", "fall"]
advance_tags_to_edit = {
    "Movie": ["metadata_language", "use_original_title"],
    "Show": ["episode_sorting", "keep_episodes", "delete_episodes", "season_display", "episode_ordering", "metadata_language", "use_original_title"],
    "Artist": ["album_sorting"]
}
tags_to_edit = {
    "Movie": ["genre", "label", "collection", "country", "director", "producer", "writer"],
    "Video": ["genre", "label", "collection", "country", "director", "producer", "writer"],
    "Show": ["genre", "label", "collection"],
    "Artist": ["genre", "label", "style", "mood", "country", "collection", "similar_artist"]
}
collection_mode_options = {
    "default": "default", "hide": "hide",
    "hide_items": "hideItems", "hideitems": "hideItems",
    "show_items": "showItems", "showitems": "showItems"
}
parental_types = ["nudity", "violence", "profanity", "alcohol", "frightening"]
parental_values = ["None", "Mild", "Moderate", "Severe"]
parental_levels = {"none": [], "mild": ["None"], "moderate": ["None", "Mild"], "severe": ["None", "Mild", "Moderate"]}
parental_labels = [f"{t.capitalize()}:{v}" for t in parental_types for v in parental_values]
previous_time = None
start_time = None

def guess_branch(version, env_version, git_branch):
    if git_branch:
        return git_branch
    elif env_version in ["nightly", "develop"]:
        return env_version
    elif version[2] > 0:
        dev_version = get_develop()
        if version[1] != dev_version[1] or version[2] <= dev_version[2]:
            return "develop"
        else:
            return "nightly"
    else:
        return "master"

def current_version(version, branch=None, nightly=False):
    if nightly or branch == "nightly":
        return get_nightly()
    elif branch == "develop":
        return get_develop()
    elif version[2] > 0:
        new_version = get_develop()
        if version[1] != new_version[1] or new_version[2] >= version[2]:
            return new_version
        return get_nightly()
    else:
        return get_master()

nightly_version = None
def get_nightly():
    global nightly_version
    if nightly_version is None:
        nightly_version = get_version("nightly")
    return nightly_version

develop_version = None
def get_develop():
    global develop_version
    if develop_version is None:
        develop_version = get_version("develop")
    return develop_version

master_version = None
def get_master():
    global master_version
    if master_version is None:
        master_version = get_version("master")
    return master_version

def get_version(level):
    try:
        url = f"https://raw.githubusercontent.com/meisnate12/Plex-Meta-Manager/{level}/VERSION"
        return parse_version(requests.get(url).content.decode().strip(), text=level)
    except requests.exceptions.ConnectionError:
        return "Unknown", "Unknown", 0

def parse_version(version, text="develop"):
    version = version.replace("develop", text)
    split_version = version.split(f"-{text}")
    return version, split_version[0], int(split_version[1]) if len(split_version) > 1 else 0

def quote(data):
    return requests.utils.quote(str(data))

def download_image(title, image_url, download_directory, filename):
    response = requests.get(image_url, headers=header())
    if response.status_code >= 400 or "Content-Type" not in response.headers or response.headers["Content-Type"] not in ["image/png", "image/jpeg"]:
        raise Failed(f"Image Error: Failed to download Image URL: {image_url}")
    new_image = os.path.join(download_directory, f"{filename}{'.png' if response.headers['Content-Type'] == 'image/png' else '.jpg'}")
    with open(new_image, "wb") as handler:
        handler.write(response.content)
    return ImageData("asset_directory", new_image, prefix=f"{title}'s ", is_url=False)

def get_image_dicts(group, alias):
    posters = {}
    backgrounds = {}

    for attr in ["url_poster", "file_poster", "url_background", "file_background"]:
        if attr in alias:
            if group[alias[attr]]:
                if "poster" in attr:
                    posters[attr] = group[alias[attr]]
                else:
                    backgrounds[attr] = group[alias[attr]]
            else:
                logger.error(f"Metadata Error: {attr} attribute is blank")
    return posters, backgrounds

def pick_image(title, images, prioritize_assets, download_url_assets, item_dir, is_poster=True, image_name=None):
    image_type = "poster" if is_poster else "background"
    if image_name is None:
        image_name = image_type
    if images:
        logger.debug(f"{len(images)} {image_type}{'s' if len(images) > 1 else ''} found:")
        for i in images:
            logger.debug(f"Method: {i} {image_type.capitalize()}: {images[i]}")
        if prioritize_assets and "asset_directory" in images:
            return images["asset_directory"]
        for attr in ["image_set", f"url_{image_type}", f"file_{image_type}", f"tmdb_{image_type}", "tmdb_profile",
                     "tmdb_list_poster", "tvdb_list_poster", f"tvdb_{image_type}", "asset_directory", "tmdb_person",
                     "tmdb_collection_details", "tmdb_actor_details", "tmdb_crew_details", "tmdb_director_details",
                     "tmdb_producer_details", "tmdb_writer_details", "tmdb_movie_details", "tmdb_list_details",
                     "tvdb_list_details", "tvdb_movie_details", "tvdb_show_details", "tmdb_show_details"]:
            if attr in images:
                if attr in ["image_set", f"url_{image_type}"] and download_url_assets and item_dir:
                    if "asset_directory" in images:
                        return images["asset_directory"]
                    else:
                        try:
                            return download_image(title, images[attr], item_dir, image_name)
                        except Failed as e:
                            logger.error(e)
                if attr == "asset_directory":
                    return images[attr]
                return ImageData(attr, images[attr], is_poster=is_poster, is_url=attr != f"file_{image_type}")

def add_dict_list(keys, value, dict_map):
    for key in keys:
        if key in dict_map:
            dict_map[key].append(int(value))
        else:
            dict_map[key] = [int(value)]

def get_list(data, lower=False, upper=False, split=True, int_list=False, trim=True):
    if split is True:               split = ","
    if data is None:                return None
    elif isinstance(data, list):    list_data = data
    elif isinstance(data, dict):    return [data]
    elif split is False:            list_data = [str(data)]
    else:                           list_data = [s.strip() for s in str(data).split(split)]

    def get_str(input_data):
        return str(input_data).strip() if trim else str(input_data)

    if lower is True:               return [get_str(d).lower() for d in list_data]
    elif upper is True:             return [get_str(d).upper() for d in list_data]
    elif int_list is True:
        try:                            return [int(get_str(d)) for d in list_data]
        except ValueError:              return []
    else:                           return [d if isinstance(d, dict) else get_str(d) for d in list_data]

def get_int_list(data, id_type):
    int_values = []
    for value in get_list(data):
        try:                        int_values.append(regex_first_int(value, id_type))
        except Failed as e:         logger.error(e)
    return int_values

def validate_date(date_text, method, return_as=None):
    if isinstance(date_text, datetime):
        date_obg = date_text
    else:
        try:
            date_obg = datetime.strptime(str(date_text), "%Y-%m-%d" if "-" in str(date_text) else "%m/%d/%Y")
        except ValueError:
            raise Failed(f"Collection Error: {method}: {date_text} must match pattern YYYY-MM-DD (e.g. 2020-12-25) or MM/DD/YYYY (e.g. 12/25/2020)")
    return datetime.strftime(date_obg, return_as) if return_as else date_obg

def validate_regex(data, col_type, validate=True):
    regex_list = get_list(data, split=False)
    valid_regex = []
    for reg in regex_list:
        try:
            re.compile(reg)
            valid_regex.append(reg)
        except re.error:
            err = f"{col_type} Error: Regular Expression Invalid: {reg}"
            if validate:
                raise Failed(err)
            else:
                logger.error(err)
    return valid_regex

def logger_input(prompt, timeout=60):
    if windows:                             return windows_input(prompt, timeout)
    elif hasattr(signal, "SIGALRM"):        return unix_input(prompt, timeout)
    else:                                   raise SystemError("Input Timeout not supported on this system")

def header(language="en-US,en;q=0.5"):
    return {"Accept-Language": "eng" if language == "default" else language, "User-Agent": "Mozilla/5.0 Firefox/102.0"}

def alarm_handler(signum, frame):
    raise TimeoutExpired

def unix_input(prompt, timeout=60):
    prompt = f"| {prompt}: "
    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(timeout)
    try:                return input(prompt)
    except EOFError:    raise Failed("Input Failed")
    finally:            signal.alarm(0)

def windows_input(prompt, timeout=5):
    sys.stdout.write(f"| {prompt}: ")
    sys.stdout.flush()
    result = []
    start_time = time.time()
    while True:
        if msvcrt.kbhit():
            char = msvcrt.getwche()
            if ord(char) == 13: # enter_key
                out = "".join(result)
                print("")
                logger.debug(f"{prompt}: {out}")
                return out
            elif ord(char) >= 32: #space_char
                result.append(char)
        if (time.time() - start_time) > timeout:
            print("")
            raise TimeoutExpired

def get_id_from_imdb_url(imdb_url):
    match = re.search("(tt\\d+)", str(imdb_url))
    if match:           return match.group(1)
    else:               raise Failed(f"Regex Error: Failed to parse IMDb ID from IMDb URL: {imdb_url}")

def regex_first_int(data, id_type, default=None):
    match = re.search("(\\d+)", str(data))
    if match:
        return int(match.group(1))
    elif default:
        logger.warning(f"Regex Warning: Failed to parse {id_type} from {data} using {default} as default")
        return int(default)
    else:
        raise Failed(f"Regex Error: Failed to parse {id_type} from {data}")

def validate_filename(filename):
    if is_valid_filename(str(filename)):
        return filename, None
    else:
        mapping_name = sanitize_filename(str(filename))
        return mapping_name, f"Log Folder Name: {filename} is invalid using {mapping_name}"

def item_title(item):
    if isinstance(item, Season):
        if f"Season {item.index}" == item.title:
            return f"{item.parentTitle} {item.title}"
        else:
            return f"{item.parentTitle} Season {item.index}: {item.title}"
    elif isinstance(item, Episode):
        season = item.parentIndex if item.parentIndex else 0
        episode = item.index if item.index else 0
        show_title = item.grandparentTitle if item.grandparentTitle else ""
        season_title = f"{item.parentTitle}: " if item.parentTitle and f"Season {season}" == item.parentTitle else ""
        return f"{show_title} S{season:02}E{episode:02}: {season_title}{item.title if item.title else ''}"
    elif isinstance(item, Movie) and item.year:
        return f"{item.title} ({item.year})"
    elif isinstance(item, Album):
        return f"{item.parentTitle}: {item.title}"
    elif isinstance(item, Track):
        return f"{item.grandparentTitle}: {item.parentTitle}: {item.title}"
    else:
        return item.title

def item_set(item, item_id):
    return {"title": item_title(item), "tmdb" if isinstance(item, Movie) else "tvdb": item_id}

def is_locked(filepath):
    locked = None
    file_object = None
    if os.path.exists(filepath):
        try:
            file_object = open(filepath, 'a', 8)
            if file_object:
                locked = False
        except IOError:
            locked = True
        finally:
            if file_object:
                file_object.close()
    return locked

def time_window(tw):
    today = datetime.now()
    if tw == "today":
        return f"{today:%Y-%m-%d}"
    elif tw == "yesterday":
        return f"{today - timedelta(days=1):%Y-%m-%d}"
    elif tw == "this_week":
        return f"{today:%Y-0%V}"
    elif tw == "last_week":
        return f"{today - timedelta(weeks=1):%Y-0%V}"
    elif tw == "this_month":
        return f"{today:%Y-%m}"
    elif tw == "last_month" and today.month == 1:
        return f"{today.year - 1}-12"
    elif tw == "last_month":
        return f"{today.year}-{today.month - 1:02}"
    elif tw == "this_year":
        return f"{today.year}"
    elif tw == "last_year":
        return f"{today.year - 1}"
    else:
        return tw

def load_files(files_to_load, method, err_type="Config", schedule=None, lib_vars=None, single=False):
    files = []
    if not lib_vars:
        lib_vars = {}
    files_to_load = get_list(files_to_load, split=False)
    if single and len(files_to_load) > 1:
        raise Failed(f"{err_type} Error: {method} can only have one entry")
    for file in files_to_load:
        if isinstance(file, dict):
            temp_vars = {}
            if "template_variables" in file and file["template_variables"] and isinstance(file["template_variables"], dict):
                temp_vars = file["template_variables"]
            for k, v in lib_vars.items():
                if k not in temp_vars:
                    temp_vars[k] = v
            asset_directory = []
            if "asset_directory" in file and file["asset_directory"]:
                for asset_path in get_list(file["asset_directory"], split=False):
                    if os.path.exists(asset_path):
                        asset_directory.append(asset_path)
                    else:
                        logger.error(f"{err_type} Error: Asset Directory Does Not Exist: {asset_path}")

            current = []
            def check_dict(attr, name):
                if attr in file:
                    if file[attr]:
                        if attr == "git" and file[attr].startswith("PMM/"):
                            current.append(("PMM Default", file[attr][4:], temp_vars, asset_directory))
                        else:
                            current.append((name, file[attr], temp_vars, asset_directory))
                    else:
                        logger.error(f"{err_type} Error: {method} {attr} is blank")

            check_dict("url", "URL")
            check_dict("git", "Git")
            check_dict("pmm", "PMM Default")
            check_dict("repo", "Repo")
            check_dict("file", "File")
            if not single and "folder" in file:
                if file["folder"] is None:
                    logger.error(f"{err_type} Error: {method} folder is blank")
                elif not os.path.isdir(file["folder"]):
                    logger.error(f"{err_type} Error: Folder not found: {file['folder']}")
                else:
                    yml_files = glob_filter(os.path.join(file["folder"], "*.yml"))
                    yml_files.extend(glob_filter(os.path.join(file["folder"], "*.yaml")))
                    if yml_files:
                        current.extend([("File", yml, temp_vars, asset_directory) for yml in yml_files])
                    else:
                        logger.error(f"{err_type} Error: No YAML (.yml|.yaml) files found in {file['folder']}")

            if schedule and "schedule" in file and file["schedule"]:
                current_time, run_hour, ignore_schedules = schedule
                logger.debug(f"Value: {file['schedule']}")
                err = None
                try:
                    schedule_check("schedule", file["schedule"], current_time, run_hour)
                except NotScheduledRange as e:
                    err = e
                except NotScheduled as e:
                    if not ignore_schedules:
                        err = e
                if err:
                    logger.info(f"Metadata Schedule:{err}\n")
                    for file_type, file_path, temp_vars, asset_directory in current:
                        logger.warning(f"{file_type}: {file_path} not scheduled to run")
                    logger.info("")
                    continue
            files.extend(current)
        else:
            if os.path.exists(file):
                files.append(("File", file, {}, None))
            else:
                logger.error(f"{err_type} Error: Path not found: {file}")
    return files

def check_num(num, is_int=True):
    try:
        return int(str(num)) if is_int else float(str(num))
    except (ValueError, TypeError):
        return None

def check_collection_mode(collection_mode):
    if collection_mode and str(collection_mode).lower() in collection_mode_options:
        return collection_mode_options[str(collection_mode).lower()]
    else:
        raise Failed(f"Config Error: {collection_mode} collection_mode invalid\n\tdefault (Library default)\n\thide (Hide Collection)\n\thide_items (Hide Items in this Collection)\n\tshow_items (Show this Collection and its Items)")

def glob_filter(filter_in):
    filter_in = filter_in.translate({ord("["): "[[]", ord("]"): "[]]"}) if "[" in filter_in else filter_in
    return glob.glob(filter_in)

def is_date_filter(value, modifier, data, final, current_time):
    if value is None:
        return True
    if modifier in ["", ".not"]:
        threshold_date = current_time - timedelta(days=data)
        if (modifier == "" and (value is None or value < threshold_date)) \
                or (modifier == ".not" and value and value >= threshold_date):
            return True
    elif modifier in [".before", ".after"]:
        filter_date = validate_date(data, final)
        if (modifier == ".before" and value >= filter_date) or (modifier == ".after" and value <= filter_date):
            return True
    elif modifier == ".regex":
        jailbreak = True
        for check_data in data:
            if re.compile(check_data).match(value.strftime("%m/%d/%Y")):
                jailbreak = True
                break
        if not jailbreak:
            return True
    return False

def is_number_filter(value, modifier, data):
    return value is None or (modifier == "" and value == data) \
            or (modifier == ".not" and value != data) \
            or (modifier == ".gt" and value <= data) \
            or (modifier == ".gte" and value < data) \
            or (modifier == ".lt" and value >= data) \
            or (modifier == ".lte" and value > data)

def is_boolean_filter(value, data):
    return (data and not value) or (not data and value)

def is_string_filter(values, modifier, data):
    jailbreak = False
    if modifier == ".regex":
        logger.trace(f"Regex Values: {values}")
    for value in values:
        for check_value in data:
            if (modifier in ["", ".not"] and check_value.lower() in value.lower()) \
                    or (modifier in [".is", ".isnot"] and value.lower() == check_value.lower()) \
                    or (modifier == ".begins" and value.lower().startswith(check_value.lower())) \
                    or (modifier == ".ends" and value.lower().endswith(check_value.lower())) \
                    or (modifier == ".regex" and re.compile(check_value).search(value)):
                jailbreak = True
                break
        if jailbreak: break
    return (jailbreak and modifier in [".not", ".isnot"]) or (not jailbreak and modifier in ["", ".is", ".begins", ".ends", ".regex"])

def check_day(_m, _d):
    if _m in [1, 3, 5, 7, 8, 10, 12] and _d > 31:
        return _m, 31
    elif _m in [4, 6, 9, 11] and _d > 30:
        return _m, 30
    elif _m == 2 and _d > 28:
        return _m, 28
    else:
        return _m, _d

def schedule_check(attribute, data, current_time, run_hour, is_all=False):
    range_collection = False
    non_existing = False
    all_check = 0
    schedules_run = 0
    next_month = current_time.replace(day=28) + timedelta(days=4)
    last_day = next_month - timedelta(days=next_month.day)
    schedule_str = ""
    if isinstance(data, str) and (("all" in data and not data.endswith("]")) or data.count("all") > 1):
        raise Failed("Schedule Error: each all schedule must be on its own line")
    elif isinstance(data, str) and "all" in data:
        data = [data]
    for schedule in get_list(data):
        run_time = str(schedule).lower()
        display = f"{attribute} attribute {schedule} invalid"
        schedules_run += 1
        if run_time.startswith("all"):
            match = re.search("\\[([^\\]]+)\\]", run_time)
            if not match:
                logger.error(f"Schedule Error: failed to parse {attribute}: {schedule}")
                continue
            try:
                schedule_str += f"\nScheduled to meet all of these:\n\t"
                schedule_str += schedule_check(attribute, match.group(1), current_time, run_hour, is_all=True)
                all_check += 1
            except NotScheduled as e:
                schedule_str += str(e)
                continue
        elif run_time.startswith(("day", "daily")):
            all_check += 1
        elif run_time.startswith("non_existing"):
            all_check += 1
            non_existing = True
        elif run_time == "never":
            schedule_str += f"\nNever scheduled to run"
        elif run_time.startswith(("hour", "week", "month", "year", "range")):
            match = re.search("\\(([^)]+)\\)", run_time)
            if not match:
                logger.error(f"Schedule Error: failed to parse {attribute}: {schedule}")
                continue
            param = match.group(1)
            if run_time.startswith("hour"):
                try:
                    if 0 <= int(param) <= 23:
                        schedule_str += f"\nScheduled to run on the {num2words(param, to='ordinal_num')} hour"
                        if run_hour == int(param):
                            all_check += 1
                    else:
                        raise ValueError
                except ValueError:
                    logger.error(f"Schedule Error: hourly {display} must be an integer between 0 and 23")
            elif run_time.startswith("week"):
                if param.lower() not in days_alias:
                    logger.error(f"Schedule Error: weekly {display} must be a day of the week i.e. weekly(Monday)")
                    continue
                weekday = days_alias[param.lower()]
                schedule_str += f"\nScheduled weekly on {pretty_days[weekday]}"
                if weekday == current_time.weekday():
                    all_check += 1
            elif run_time.startswith("month"):
                try:
                    if 1 <= int(param) <= 31:
                        schedule_str += f"\nScheduled monthly on the {num2words(param, to='ordinal_num')}"
                        if current_time.day == int(param) or (current_time.day == last_day.day and int(param) > last_day.day):
                            all_check += 1
                    else:
                        raise ValueError
                except ValueError:
                    logger.error(f"Schedule Error: monthly {display} must be an integer between 1 and 31")
            elif run_time.startswith("year"):
                try:
                    if "/" in param:
                        opt = param.split("/")
                        month = int(opt[0])
                        day = int(opt[1])
                        schedule_str += f"\nScheduled yearly on {pretty_months[month]} {num2words(day, to='ordinal_num')}"
                        if current_time.month == month and (current_time.day == day or (current_time.day == last_day.day and day > last_day.day)):
                            all_check += 1
                    else:
                        raise ValueError
                except ValueError:
                    logger.error(f"Schedule Error: yearly {display} must be in the MM/DD format i.e. yearly(11/22)")
            elif run_time.startswith("range"):
                match = re.match("^(1[0-2]|0?[1-9])/(3[01]|[12][0-9]|0?[1-9])-(1[0-2]|0?[1-9])/(3[01]|[12][0-9]|0?[1-9])$", param)
                if not match:
                    logger.error(f"Schedule Error: range {display} must be in the MM/DD-MM/DD format i.e. range(12/01-12/25)")
                    continue
                month_start, day_start = check_day(int(match.group(1)), int(match.group(2)))
                month_end, day_end = check_day(int(match.group(3)), int(match.group(4)))
                month_check, day_check = check_day(current_time.month, current_time.day)
                check = datetime.strptime(f"{month_check}/{day_check}", "%m/%d")
                start = datetime.strptime(f"{month_start}/{day_start}", "%m/%d")
                end = datetime.strptime(f"{month_end}/{day_end}", "%m/%d")
                range_collection = True
                schedule_str += f"\nScheduled between {pretty_months[month_start]} {num2words(day_start, to='ordinal_num')} and {pretty_months[month_end]} {num2words(day_end, to='ordinal_num')}"
                if start <= check <= end if start < end else (check <= end or check >= start):
                    all_check += 1
        else:
            logger.error(f"Schedule Error: {display}")
    if is_all:
        schedule_str.replace("\n", "\n\t")
    if (all_check == 0 and not is_all) or (is_all and schedules_run != all_check):
        if non_existing:
            raise NonExisting(schedule_str)
        elif range_collection:
            raise NotScheduledRange(schedule_str)
        else:
            raise NotScheduled(schedule_str)
    return schedule_str

def check_int(value, datatype="int", minimum=1, maximum=None):
    try:
        value = int(str(value)) if datatype == "int" else float(str(value))
        if (maximum is None and minimum <= value) or (maximum is not None and minimum <= value <= maximum):
            return value
    except ValueError:
        pass

def parse_and_or(error, attribute, data, test_list):
    out = ""
    final = ""
    ands = [d.strip() for d in data.split(",")]
    for an in ands:
        ors = [a.strip() for a in an.split("|")]
        or_num = []
        for item in ors:
            if not item:
                raise Failed(f"{error} Error: Cannot have a blank {attribute}")
            if str(item) not in test_list:
                raise Failed(f"{error} Error: {attribute} {item} is invalid")
            or_num.append(str(test_list[str(item)]))
        if final:
            final += ","
        final += "|".join(or_num)
        if out:
            out += f" and "
        if len(ands) > 1 and len(ors) > 1:
            out += "("
        if len(ors) > 1:
            out += ' or '.join([test_list[test_list[str(o)]] if test_list else o for o in ors])
        else:
            out += test_list[test_list[str(ors[0])]] if test_list else ors[0]
        if len(ands) > 1 and len(ors) > 1:
            out += ")"
    return out, final

def parse(error, attribute, data, datatype=None, methods=None, parent=None, default=None, options=None, translation=None, minimum=1, maximum=None, regex=None, range_split=None):
    display = f"{parent + ' ' if parent else ''}{attribute} attribute"
    if options is None and translation is not None:
        options = [o for o in translation]
    value = data[methods[attribute]] if methods and attribute in methods else data

    if datatype in ["list", "commalist", "strlist", "lowerlist"]:
        final_list = []
        if value:
            if datatype in ["commalist", "strlist"] and isinstance(value, dict):
                raise Failed(f"{error} Error: {display} {value} must be a list or string")
            if datatype == "commalist":
                value = get_list(value)
            if datatype == "lowerlist":
                value = get_list(value, lower=True)
            if not isinstance(value, list):
                value = [value]
            for v in value:
                if v:
                    if options is None or (options and (v in options or (datatype == "strlist" and str(v) in options))):
                        final_list.append(str(v) if datatype == "strlist" else v)
                    elif options:
                        raise Failed(f"{error} Error: {display} {v} is invalid; Options include: {', '.join(options)}")
        return final_list
    elif datatype == "intlist":
        if value:
            try:
                return [int(v) for v in value if v] if isinstance(value, list) else [int(value)]
            except ValueError:
                pass
        return []
    elif datatype == "listdict":
        final_list = []
        for dict_data in get_list(value):
            if isinstance(dict_data, dict):
                final_list.append(dict_data)
            else:
                raise Failed(f"{error} Error: {display} {dict_data} is not a dictionary")
        return final_list
    elif datatype in ["dict", "dictlist", "dictdict", "strdict", "dictliststr"]:
        if isinstance(value, dict):
            if datatype == "dict":
                return value
            elif datatype == "dictlist":
                return {k: v if isinstance(v, list) else [v] for k, v in value.items()}
            elif datatype == "dictliststr":
                return {str(k): [str(y) for y in v] if isinstance(v, list) else [str(v)] for k, v in value.items()}
            elif datatype == "strdict":
                return {str(k): str(v) for k, v in value.items()}
            else:
                final_dict = {}
                for dict_key, dict_data in value.items():
                    if isinstance(dict_data, dict) and dict_data:
                        new_data = {}
                        for dict_data_key, dict_data_data in dict_data.items():
                            new_data[str(dict_data_key)] = dict_data_data
                        final_dict[dict_key] = new_data
                    else:
                        raise Failed(f"{error} Warning: {display} {dict_key} is not a dictionary")
                return final_dict
        else:
            raise Failed(f"{error} Error: {display} {value} is not a dictionary")
    elif methods and attribute not in methods:
        message = f"{display} not found"
    elif value is None:
        message = f"{display} is blank"
    elif regex is not None:
        regex_str, example = regex
        if re.compile(regex_str).match(str(value)):
            return str(value)
        else:
            message = f"{display}: {value} must match pattern {regex_str} e.g. {example}"
    elif datatype == "bool":
        if isinstance(value, bool):
            return value
        elif isinstance(value, (int, float)):
            return value > 0
        elif str(value).lower() in ["t", "true", "y", "yes"]:
            return True
        elif str(value).lower() in ["f", "false", "n", "no"]:
            return False
        else:
            message = f"{display} must be either true or false"
    elif datatype in ["int", "float"]:
        if range_split:
            range_values = str(value).split(range_split)
            if len(range_values) == 2:
                start = check_int(range_values[0])
                end = check_int(range_values[1])
                if start and end and start < end:
                    return f"{start}{range_split}{end}"
        else:
            new_value = check_int(value, datatype=datatype, minimum=minimum, maximum=maximum)
            if new_value is not None:
                return new_value
        message = f"{display} {value} must {'each ' if range_split else ''}be {'an integer' if datatype == 'int' else 'a number'}"
        message = f"{message} {minimum} or greater" if maximum is None else f"{message} between {minimum} and {maximum}"
        if range_split:
            message = f"{message} separated by a {range_split}"
    elif (translation is not None and str(value).lower() not in translation) or \
            (options is not None and translation is None and str(value).lower() not in options):
        message = f"{display} {value} must be in {', '.join([str(o) for o in options])}"
    else:
        return translation[value] if translation is not None else value

    if default is None:
        raise Failed(f"{error} Error: {message}")
    else:
        logger.warning(f"{error} Warning: {message} using {default} as default")
        return translation[default] if translation is not None else default

def parse_cords(data, parent, required=False):
    horizontal_align = parse("Overlay", "horizontal_align", data["horizontal_align"], parent=parent,
                             options=["left", "center", "right"]) if "horizontal_align" in data else None
    if required and horizontal_align is None:
        raise Failed(f"Overlay Error: {parent} horizontal_align is required")

    vertical_align = parse("Overlay", "vertical_align", data["vertical_align"], parent=parent,
                           options=["top", "center", "bottom"]) if "vertical_align" in data else None
    if required and vertical_align is None:
        raise Failed(f"Overlay Error: {parent} vertical_align is required")

    horizontal_offset = None
    if "horizontal_offset" in data and data["horizontal_offset"] is not None:
        x_off = data["horizontal_offset"]
        per = False
        if str(x_off).endswith("%"):
            x_off = x_off[:-1]
            per = True
        x_off = check_num(x_off)
        error = f"Overlay Error: {parent} horizontal_offset: {data['horizontal_offset']} must be a number"
        if x_off is None:
            raise Failed(error)
        if horizontal_align != "center" and not per and x_off < 0:
            raise Failed(f"{error} 0 or greater")
        elif horizontal_align != "center" and per and (x_off > 100 or x_off < 0):
            raise Failed(f"{error} between 0% and 100%")
        elif horizontal_align == "center" and per and (x_off > 50 or x_off < -50):
            raise Failed(f"{error} between -50% and 50%")
        horizontal_offset = f"{x_off}%" if per else x_off
    if required and horizontal_offset is None:
        raise Failed(f"Overlay Error: {parent} horizontal_offset is required")

    vertical_offset = None
    if "vertical_offset" in data and data["vertical_offset"] is not None:
        y_off = data["vertical_offset"]
        per = False
        if str(y_off).endswith("%"):
            y_off = y_off[:-1]
            per = True
        y_off = check_num(y_off)
        error = f"Overlay Error: {parent} vertical_offset: {data['vertical_offset']} must be a number"
        if y_off is None:
            raise Failed(error)
        if vertical_align != "center" and not per and y_off < 0:
            raise Failed(f"{error} 0 or greater")
        elif vertical_align != "center" and per and (y_off > 100 or y_off < 0):
            raise Failed(f"{error} between 0% and 100%")
        elif vertical_align == "center" and per and (y_off > 50 or y_off < -50):
            raise Failed(f"{error} between -50% and 50%")
        vertical_offset = f"{y_off}%" if per else y_off
    if required and vertical_offset is None:
        raise Failed(f"Overlay Error: {parent} vertical_offset is required")

    return horizontal_offset, horizontal_align, vertical_offset, vertical_align

def replace_label(_label, _data):
    replaced = False
    if isinstance(_data, dict):
        final_data = {}
        for sm, sd in _data.items():
            try:
                _new_data, _new_replaced = replace_label(_label, sd)
                final_data[sm] = _new_data
                if _new_replaced:
                    replaced = True
            except Failed:
                continue
    elif isinstance(_data, list):
        final_data = []
        for li in _data:
            try:
                _new_data, _new_replaced = replace_label(_label, li)
                final_data.append(_new_data)
                if _new_replaced:
                    replaced = True
            except Failed:
                continue
    elif "<<smart_label>>" in str(_data):
        final_data = str(_data).replace("<<smart_label>>", _label)
        replaced = True
    else:
        final_data = _data

    return final_data, replaced

def check_time(message, end=False):
    global previous_time
    global start_time
    current_time = time.time()
    if end:
        previous_time = start_time
    if previous_time is None:
        logger.debug(f"{message}: {current_time}")
        start_time = current_time
    else:
        logger.debug(f"{message}: {current_time - previous_time}")
    previous_time = None if end else current_time

system_fonts = []
def get_system_fonts():
    global system_fonts
    if not system_fonts:
        dirs = []
        if sys.platform == "win32":
            windir = os.environ.get("WINDIR")
            if windir:
                dirs.append(os.path.join(windir, "fonts"))
        elif sys.platform in ("linux", "linux2"):
            lindirs = os.environ.get("XDG_DATA_DIRS", "")
            if not lindirs:
                lindirs = "/usr/share"
            dirs += [os.path.join(lindir, "fonts") for lindir in lindirs.split(":")]
        elif sys.platform == "darwin":
            dirs += ["/Library/Fonts", "/System/Library/Fonts", os.path.expanduser("~/Library/Fonts")]
        else:
            return dirs
        system_fonts = [n for d in dirs for _, _, ns in os.walk(d) for n in ns]
    return system_fonts

class YAML:
    def __init__(self, path=None, input_data=None, check_empty=False, create=False, start_empty=False):
        self.path = path
        self.input_data = input_data
        self.yaml = ruamel.yaml.YAML()
        self.yaml.indent(mapping=2, sequence=2)
        try:
            if input_data:
                self.data = self.yaml.load(input_data)
            else:
                if start_empty or (create and not os.path.exists(self.path)):
                    with open(self.path, 'w'):
                        pass
                    self.data = {}
                else:
                    with open(self.path, encoding="utf-8") as fp:
                        self.data = self.yaml.load(fp)
        except ruamel.yaml.error.YAMLError as e:
            e = str(e).replace("\n", "\n      ")
            raise Failed(f"YAML Error: {e}")
        except Exception as e:
            raise Failed(f"YAML Error: {e}")
        if not self.data or not isinstance(self.data, dict):
            if check_empty:
                raise Failed("YAML Error: File is empty")
            self.data = {}

    def save(self):
        if self.path:
            with open(self.path, 'w', encoding="utf-8") as fp:
                self.yaml.dump(self.data, fp)


