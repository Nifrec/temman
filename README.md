# Temman - Template Manager
A simple tool to make organising your personal templates easier.

## Use case
Recognise the following?
You want to start a new project (e.g., a LaTeX document, programming project,
etc.), but you don't remember all necessary boilerplate
or want to reuse nice definitions/macros that you invented
in your previous project.
So you go back to your previous project,
copy it, and delete the things specific to the old project
in order to obtain a clean template.

**Better idea:** make a global template in one place
and make a local copy of it for every new project.
This is the essence of Temman.

This still has one problem: you may make changes to the template locally
that you'd also like to use next time.
Copying them back to the template is a new fuss.
Or you updated your global template, and the local copy is outdated.

Temman solves this as follows:
* A 'global' part of the template can be synchronised with to your
    templates collection.
* A 'local' part of the template (indented to be edited as part of the project)
    will never be synchronised.
    
## How does this work?
Simple:
* Create a new project with `temman new my_template`.
    It simply copies files from a designated collection of templates.
    This are just directories containing the local parts
    of a template and a subdirectory `globaltemplate` that can
    be synchronised.
* Push changes to the global template back to your template
    collection via `temman push`.
* Pull updates from the global template collection
    to your local project via `temman pull`.
* Temman keeps metadata in your project in a hidden file `.temman.json`.

## Example
### Installation
Alice installs Temman as follows:
1. She stores her templates in `/home/alice/templates`.
2. She changes the global variable `TEMPLATE_SUPERDIR` 
    in `temman.py` to
    `TEMPLATE_SUPERDIR = "/home/alice/templates"`.
3. She copies (or creates a softlink to) `temman.py`
    as `temman` into a directory on her PATH.
    (e.g., `sudo cp temman.py /bin/temman` if you want to install
    it globally for all users).

### Usage
Alice wants to create a new project named `foo` 
in `/home/alice/projects/`.
She changed directory to the latter, but forgot
the name of her favourite template;
running
```
temman -l
```
refreshes her memory and reminds her that
she had created a `wonderland_tex` template 
(i.e., as a subdirectory of `/home/alice/templates`).
Now she runs:
```
temman new wonderland_tex -n foo
```
to create the new project named `foo` as `/home/alice/projects/foo`.

Some time later she made changes to her macros in
`/home/alice/projects/foo/globaltemplate` that she
wants to reuse in future projects based on `wonderland_tex`.
She changes directory to `/home/alice/projects/foo`
and runs:
```
temman push
```

Another time she made changes her macros in `wonderland_tex`
while working on another project,
but now she wants to update the macros in the `foo` project as well.
She changes directory to `/home/alice/projects/foo`
and runs:
```
temman pull
```

## Format of template collection
Your template collection (to be stored in `TEMPLATE_SUPERDIR`)
is a directory containing a subdirectory for every template.
If you have a template named `wonderland_tex`,
then `temman new wonderland_tex -n foo` copies all files
from `wonderland_tex` into the new project.
The only exception are files prefixed with `DOT_`,
these will be renamed to use an actual `.`.
For example, `DOT_gitignore` will become `.gitignore` in the local copy.
Other than that, all files are simply copied.

Every project should contain a subdirectory named `globaltemplate`
that will be synchronised via `temman push` and `temman pull`.
Pushing will rename files starting with a `.` to `DOT_`.

## Tips and warnings
* The included templates are my favourite LaTeX templates.
    I always compile LaTeX with `--output-directory=output`,
    hence the `output` subdirectories.
* Use git (or another version management system) to track
    changes in your template collection.
    A nice backup when you accidentally push the wrong things.
* Temman is not git, it is far dumber and does not even
    check the content of files.
    The push and pull functions simply overwrite files.
* If you decide to change the local part of the template,
    then Temman cannot synchronise (via `temman pull`) 
    this back to existing projects.
* Temman ignores symbolic links.

## Ideas for improvements
* Make Temman use git to implement more careful
    variants of its `push` and `pull` actions,
    that can also pull changes to the local part of a template.
* Come up with a better behaviour for dealing with symbolic links.
    Currently I am a bit in doubt what the best policy should be.
    The main pain are symlinks with a destination within
    the template.
