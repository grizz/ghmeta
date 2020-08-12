#!/bin/env python

import os
import getpass

import click
from github import Github
from github.GithubException import UnknownObjectException
import github.GithubObject
import yaml


def auth():
    token = os.environ.get("GHMETA_TOKEN", None)
    if not token:
        raise Exception(
            "requires environment variable GHMETA_TOKEN to be set to a github personal access token"
        )

    return Github(token)


def load_local(filename="data.yml"):
    """ Loads local metadata from file. """
    with open(filename) as f:
        docs = list(yaml.load_all(f, Loader=yaml.FullLoader))
        if len(docs) != 1:
            raise Exception("only supports single document yaml files")
        return docs[0]


def load_github(repo):
    data = dict(ghmeta={"push_to": []}, labels=[], milestones=[])

    for each in repo.get_labels():
        data["labels"].append(
            dict(name=each.name, color=each.color, description=each.description)
        )

    for each in repo.get_milestones(state="open"):
        data["milestones"].append(dict(title=each.title, description=each.description))

    return data


def push_data(repo, data):
    """ Pushes data to github repos. """

    overwrite = True

    # milestaones need to be referenced by id, so we need to get the full list first
    existing_milestones = {}
    for each in repo.get_milestones():
        existing_milestones[each.title] = each

    for milestone in data["milestones"]:
        title = milestone["title"]
        # TODO add state
        if overwrite and title in existing_milestones:
            print(f"updating milestone `{title}` to `{milestone['description']}`")
            existing_milestones[title].edit(title, "open", milestone["description"])
        else:
            repo.create_milestone(title, "open", milestone["description"])

    for label in data["labels"]:
        name = label["name"]
        # github fails on None, so make sure it's at least an empty string
        description = label.get("description", "") or ""

        try:
            existing_label = repo.get_label(label["name"])
            if overwrite:
                print(f"updating label `{name}` to #{label['color']} `{description}`")
                existing_label.edit(name, label["color"], description)

            continue

        except UnknownObjectException:
            pass
        repo.create_label(name, label["color"], description)


@click.command()
@click.option(
    "--pull-from",
    help="Read metadata from here, default is none meaning local file (`data.yml`).",
)
@click.option(
    "--push-to", help="Push metadata to these repos (may be a comma separated list"
)
@click.argument("command", default="display")
def ghmeta(command, pull_from, push_to):
    ghobj = auth()

    if pull_from:
        data = load_github(ghobj.get_repo(pull_from))
    else:
        data = load_local()

    # if push_to is passed, overwrite file data
    if push_to:
        data["ghmeta"]["push_to"] = push_to.split(",")

    if command == "display":
        print(yaml.dump(data))
    elif command == "push":
        push_to = data["ghmeta"]["push_to"]
        if not push_to:
            raise Exception("nothing to push to, set push_to in data or command line")
        for repo_url in push_to:
            print(f"syncing {repo_url}")
            push_data(ghobj.get_repo(repo_url), data)
    else:
        raise Exception(f"unknown command {command}")


if __name__ == "__main__":
    ghmeta()
