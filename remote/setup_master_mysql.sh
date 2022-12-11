#!/bin/sh

sudo apt-get update
sudo apt-get -y upgrade
cd /home/ubuntu

# Download MySQL server
wget wget https://downloads.mysql.com/archives/get/p/14/file/mysql-cluster-community-management-server_7.6.23-1ubuntu18.04_amd64.deb
sudo dpkg mysql-cluster-community-management-server_7.6.23-1ubuntu18.04_amd64.deb

wget https://downloads.mysql.com/archives/get/p/14/file/mysql-cluster_7.6.23-1ubuntu18.04_amd64.deb-bundle.tar
sudo tar -xvf mysql-cluster_7.6.23-1ubuntu18.04_amd64.deb-bundle.tar

# Install Sakila Database
sudo wget http://downloads.mysql.com/docs/sakila-db.zip
sudo apt -y --fix-broken install
sudo apt install unzip
sudo unzip sakila-db.zip -d "/tmp/"

# Install benchmarking tool
sudo apt-get -y install sysbench

# Get IPs from user through console input
echo "Enter MASTER_HOSTNAME (internal/private DNS):"
read MASTER_HOSTNAME
export MASTER_HOSTNAME

echo "Enter SLAVE0_HOSTNAME (internal/private DNS):"
read SLAVE0_HOSTNAME
export SLAVE0_HOSTNAME

echo "Enter SLAVE1_HOSTNAME  (internal/private DNS):"
read SLAVE1_HOSTNAME
export SLAVE1_HOSTNAME

echo "Enter SLAVE2_HOSTNAME  (internal/private DNS):"
read SLAVE2_HOSTNAME
export SLAVE2_HOSTNAME

# Create and write config for cluster manager
sudo mkdir /var/lib/mysql-cluster
sudo touch /var/lib/mysql-cluster/config.ini
sudo chmod 777 /var/lib/mysql-cluster/config.ini
sudo cat <<EOF >/var/lib/mysql-cluster/config.ini
[ndbd default]
# Options affecting ndbd processes on all data nodes:
NoOfReplicas=1	# Number of replicas

[ndb_mgmd]
# Management process options:
hostname=$MASTER_HOSTNAME # Hostname of the manager
datadir=/var/lib/mysql-cluster 	# Directory for the log files

[ndbd]
hostname=$SLAVE0_HOSTNAME # Hostname/IP of the first data node
NodeId=2			# Node ID for this data node
datadir=/usr/local/mysql/data	# Remote directory for the data files

[ndbd]
hostname=$SLAVE1_HOSTNAME # Hostname/IP of the second data node
NodeId=3			# Node ID for this data node
datadir=/usr/local/mysql/data	# Remote directory for the data files

[ndbd]
hostname=$SLAVE2_HOSTNAME # Hostname/IP of the third data node
NodeId=4			# Node ID for this data node
datadir=/usr/local/mysql/data	# Remote directory for the data files

[mysqld]
# SQL node options:
hostname=$MASTER_HOSTNAME # In our case the MySQL server/client is on the same Droplet as the cluster manager
EOF

sudo mkdir /usr/mysql-cluster
sudo ndb_mgmd -f /var/lib/mysql-cluster/config.ini

pkill -f ndb_mgmd

sudo touch /etc/systemd/system/ndb_mgmd.service
sudo chmod 777 /etc/systemd/system/ndb_mgmd.service
sudo cat <<EOF >/etc/systemd/system/ndb_mgmd.service
[Unit]
Description=MySQL NDB Cluster Management Server
After=network.target auditd.service

[Service]
Type=forking
ExecStart=/usr/sbin/ndb_mgmd -f /var/lib/mysql-cluster/config.ini
ExecReload=/bin/kill -HUP $MAINPID
KillMode=process
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ndb_mgmd
sudo systemctl start ndb_mgmd
sleep 2
sudo systemctl status ndb_mgmd
