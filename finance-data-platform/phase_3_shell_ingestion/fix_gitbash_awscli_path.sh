#!/bin/bash
# Fix AWS CLI PATH for Git Bash on Windows
# Usage: source fix_gitbash_awscli_path.sh

# Try common install locations
if [ -d "/c/Program Files/Amazon/AWSCLIV2" ]; then
  export PATH="$PATH:/c/Program Files/Amazon/AWSCLIV2"
elif [ -d "/c/Program Files (x86)/Amazon/AWSCLIV2" ]; then
  export PATH="$PATH:/c/Program Files (x86)/Amazon/AWSCLIV2"
elif [ -d "/c/Users/$USERNAME/AppData/Local/Programs/Python/Python39/Scripts" ]; then
  export PATH="$PATH:/c/Users/$USERNAME/AppData/Local/Programs/Python/Python39/Scripts"
fi

echo "PATH updated. aws --version output:"
aws --version
