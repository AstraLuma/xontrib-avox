# xontrib-avox
Xontrib for Xonsh that automatically activates and deactivates virtual environments as you `cd` around.

Warning: Incompatible with autoxsh due to cd aliasing.

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
xontrib load avox
```

in your `.xonshrc`

Avox respects the `$VIRTUALENV_HOME`.