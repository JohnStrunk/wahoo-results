# Wahoo! Results - https://github.com/JohnStrunk/wahoo-results
# Copyright (C) 2020 - John D. Strunk
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

'''Version information'''
from typing import List, Optional
import datetime
import re

import dateutil.parser
import dateutil.tz
import requests
import semver  #type: ignore

#pylint: disable=too-few-public-methods
class ReleaseInfo:
    """
    ReleaseInfo describes a single release from a GitHub repository.
    """
    tag: str                      # The git tag of the release
    url: str                      # The url to the release page
    draft: bool                   # Whether the release is a draft
    prerelease: bool              # Whether the release is a prerelease
    published: datetime.datetime  # When the release was published
    semver: str                   # The version corresponding to the tag

    def __init__(self, release_json):
        self.tag = release_json['tag_name']
        self.url = release_json['html_url']
        self.draft = release_json['draft']
        self.prerelease = release_json['prerelease']
        self.published = dateutil.parser.isoparse(release_json['published_at'])
        self.semver = re.match(r'^v?(.*)$', self.tag).group(1)


def releases(user_repo: str) -> List[ReleaseInfo]:
    """
    Retrieves the list of releases for the provided repo. user_repo should be
    of the form "user/repo" (i.e., "JohnStrunk/wahoo-results")
    """
    url = f'https://api.github.com/repos/{user_repo}/releases'
    # The timeout may be too fast, but it's going to hold up displaying the
    # settings screen. Better to miss an update than hang for too long.
    resp = requests.get(url, headers={'Accept': 'application/vnd.github.v3+json'}, timeout=2)
    if not resp.ok:
        return []

    body = resp.json()
    return list(map(ReleaseInfo, body))

def highest_semver(rlist: List[ReleaseInfo]) -> ReleaseInfo:
    """
    Takes a list of releases and returns the one with the highest semantic
    version tag. Assumes the tag is the semver string with an optional leading
    "v" (e.g., "1.2" or "v1.2")
    """
    highest = rlist[0]
    for release in rlist:
        if semver.compare(release.semver, highest.semver) > 0:
            highest = release
    return highest

def git_semver(wrv: str) -> str:
    """
    Returns a legal semver description of the Wahoo Results version
    identifier.

    >>> git_semver('1.0.0')
    '1.0.0'
    >>> git_semver('v1.0')
    '1.0'
    >>> git_semver('v0.3.2-2-g97e7a82')
    '0.3.2-dev.2+g97e7a82'
    """
    # groups: tag (w/o v), commits, hash (w/ g)
    components = re.match(r'^v?([^-]+)(?:-(\d+)-(g[0-9a-f]+))?$', wrv)
    if components is None:
        return "0.0.1"
    version = components.group(1)
    if components.group(2) is not None:
        commits = components.group(2)
        sha = components.group(3)
        version += f'-dev.{commits}+{sha}'
    return version

def latest() -> Optional[ReleaseInfo]:
    """Retrieves the latest release info"""
    rlist = releases("JohnStrunk/wahoo-results")
    if len(rlist) == 0:
        return None
    return highest_semver(rlist)

def is_latest_version(latest_version: Optional[ReleaseInfo], wrv:str) -> bool:
    """Returns true if the running version is the most recent"""
    if latest_version is None:
        return True
    if wrv == "unreleased":
        return False
    return semver.compare(latest_version.semver, git_semver(wrv)) <= 0
