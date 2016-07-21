"""Automatic vox changer"""
import os
import sys
import venv
import shutil
import builtins
import collections.abc

from xonsh.platform import ON_POSIX, ON_WINDOWS, scandir
import xonsh.dirstack

VirtualEnvironment = collections.namedtuple('VirtualEnvironment', ['env', 'bin'])

class Vox(collections.abc.Mapping):
    """Basically a clone of the Vox class, but usable from Python"""

    def __init__(self):
        if not builtins.__xonsh_env__.get('VIRTUALENV_HOME'):
            home_path = os.path.expanduser('~')
            self.venvdir = os.path.join(home_path, '.virtualenvs')
            builtins.__xonsh_env__['VIRTUALENV_HOME'] = self.venvdir
        else:
            self.venvdir = builtins.__xonsh_env__['VIRTUALENV_HOME']

    def create(self, name):
        """
        Create a virtual environment in $VIRTUALENV_HOME with python3's `venv`.
        """
        env_path = os.path.join(self.venvdir, name)
        venv.create(env_path, with_pip=True)

    @staticmethod
    def _binname():
        if ON_WINDOWS:
            return 'Scripts'
        elif ON_POSIX:
            return 'bin'
        else:
            raise OSError('This OS is not supported.')

    def __getitem__(self, name):
        if name is ...:
            env_path = builtins.__xonsh_env__['VIRTUAL_ENV']
        elif os.path.isabs(name):
            env_path = name
        else:
            env_path = os.path.join(self.venvdir, name)
        bin_dir = self._binname()
        bin_path = os.path.join(env_path, bin_dir)
        if not os.path.exists(bin_path):
            raise KeyError()
        return VirtualEnvironment(env_path, bin_path)

    def __iter__(self):
        """List available virtual environments."""
        # FIXME: Handle subdirs
        for x in scandir(self.venvdir):
            if x.is_dir():
                yield x.name

    def __len__(self):
        l = 0
        for _ in self:
            l += 1
        return l

    def active(self):
        """
        Get the name of the active virtual environment
        """
        if 'VIRTUAL_ENV' not in builtins.__xonsh_env__:
            return
        env_path = builtins.__xonsh_env__['VIRTUAL_ENV']
        if env_path.startswith(self.venvdir):
            name = env_path[len(self.venvdir):]
            if name[0] == '/':
                name = name[1:]
            return name
        else:
            return env_path

    def activate(self, name):
        """
        Activate a virtual environment.
        """
        env = builtins.__xonsh_env__
        env_path, bin_path = self[name]
        if 'VIRTUAL_ENV' in env:
            self.deactivate()

        type(self).oldvars = {'PATH': env['PATH']}
        env['PATH'].insert(0, bin_path)
        env['VIRTUAL_ENV'] = env_path
        if 'PYTHONHOME' in env:
            type(self).oldvars['PYTHONHOME'] = env.pop('PYTHONHOME')

    def deactivate(self):
        """
        Deactive the active virtual environment.
        """
        env = builtins.__xonsh_env__
        if 'VIRTUAL_ENV' not in env:
            raise RuntimeError('No environment currently active.')

        env_path, bin_path = self[...]
        env_name = self.active()

        for k,v in type(self).oldvars.items():
            env[k] = v
        del type(self).oldvars

        env.pop('VIRTUAL_ENV')

        return env_name

    def __delitem__(self, name):
        """
        Remove a virtual environment.
        """
        env_path = self[name].env
        if builtins.__xonsh_env__.get('VIRTUAL_ENV') == env_path:
            raise RuntimeError('The "%s" environment is currently active.' % name)
        shutil.rmtree(env_path)

import argparse

