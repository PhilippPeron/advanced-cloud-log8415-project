#!/bin/sh

sudo apt-get -qq update
cd /home/ubuntu

wget https://dev.mysql.com/get/Downloads/MySQL-Cluster-8.0/mysql-cluster-community-data-node_8.0.31-1ubuntu20.04_amd64.deb
sudo apt install libclass-methodmaker-perl
dpkg -i mysql-cluster-community-data-node_8.0.31-1ubuntu20.04_amd64.deb

echo "Enter MASTER_HOSTNAME  (internal/private DNS):"
read MASTER_HOSTNAME
export MASTER_HOSTNAME

sudo touch /etc/my.cnf
sudo chmod 777 /etc/my.cnf
sudo cat <<EOF >/etc/my.cnf
[mysql_cluster]
# Options for NDB Cluster processes:
ndb-connectstring=$MASTER_HOSTNAME  # location of cluster manager
EOF

sudo mkdir -p /usr/local/mysql/data
ndbd
sudo pkill -f ndbd

sudo touch /etc/systemd/system/ndbd.service
sudo chmod 777 /etc/systemd/system/ndbd.service
sudo cat <<EOF >/etc/systemd/system/ndbd.service
[Unit]
Description=MySQL NDB Data Node Daemon
After=network.target auditd.service

[Service]
Type=forking
ExecStart=/usr/sbin/ndbd
ExecReload=/bin/kill -HUP $MAINPID
KillMode=process
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl start ndbd
sudo systemctl enable ndbd
sleep 2
sudo systemctl status ndbd