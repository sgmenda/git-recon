"""
Copyright 2021 sanketh <snkth.com>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import time
import git
import logging
import os
import toml

from collections import namedtuple
from jinja2 import Template

logging.basicConfig(
    format="%(asctime)s::%(levelname)s::%(message)s", level=logging.INFO
)

Project = namedtuple("Project", "name, url, branch, commitUrlPrefix")
Commit = namedtuple(
    "Commit", "projectName, triggeredKeyword, url, summary, author, date, message"
)


def processCommit(project, commit, keywords):
    """
    Takes a commit object and a list of keywords and returns (True, [keyword])
    if it finds [keyword] in the commit's patch, and (False, None) otherwise.
    """

    # TODO: Support advanced searching, like project-specific keywords,
    # file-extension-specific keywords, and general constaints on the commit
    # (like minimum number of files touched.)

    # diff against the parent to get the patch
    parent = commit.parents[0] if commit.parents else EMPTY_TREE_SHA
    for diff in commit.diff(parent, create_patch=True):
        diffString = diff.__str__().lower()
        for keyword in keywords:
            # The first condition is to prevent, for instance, OpenSSL
            # commits triggering the OpenSSL keyword.
            if (keyword not in project.name.lower()) and (
                (keyword in diffString) or (keyword in commit.message)
            ):
                return True, keyword

    return False, None


def getRelevantCommitsFromProject(
    dataDir, timeRange, maxCommits, keywords, project: Project
):
    """
    Clones the project to [dataDir]/data/[project name] and looks for
    commits from the last `timeRange` seconds that contain any of the `keywords`.
    """

    # TODO: If it is a GitHub repo, use the GitHub API instead, it is much
    # cheaper and might allow inclusion of huge projects like Firefox and
    # Chromium.

    projectPath = os.path.join(os.getcwd(), "data", project.name)
    try:
        os.mkdir(projectPath)
        repo = git.Repo.clone_from(project.url, projectPath, branch=project.branch)
    except FileExistsError:
        logging.info(
            f"There is an existing clone of {project.name}, using that instead of re-cloning."
        )
        repo = git.Repo(projectPath)
        repo.remotes.origin.fetch()
        repo.git.checkout(project.branch)
        repo.remotes.origin.pull()

    minAge = int(time.time()) - timeRange
    commits = repo.iter_commits(
        max_count=maxCommits,
        since=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(minAge)),
    )

    matchingCommits = []

    for commit in commits:
        res, keyword = processCommit(project, commit, keywords)
        if res == True:
            matchingCommits.append(
                Commit(
                    project.name,
                    keyword,
                    project.commitUrlPrefix + bytes.hex(commit.binsha),
                    commit.summary,
                    commit.author,
                    time.strftime(
                        "%a, %d %b %Y",
                        time.localtime(commit.committed_date),
                    ),
                    commit.message,
                )
            )
    return matchingCommits


def getRelevantCommits(timeRange, maxCommits, keywords, trackingProjects):
    """
    Retrives commits from the last `timeRange` seconds from the `trackingProjects`
    whose patches contain any of the `keywords`.
    """
    matchingCommits = []
    # Create the data directory
    dataDir = os.path.join(os.getcwd(), "data")
    try:
        os.mkdir(dataDir)
    except FileExistsError:
        logging.info(f"There is an existing data directory ({dataDir})")

    for project in trackingProjects:
        logging.info(f"Processing {project}")
        matchingCommits += getRelevantCommitsFromProject(
            dataDir, timeRange, maxCommits, keywords, project
        )
    return matchingCommits


def generateFeed(outFile, matchingCommits):
    # TODO: put template in a html file
    template = """
<html>
<head>
<title>Git Recon</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta1/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-giJF6kkoqNQ00vy+HMDP7azOuL0xtbfIcaT9wjKHr8RbDVddVHyTfAAsrekwKmP1" crossorigin="anonymous">
</head>
<body>
<div class="container-fluid">
<h1>Git Recon</h1>
<div class="alert alert-info" role="alert">
Found {{lenMatchingCommits}} keyword matches!
</div>
<table class="table table-hover" style="width:100%">
<tr>
<th scope="col">Summary</th>
<th scope="col">Project</th>
<th scope="col">Triggered Keyword</th>
<th scope="col">Author</th>
<th scope="col">Date</th>
</tr>
{% for commit in matchingCommits %}
    <tr>
    <td><a href="{{commit.url}}">{{commit.summary}}</a></td>
    <td>{{commit.projectName}}</td>
    <td>{{commit.triggeredKeyword}}</td>
    <td>{{commit.author}}</td>
    <td>{{commit.date}}</td>
    </tr>
{% endfor %}
</table>
</div>
<footer>
<div class="container">
<span class="text-muted">
<strong>Last Updated:</strong> {{lastUpdated}};
Generated using <a href="https://github.com/sgmenda/git-recon">sgmenda/git-recon</a>
</span>
</div>
</footer>
</body>
</html>
    """

    t = Template(template)
    with open(outFile, "w") as f:
        f.write(
            t.render(
                matchingCommits=matchingCommits,
                lenMatchingCommits=len(matchingCommits),
                lastUpdated=time.strftime(
                    "%a, %d %b %Y, %H:%M:%S +0000",
                    time.gmtime(),
                ),
            )
        )


if __name__ == "__main__":

    # Load options from the config file
    config = toml.load(os.path.join(os.getcwd(), "config.toml"))
    timeRange = config["timeRange"]
    maxCommits = config["maxCommits"]
    keywords = [k.lower() for k in config["keywords"]]
    trackingProjects = [
        Project(
            p,
            config["projects"][p]["url"],
            config["projects"][p]["branch"],
            config["projects"][p]["commitUrlPrefix"],
        )
        for p in config["projects"]
    ]

    # Get relevant commits
    matchingCommits = getRelevantCommits(
        timeRange, maxCommits, keywords, trackingProjects
    )

    # Write relevant commits to a html file
    outFile = os.path.join(os.getcwd(), "docs", "index.html")
    generateFeed(outFile, matchingCommits)
