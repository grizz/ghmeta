#!/bin/env python
import argparse
import os
import re
from datetime import datetime

from github import Github
from github.GithubException import UnknownObjectException
import github.GithubObject

from ghmeta import auth


def get_release_notes(repo, milestone):
    ghobj = auth()

    for milestone in ghobj.get_repo(repo).get_milestones():
        if milestone.title.lower() == "next release":
            next_release = milestone

    notes = []
    for issue in ghobj.get_repo(repo).get_issues(milestone=next_release):
        meta = {}
        meta["number"] = int(issue.number)
        meta["title"] = issue.title
        meta["url"] = issue.url.replace("api.", "").replace("repos/", "")
        meta["body"] = extract_release_notes(issue) or "NO RELEASE NOTES"
        meta["bug"] = is_bug(issue)
        notes.append(meta)

    create_md_file(notes)


def create_md_file(notes):
    notes.sort(key=lambda x: (x["bug"], x["number"]))
    file_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "release_notes"
    )
    date_str = datetime.strftime(datetime.now(), "%Y%m%d")
    filename = os.path.join(file_dir, f"release_notes_{date_str}.md")
    with open(
        filename, "w", encoding="utf-8", errors="xmlcharrefreplace"
    ) as output_file:
        output_file.write(headers())
        for row in notes:
            output_file.write(format_row(row))


def format_row(row):
    row["title"] = md_escape(row["title"])
    print(row["title"])
    row["body"] = md_escape(row["body"])
    title = "[#{number} {title}]({url})".format(**row)
    return f'| {title} | {row["body"] } |\n'


def md_escape(string):
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
    labels = issue.get_labels()
    bug = False
    for l in labels:
        if l.name.lower() == "bug":
            bug = True
            break

    return bug


def extract_release_notes(issue):
    comments = issue.get_comments()

    release_notes = None
    for comment in comments:
        body = comment.body.lower()
        if body.find("**release note") > -1:
            release_notes = format_body(body)

    return release_notes


def format_body(text):
    text = re.sub(r"\*\*release note[s]?\*\*", "", text)
    text = " ".join(text.split())
    return text.capitalize()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract release notes from Github issues and format into a Markdown table."
    )
    parser.add_argument("--repository", "-r", type=str, help="Repository to scan")
    parser.add_argument(
        "--milestone", "-m", type=str, help="Name of milestone", default="Next Release"
    )
    args = parser.parse_args()

    get_release_notes(args.repository, args.milestone)
