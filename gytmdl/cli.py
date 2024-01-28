import json
import logging
import shutil
from pathlib import Path
import os
import click
from concurrent.futures import ThreadPoolExecutor
from . import __version__
from .dl import Dl
from typing import Tuple
EXCLUDED_PARAMS = (
    "urls",
    "config_location",
    "url_txt",
    "no_config_file",
    "version",
    "help",
)

def write_default_config_file(ctx: click.Context):
    ctx.params["config_location"].parent.mkdir(parents=True, exist_ok=True)
    config_file = {
        param.name: param.default
        for param in ctx.command.params
        if param.name not in EXCLUDED_PARAMS
    }
    with open(ctx.params["config_location"], "w") as f:
        f.write(json.dumps(config_file, indent=4))


def no_config_callback(
    ctx: click.Context, param: click.Parameter, no_config_file: bool
):
    if no_config_file:
        return ctx
    if not ctx.params["config_location"].exists():
        write_default_config_file(ctx)
    with open(ctx.params["config_location"], "r") as f:
        config_file = dict(json.load(f))
    for param in ctx.command.params:
        if (
            config_file.get(param.name) is not None
            and not ctx.get_parameter_source(param.name)
            == click.core.ParameterSource.COMMANDLINE
        ):
            ctx.params[param.name] = param.type_cast_value(ctx, config_file[param.name])
    return ctx


@click.command()
@click.argument(
    "urls",
    nargs=-1,
    type=str,
    required=True,
)
@click.option(
    "--final-path",
    "-f",
    type=Path,
    default="./YouTube Music",
    help="Path where the downloaded files will be saved.",
)
@click.option(
    "--temp-path",
    "-t",
    type=Path,
    default="./temp",
    help="Path where the temporary files will be saved.",
)
@click.option(
    "--cookies-location",
    "-c",
    type=Path,
    default=None,
    help="Location of the cookies file.",
)
@click.option(
    "--ffmpeg-location",
    type=Path,
    default="ffmpeg",
    help="Location of the FFmpeg binary.",
)
@click.option(
    "--config-location",
    type=Path,
    default=Path.home() / ".gytmdl" / "config.json",
    help="Location of the config file.",
)
@click.option(
    "--itag",
    "-i",
    type=click.Choice(["141", "251", "140"]),
    default="140",
    help="Itag (audio quality).",
)
@click.option(
    "--cover-size",
    type=click.IntRange(0, 16383),
    default=1200,
    help="Size of the cover.",
)
@click.option(
    "--cover-format",
    type=click.Choice(["jpg", "png"]),
    default="jpg",
    help="Format of the cover.",
)
@click.option(
    "--cover-quality",
    type=click.IntRange(1, 100),
    default=94,
    help="JPEG quality of the cover.",
)
@click.option(
    "--template-folder",
    type=str,
    default="{album_artist}/{album}",
    help="Template of the album folders as a format string.",
)
@click.option(
    "--template-file",
    type=str,
    default="{track:02d} {title}",
    help="Template of the song files as a format string.",
)
@click.option(
    "--exclude-tags",
    "-e",
    type=str,
    default=None,
    help="List of tags to exclude from file tagging separated by commas without spaces.",
)
@click.option(
    "--truncate",
    type=int,
    default=40,
    help="Maximum length of the file/folder names.",
)
@click.option(
    "--log-level",
    "-l",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
    help="Log level.",
)
@click.option(
    "--save-cover",
    "-s",
    is_flag=True,
    help="Save cover as a separate file.",
)
@click.option(
    "--overwrite",
    "-o",
    is_flag=True,
    help="Overwrite existing files.",
)
@click.option(
    "--print-exceptions",
    "-p",
    is_flag=True,
    help="Print exceptions.",
)
@click.option(
    "--url-txt",
    "-u",
    is_flag=True,
    help="Read URLs as location of text files containing URLs.",
)
@click.option(
    "--no-config-file",
    "-n",
    is_flag=True,
    callback=no_config_callback,
    help="Don't use the config file.",
)
@click.option(
    "--num_workers",
    type=int,
    default=3,
    help="Number of concurrent downloads",
)
@click.version_option(__version__)
@click.help_option("-h", "--help")

