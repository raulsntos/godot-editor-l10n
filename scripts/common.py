import enum
import fnmatch
import os.path
import re
from typing import Dict, List, Set


class Message:
    __slots__ = ("msgid", "msgid_plural", "msgctxt", "comments", "locations")

    def format(self):
        lines = []

        if self.comments:
            for i, content in enumerate(self.comments):
                prefix = "#. TRANSLATORS:" if i == 0 else "#."
                lines.append(prefix + content)

        lines.append("#: " + " ".join(self.locations))

        if self.msgctxt:
            lines.append('msgctxt "{}"'.format(self.msgctxt))

        if self.msgid_plural:
            lines += [
                'msgid "{}"'.format(self.msgid),
                'msgid_plural "{}"'.format(self.msgid_plural),
                'msgstr[0] ""',
                'msgstr[1] ""',
            ]
        else:
            lines += [
                'msgid "{}"'.format(self.msgid),
                'msgstr ""',
            ]

        return "\n".join(lines)


class ExtractType(enum.IntEnum):
    TEXT = 1
    PROPERTY_PATH = 2
    GROUP = 3
    SUBGROUP = 4


class PropertyNameProcessor:
    remaps: Dict[str, str] = {}
    stop_words: Set[str] = set()

    # See String::_camelcase_to_underscore().
    capitalize_re = re.compile(r"(?<=\D)(?=\d)|(?<=\d)(?=\D([a-z]|\d))")

    def __init__(self):
        remap_re = re.compile(r'^\t*capitalize_string_remaps\["(?P<from>.+)"\] = (String::utf8\()?"(?P<to>.+)"')
        stop_words_re = re.compile(r'^\t*"(?P<word>.+)",')
        is_inside_stop_words = False
        with open("editor/editor_property_name_processor.cpp") as f:
            for line in f:
                if is_inside_stop_words:
                    m = stop_words_re.search(line)
                    if m:
                        self.stop_words.add(m.group("word"))
                    else:
                        is_inside_stop_words = False
                else:
                    m = remap_re.search(line)
                    if m:
                        self.remaps[m.group("from")] = m.group("to")

                if not is_inside_stop_words and not self.stop_words:
                    is_inside_stop_words = "stop_words = " in line

    def process_name(self, name: str) -> str:
        # See EditorPropertyNameProcessor::process_name().
        capitalized_parts = []
        parts = list(filter(bool, name.split("_")))  # Non-empty only.
        for i, segment in enumerate(parts):
            if i > 0 and i + 1 < len(parts) and segment in self.stop_words:
                capitalized_parts.append(segment)
                continue

            remapped = self.remaps.get(segment)
            if remapped:
                capitalized_parts.append(remapped)
            else:
                # See String::capitalize().
                # fmt: off
                capitalized_parts.append(" ".join(
                    part.title()
                    for part in self.capitalize_re.sub("_", segment).replace("_", " ").split()
                ))
                # fmt: on

        return " ".join(capitalized_parts)


def get_source_files() -> List[str]:
    matches = []
    for root, dirnames, filenames in os.walk("."):
        dirnames[:] = [d for d in dirnames if d not in ["thirdparty"]]
        for filename in fnmatch.filter(filenames, "*.cpp"):
            matches.append(os.path.join(root, filename))
        for filename in fnmatch.filter(filenames, "*.h"):
            matches.append(os.path.join(root, filename))
    matches.sort()
    return matches
