# Wahoo! Results - https://github.com/JohnStrunk/wahoo-results
# Copyright (C) 2025 - John D. Strunk
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

"""Time resolver(s)."""

from typing import Literal

from raceinfo import Lane, Time, TimeResolver, truncate_hundredths


def standard_resolver(
    min_times: int, threshold: Time, min_valid_time: Time = Time("10.00")
) -> TimeResolver:
    """
    Get a standard time resolver for a lane.

    The standard resolver will:

    1. Remove all times that are less than the minimum valid time.
    2. Use the primary time if it is present and supported (within the
       threshold) by at least one backup time.
    3. If there is no primary, it will use a composite of the backup times
       (average or median) as long as all backups are within the threshold of
       the calculated time.

    :param min_times: The minimum number of backup times required for them to be
        used to generate a final time
    :param threshold: The threshold for validating a final time against its
        backup times and/or its components
    :param min_valid_time: The minimum valid time for a time to be considered
        valid. This is used to filter out invalid times.
    """

    def strip_invalid_times(lane: Lane) -> None:
        if lane.primary is not None and lane.primary < min_valid_time:
            lane.primary = None
        if lane.backups is not None:
            for i, backup in enumerate(lane.backups):
                if backup is not None and backup < min_valid_time:
                    lane.backups[i] = None
        if lane.splits is not None:
            for i, split in enumerate(lane.splits):
                if split is not None and split < min_valid_time:
                    lane.splits[i] = None

    def resolve_final_time(lane: Lane) -> None:
        lane.final_time = None
        if lane.backups is None:  # No backups, so we can't do anything
            return
        valid_backups = [backup for backup in lane.backups if backup is not None]
        # See if we can use the primary time
        if lane.primary is not None:
            # Check if the primary is supported by at least one backup time
            if _is_supported_by(lane.primary, valid_backups, threshold, "any"):
                lane.final_time = lane.primary
                return
        # We don't have a primary time or it is not supported by any backup times, so we need to use the backups
        if len(valid_backups) >= min_times:
            candidate = _get_candidate(valid_backups)
            if candidate is not None:
                if _is_supported_by(candidate, valid_backups, threshold, "all"):
                    lane.final_time = candidate

    def resolve(lane: Lane) -> None:
        strip_invalid_times(lane)
        resolve_final_time(lane)

    return resolve


def _is_supported_by(
    candidate: Time,
    backups: list[Time],
    threshold: Time,
    by: Literal["all"] | Literal["any"],
) -> bool:
    """
    Check if a candidate time is supported by a set of backup times.

    :param candidate: The candidate time
    :param backups: The backup times
    :param threshold: The threshold for validating a final time against its backup times and/or its components
    :param by: "all" if all backups must be within the threshold, "any" if any backup must be within the threshold
    :returns: True if the candidate is supported by the backups, False otherwise

    Examples:
    >>> _is_supported_by(Time("30.00"), [Time("29.00")], Time("0.30"), "any")
    False
    >>> _is_supported_by(Time("30.00"), [Time("29.70")], Time("0.30"), "any")
    True
    >>> _is_supported_by(
    ...     Time("30.00"), [Time("25.00"), Time("30.20")], Time("0.30"), "any"
    ... )
    True
    >>> _is_supported_by(
    ...     Time("30.00"), [Time("25.00"), Time("30.20")], Time("0.30"), "all"
    ... )
    False
    >>> _is_supported_by(
    ...     Time("30.00"), [Time("25.00"), Time("30.20")], Time("0.10"), "any"
    ... )
    False
    """
    if by == "all":
        return all(abs(candidate - backup) <= threshold for backup in backups)
    else:
        return any(abs(candidate - backup) <= threshold for backup in backups)


def _get_candidate(raw_times: list[Time]) -> Time | None:
    """
    Get a candidate time from a list of raw times.

    - For 1 time, it is the time itself.
    - For 2 times, it is the average of the two times.
    - For 3 or more times, it is the median of the times. When there is an even
      number of times, the average of the two middle times is used.

    :param raw_times: The individual times
    :returns: The candidate time or None if no times are present

    Examples::
    >>> _get_candidate([])
    >>> _get_candidate([Time(100)])
    Decimal('100.00')
    >>> _get_candidate([Time(100), Time(200)])
    Decimal('150.00')
    >>> _get_candidate([Time(200), Time(100), Time(300)])
    Decimal('200.00')
    >>> _get_candidate([Time(300), Time(100), Time(200), Time(400)])
    Decimal('250.00')
    >>> _get_candidate([Time(10.25), Time(10.00)])
    Decimal('10.12')
    """
    num_times = len(raw_times)
    if num_times == 0:
        return None

    sorted_times = sorted(raw_times)
    if num_times % 2 == 0:
        candidate = (
            sorted_times[num_times // 2 - 1] + sorted_times[num_times // 2]
        ) / 2
    else:
        candidate = sorted_times[num_times // 2]

    if candidate is not None:
        return truncate_hundredths(candidate)
    return None
