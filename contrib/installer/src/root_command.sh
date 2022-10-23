# Settings
source_url=${args[source]}
publisher=${args[publisher]}
# Flags
no_call=${args[--no-call]}
dry_run=${args[--dry-run]}

REQS="wget apt-transport-https"

function do_call() {
    if [[ $dry_run ]]; then
        echo -e "### DRY RUN: \n$1"
    else
        $1
    fi
}

function get_distribution {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si)
        VER=$(lsb_release -sr)
    elif [ -f /etc/lsb-release ]; then
        . /etc/lsb-release
        OS=$DISTRIB_ID
        VER=$DISTRIB_RELEASE
    elif [ -f /etc/debian_version ]; then
        OS=Debian
        VER=$(cat /etc/debian_version)
    elif [ -f /etc/SuSe-release ]; then
        OS=SEL
    elif [ -f /etc/redhat-release ]; then
        OS=RedHat
    else
        OS=$(uname -s)
        VER=$(uname -r)
    fi
}

echo "### Installer for InvenTree - source: $publisher/$source_url"

get_distribution
echo "### Detected distribution: $OS $VER"

echo "### Installing required packages for download"
for pkg in $REQS; do
    if dpkg-query -W -f'${Status}' "$pkg" 2>/dev/null | grep -q "ok installed"; then
        true
    else
        do_call "sudo apt-get -yqq install $pkg"
    fi
done

echo "### Adding key and package source"
# Add key
do_call "wget -qO- https://dl.packager.io/srv/$publisher/InvenTree/key | sudo apt-key add -"
# Add packagelist
do_call "sudo wget -O /etc/apt/sources.list.d/inventree.list https://dl.packager.io/srv/$publisher/InvenTree/$source_url/installer/${lsb_dist}/${dist_version}.repo"

echo "### Updateing package lists"
do_call "sudo apt-get update"

# Set up environment for install
echo "### Setting installer args"
if [[ $no_call ]]; then
    do_call "export NO_CALL=true"
fi

echo "### Installing InvenTree"
do_call "sudo apt-get install inventree -y"

echo "### Install done!"