class AvoxHandler:
    parser = argparse.ArgumentParser(prog='vox', description=__doc__)
    subparsers = parser.add_subparsers(dest='command')

    create = subparsers.add_parser('new', aliases=['create'], help='Create a new virtual environment')
    create.add_argument('--system-site-packages', default=False,
                        action='store_true', dest='system_site',
                        help='Give the virtual environment access to the '
                             'system site-packages dir.')
    from xonsh.platform import ON_WINDOWS
    if ON_WINDOWS:
        use_symlinks = False
    else:
        use_symlinks = True

    group = create.add_mutually_exclusive_group()
    group.add_argument('--symlinks', default=use_symlinks,
                       action='store_true', dest='symlinks',
                       help='Try to use symlinks rather than copies, '
                            'when symlinks are not the default for '
                            'the platform.')
    group.add_argument('--copies', default=not use_symlinks,
                       action='store_false', dest='symlinks',
                       help='Try to use copies rather than symlinks, '
                            'even when symlinks are the default for '
                            'the platform.')
    create.add_argument('--without-pip', dest='with_pip',
                        default=True, action='store_false',
                        help='Skips installing or upgrading pip in the '
                             'virtual environment (pip is bootstrapped '
                             'by default)')

    remove = subparsers.add_parser('remove', aliases=['rm', 'delete', 'del'], help='Remove virtual environment')
    subparsers.add_parser('help', help='Show this help')

    aliases = {
        'new': 'create',
        'rm': 'remove',
        'delete': 'remove',
        'del': 'remove',
    }

    @classmethod
    def handler(cls, args, stdin=None):
        return cls()(args, stdin)

    def __init__(self):
        if not builtins.__xonsh_env__.get('PROJECT_DIRS'):
            print("Warning: Unconfigured $PROJECT_DIRS. Using ~/code")
            home_path = os.path.expanduser('~')
            self.projdirs = [os.path.join(home_path, 'code')]
            builtins.__xonsh_env__['PROJECT_DIRS'] = self.projdirs
        else:
            self.projdirs = builtins.__xonsh_env__['PROJECT_DIRS']
            if isinstance(self.projdirs, str):
                self.projdirs = [self.projdirs]

        self.vox = Vox()

    def env(self, pwd=None):
        """
        Figure out the environment name for a directory.
        """
        if pwd is None or pwd is ...:
            pwd = os.getcwd()
        for pd in self.projdirs:
            if pd == pwd:
                return
            elif pwd.startswith(pd):
                proj = pwd[len(pd):]
                if proj[0] == '/': proj = proj[1:]
                break
        else:
            return

        envs = set(self.vox)
        while proj:
            if proj in envs:
                return proj
            proj = os.path.dirname(proj)
        else:
            return

    def envForNew(self, pwd=None):
        """
        Guess an environment name for a directory without actually seeing what environments exist.
        """
        if pwd is None or pwd is ...:
            pwd = os.getcwd()
        for pd in builtins.__xonsh_env__['PROJECT_DIRS']:
            if pwd.startswith(pd):
                proj = pwd[len(pd):]
                if proj[0] == '/': proj = proj[1:]
                return proj
        else:
            return

    def __call__(self, args, stdin=None):
        args = self.parser.parse_args(args)
        cmd = self.aliases.get(args.command, args.command)
        if cmd is None:
            self.parser.print_usage()
        else:
            getattr(self, 'cmd_'+cmd)(args, stdin)

    def cmd_new(self, args, _=None):
        if self.vox.active():
            self.vox.deactivate()
        if self.env() is not None:
            print("Working directory already has a virtual environment.", file=sys.stderr)
            return
        proj = self.envForNew()
        if proj is None:
            print("Working directory not a project. Is $PROJECT_DIRS configured correctly?", file=sys.stderr)
            return
        if proj in self.vox:
            print("Conflict! Project matches name of existing virtual environment, but wasn't detected. Possibly a bug?", file=sys.stderr)
            return
        print("Creating virtual environment {}...".format(proj))
        self.vox.create(proj)
        print("Activating...")
        self.vox.activate(proj)

    def cmd_remove(self, args, _=None):
        if self.vox.active():
            self.vox.deactivate()
        proj = self.env()
        if proj is None:
            print("No virtual environment for the current directory", file=sys.stderr)
            return
        print("Deleting {}...".format(proj))
        del self.vox[proj]

    def cmd_help(self, args, stdin=None):
        self.parser.print_help()

    @classmethod
    def cd_handler(cls, args, stdin=None):
        self = cls()
        oldve = self.vox.active()
        rtn = xonsh.dirstack.cd(args, stdin)
        newve = self.env()
        if oldve != newve:
            if newve is None:
                self.vox.deactivate()
            else:
                self.vox.activate(newve)
        return rtn

builtins.aliases['avox'] = AvoxHandler.handler
builtins.aliases['cd'] = AvoxHandler.cd_handler

AvoxHandler.cd_handler('.')  # I think this is a no-op for changing directories?