# Settings
source_url=${args[source]}
publisher=${args[publisher]}
# Flags
no_call=${args[--no-call]}
dry_run=${args[--dry-run]}

function do_call() {
    if [[ $dry_run ]]; then
        echo -e "### DRY RUN: \n$1"
    else
        $1
    fi
}

echo "Installer for InvenTree - source: $publisher/$source_url"

echo "### Installing required packages for download"
do_call "sudo apt-get install wget apt-transport-https -y"

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
