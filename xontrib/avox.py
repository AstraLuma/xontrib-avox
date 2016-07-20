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
        home_path = os.path.expanduser('~')
        if not builtins.__xonsh_env__.get('VIRTUALENV_HOME'):
            self.venvdir = os.path.join(home_path, '.virtualenvs')
            builtins.__xonsh_env__['VIRTUALENV_HOME'] = self.venvdir
        else:
            self.venvdir = builtins.__xonsh_env__['VIRTUALENV_HOME']

        if not builtins.__xonsh_env__.get('PROJECT_DIRS'):
            print("Warning: Unconfigured $PROJECT_DIRS. Using ~/code")
            self.projdirs = [os.path.join(home_path, 'code')]
            builtins.__xonsh_env__['PROJECT_DIRS'] = self.projdirs
        else:
            self.projdirs = builtins.__xonsh_env__['PROJECT_DIRS']
            if isinstance(self.projdirs, str):
                self.projdirs = [self.projdirs]

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

        envs = set(self)
        while proj:
            proj = os.path.dirname(proj)
            if proj in envs:
                return proj
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

def cd_handler(args, stdin=None):
    vox = Vox()
    oldve = vox.active()
    rtn = xonsh.dirstack.cd(args, stdin)
    newve = vox.env()
    if oldve != newve:
        if newve is None:
            vox.deactivate()
        else:
            vox.activate(newve)
    return rtn
builtins.aliases['cd'] = cd_handler

class AVoxHandler:
    commands = {
        'new': 'new',
        'create': 'new',
        'remove': 'remove',
        'delete': 'remove',
        'del': 'remove',
        'rm': 'remove',
        'help': 'help',
    }

    def __call__(self, args, stdin=None):
        if not args:
            self.help(None, None)
            return
        cmd, params = args[0], args[1:]
        cmd = self.commands[cmd]
        vox = Vox()
        getattr(self, cmd)(vox, params, stdin)

    def new(self, vox, args, _=None):
        if vox.active():
            vox.deactivate()
        if vox.env() is not None:
            print("Working directory already has a virtual environment.", file=sys.stderr)
            return
        proj = vox.envForNew()
        if proj is None:
            print("Working directory not a project. Is $PROJECT_DIRS configured correctly?", file=sys.stderr)
            return
        if proj in vox:
            print("Conflict! Project matches name of existing virtual environment, but wasn't detected. Possibly a bug?", file=sys.stderr)
            return
        print("Creating virtual environment {}...".format(proj))
        vox.create(proj)
        print("Activating...")
        vox.activate(proj)

    def remove(self, vox, args, _=None):
        if vox.active():
            vox.deactivate()
        proj = vox.env()
        if proj is None:
            print("No virtual environment for the current directory", file=sys.stderr)
            return
        print("Deleting {}...".format(proj))
        del vox[proj]

    def help(self, vox, args, _=None):
        print("""Available commands:
    avox new (create)
        Create new virtual environment in $VIRTUALENV_HOME
    avox remove (rm, delete, del)
        Remove virtual environment
    avox help (-h, --help)
        Show help
""")

builtins.aliases['avox'] = AVoxHandler()

cd_handler('.')  # I think this is a no-op for changing directories?