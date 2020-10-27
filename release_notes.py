#!/bin/env python
import argparse
import os
import re
from datetime import datetime
import logging


from github import Github
from github.GithubException import UnknownObjectException
import github.GithubObject

from ghmeta import auth


def get_release_notes(repo_name, milestone_name):
    """
    Extracts release notes from Github issues and outputs a Markdown file with
    extracted information.

        Parameters:
            repo_name (str): Name of the repo from which to pull milestones/issues
            milestone_name (str): Name of the milestone from which to pull issues
    """
    logger = logging.getLogger(__name__)

    logger.info(
        f'Creating release notes for repository "{repo_name}" and milestone "{milestone_name}"'
    )
    ghobj = auth()

    repo = ghobj.get_repo(repo_name)
    # Target milestone defaults to 'next release'
    target_milestone = get_target_milestone_instance(repo, milestone_name)

    notes = []
    for issue in repo.get_issues(milestone=target_milestone):
        meta = {}
        meta["number"] = int(issue.number)
        meta["title"] = issue.title
        meta["url"] = issue.url.replace("api.", "").replace("repos/", "")
        meta["body"] = extract_release_notes(issue) or "NO RELEASE NOTES"
        meta["bug"] = is_bug(issue)
        notes.append(meta)

    logger.info(f"{len(notes)} issue(s) found.")
    create_md_file(notes)


def get_target_milestone_instance(repo, milestone_name):
    """
    Finds the milestone object that matches the given milestone name

        Parameters:
            repo (Github.Repository): Instance of a repository class from Github client
            milestone_name (str): Name of the milestone

        Returns:
            milestone (Github.Milestone): Instance of the milestone class from Github client
    """

    for milestone_inst in repo.get_milestones():
        if milestone_inst.title.lower() == milestone_name.lower():
            target_milestone = milestone_inst
            return target_milestone

    # if we do not find the designated milestone
    raise ValueError(
        f'No milestone found with the name "{milestone_name}" in repository "{repo.full_name}"'
    )


def create_md_file(notes):
    """
    Creates the Markdown file given the extract release notes text and meta information.

        Parameters:
            notes (List[Dict]): List of dictionaries, each dictionary containing the 
                                release note information from a single Github issue.

    """

    logger = logging.getLogger(__name__)

    notes.sort(key=lambda x: (x["bug"], x["number"]))
    file_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "release_notes"
    )
    date_str = datetime.strftime(datetime.now(), "%Y%m%d")
    filename = os.path.join(file_dir, f"release_notes_{date_str}.md")
    with open(
        filename, "w", encoding="utf-8", errors="xmlcharrefreplace"
    ) as output_file:
        logger.info(f"Writing release notes to file {filename}")
        output_file.write(headers())
        for row in notes:
            output_file.write(format_row(row))


def format_row(row):
    """
    Formats a dictionary into a single row of the Markdown table.
        Parameters:
            row (Dict): a dictionary representing a single release note
        Returns:
            row (str): a formatted string for writing to the MD file
    """
    row["title"] = md_escape(row["title"])
    row["body"] = md_escape(row["body"])
    title = "[#{number} {title}]({url})".format(**row)
    return f'| {title} | {row["body"] } |\n'


def md_escape(string):
    """Escape a string for inclusion in a Markdown file."""
    for k, v in escape_table().items():
        string = string.replace(k, v)
    return string


def escape_table():
    return {
        "*": "\*",
        "_": "\_",
        "{": "\{",
        "}": "\}",
        "[": "\[",
        "]": "\]",
        "(": "\(",
        ")": "\)",
        "#": "\#",
        "+": "\+",
        "-": "\-",
        ".": "\.",
        "!": "\!",
        "|": "\|",
    }


def headers():
    return (
        """| **GitHub Issue** | **Summary** |\n"""
        """| ----------------- | ----------- |\n"""
    )


def is_bug(issue):
    """Returns true if an issue include the "bug" label """
    labels = issue.get_labels()
    bug = False
    for l in labels:
        if l.name.lower() == "bug":
            bug = True
            break

    return bug


def extract_release_notes(issue):
    """ Finds the last comment with 'release notes' information in a Github issue chain"""
    comments = issue.get_comments()

    release_notes = None
    for comment in comments:
        body = comment.body.lower()
        if body.find("**release note") > -1:
            release_notes = format_body(body)

    return release_notes


def format_body(text):
    """ Formats the text of a given 'release notes' comment """
    text = re.sub(r"\*\*release note[s]?\*\*", "", text)
    text = " ".join(text.split())
    return text.capitalize()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract release notes from Github issues and format into a Markdown table."
    )
    parser.add_argument(
        "--repository", "-r", type=str, help="Repository to scan", required=True
    )
    parser.add_argument(
        "--milestone", "-m", type=str, help="Name of milestone", default="next release"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    get_release_notes(args.repository, args.milestone)
