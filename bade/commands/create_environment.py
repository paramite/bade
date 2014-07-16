# -*- coding: utf-8 -*-

import click
import os
import re

from ..utils import execute


_status_regex = re.compile(r'^(?P<hash>\w+)\s(?P<dir>[\w\-\_]+)\s.*')
_module_regex = re.compile(
    r'path\s*=\s*(?P<path>[\w\/\-_]+)\s*\n'
     '\s*url\s*=\s*(?P<url>[\w\.\/\:\-_]+)\n'
)


def command(config, repo, base, target, branches):
    """Clones all submodule repos of 'repo' to 'target' directory and sets
    them remote named patches with url composed from
    <base>/<submodule-basename>-patches. Patches remotes have to exist
    in advance. If list of 'branches' are given also patches branches
    are created and pushed to patches repos. Format of branches item is:
    main-repo-branch:patches-repo-branch
    """
    repo = os.path.abspath(repo)
    target = os.path.abspath(target)
    _locals = locals()

    if not os.path.exists(repo):
        click.echo('Given repo does not exist: {repo}'.format(**_locals))
        return 1

    if config.verbose:
        click.echo(
            'Creating target directory: {target}'.format(**_locals)
        )
    os.makedirs(os.path.abspath(target))

    rc, stdout, stderr = execute(
        'cd {repo} && git submodule status'.format(**_locals)
    )
    for line in stdout.split('\n'):
        match = _status_regex.match(line.strip())
        if not match:
            continue

        module = match.group('dir')
        commit = match.group('hash')
        _locals = locals()
        rc, stdout, stderr = execute(
            'cd {repo} && cat .gitmodules |'
            ' grep -A2 "\\[submodule \\"{module}\\"\\]"'.format(**_locals)
        )
        match = _module_regex.search(stdout)
        if not match:
            raise RuntimeError('Module {module} has not been found '
                               'in .gitmodules'.format(**_locals))

        path = match.group('path')
        url = match.group('url')
        base_name = os.path.basename(url)
        if base_name.endswith('.git'):
           base_name = base_name[:-4]
        base_name = '{0}-patches'.format(base_name)
        _locals = locals()
        if config.verbose:
            click.echo(
                'Initializing patches repo for {module}'.format(**_locals),
                nl=False
            )
        rc, stdout, stderr = execute(
            'cd {target} && '
            'git clone {url} {path}'.format(**_locals)
        )

        rc, stdout, stderr = execute(
            'cd {target}/{path} && '
            'git remote add patches {base}/{base_name} && '
            'git fetch --all'.format(**_locals)
        )
        if config.verbose:
            click.echo(' ... DONE')
