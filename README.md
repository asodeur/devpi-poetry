devpi-poetry
============

Plug-Ins to Work with `devpi` and Poetry
----------------------------------------
> **WARNING:** Until the plugin system for Poetry arrives this can be considered a proof-of-concept
> at best. Currently, the primary intention is to learn what it would take to integrate Poetry and
> `devpi` and come-up with consolidated requirements. 

We are running (what we believe is) a fairly common setup except for the use of Poetry:
1. A local [devpi](https://devpi.net/docs/devpi/devpi/stable/%2Bd/index.html) repository with a 
production and a staging index
2. Per developer development indices
3. Index pull request workflow as in [devpi-pr](https://github.com/fschulze/devpi-pr)
4. [Poetry](https://poetry.eustace.io/) as package manager

We are working on the assumption we will never install from more than one index at once (creating
a local `devpi` index with suitable bases if required). The required steps to get the workflow above
going are
1. Make Poetry use the current index (as set by `devpi use`) for package installation exclusively
2. Populate index pull requests for [devpi-pr](https://github.com/fschulze/devpi-pr) from `poetry.lock`
files

The intention is to handle step one with a plugin to Poetry and step two with a devpi-client plugin.

Using the Current `devpi` Index from Poetry
-------------------------------------------
Until the Poetry plugin system arrives this requires the 
[patched Poetry](https://github.com/asodeur/poetry/tree/develop_rwest) available via the link. 
This includes [PR 882](https://github.com/sdispater/poetry/pull/882),
[PR 740](https://github.com/sdispater/poetry/pull/740), and 
[adds](https://github.com/asodeur/poetry/blob/develop_rwest/poetry/console/config/application_config.py#L36)
an [event handler](https://github.com/asodeur/devpi-poetry/blob/master/devpi_poetry/use_current_devpi_index.py#L14) 
to process the configuration before each command. The event handler will replace the url
of any repository encountered in `pyproject.toml` or `poetry.lock` with the current `devpi`
index url.

> **WARNING:** currently Poetry will always use the currently active index. Calling Poetry 
> indirectly via `devpi` with an `--index` option (like in 
> `devpi test --index=<other> <my_poetry_package>`) will ignore the provided index and
> use the current index instead.



Populating Pull Requests from `poetry.lock`
-------------------------------------------
This is achieved with a devpi-client plugin. The plugin reads the `poetry.lock` file and locates
the packages on the current index. Unless `--include-local-bases` is given packages inherited from
local bases will not be pushed.   
```  
usage: devpi poetry-push [-h] [--debug] [-y] [-v] [--clientdir DIR]
                         [--pypirc path] [--no-dev] [--include-local-bases]
                         TARGETSPEC

push all packages from poetry lock-file to an internal or external index. You
can push a release with all its release files either to an external pypi
server ("pypi:REPONAME") where REPONAME needs to be defined in your
``.pypirc`` file. Or you can push to another devpi index ("user/name").

positional arguments:
  TARGETSPEC            local or remote target index. local targets are of
                        form 'USER/NAME', specifying an existing writeable
                        local index. remote targets are of form 'REPO:' where
                        REPO must be an existing entry in the pypirc file.

optional arguments:
  -h, --help            show this help message and exit
  --pypirc path         path to pypirc
  --no-dev              do not push dev dependencies
  --include-local-bases
                        push dependencies from non-mirror base indices as well

generic options:
  --debug               show debug messages including more info on server
                        requests
  -y                    assume 'yes' on confirmation questions
  -v, --verbose         increase verbosity
  --clientdir DIR       directory for storing login and other state
```


