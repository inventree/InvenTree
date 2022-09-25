get_distribution() {
    lsb_dist=""
    # Every system that we officially support has /etc/os-release
    if [ -r /etc/os-release ]; then
        lsb_dist="$(. /etc/os-release && echo "$ID")"
    fi
    # Returning an empty string here should be alright since the
    # case statements don't act unless you provide an actual value
    echo "$lsb_dist"
}

get_distribution
case "$lsb_dist" in
ubuntu)
    if command_exists lsb_release; then
        dist_version="$(lsb_release -r | cut -f2)"
    fi
    if [ -z "$dist_version" ] && [ -r /etc/lsb-release ]; then
        dist_version="$(. /etc/lsb-release && echo "$DISTRIB_RELEASE")"
    fi
    ;;
debian | raspbian)
    dist_version="$(sed 's/\/.*//' /etc/debian_version | sed 's/\..*//')"
    lsb_dist="debian"
    ;;
centos | rhel | sles)
    if [ -z "$dist_version" ] && [ -r /etc/os-release ]; then
        dist_version="$(. /etc/os-release && echo "$VERSION_ID")"
    fi
    ;;
*)
    if command_exists lsb_release; then
        dist_version="$(lsb_release --release | cut -f2)"
    fi
    if [ -z "$dist_version" ] && [ -r /etc/os-release ]; then
        dist_version="$(. /etc/os-release && echo "$VERSION_ID")"
    fi
    ;;
esac
echo "### ${lsb_dist} ${dist_version} detected"

# Make sure the depencies are there
sudo apt-get install wget apt-transport-https -y

echo "### Add key and package source"
# Add key
wget -qO- https://dl.packager.io/srv/matmair/InvenTree/key | sudo apt-key add -
# Add packagelist
sudo wget -O /etc/apt/sources.list.d/inventree.list https://dl.packager.io/srv/matmair/InvenTree/deploy-test/installer/${lsb_dist}/${dist_version}.repo

echo "### Install InvenTree"
# Update repos and install inventree
sudo apt-get update
sudo apt-get install inventree -y
