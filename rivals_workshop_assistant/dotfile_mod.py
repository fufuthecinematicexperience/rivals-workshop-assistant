import datetime
import typing
from datetime import datetime
from pathlib import Path

import rivals_workshop_assistant.info_files as info_files
from rivals_workshop_assistant.file_handling import File
from rivals_workshop_assistant.paths import ASSISTANT_FOLDER

FILENAME = ".assistant"
PATH = ASSISTANT_FOLDER / FILENAME

LIBRARY_VERSION_FIELD = "library_version"


def get_library_version_string(dotfile: dict) -> typing.Optional[str]:
    return dotfile.get(LIBRARY_VERSION_FIELD, None)


ASSISTANT_VERSION_FIELD = "assistant_version"


def get_assistant_version_string(dotfile: dict) -> typing.Optional[str]:
    return dotfile.get(ASSISTANT_VERSION_FIELD, None)


LAST_UPDATED_FIELD = "last_updated"
PROCESSED_TIME_FIELD = "processed_time"
SEEN_FILES_FIELD = "seen_files"
INJECT_CLIENTS_FIELD = "injection_clients"


def read(root_dir: Path) -> dict:
    """Controller"""
    return info_files.read(root_dir / PATH)


def save_dotfile(root_dir: Path, content: dict):
    """Controller"""
    info_files.save(path=root_dir / PATH, content=content)


def update_dotfile_after_saving(
    dotfile: dict, now: datetime, seen_files: typing.List[File]
):
    dotfile[PROCESSED_TIME_FIELD] = now
    dotfile[SEEN_FILES_FIELD] = [file.path.as_posix() for file in seen_files]


def update_dotfile_injection_clients(dotfile:dict, clientscript:Path, dependencies:typing.List[Path]):
    if INJECT_CLIENTS_FIELD not in dotfile:
        dotfile[INJECT_CLIENTS_FIELD] = {}
    
    if len(dependencies) > 0:
        dotfile[INJECT_CLIENTS_FIELD][clientscript.as_posix()] = [dep.as_posix() for dep in dependencies]
    elif clientscript.as_posix() in dotfile[INJECT_CLIENTS_FIELD]:
        dotfile[INJECT_CLIENTS_FIELD].pop(clientscript.as_posix())


def get_clients_for_injection(dotfile:dict, injectionscript:Path) -> typing.List[Path]:
    if INJECT_CLIENTS_FIELD not in dotfile:
        return []
    
    str_path = injectionscript.as_posix()
    clientslist = []
    for key in dotfile[INJECT_CLIENTS_FIELD].keys():
        if str_path in dotfile[INJECT_CLIENTS_FIELD][key]:
            clientslist.append(Path(key))

    return clientslist


def get_processed_time(dotfile: dict, path: Path) -> typing.Optional[datetime]:
    seen_files = dotfile.get(SEEN_FILES_FIELD, [])
    if seen_files is None:
        seen_files = []
    if path.as_posix() in seen_files:
        return dotfile.get(PROCESSED_TIME_FIELD, None)
    else:
        return None
