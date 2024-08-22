#!/bin/python3
"""
This file if part of 'temman',
a small tool for organising personal plaintext templates
(in particular for LaTeX projects).

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

Commandline commands for 
(1) making a new project based on a given template.
(2) updating the local copy of a template by pulling changes
    made to the template.
(3) updating the global template by pushing changes
    made in the local copy back to the global version.
"""
from __future__ import annotations
from typing import Any
import argparse
import os
import shutil
import json
import warnings

# Directory containing the templates,
# which are each a subdirectory of the following:
TEMPLATE_SUPERDIR = "/home/nifrec/system/latex/templates"

DOTS_LONG = "DOT_"

SYNCHED_DIR_NAME = "globaltemplate"

# Maximum number of characters in a printed path.
# For longer paths, the suffix will be removed.
MAX_PATH_PRINT_LEN = 50

CACHE_FILENAME = ".temman.json"
# JSON field for the name of a template.
CACHE_KEY_TEMPLATE = "template"
# JSON field for the directory a template is stored in.
CACHE_KEY_TEMPLATE_DIR = "template_dir"

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
                            + "\nDefault: name of template"))
    parser_new.add_argument("-d", action="store", 
                            help="directory to create new project in."
                            + "\nDefault: current working directory",
                            default=os.getcwd()
                            )
    parser_new.set_defaults(cmd="new")

    parser_pull = subparses.add_parser(
            "pull", help="update globaltemplate in am existing project")
    parser_pull.add_argument("-d", action="store", 
                            help="root directory of target project."
                            + "\nDefault: current working directory",
                            default=os.getcwd()
                            )
    parser_pull.set_defaults(cmd="pull")

    parser_push = subparses.add_parser(
            "push", help="update globaltemplate in template collection based"
                         + "on globaltemplate in local project")
    parser_push.add_argument("-d", action="store", 
                            help="root directory of local project."
                            + "\nDefault: current working directory",
                            default=os.getcwd()
                            )
    parser_push.set_defaults(cmd="push")

    return parser


def parse_arguments(parser: argparse.ArgumentParser,
                    template_dirs: dict[str, str]
                    ) -> None:
    parse = parser.parse_args()
    parsed_args = vars(parse)
    if parsed_args["l"]:
        print("Available templates:")
        for name in template_dirs.keys():
            print(f"* {name}")
    # The user selected the subcommand 'new':
    elif parse.cmd == "new":
        exec_subcommand_new(parsed_args, template_dirs)
    elif parse.cmd == "push":
        exec_subcommand_pull_push(parsed_args, template_dirs, push=True)
    elif parse.cmd == "pull":
        exec_subcommand_pull_push(parsed_args, template_dirs, push=False)
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
    if parsed_args["n"] is not None:
        new_proj_name = parsed_args["n"]
    else:
        new_proj_name = parsed_args["template"]
    new_proj_dir = os.path.join(new_proj_superdir, new_proj_name)
    message = f"About to create a project in:\n{new_proj_dir}\nContinue?"
    get_confirmation(message)

    template_dir = template_dirs[parsed_args["template"]]
    copy_dir(template_dir, new_proj_dir, False)

    create_json_cache(parsed_args["template"],
                      template_dir,
                      new_proj_dir)

def exec_subcommand_pull_push(parsed_args: dict[str, Any],
                              template_dirs: dict[str, str],
                              push: bool):
    """
    If `push` is `False`, then remove the `globaltemplate`
    in the local project and replace it with a fresh
    copy from the corresponding template in the template collection.
    If `push` is `True` instead, remove the `globaltemplate`
    in the corresponding template in the collection
    and replace it with the `globaltemplate` of the local project.
    """
    project_dir = parsed_args["d"]
    cache = load_cache(parsed_args["d"])
    template = cache[CACHE_KEY_TEMPLATE]
    template_dir = cache[CACHE_KEY_TEMPLATE_DIR]

    if template not in template_dirs.keys():
        warnings.warn(
            f"Misconfiguration: cached template name '{template}'\n"
            + "does not occur in configured templates",
            RuntimeWarning)
    if template_dir != template_dirs[template]:
        warnings.warn(
            f"Misconfiguration: cached template's directory"
            + f"\t{template_dir}\n"
            + "does not match the directory in the configured templated",
            RuntimeWarning)
    if SYNCHED_DIR_NAME not in os.listdir(project_dir):
        print("Current project has no `globaltemplate` directory:\n"
              + "nothing to synchronise.")
    if push:
        source_dir = os.path.join(project_dir, SYNCHED_DIR_NAME)
        target_dir = os.path.join(template_dir, SYNCHED_DIR_NAME)
        spell_out_dots = True
    else:
        source_dir = os.path.join(template_dir, SYNCHED_DIR_NAME)
        target_dir = os.path.join(project_dir, SYNCHED_DIR_NAME)
        spell_out_dots = False

    confirm_msg = (f"Override the content of\n\t{target_dir}\n"
        + f"with\n\t{source_dir}\n?")
    get_confirmation(confirm_msg)
    if not os.path.exists(target_dir):
        warnings.warn("The `globaltemplate` of the target does not exist.")
    else:
        print(f"Removing\n\t{target_dir}\n")
        shutil.rmtree(target_dir)
    
    copy_dir(source_dir, target_dir, spell_out_dots)

def create_json_cache(template_name: str,
                    template_dir: str,
                    location: str):
    """
    Create a new JSON file (with name `CACHE_FILENAME`)
    in `location` with the given values for fields.
    """
    cache : dict[str, str] = {
            CACHE_KEY_TEMPLATE : template_name,
            CACHE_KEY_TEMPLATE_DIR : template_dir
            } 
    filepath = os.path.join(location, CACHE_FILENAME)
    print("Creating cache file:\n\t" + filepath)
    with open(filepath, "w") as fp:
        json.dump(cache, fp)

def load_cache(location: str) -> dict[str, str]:
    """
    Load a Temman cache file from a project created
    with `Temman new` with as root directory `location`.
    """
    filepath = os.path.join(location, CACHE_FILENAME)
    if not os.path.exists(filepath):
        raise RuntimeError(f"Temman cache file\t\n{filepath}\nnot found."
                           " Are you sure that\t\n{location}\n"
                           "is a project created with `temman new`?")
    with open(filepath, "r") as fp:
        return json.load(fp)
    
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
                os.symlink(src=new_target, dst=new_path,
                           target_is_directory=entry.is_dir())

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
    else:
        msg += inp
    msg += "\nNew copy:\n\t"
    if len(outp) > MAX_PATH_PRINT_LEN:
        msg += "..." + outp[(-MAX_PATH_PRINT_LEN - 3):]
    else:
        msg += outp
    msg += "\n"
    print(msg)

if __name__ == "__main__":
    main()
