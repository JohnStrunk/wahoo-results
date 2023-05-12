# Wahoo! Results - https://github.com/JohnStrunk/wahoo-results
# Copyright (C) 2022 - John D. Strunk
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

"""Python script to build Wahoo! Results executable"""

import os
import shutil
import subprocess

import PyInstaller.__main__
import PyInstaller.utils.win32.versioninfo as vinfo
import semver  # type: ignore

import wh_version

print("Starting build process...\n")

# Remove any previous build artifacts
try:
    shutil.rmtree("build")
except FileNotFoundError:
    pass

# Determine current git tag
git_ref = (
    subprocess.check_output('git describe --tags --match "v*" --long', shell=True)
    .decode("utf-8")
    .rstrip()
)
wr_version = wh_version.git_semver(git_ref)
print(f"Building Wahoo Results, version: {wr_version}")
version = semver.version.Version.parse(wr_version)

with open("version.py", "w") as f:
    f.write('"""Version information"""\n\n')
    f.write(f'WAHOO_RESULTS_VERSION = "{wr_version}"\n')

    # Sentry API key
    dsn = os.getenv("SENTRY_DSN")
    if dsn is not None:
        f.write(f'SENTRY_DSN = "{dsn}"\n')
    else:
        f.write("SENTRY_DSN = None\n")

    # Segment API key
    segment = os.getenv("SEGMENT_WRITE_KEY")
    if segment is None:
        segment = "unknown"
    f.write(f'SEGMENT_WRITE_KEY = "{segment}"\n')

    # ipinfo.io
    ipinfo = os.getenv("IPINFO_TOKEN")
    if ipinfo is not None:
        f.write(f'IPINFO_TOKEN = "{ipinfo}"\n')
    else:
        f.write("IPINFO_TOKEN = None\n")

    f.flush()
    f.close()

# Create file info to embed in executable
v = vinfo.VSVersionInfo(
    ffi=vinfo.FixedFileInfo(
        filevers=(version.major, version.minor, version.patch, 0),
        prodvers=(version.major, version.minor, version.patch, 0),
        mask=0x3F,
        flags=0x0,
        OS=0x4,
        fileType=0x1,
        subtype=0x0,
    ),
    kids=[
        vinfo.StringFileInfo(
            [
                vinfo.StringTable(
                    "040904e4",
                    [
                        # https://docs.microsoft.com/en-us/windows/win32/menurc/versioninfo-resource
                        # Required fields:
                        vinfo.StringStruct("CompanyName", "John D. Strunk"),
                        vinfo.StringStruct("FileDescription", "Wahoo! Results"),
                        vinfo.StringStruct("FileVersion", wr_version),
                        vinfo.StringStruct("InternalName", "wahoo_results"),
                        vinfo.StringStruct("ProductName", "Wahoo! Results"),
                        vinfo.StringStruct("ProductVersion", wr_version),
                        vinfo.StringStruct("OriginalFilename", "wahoo-results.exe"),
                        # Optional fields
                        vinfo.StringStruct(
                            "LegalCopyright", "(c) John D. Strunk - AGPL-3.0-or-later"
                        ),
                    ],
                )
            ]
        ),
        vinfo.VarFileInfo(
            [
                # 1033 -> Engligh; 1252 -> charsetID
                vinfo.VarStruct("Translation", [1033, 1252])
            ]
        ),
    ],
)
with open("wahoo-results.fileinfo", "w") as f:
    f.write(str(v))
    f.flush()
    f.close()

print("Invoking PyInstaller to generate executable...\n")

# Build it
PyInstaller.__main__.run(["--distpath=.", "--workpath=build", "wahoo-results.spec"])
