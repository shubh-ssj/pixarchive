from dataclasses import dataclass, field, fields as dc_fields
from typing import Optional


@dataclass
class DownloadOptions:
    # Output
    output_dir: Optional[str] = None
    filename_pattern: Optional[str] = None
    zip_archive: bool = False
    set_mtime: bool = False

    # Filters
    item_filter: Optional[str] = None
    image_filter: Optional[str] = None
    index_range: Optional[str] = None
    chapter_range: Optional[str] = None

    # Behaviour
    skip_existing: bool = True
    write_metadata: bool = False
    write_tags: bool = False
    write_info_json: bool = False
    dry_run: bool = False
    verbose: bool = False

    # Network
    retries: int = 4
    timeout: float = 30.0
    rate_limit: Optional[str] = None
    cookies_from_browser: Optional[str] = None
    cookies_file: Optional[str] = None
    proxy: Optional[str] = None

    def to_argv(self) -> list[str]:
        """Convert options to gallery-dl CLI arguments."""
        args: list[str] = []

        if self.output_dir:
            args += ["--destination", self.output_dir]
        if self.filename_pattern:
            args += ["--filename", self.filename_pattern]
        if self.zip_archive:
            args += ["--zip"]
        if self.set_mtime:
            args += ["--mtime"]

        if self.item_filter:
            args += ["--filter", self.item_filter]
        if self.image_filter:
            args += ["--image-filter", self.image_filter]
        if self.index_range:
            args += ["--range", self.index_range]
        if self.chapter_range:
            args += ["--chapter-range", self.chapter_range]

        if self.skip_existing:
            args += ["--skip"]
        if self.write_metadata:
            args += ["--write-metadata"]
        if self.write_tags:
            args += ["--write-tags"]
        if self.write_info_json:
            args += ["--write-info-json"]
        if self.dry_run:
            args += ["--simulate"]
        if self.verbose:
            args += ["--verbose"]

        # Compare against the dataclass-declared defaults so there's a single
        # source of truth — changing the default above automatically updates this.
        _defaults = {f.name: f.default for f in dc_fields(self)}
        if self.retries != _defaults["retries"]:
            args += ["--retries", str(self.retries)]
        if self.timeout != _defaults["timeout"]:
            args += ["--timeout", str(self.timeout)]

        if self.rate_limit:
            args += ["--rate", self.rate_limit]
        if self.cookies_from_browser:
            args += ["--cookies-from-browser", self.cookies_from_browser]
        if self.cookies_file:
            args += ["--cookies", self.cookies_file]
        if self.proxy:
            args += ["--proxy", self.proxy]

        return args
