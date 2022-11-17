#!/bin/sh

sudo apt-get update
cd /home/ubuntu

wget https://dev.mysql.com/get/Downloads/MySQL-Cluster-8.0/mysql-cluster-community-management-server_8.0.31-1ubuntu20.04_amd64.deb
sudo dpkg -i mysql-cluster-community-management-server_8.0.31-1ubuntu20.04_amd64.deb

# Get IPs from console
echo "Enter MASTER_HOSTNAME:"
read MASTER_HOSTNAME
export MASTER_HOSTNAME

echo "Enter SLAVE0_HOSTNAME:"
read SLAVE0_HOSTNAME
export SLAVE0_HOSTNAME

echo "Enter SLAVE1_HOSTNAME:"
read SLAVE1_HOSTNAME
export SLAVE1_HOSTNAME

echo "Enter SLAVE2_HOSTNAME:"
read SLAVE2_HOSTNAME
export SLAVE2_HOSTNAME

# Create and write config for cluster manager
sudo mkdir /var/lib/mysql-cluster
sudo touch /var/lib/mysql-cluster/config.ini
sudo chmod 777 /var/lib/mysql-cluster/config.ini
sudo cat <<EOF >/var/lib/mysql-cluster/config.ini
[ndbd default]
# Options affecting ndbd processes on all data nodes:
NoOfReplicas=3	# Number of replicas

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