class cli_class:
    def __init__(self,
        urls: Tuple[str],
        final_path: Path,
        temp_path: Path,
        cookies_location: Path,
        ffmpeg_location: Path,
        config_location: Path,
        itag: str,
        cover_size: int,
        cover_format: str,
        cover_quality: int,
        template_folder: str,
        template_file: str,
        exclude_tags: str,
        truncate: int,
        log_level: str,
        save_cover: bool,
        overwrite: bool,
        print_exceptions: bool,
        url_txt: bool,
        no_config_file: bool,
        num_workers: int=3) -> None:
        
        logging.basicConfig(
            format="[%(levelname)-8s %(asctime)s] %(message)s",
            datefmt="%H:%M:%S",
        )
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        if not shutil.which(str(ffmpeg_location)):
            self.logger.critical(f'FFmpeg not found at "{ffmpeg_location}"')
            return
        if cookies_location is not None and not cookies_location.exists():
            self.logger.critical(f'Cookies file not found at "{cookies_location}"')
            return
        else:
            self.logger.debug(f'Cookies file found at "{cookies_location}"')
        if url_txt:
            self.logger.debug("Reading URLs from text files")
            _urls = []
            for url in urls:
                with open(url, "r") as f:
                    _urls.extend(f.read().splitlines())
            urls = tuple(_urls)
        self.logger.debug("Starting downloader")
        local_vars = locals()
        local_vars.pop('self')
        self.dl = Dl(**local_vars)
        self.urls = urls
        self.print_exceptions = print_exceptions
        self.overwrite = overwrite
        self.save_cover = save_cover
        self.error_count = 0
        self.temp_path = temp_path
        self.num_workers=num_workers
        self.cli()

    def cli(
        self
    ):
        
        self.download_queue = []
        for i, url in enumerate(self.urls):
            try:
                self.logger.debug(f'Checking "{url}" (URL {i + 1}/{len(self.urls)})')
                self.download_queue.append(self.dl.get_download_queue(url))
            except Exception:
                self.logger.error(
                    f"Failed to check URL {i + 1}/{len(self.urls)}", exc_info=self.print_exceptions
                )
        
        self.logger.debug(f"Download queue:")
        for i, url in enumerate(self.download_queue):
            with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
                executor.map(self.download_track, url)
        self.logger.info(f"Done ({self.error_count} error(s))")

    def download_track(self, track):
        # for j, track in enumerate(url):
        self.logger.info(
            f'Downloading "{track["title"]}" '
            # f'Downloading "{track["title"]}" (track {j + 1}/{len(url)} from URL {i + 1}/{len(download_queue)})'
        )
        try:
            self.logger.debug("Getting tags")
            ytmusic_watch_playlist = self.dl.get_ytmusic_watch_playlist(track["id"])
            if ytmusic_watch_playlist is None:
                self.logger.warning("Track is a video, using song equivalent")
                track["id"] = self.dl.search_track(track["title"])
                self.logger.debug(f'Video ID changed to "{track["id"]}"')
                ytmusic_watch_playlist = self.dl.get_ytmusic_watch_playlist(track["id"])
            tags = self.dl.get_tags(ytmusic_watch_playlist)
            final_location = self.dl.get_final_location(tags)
            self.logger.debug(f'Final location is "{final_location}"')
            if not final_location.exists() or self.overwrite:
                temp_location = self.dl.get_temp_location(track["id"])
                self.logger.debug(f'Downloading to "{temp_location}"')
                self.dl.download(track["id"], temp_location)
                fixed_location = self.dl.get_fixed_location(track["id"])
                self.logger.debug(f'Remuxing to "{fixed_location}"')
                self.dl.fixup(temp_location, fixed_location)
                self.logger.debug("Applying tags")
                self.dl.apply_tags(fixed_location, tags)
                self.logger.debug("Moving to final location")
                self.dl.move_to_final_location(fixed_location, final_location)
                
            else:
                self.logger.warning("File already exists at final location, skipping")
            if self.save_cover:
                cover_location = self.dl.get_cover_location(final_location)
                if not cover_location.exists() or self.overwrite:
                    self.logger.debug(f'Saving cover to "{cover_location}"')
                    self.dl.save_cover(tags, cover_location)
                else:
                    self.logger.debug(
                        f'File already exists at "{cover_location}", skipping'
                    )
        except Exception:
            self.error_count += 1
            self.logger.error(
                # f'Failed to download "{track["title"]}" (track {j + 1}/{len(url)} from URL '
                # + f"{i + 1}/{len(download_queue)})",
                f'Failed to download "{track["title"]}"',
                exc_info=self.print_exceptions,
            )
        finally:
            if self.temp_path.exists():
                self.logger.debug(f'Cleaning up "{self.temp_path}"')
                os.remove(temp_location)
                # self.dl.cleanup()
      