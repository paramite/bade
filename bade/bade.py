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

from .commands import create_environment, rebase
from . import utils

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


@bade.command('create-environment')
@click.option('--repo', default='.',
              help='Base Git repository')
@click.option('--base', help='Base URL for patches repos')
@click.option('--target', default='.',
              help='Target directory for patches repos')
@click.option('--branches', default='',
              help='Comma separated list of items in format '
                   'main_branch:patches_branch')
@click.argument('name', default='default')
@pass_config
def create_environment_wrapper(config, repo, base, target, branches, name):
    """Creates patches environment.
    Accepts arguments: [environment_name]
    """
    try:
        create_environment.command(config, repo, base, target, branches, name)
    except utils.ExecutionError as ex:
        click.echo(ex)
        if config.verbose:
            click.echo(
                '========= stdout =========\n{stdout}\n'
                '========= stderr =========\n{stderr}'.format(**ex.__dict__)
            )
    except Exception as ex:
        click.echo(ex)
        if config.verbose:
            raise


@bade.command('rebase')
@click.argument('environment', required=True)
@click.argument('branch', required=True)
@click.argument('module', default='')
@pass_config
def rebase_wrapper(config, environment, branch, module):
    """Rebases branch for given module of given environment.
    Accepts arguments: environment_name, patch_branch_name, module_name
    """
    try:
        rebase.command(config, environment, branch, module)
    except utils.ExecutionError as ex:
        click.echo(ex)
        if config.verbose:
            click.echo(
                '========= stdout =========\n{stdout}\n'
                '========= stderr =========\n{stderr}'.format(**ex.__dict__)
            )
    except Exception as ex:
        click.echo(ex)
        if config.verbose:
            raise

if __name__ == '__main__':
    bade()
