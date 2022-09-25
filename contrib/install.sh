# Make sure the depencies are there
sudo apt-get install wget apt-transport-https -y

# Add key
wget -qO- https://dl.packager.io/srv/matmair/InvenTree/key | sudo apt-key add -

# Add packagelist
sudo wget -O /etc/apt/sources.list.d/inventree.list https://dl.packager.io/srv/matmair/InvenTree/deploy-test/installer/ubuntu/20.04.repo

# Update repos and install inventree
sudo apt-get update
sudo apt-get install inventree -y
