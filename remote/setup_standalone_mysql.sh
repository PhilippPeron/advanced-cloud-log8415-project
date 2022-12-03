#!/bin/sh

sudo apt-get -y update
sudo apt-get -y install mysql-server

# Install Sakila Database
sudo wget http://downloads.mysql.com/docs/sakila-db.zip
sudo apt install unzip
sudo unzip sakila-db.zip -d "/tmp/"
sudo mysql -e "SOURCE /tmp/sakila-db/sakila-schema.sql;"
sudo mysql -e "SOURCE /tmp/sakila-db/sakila-data.sql;"

# Run mysql_secure_installation.sh partially
sudo mysql -e "UPDATE mysql.user SET Password=PASSWORD('root') WHERE User='root';"
sudo mysql -e "DELETE FROM mysql.user WHERE User='';"
sudo mysql -e "DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');"
sudo mysql -e "DROP DATABASE IF EXISTS test;"
sudo mysql -e "FLUSH PRIVILEGES;"
# Add Phlipp as user and grant all privileges
sudo mysql -e "CREATE USER 'philipp'@'localhost' IDENTIFIED BY 'mypassword';"
sudo mysql -e "GRANT ALL PRIVILEGES on sakila.* TO 'philipp'@'localhost';"

# Install sysbench
sudo apt-get -y install sysbench
# Run benchmarks
sudo sysbench --db-driver=mysql --mysql-user=philipp --mysql_password=mypassword --mysql-db=sakila --tables=8 --table-size=1000 /usr/share/sysbench/oltp_read_write.lua prepare
sudo sysbench --db-driver=mysql --mysql-user=philipp --mysql_password=mypassword --mysql-db=sakila --tables=8 --table-size=1000 --num-threads=6 --max-time=120 /usr/share/sysbench/oltp_read_write.lua run > ./results_standalone.txt