#!/bin/bash

# Utility to run a command on every branch matching a pattern.

set -e

if [[ $# -eq 0 ]]; then
    echo "$0 <branch-pattern> <command>"
    echo "branch pattern not given"
    echo "Example: $0 \"bench/foo\" git cherry-pick abcd1234"
    echo "Example: $0 \"bench/foo\" git checkout -b 'bench/\$comparison-bar/\$case'"
    echo "Variables available to command:"
    echo "- \$branch: current full branch name"
    echo "- \$bench: first element of branch (typically literal 'bench')"
    echo "- \$comparison: second element of branch"
    echo "- \$case: third element of branch"
    echo "- \$parts: array of elements of branch"
    exit 1
fi

BRANCH_PATTERN="$1"
shift
CMD=( "$@" )

branches=( $(git branch | grep "$BRANCH_PATTERN") )
echo "Applying command to:"
printf '%s\n' "${branches[@]}"


ORIG_BRANCH=$(git rev-parse --abbrev-ref HEAD)

for branch in "${branches[@]}"
do
    echo ""
    # Store useful variables for commands to substitute
    parts=( ${branch//\// } )
    bench="${parts[0]}"
    comparison="${parts[1]}"
    case="${parts[2]}"

    git checkout "$branch"
    eval "${CMD[*]}" || exit
    # eval "$@" || exit
done

git checkout "$ORIG_BRANCH"
