#!/bin/bash

echo Cloning repository
git clone https://${GH_TOKEN}@github.com/$TRAVIS_REPO_SLUG -b ngtv-v1 ngtv-v1
echo -e \\033[32mRepository cloned successfully\\033[0m
