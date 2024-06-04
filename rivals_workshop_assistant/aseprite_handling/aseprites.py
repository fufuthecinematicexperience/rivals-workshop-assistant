import asyncio
import itertools
from datetime import datetime
from pathlib import Path
from typing import List, TYPE_CHECKING, Iterable, Dict

from rivals_workshop_assistant import assistant_config_mod
from rivals_workshop_assistant.aseprite_handling.anims import Anim
from rivals_workshop_assistant.aseprite_handling.windows import Window
from rivals_workshop_assistant.dotfile_mod import get_script_processed_time
from rivals_workshop_assistant.file_handling import File, _get_modified_time
from rivals_workshop_assistant.aseprite_handling._aseprite_loading import (
    RawAsepriteFile,
)
from rivals_workshop_assistant.aseprite_handling.layers import AsepriteLayers
from rivals_workshop_assistant.run_context import RunContext

if TYPE_CHECKING:
    from rivals_workshop_assistant.aseprite_handling.tags import TagColor
    from rivals_workshop_assistant.aseprite_handling.params import (
        AsepritePathParams,
        AsepriteConfigParams,
    )


class AsepriteFileContent:
    """Data class for the contents of an aseprite file."""

    def __init__(
        self,
        anim_tag_colors: List["TagColor"],
        window_tag_colors: List["TagColor"],
        layer_tag_colors: List["TagColor"],
        file_data: "RawAsepriteFile",
        is_fresh: bool = False,
        layers: "AsepriteLayers" = None,  # just so it can be mocked
    ):
        self.file_data = file_data
        self.anim_tag_colors = anim_tag_colors
        self.window_tag_colors = window_tag_colors
        self.layer_tag_colors = layer_tag_colors
        self.is_fresh = is_fresh

        if layers is None and file_data is not None:
            self.layers = AsepriteLayers.from_file(self.file_data)

    @property
    def num_frames(self):
        return self.file_data.get_num_frames()

    @property
    def tags(self):
        return self.file_data.get_tags()

    @classmethod
    def from_path(
        cls,
        path: Path,
        anim_tag_colors: List["TagColor"],
        window_tag_colors: List["TagColor"],
        is_fresh: bool,
    ):
        with open(path, "rb") as f:
            contents = f.read()
            raw_aseprite_file = RawAsepriteFile(contents)
        return cls(
            file_data=raw_aseprite_file,
            anim_tag_colors=anim_tag_colors,
            window_tag_colors=window_tag_colors,
            is_fresh=is_fresh,
        )


class Aseprite(File):
    def __init__(
        self,
        path: Path,
        anim_tag_colors: List["TagColor"],
        window_tag_colors: List["TagColor"],
        modified_time: datetime = None,
        processed_time: datetime = None,
        content=None,
        anims: Anim = None,
        anim_hashes: Dict[str, str] = None,  # None for testing only
    ):
        super().__init__(path, modified_time, processed_time)
        self.anim_tag_colors = anim_tag_colors
        self.window_tag_colors = window_tag_colors
        self.anim_hashes = anim_hashes
        self._content = content
        self._anims = anims

    @property
    def content(self) -> AsepriteFileContent:
        if self._content is None:
            self._content = AsepriteFileContent.from_path(
                path=self.path,
                anim_tag_colors=self.anim_tag_colors,
                window_tag_colors=self.window_tag_colors,
                is_fresh=self.is_fresh,
            )
        return self._content

    @property
    def name(self):
        return self.path.stem

    @property
    def anims(self):
        if self._anims is None:
            self._anims = self.get_anims()
        return self._anims

    async def save(
        self,
        path_params: "AsepritePathParams",
        config_params: "AsepriteConfigParams",
    ):
        coroutines = []
        for anim in self.anims:
            if anim.is_fresh:
                coroutines.append(
                    anim.save(path_params, config_params, aseprite_file_path=self.path)
                )
        await asyncio.gather(*coroutines)

    def get_anims(self):
        tag_anims = [
            self.make_anim_with_windows_in_range(
                name=tag.name,
                start=tag.start,
                end=tag.end,
                file_is_fresh=self.is_fresh,
                content=self.content,
                anim_hashes=self.anim_hashes,
            )
            for tag in self.content.tags
            if tag.color in self.anim_tag_colors
        ]
        if tag_anims:
            return tag_anims
        else:
            return [
                self.make_anim_with_windows_in_range(
                    name=self.name,
                    start=0,
                    end=self.content.num_frames - 1,
                    file_is_fresh=self.is_fresh,
                    content=self.content,
                    anim_hashes=self.anim_hashes,
                )
            ]

    def make_anim_with_windows_in_range(
        self,
        name: str,
        start: int,
        end: int,
        file_is_fresh: bool,
        content: "AsepriteFileContent",
        anim_hashes: Dict[str, str],
    ):
        return Anim(
            name=name,
            start=start,
            end=end,
            windows=self.get_windows_in_frame_range(start=start, end=end),
            file_is_fresh=file_is_fresh,
            content=content,
            anim_hashes=anim_hashes,
        )

    def get_windows_in_frame_range(self, start: int, end: int):
        tags_in_frame_range = [
            window
            for window in self.content.tags
            if window.color in self.window_tag_colors
            and start <= window.start <= end
            and start <= window.end <= end
        ]
        windows = [
            Window(name=tag.name, start=tag.start - start + 1, end=tag.end - start + 1)
            for tag in tags_in_frame_range
        ]
        return windows

    def __str__(self):
        return self.path.name


def read_aseprites(run_context: RunContext) -> List[Aseprite]:
    ase_paths: Iterable[Path] = itertools.chain(
        *[
            list((run_context.root_dir / "anims").rglob(f"*.{filetype}"))
            for filetype in ("ase", "aseprite")
        ]
    )
    processed_time = get_script_processed_time(dotfile=run_context.dotfile)
    aseprites = []
    for path in ase_paths:
        aseprite = read_aseprite(
            run_context=run_context,
            path=path,
            processed_time=processed_time,
        )
        aseprites.append(aseprite)
    return aseprites


def read_aseprite(
    run_context: RunContext, path: Path, processed_time: datetime = None
) -> Aseprite:
    if processed_time is None:
        processed_time = get_script_processed_time(dotfile=run_context.dotfile)

    aseprite = Aseprite(
        path=path,
        modified_time=_get_modified_time(path),
        processed_time=processed_time,
        anim_tag_colors=assistant_config_mod.get_anim_tag_color(
            run_context.assistant_config
        ),
        window_tag_colors=assistant_config_mod.get_window_tag_color(
            run_context.assistant_config
        ),
        anim_hashes=run_context.dotfile.setdefault("anim_hashes", {}).setdefault(
            path.stem, {}
        ),
    )
    return aseprite
