PKG_ROOT=/home/simonmeggle/Documents/01_dev/rmkv2/robotmk

msg=$1

pushd $PKG_ROOT

git add .. &&
    git commit -m "$msg" &&
    bumpversion patch --tag --commit &&
    # git add . &&
    # git commit -m "Bumped version" &&
    git push && git push --tags

flit publish

popd
