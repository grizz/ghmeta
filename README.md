
## ghmeta.py

A quick script to sync labels and milestones between GitHub repos.

### Set up

#### Requirements

- python 3.6+
-  environment variable `GHMETA_TOKEN` to be set to a GitHub personal access token (<https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token>) with access to the repos you wish to operate on.

```sh
export GHMETA_TOKEN=$TOKEN
pipenv install
pipenv run ./ghmeta.py
```

### Usage

```
Usage: ghmeta.py [OPTIONS] [COMMAND]

Options:
  --pull-from TEXT  Read metadata from here, default is none meaning local
                    file (`data.yml`).

  --push-to TEXT    Push metadata to these repos (may be a comma separated
                    list

  --help            Show this message and exit.
```

`$REPO_URL` is a GitHub user/pass combination, so for example `grizz/ghmeta`

Default command is display, which will show from the yaml file `data.yml` by default. The other command is `push` which will take from the data source and push to one or more GitHub repos.

To create a new data file, you can run `ghmeta.py --pull-from=$REPO_URL > data.yml`

To push the source to destination repos, you'll need to supply a list of `$REPO_URL`s to push to using either the command line `--push-to=user/repo0,user/repo2` or the data file as:

```yml
ghmeta:
  push_to:
  - user/repo0
  - user/repo1
```

The data file will be made correctly when combining the two commands as such:

```sh
ghmeta.py --pull-from=$REPO_URL --push-to=$REPO_URL > data.yml
```

Or directly sync between two with:

```sh
ghmeta.py --pull-from=$REPO_URL --push-to=$REPO_URL push`
```

## TODO:

- add `--delete` flag
- add `--exclude` flag
- add `--overwrite` flag

