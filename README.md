# xontrib-avox
Xontrib for Xonsh that automatically activates and deactivates virtual environments as you `cd` around. It's based on the idea of projects and projects living in specific directories.

For example, if you've set `$PROJECT_DIRS = [p"~/code"]` and have the project directory `~/code/spam`, avox will use the venv name `spam`.

<hr>


## Installation
Just do a
```console
pip install xontrib-avox
```

or you can clone the repo with pip
```console
pip install git+https://github.com/astronouth7303/xontrib-avox
```

## Configuration
It's required to configure `$PROJECT_DIRS`:
```console
$PROJECT_DIRS = ["~/code"]
```

To automatically load avox at startup, put
```console
xontrib load autovox avox
```

in your `.xonshrc`

Avox respects `$VIRTUALENV_HOME`.
