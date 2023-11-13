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

# Check if os and version is supported
get_distribution
echo "### Detected distribution: $OS $VER"
SUPPORTED=true          # is this OS supported?
NEEDS_LIBSSL1_1=false   # does this OS need libssl1.1?

DIST_OS=${OS,,}
DIST_VER=$VER

case "$OS" in
    Ubuntu)
        if [[ $VER == "22.04" ]]; then
            SUPPORTED=true
            NEEDS_LIBSSL1_1=true
            DIST_VER="20.04"
        elif [[ $VER == "20.04" ]]; then
            SUPPORTED=true
        else
            SUPPORTED=false
        fi
        ;;
    "Debian GNU/Linux" | "debian gnu/linux" | Raspbian)
        if [[ $VER == "12" ]]; then
            SUPPORTED=true
        elif [[ $VER == "11" ]]; then
            SUPPORTED=true
        elif [[ $VER == "10" ]]; then
            SUPPORTED=true
        else
            SUPPORTED=false
        fi
        DIST_OS=debian
        ;;
    *)
        echo "### Distribution not supported"
        SUPPORTED=false
        ;;
esac

if [[ $SUPPORTED != "true" ]]; then
    echo "This OS is currently not supported."
    echo "Please install manually using https://docs.inventree.org/en/stable/start/install/"
    echo "or check https://github.com/inventree/InvenTree/issues/3836 for packaging for your OS."
    echo "If you think this is a bug please file an issue at"
    echo "https://github.com/inventree/InvenTree/issues/new?template=install.yaml"

    exit 1
fi

echo "### Installing required packages for download"
for pkg in $REQS; do
    if dpkg-query -W -f'${Status}' "$pkg" 2>/dev/null | grep -q "ok installed"; then
        true
    else
        do_call "sudo apt-get -yqq install $pkg"
    fi
done

if [[ $NEEDS_LIBSSL1_1 == "true" ]]; then
    echo "### Pathching for libssl1.1"

    echo "deb http://security.ubuntu.com/ubuntu focal-security main" | sudo tee /etc/apt/sources.list.d/focal-security.list
    do_call "sudo apt-get update"
    do_call "sudo apt-get install libssl1.1"
    sudo rm /etc/apt/sources.list.d/focal-security.list
fi

echo "### Getting and adding key"
curl -fsSL https://dl.packager.io/srv/$publisher/InvenTree/key | gpg --dearmor | tee /etc/apt/trusted.gpg.d/pkgr-inventree.gpg> /dev/null
echo "### Adding package source"
SOURCE_URL="deb [signed-by=/etc/apt/trusted.gpg.d/pkgr-inventree.gpg] https://dl.packager.io/srv/deb/$publisher/InvenTree/$source_url/$DIST_OS $DIST_VER main"
echo "$SOURCE_URL" | tee /etc/apt/sources.list.d/inventree.list > /dev/null
echo "### Updating package lists"
do_call "sudo apt-get update"

# Set up environment for install
echo "### Setting installer args"
if [[ $no_call ]]; then
    do_call "export NO_CALL=true"
fi

echo "### Installing InvenTree"
do_call "sudo apt-get install inventree -y"

echo "### Install done!"
