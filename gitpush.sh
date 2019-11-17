#!/bin/bash

cd ngtv-v1
if [ -n "$(git status --porcelain)" ]; then
    echo -e \\033[32mChanges detected, configuring git\\033[0m
    git config user.name 'Turner Schedule API'
    git config user.email 'turner.info@turner.com'
    git config push.default simple
    echo -e \\033[32mGit configuration completed. Committing changes now\\033[0m
    git add -A
    git commit -m 'Database update'
    echo -e \\033[32mChanges committed, pushing\\033[0m
    git push
fi
