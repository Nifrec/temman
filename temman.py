#!/bin/python3
"""
This file if part of 'niflatex',
Nifrec's (Lulof Pirée)'s small tool for organising 
personal LaTeX templates.

--------------------------------------------------------------------------------

Author: Lulof Pirée

Copyright © 2024 Lulof Pirée

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

--------------------------------------------------------------------------------
*File content:*

Interactive commands for 
(1) making a new project based on a given template.
(2) updating the local copy of a template by pulling changes
    made to the template.
(3) updating the global template by pushing changes
    made in the local copy back to the global version.
"""
from __future__ import annotations
from typing import Any
import argparse
import sys
import os
import shutil

# Directory containing the templates,
# which are each a subdirectory of the following:
TEMPLATE_SUPERDIR = "/home/nifrec/system/latex/templates"

DOTS_LONG = "DOT_"

# Maximum number of characters in a printed path.
# For longer paths, the suffix will be removed.
MAX_PATH_PRINT_LEN = 50

"""TODO:
    Implement new copying and DOT_ renaming.
    Implement hidden file.
    Rename this file.
    Implement push and pull.
    Actually make useful templates, test and debug.
"""

def main(template_dir: str = TEMPLATE_SUPERDIR):
    template_dirs = get_template_dirs(template_dir)
    parser = build_parser(template_dirs)
    parse_arguments(parser, template_dirs)

def build_parser(template_dirs: dict[str, str]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", action="store_true", 
                        help="list existing templates (overrides subcommands)")
    subparses=parser.add_subparsers(title="subcommands")

    parser_new = subparses.add_parser("new", 
                                      help="create a new project"
                                      + " based on a given template")
    parser_new.add_argument("template", type=str, choices=template_dirs.keys())
    parser_new.add_argument("-n", type=str, 
                            action="store",
                            help=("name for new project directory."
                            + "Default: name of template"))
    parser_new.add_argument("-d", action="store", 
                            help="directory to create new project in."
                            + "Default: current working directory",
                            default=os.getcwd()
                            )
    return parser


def parse_arguments(parser: argparse.ArgumentParser,
                    template_dirs: dict[str, str]
                    ) -> None:
    parsed_args = vars(parser.parse_args())
    if parsed_args["l"]:
        print("Available templates:")
        for name in template_dirs.keys():
            print(f"* {name}")
    # The user selected the subcommand 'new':
    elif "template" in parsed_args.keys(): 
        exec_subcommand_new(parsed_args, template_dirs)

    else:
        parser.print_help()

def get_template_dirs(template_superdir = TEMPLATE_SUPERDIR) -> dict[str, str]:
    """
    Return a dictionary mapping every found template
    to the filepath of that template.
    """
    if not os.path.exists(template_superdir):
        print("Error: template directory '{template_dir}' not found.")
    template_names = os.listdir(template_superdir)
    if len(template_names) == 0:
        print("Error: no templates found in {template_dir}.")
        exit()
    return {name : os.path.join(template_superdir, name) 
            for name in template_names}

def exec_subcommand_new(parsed_args: dict[str, Any],
                        template_dirs: dict[str, str]):
    assert "template" in parsed_args.keys() and \
            parsed_args["template"] in template_dirs.keys(), \
            "Bug: exec_subcommand_new received non-existing template."
    new_proj_superdir = parsed_args["d"]
    if "n" in parsed_args.keys():
        new_proj_name = parsed_args["n"]
    else:
        new_proj_name = parsed_args["template"]
    new_proj_dir = os.path.join(new_proj_superdir, new_proj_name)
    message = f"About to create a project in:\n{new_proj_dir}\nContinue?"
    get_confirmation(message)
    
def get_confirmation(message: str):
    """
    Prompt the message and another line "Please type 'y' or 'n': "
    and ask the user to type 'y' or 'n'.
    Repeat if the user inputted another string.
    Exit if the user gave 'n'.
    Return successfully if the user gave 'y'.
    """
    submessage = "Please type 'y' or 'n': "
    while True:
        print(message)
        print(submessage, end="")
        user_inp = str.lower(input())
        if user_inp in ["y", "yes"]:
            return
        elif user_inp in ["n", "no"]:
            exit()
        else:
            print(f"Unrecognised input '{user_inp}', please try again.")

def copy_dir(input_dir: str,
             output_dir: str,
             lengthen_dots: bool):
    """
    Copy content from the input_dir to the output_dir
    (both should be paths to a directory on the OS.
    If lengthen_dots is True,
    then files whose names are of the form `.foo`
    to `DOT_foo`. If False, then names
    of the form `DOT_foo` will be changed to `.foo`.

    This function will probably loop if circular links exist.
    """
    __copy_dir_rec(input_dir, input_dir, output_dir, output_dir, lengthen_dots)

def __copy_dir_rec(inp_master_dir: str,
                   input_dir: str,
                   output_master_dir : str,
                   output_dir: str,
                   lengthen_dots: bool):
    assert os.path.exists(input_dir)
    if not os.path.exists(output_dir):
        print(f"Making directory:\n\t{output_dir}\n")
        os.makedirs(output_dir)

    if lengthen_dots:
        old_prefix = "."
        new_prefix = DOTS_LONG
    else:
        old_prefix = DOTS_LONG
        new_prefix = "."

    with os.scandir(input_dir) as it:
        for entry in it:
            new_name = change_prefix(old_prefix, new_prefix, entry.name)
            new_path = os.path.join(output_dir, new_name)
            if entry.is_dir() and not entry.is_symlink():
                print(f"New directory. Input dir: \n\t{entry.path}")
                __copy_dir_rec(inp_master_dir,
                               entry.path, output_master_dir,
                               new_path, lengthen_dots)
            elif entry.is_file() and not entry.is_symlink():
                print_copy_file(inp=entry.path, outp=new_path, 
                                note="Regular file")
                shutil.copyfile(entry.path, new_path, follow_symlinks = False)
            elif entry.is_symlink():
                abs_target = os.path.realpath(entry.path)
                if abs_target.startswith(os.path.realpath(inp_master_dir)):
                    # The symbolic link links to within the template.
                    # We need to rename the target.
                    new_subpath = []
                    head = abs_target
                    while head != os.path.realpath(inp_master_dir):
                        (head, tail) = os.path.split(head)
                        new_subpath.append(
                            change_prefix(old_prefix, new_prefix, tail))
                    new_target = str.join("", reversed(new_subpath))
                    new_target = os.path.join(output_master_dir, new_target)
                else:
                    new_target = abs_target
                print_copy_file(inp=entry.path, outp=new_path, 
                                note="Symlink with old target:\n\t"
                                + abs_target + "\nAnd new target:\n\t"
                                + new_target)

def change_prefix(old_prefix: str, new_prefix: str, name: str) -> str:
    """
    If the string `name` starts with the `old_prefix`,
    return the same string but with the `old_prefix` replaced
    by the `new_prefix`.
    Otherwise return the input name.
    """
    if name.startswith(old_prefix):
        return new_prefix + name[len(old_prefix):]
    else:
        return name

def print_copy_file(inp: str, outp: str, note : None | str):
    msg = ""
    if note is not None:
        msg = note + "\n"
    msg += "Original:\n\t"
    if len(inp) > MAX_PATH_PRINT_LEN:
        msg += "..." + inp[(-MAX_PATH_PRINT_LEN - 3):]
    msg += "\nNew copy:\n\t"
    if len(outp) > MAX_PATH_PRINT_LEN:
        msg += "..." + outp[(-MAX_PATH_PRINT_LEN + 3):]
    msg += "\n"
    print(msg)

if __name__ == "__main__":
    main()
