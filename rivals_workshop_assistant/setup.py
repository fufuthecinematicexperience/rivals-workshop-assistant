from pathlib import Path

from rivals_workshop_assistant import paths as paths
from rivals_workshop_assistant.injection import paths as inject_paths
from rivals_workshop_assistant.injection.installation import create_file, \
    DEFAULT_CONFIG


def make_basic_folder_structure(root_dir: Path):
    (root_dir / inject_paths.USER_INJECT_FOLDER).mkdir(
        parents=True, exist_ok=True)

    create_file(path=(root_dir / paths.ASSISTANT_CONFIG_PATH),
                content=DEFAULT_CONFIG)