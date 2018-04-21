ITWS-2 Project

#Required Tools: 

Python 3.4+ and all packages in requirements.txt, a simple pip install should suffice for those. Use a virtualenvironment to not fuck up.

#Setup:

1. clone
2. run the following commands:

export FLASK_APP='iclone.py'

flask db init

flask db migrate

flask db upgrade

3. In order to run it in Debug mode (suggested for development), do export FLASK_DEBUG=1

#Running:
flask run should do. 
After any changes to the models, run flask db migrate and flask db upgrade again


(borrowed from https://musescore.org/en/handbook/developers-handbook/finding-your-way-around/git-workflow . Please check that page out too)

#Collaborative work:

FOR ANY modifications whatsoever, use branches

#Keeping your repo up to date with the main repo:
In order to get the latest updates from the main repository, do a one-time setup to establish it as a remote by entering:

$ git remote add upstream git://github.com/musescore/MuseScore.git

The main repo will be now known as upstream. Your fork is known as origin. The origin remote is automatically created after cloning your GitHub fork to your computer. To verify that you have two remotes, you can type:

$ git remote

Rebase your branch on the latest upstream

To keep your development branch up to date, rebase your changes on top of the current state of the upstream master.

\# get the changes from upstream
$ git fetch upstream
\# switch to your local master branch
$ git checkout master
$ git rebase upstream/master
\# switch to your topical branch
$ git checkout 78359-slurlayout
\# make sure all is committed as necessary in branch before rebasing
$ git rebase master

Rebase will put all your commits in the branch on hold, get the last changes, and apply your commits on top of it. You might need to resolve conflicts if you changed a file that has been changed in the main repo. To do so, edit the files, then:

$ git add [filename]
$ git rebase --continue 

Another (and shorter) way to update your development branch is $ git pull --rebase upstream master. Should you have changes that are not yet commited to your branch, use $ git stash before the rebase and $ git stash pop after.
Make a pull request to send your changes to MuseScore

When you are ready to send your modified code to MuseScore, push your branch in your origin remote.

$ git push origin 78359-slurlayout

Then do a pull request to MuseScore on GitHub. Go to your GitHub page, select the branch on the left, and press the Pull Request button at the top. Choose your branch, add a comment and submit your pull request. If you are fixing an issue from the tracker, set the issue's status to "patch (code needs review)" with a link to your pull request on GitHub. One of the developers with push rights on the main repo will merge your request ASAP. Important: If you haven't signed the MuseScore CLA yet, do this first as it's a requirement for your pull request to be accepted. After having made a Pull Request don't pull/merge anymore, it'll mess up the commit history. If you (have to) rebase, use 'push --force' ($ git push --force) to send it up to your GitHub repository, this will update the PR too. Be careful not to do this while the core team is working on merging in your PR. 

