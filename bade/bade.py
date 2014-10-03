#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  bade.py
#
#  Copyright 2014 Martin Magr <mmagr@redhat.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

import click
import os

from . import commands
from . import utils


DEFAULT_OUTPUT = os.path.expanduser(
    '~/rpmbuild/SPECS/openstack-puppet-modules.spec'
)
DEFAULT_TEMPLATE = 'openstack-puppet-modules.template'


# Setup option container
class Config(object):
    def __init__(self):
        self.verbose = False

pass_config = click.make_pass_decorator(Config, ensure=True)


@click.group()
@click.option('--verbose', is_flag=True, help='Enable verbose mode')
@pass_config
def bade(config, verbose):
    config.verbose = verbose


@bade.command('init')
@click.option('--commit', is_flag=True,
              help='Create commit after initialization.')
@click.argument('repo', default='.')
@pass_config
def init_wrapper(config, repo, commit):
    """Creates git subtree hierarchy from Puppetfile located in cwd or
    from repo given by argument."""
    try:
        utils.shout(
            'Initializing git subtree hierarchy for {0}'.format(repo),
            verbose=config.verbose,
            level='info'
        )
        commands.init.command(config, repo, commit)
    except utils.ExecutionError as ex:
        utils.shout(ex, verbose=True, level='error')
        utils.shout(
            '====== stdout ======\n{stdout}\n'
            '====== stderr ======\n{stderr}'.format(**ex.__dict__),
            verbose=config.verbose,
            level=None,
        )
    except Exception as ex:
        utils.shout(ex, verbose=True, level='error')
        if config.verbose:
            raise


@bade.command('sync')
@click.option('--commit', is_flag=True,
              help='Create commit after sync.')
@click.argument('repo', default='.')
@pass_config
def sync_wrapper(config, repo, commit):
    """Updates git subtree hierarchy from Puppetfile located in cwd or
    from repo given by argument."""
    try:
        utils.shout(
            'Updating git subtree hierarchy for {0}'.format(repo),
            verbose=config.verbose,
            level='info'
        )
        commands.sync.command(config, repo, commit)
    except utils.ExecutionError as ex:
        utils.shout(ex, verbose=True, level='error')
        utils.shout(
            '====== stdout ======\n{stdout}\n'
            '====== stderr ======\n{stderr}'.format(**ex.__dict__),
            verbose=config.verbose,
            level=None,
        )
    except Exception as ex:
        utils.shout(ex, verbose=True, level='error')
        if config.verbose:
            raise


@bade.command('spec')
@click.option('--version', required=True,
              help='Version for a tag.')
@click.option('--release', required=True,
              help='Release for a tag.')
@click.option('--old', required=True,
              help='Path to old SPEC file.')
@click.option('--output', default=DEFAULT_OUTPUT,
               help='Path to output SPEC file.')
@click.option('--template', default=DEFAULT_TEMPLATE,
               help='Path to template from which SPEC is generated.')
@click.argument('repo', default='.')
@pass_config
def sync_wrapper(config, repo, version, release, old, output,
                 template):
    """Generates SPEC file from Puppetfile and tags repo appropriately.
    """
    try:
        utils.shout(
            'Generating SPEC file {0} from template {1}'.format(
                output, template
            ),
            verbose=config.verbose,
            level='info'
        )
        commands.spec.command(config, repo, version, release, old,
                              output, template)
    except utils.ExecutionError as ex:
        utils.shout(ex, verbose=True, level='error')
        utils.shout(
            '====== stdout ======\n{stdout}\n'
            '====== stderr ======\n{stderr}'.format(**ex.__dict__),
            verbose=config.verbose,
            level=None,
        )
    except Exception as ex:
        utils.shout(ex, verbose=True, level='error')
        if config.verbose:
            raise


@bade.command('clean')
@click.option('--branch', default=None,
              help='Base branch to clean')
@click.argument('repo', default='.')
@pass_config
def clean_wrapper(config, repo, branch):
    """Removes module branches which have been created to synchronize base
    branch.
    """
    if not branch:
        branch = utils.get_current_branch(repo)
    try:
        utils.shout(
            'Removing module branches for base branch {0}'.format(branch),
            verbose=config.verbose,
            level='info'
        )
        commands.clean.command(config, repo, branch)
    except utils.ExecutionError as ex:
        utils.shout(ex, verbose=True, level='error')
        utils.shout(
            '====== stdout ======\n{stdout}\n'
            '====== stderr ======\n{stderr}'.format(**ex.__dict__),
            verbose=config.verbose,
            level=None,
        )
    except Exception as ex:
        utils.shout(ex, verbose=True, level='error')
        if config.verbose:
            raise

if __name__ == '__main__':
    bade()
