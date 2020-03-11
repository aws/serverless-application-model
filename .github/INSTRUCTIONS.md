# WARNING !!!!
The contents of this directory are included here by adding the repo https://github.com/Flux7Labs/central-repo-dot-github as
a subtree. If you need to make any changes to the contents of this directory, you should understand subtrees and make
an educated decision based on what you want to do and the impact to other users of this repo and how you will
handle conflicts in an update

# central-repo-dot-github
Central repo to hold the contents of .github directory

To learn more about the .github directory go here:
https://help.github.com/en/articles/creating-a-pull-request-template-for-your-repository

# Setup
To add the contents of this directory to your repo use the command:
```
git subtree add --prefix .github git@github.com:Flux7Labs/central-repo-dot-github.git master --squash
```
# Updates
For subsequent updates from the main repository use the command: 
```
git subtree pull --prefix .github git@github.com:Flux7Labs/central-repo-dot-github.git master --squash
```
