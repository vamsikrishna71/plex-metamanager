import os, re
from datetime import datetime
from modules import plex, util, overlay
from modules.builder import CollectionBuilder
from modules.util import Failed, FilterFailed, NonExisting, NotScheduled
from num2words import num2words
from plexapi.exceptions import BadRequest
from plexapi.video import Movie, Show, Season, Episode
from PIL import Image, ImageFilter

logger = util.logger

class Overlays:
    def __init__(self, config, library):
        self.config = config
        self.library = library
        self.overlays = []

    def run_overlays(self):
        overlay_start = datetime.now()
        logger.info("")
        logger.separator(f"{self.library.name} Library Overlays")
        logger.info("")
        os.makedirs(self.library.overlay_backup, exist_ok=True)

        key_to_overlays = {}
        properties = {}
        if not self.library.remove_overlays:
            key_to_overlays, properties = self.compile_overlays()
        ignore_list = [rk for rk in key_to_overlays]

        old_overlays = [la for la in self.library.Plex.listFilterChoices("label") if str(la.title).lower().endswith(" overlay")]
        if old_overlays:
            logger.separator(f"Removing Old Overlays for the {self.library.name} Library")
            logger.info("")
            for old_overlay in old_overlays:
                label_items = self.get_overlay_items(label=old_overlay)
                if label_items:
                    logger.info("")
                    logger.separator(f"Removing {old_overlay.title}")
                    logger.info("")
                    for i, item in enumerate(label_items, 1):
                        item_title = self.library.get_item_sort_title(item, atr="title")
                        logger.ghost(f"Restoring {old_overlay.title}: {i}/{len(label_items)} {item_title}")
                        self.remove_overlay(item, item_title, old_overlay.title, [
                            os.path.join(self.library.overlay_folder, old_overlay.title[:-8], f"{item.ratingKey}.png")
                        ])
            logger.info("")

        remove_overlays = self.get_overlay_items(ignore=ignore_list)
        if self.library.is_show:
            remove_overlays.extend(self.get_overlay_items(libtype="episode", ignore=ignore_list))
            remove_overlays.extend(self.get_overlay_items(libtype="season", ignore=ignore_list))
        elif self.library.is_music:
            remove_overlays.extend(self.get_overlay_items(libtype="album", ignore=ignore_list))

        if remove_overlays:
            logger.separator(f"Removing {'All ' if self.library.remove_overlays else ''}Overlays for the {self.library.name} Library")
            for i, item in enumerate(remove_overlays, 1):
                item_title = self.library.get_item_sort_title(item, atr="title")
                logger.ghost(f"Restoring: {i}/{len(remove_overlays)} {item_title}")
                self.remove_overlay(item, item_title, "Overlay", [
                    os.path.join(self.library.overlay_backup, f"{item.ratingKey}.png"),
                    os.path.join(self.library.overlay_backup, f"{item.ratingKey}.jpg")
                ])
            logger.exorcise()
        else:
            logger.separator(f"No Overlays to Remove for the {self.library.name} Library")
        logger.info("")
        if not self.library.remove_overlays:
            logger.separator(f"{'Re-' if self.library.reapply_overlays else ''}Applying Overlays for the {self.library.name} Library")
            logger.info("")
            for i, (over_key, (item, over_names)) in enumerate(sorted(key_to_overlays.items(), key=lambda io: self.library.get_item_sort_title(io[1][0])), 1):
                item_title = self.library.get_item_sort_title(item, atr="title")
                try:
                    logger.ghost(f"Overlaying: {i}/{len(key_to_overlays)} {item_title}")
                    image_compare = None
                    overlay_compare = None
                    poster = None
                    if self.config.Cache:
                        image, image_compare, overlay_compare = self.config.Cache.query_image_map(item.ratingKey, f"{self.library.image_table_name}_overlays")
                    self.library.reload(item, force=True)

                    overlay_compare = [] if overlay_compare is None else util.get_list(overlay_compare, split="|")
                    has_overlay = any([item_tag.tag.lower() == "overlay" for item_tag in self.library.item_labels(item)])

                    compare_names = {properties[ov].get_overlay_compare(): ov for ov in over_names}
                    blur_num = 0
                    applied_names = []
                    queue_overlays = {}
                    for over_name in over_names:
                        current_overlay = properties[over_name]
                        if current_overlay.name.startswith("blur"):
                            logger.info(over_name)
                            blur_test = int(re.search("\\(([^)]+)\\)", current_overlay.name).group(1))
                            if blur_test > blur_num:
                                blur_num = blur_test
                        elif current_overlay.queue_name:
                            if current_overlay.queue not in queue_overlays:
                                queue_overlays[current_overlay.queue] = {}
                            if current_overlay.weight in queue_overlays[current_overlay.queue]:
                                raise Failed("Overlay Error: Overlays in a queue cannot have the same weight")
                            queue_overlays[current_overlay.queue][current_overlay.weight] = over_name
                        else:
                            applied_names.append(over_name)

                    overlay_change = "" if has_overlay else "No Overlay Label"
                    if not overlay_change:
                        for oc in overlay_compare:
                            if oc not in compare_names:
                                overlay_change = f"{oc} not in {compare_names}"

                    if not overlay_change:
                        for compare_name, original_name in compare_names.items():
                            if compare_name not in overlay_compare or properties[original_name].updated:
                                overlay_change = f"{compare_name} not in {overlay_compare} or {properties[original_name].updated}"

                    if self.config.Cache:
                        for over_name in over_names:
                            if properties[over_name].name.startswith("text"):
                                for cache_key, cache_value in self.config.Cache.query_overlay_special_text(item.ratingKey).items():
                                    actual = plex.attribute_translation[cache_key] if cache_key in plex.attribute_translation else cache_key
                                    if not hasattr(item, actual):
                                        continue
                                    actual_value = getattr(item, actual)
                                    if cache_value is None or actual_value is None:
                                        continue
                                    if cache_key in overlay.float_vars:
                                        cache_value = float(cache_value)
                                    if cache_key in overlay.int_vars:
                                        cache_value = int(cache_value)
                                    if cache_key in overlay.date_vars:
                                        actual_value = actual_value.strftime("%Y-%m-%d")
                                    if actual_value != cache_value:
                                        overlay_change = f"Special Text Changed from {cache_value} to {actual_value}"
                    try:
                        poster, background, item_dir, name = self.library.find_item_assets(item)
                        if not poster and self.library.assets_for_all:
                            if (isinstance(item, Episode) and self.library.show_missing_episode_assets) or \
                                    (isinstance(item, Season) and self.library.show_missing_season_assets) or \
                                    (not isinstance(item, (Episode, Season)) and self.library.show_missing_assets):
                                if self.library.asset_folders:
                                    logger.warning(f"Asset Warning: No poster found for '{item_title}' in the assets folder '{item_dir}'")
                                else:
                                    logger.warning(f"Asset Warning: No poster '{name}' found in the assets folders")
                        if background:
                            self.library.upload_images(item, background=background)
                    except Failed as e:
                        if self.library.assets_for_all and self.library.show_missing_assets:
                            logger.warning(e)

                    has_original = None
                    new_backup = None
                    if poster:
                        if image_compare and str(poster.compare) != str(image_compare):
                            changed_image = True
                        if os.path.exists(os.path.join(self.library.overlay_backup, f"{item.ratingKey}.png")):
                            os.remove(os.path.join(self.library.overlay_backup, f"{item.ratingKey}.png"))
                        if os.path.exists(os.path.join(self.library.overlay_backup, f"{item.ratingKey}.jpg")):
                            os.remove(os.path.join(self.library.overlay_backup, f"{item.ratingKey}.jpg"))
                    elif has_overlay:
                        if os.path.exists(os.path.join(self.library.overlay_backup, f"{item.ratingKey}.png")):
                            has_original = os.path.join(self.library.overlay_backup, f"{item.ratingKey}.png")
                        elif os.path.exists(os.path.join(self.library.overlay_backup, f"{item.ratingKey}.jpg")):
                            has_original = os.path.join(self.library.overlay_backup, f"{item.ratingKey}.jpg")
                        if self.library.reset_overlays:
                            reset_list = self.library.reset_overlays
                        elif has_original is None and not self.library.reset_overlays:
                            reset_list = ["plex", "tmdb"]
                        else:
                            reset_list = []
                        try:
                            new_backup = self.library.item_posters(item, providers=reset_list)
                        except Failed as e:
                            if any(r in reset_list for r in ["plex", "tmdb"]):
                                logger.error(e)
                    else:
                        new_backup = item.posterUrl
                    logger.info(f"\n{item_title}")
                    if new_backup:
                        try:
                            has_original = self.library.check_image_for_overlay(new_backup, os.path.join(self.library.overlay_backup, f"{item.ratingKey}"))
                        except Failed as e:
                            raise Failed(f"  Overlay Error: {e}")
                    poster_compare = None
                    if poster is None and has_original is None:
                        logger.error(f"  Overlay Error: No poster found")
                    elif self.library.reapply_overlays or new_backup or overlay_change:
                        try:
                            if not self.library.reapply_overlays and new_backup:
                                logger.trace("  Overlay Reason: New image detected")
                            elif not self.library.reapply_overlays and overlay_change:
                                logger.trace(f"  Overlay Reason: Overlay changed {overlay_change}")
                            canvas_width, canvas_height = overlay.get_canvas_size(item)
                            with Image.open(poster.location if poster else has_original) as new_poster:
                                exif_tags = new_poster.getexif()
                                exif_tags[0x04bc] = "overlay"
                                new_poster = new_poster.convert("RGB").resize((canvas_width, canvas_height), Image.LANCZOS)

                                if blur_num > 0:
                                    new_poster = new_poster.filter(ImageFilter.GaussianBlur(blur_num))

                                def get_text(text_overlay):
                                    full_text = text_overlay.name[5:-1]
                                    for format_var in overlay.vars_by_type[text_overlay.level]:
                                        if f"<<{format_var}" in full_text and format_var == "originally_available[":
                                            mod = re.search("<<originally_available\\[(.+)]>>", full_text).group(1)
                                            format_var = "originally_available"
                                        elif f"<<{format_var}>>" in full_text and format_var.endswith(tuple(m for m in overlay.double_mods)):
                                            mod = format_var[-2:]
                                            format_var = format_var[:-2]
                                        elif f"<<{format_var}>>" in full_text and format_var.endswith(tuple(m for m in overlay.single_mods)):
                                            mod = format_var[-1]
                                            format_var = format_var[:-1]
                                        elif f"<<{format_var}>>" in full_text:
                                            mod = ""
                                        else:
                                            continue
                                        if format_var == "show_title":
                                            actual_attr = "parentTitle" if text_overlay.level == "season" else "grandparentTitle"
                                        elif format_var in plex.attribute_translation:
                                            actual_attr = plex.attribute_translation[format_var]
                                        else:
                                            actual_attr = format_var
                                        if format_var == "bitrate":
                                            actual_value = None
                                            for media in item.media:
                                                current = int(media.bitrate)
                                                if actual_value is None:
                                                    actual_value = current
                                                    if mod == "":
                                                        break
                                                elif mod == "H" and current > actual_value:
                                                    actual_value = current
                                                elif mod == "L" and current < actual_value:
                                                    actual_value = current
                                        else:
                                            if not hasattr(item, actual_attr) or getattr(item, actual_attr) is None:
                                                raise Failed(f"Overlay Warning: No {full_text} found")
                                            actual_value = getattr(item, actual_attr)
                                            if format_var == "versions":
                                                actual_value = len(actual_value)
                                        if self.config.Cache:
                                            cache_store = actual_value.strftime("%Y-%m-%d") if format_var in overlay.date_vars else actual_value
                                            self.config.Cache.update_overlay_special_text(item.ratingKey, format_var, cache_store)
                                        sub_value = None
                                        if format_var == "originally_available":
                                            if mod:
                                                sub_value = "<<originally_available\\[(.+)]>>"
                                                final_value = actual_value.strftime(mod)
                                            else:
                                                final_value = actual_value.strftime("%Y-%m-%d")
                                        elif format_var == "runtime":
                                            if mod == "H":
                                                final_value = int((actual_value / 60000) // 60)
                                            elif mod == "M":
                                                final_value = int((actual_value / 60000) % 60)
                                            else:
                                                final_value = int(actual_value / 60000)
                                        elif mod == "%":
                                            final_value = int(actual_value * 10)
                                        elif mod == "#":
                                            final_value = str(actual_value)[:-2] if str(actual_value).endswith(".0") else actual_value
                                        elif mod == "W":
                                            final_value = num2words(int(actual_value))
                                        elif mod == "WU":
                                            final_value = num2words(int(actual_value)).upper()
                                        elif mod == "WL":
                                            final_value = num2words(int(actual_value)).lower()
                                        elif mod == "0":
                                            final_value = f"{int(actual_value):02}"
                                        elif mod == "00":
                                            final_value = f"{int(actual_value):03}"
                                        elif mod == "/":
                                            final_value = f"{float(actual_value) / 2:.1f}"
                                        elif mod == "U":
                                            final_value = str(actual_value).upper()
                                        elif mod == "L":
                                            final_value = str(actual_value).lower()
                                        elif mod == "P":
                                            final_value = str(actual_value).title()
                                        else:
                                            final_value = actual_value
                                        if sub_value:
                                            full_text = re.sub(sub_value, str(final_value), full_text)
                                        else:
                                            full_text = full_text.replace(f"<<{format_var}{mod}>>", str(final_value))
                                    return str(full_text)

                                for over_name in applied_names:
                                    current_overlay = properties[over_name]
                                    if current_overlay.name.startswith("text"):
                                        if "<<" in current_overlay.name:
                                            image_box = current_overlay.image.size if current_overlay.image else None
                                            try:
                                                overlay_image, addon_box = current_overlay.get_backdrop((canvas_width, canvas_height), box=image_box, text=get_text(current_overlay))
                                            except Failed as e:
                                                logger.warning(f"  {e}")
                                                continue
                                            new_poster.paste(overlay_image, (0, 0), overlay_image)
                                        else:
                                            overlay_image, addon_box = current_overlay.get_canvas(item)
                                            new_poster.paste(overlay_image, (0, 0), overlay_image)
                                        if current_overlay.image:
                                            new_poster.paste(current_overlay.image, addon_box, current_overlay.image)
                                    elif current_overlay.name == "backdrop":
                                        overlay_image, _ = current_overlay.get_canvas(item)
                                        new_poster.paste(overlay_image, (0, 0), overlay_image)
                                    else:
                                        if current_overlay.has_coordinates():
                                            overlay_image, overlay_box = current_overlay.get_canvas(item)
                                            if overlay_image is not None:
                                                new_poster.paste(overlay_image, (0, 0), overlay_image)
                                            new_poster.paste(current_overlay.image, overlay_box, current_overlay.image)
                                        else:
                                            new_poster = new_poster.resize(current_overlay.image.size, Image.LANCZOS)
                                            new_poster.paste(current_overlay.image, (0, 0), current_overlay.image)
                                            new_poster = new_poster.resize((canvas_width, canvas_height), Image.LANCZOS)

                                for queue, weights in queue_overlays.items():
                                    cords = self.library.queues[queue]
                                    sorted_weights = sorted(weights.items(), reverse=True)
                                    for o, cord in enumerate(cords):
                                        if len(sorted_weights) <= o:
                                            break
                                        over_name = sorted_weights[o][1]
                                        current_overlay = properties[over_name]
                                        if current_overlay.name.startswith("text"):
                                            image_box = current_overlay.image.size if current_overlay.image else None
                                            try:
                                                overlay_image, addon_box = current_overlay.get_backdrop((canvas_width, canvas_height), box=image_box, text=get_text(current_overlay), new_cords=cord)
                                            except Failed as e:
                                                logger.warning(f"  {e}")
                                                continue
                                            new_poster.paste(overlay_image, (0, 0), overlay_image)
                                            if current_overlay.image:
                                                new_poster.paste(current_overlay.image, addon_box, current_overlay.image)
                                        else:
                                            if current_overlay.has_back:
                                                overlay_image, overlay_box = current_overlay.get_backdrop((canvas_width, canvas_height), box=current_overlay.image.size, new_cords=cord)
                                                new_poster.paste(overlay_image, (0, 0), overlay_image)
                                            else:
                                                overlay_box = current_overlay.get_coordinates((canvas_width, canvas_height), box=current_overlay.image.size, new_cords=cord)
                                            new_poster.paste(current_overlay.image, overlay_box, current_overlay.image)
                                temp = os.path.join(self.library.overlay_folder, "temp.jpg")
                                new_poster.save(temp, exif=exif_tags)
                                self.library.upload_poster(item, temp)
                                self.library.edit_tags("label", item, add_tags=["Overlay"], do_print=False)
                                poster_compare = poster.compare if poster else item.thumb
                                logger.info(f"  Overlays Applied: {', '.join(over_names)}")
                        except (OSError, BadRequest, SyntaxError) as e:
                            logger.stacktrace()
                            raise Failed(f"  Overlay Error: {e}")
                    else:
                        logger.info("  Overlay Update Not Needed")

                    if self.config.Cache and poster_compare:
                        self.config.Cache.update_image_map(item.ratingKey, f"{self.library.image_table_name}_overlays", item.thumb, poster_compare, overlay='|'.join(compare_names))
                except Failed as e:
                    logger.error(f"  {e}\n  Overlays Attempted on {item_title}: {', '.join(over_names)}")
                except Exception as e:
                    logger.info(e)
                    logger.info(type(e))
                    logger.stacktrace()
                    logger.error("")
                    logger.error(f"Overlays Attempted on {item_title}: {', '.join(over_names)}")
        logger.exorcise()
        for _, over in properties.items():
            if over.image:
                over.image.close()
        overlay_run_time = str(datetime.now() - overlay_start).split('.')[0]
        logger.info("")
        logger.separator(f"Finished {self.library.name} Library Overlays\nOverlays Run Time: {overlay_run_time}")
        return overlay_run_time

    def compile_overlays(self):
        key_to_item = {}
        properties = {}
        overlay_groups = {}
        key_to_overlays = {}

        for overlay_file in self.library.overlay_files:
            for k, v in overlay_file.overlays.items():
                try:
                    builder = CollectionBuilder(self.config, overlay_file, k, v, library=self.library, overlay=True)
                    logger.info("")

                    logger.separator(f"Gathering Items for {k} Overlay", space=False, border=False)

                    prop_name = builder.overlay.mapping_name
                    properties[prop_name] = builder.overlay

                    builder.display_filters()

                    for method, value in builder.builders:
                        logger.debug("")
                        logger.debug(f"Builder: {method}: {value}")
                        logger.info("")
                        try:
                            builder.filter_and_save_items(builder.gather_ids(method, value))
                        except NonExisting as e:
                            if builder.ignore_blank_results:
                                logger.warning("")
                                logger.warning(e)
                            else:
                                raise Failed(e)

                    added_titles = []
                    if builder.found_items:
                        for item in builder.found_items:
                            key_to_item[item.ratingKey] = item
                            added_titles.append(item)
                            if item.ratingKey not in properties[prop_name].keys:
                                properties[prop_name].keys.append(item.ratingKey)
                    if added_titles:
                        logger.info(f"{len(added_titles)} Items found for {prop_name}")
                        logger.trace(f"Titles Found: {[self.library.get_item_sort_title(a, atr='title') for a in added_titles]}")
                    else:
                        logger.warning(f"No Items found for {prop_name}")
                    logger.info("")
                except NotScheduled as e:
                    logger.info(e)
                except FilterFailed:
                    pass
                except Failed as e:
                    logger.stacktrace()
                    logger.error(e)
                    logger.info("")
                except Exception as e:
                    logger.stacktrace()
                    logger.error(f"Unknown Error: {e}")
                    logger.info("")

        logger.separator(f"Overlay Operation for the {self.library.name} Library")
        logger.debug("")
        logger.debug(f"Remove Overlays: {self.library.remove_overlays}")
        logger.debug(f"Reapply Overlays: {self.library.reapply_overlays}")
        logger.debug(f"Reset Overlays: {self.library.reset_overlays}")
        logger.debug("")
        logger.separator(f"Number of Items Per Overlay", space=False, border=False)
        logger.debug("")

        longest = 7
        for overlay_name in properties:
            if len(overlay_name) > longest:
                longest = len(overlay_name)

        logger.debug(f"{'Overlay':^{longest}} | Number |")
        logger.debug(f"{logger.separating_character * longest} | {logger.separating_character * 6} |")
        for overlay_name, over_obj in properties.items():
            logger.debug(f"{overlay_name:<{longest}} | {len(over_obj.keys):^6} |")
        logger.debug("")

        for overlay_name, over_obj in properties.items():
            if over_obj.group:
                if over_obj.group not in overlay_groups:
                    overlay_groups[over_obj.group] = {}
                overlay_groups[over_obj.group][overlay_name] = over_obj.weight

        for overlay_name, over_obj in properties.items():
            for over_key in over_obj.keys:
                if over_key not in key_to_overlays:
                    key_to_overlays[over_key] = (key_to_item[over_key], [])
                key_to_overlays[over_key][1].append(overlay_name)

        for over_key, (item, over_names) in key_to_overlays.items():
            group_status = {}
            for over_name in over_names:
                for suppress_name in properties[over_name].suppress:
                    if suppress_name in over_names:
                        key_to_overlays[over_key][1].remove(suppress_name)
            for over_name in over_names:
                for overlay_group, group_names in overlay_groups.items():
                    if over_name in group_names:
                        if overlay_group not in group_status:
                            group_status[overlay_group] = []
                        group_status[overlay_group].append(over_name)
            for gk, gv in group_status.items():
                if len(gv) > 1:
                    final = None
                    for v in gv:
                        if final is None or overlay_groups[gk][v] > overlay_groups[gk][final]:
                            final = v
                    for v in gv:
                        if final != v:
                            key_to_overlays[over_key][1].remove(v)
        return key_to_overlays, properties

    def get_overlay_items(self, label="Overlay", libtype=None, ignore=None):
        items = self.library.search(label=label, libtype=libtype)
        return items if not ignore else [o for o in items if o.ratingKey not in ignore]

    def remove_overlay(self, item, item_title, label, locations):
        try:
            poster, _, _, _ = self.library.find_item_assets(item)
        except Failed:
            poster = None
        is_url = False
        poster_location = None
        if poster:
            poster_location = poster.location
        elif any([os.path.exists(loc) for loc in locations]):
            poster_location = next((loc for loc in locations if os.path.exists(loc)))
        if not poster_location:
            is_url = True
            try:
                poster_location = self.library.item_posters(item)
            except Failed:
                pass
        if poster_location:
            self.library.upload_poster(item, poster_location, url=is_url)
            self.library.edit_tags("label", item, remove_tags=[label], do_print=False)
            for loc in locations:
                if os.path.exists(loc):
                    os.remove(loc)
        else:
            logger.error(f"No Poster found to restore for {item_title}")
