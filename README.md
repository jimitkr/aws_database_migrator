# AWS Database Migrator (in development)
Migrate on-premise databases to AWS RDS instances of the sme engine via a full load. 

How to use:
1) Edit setup/config.properties to reflect your AWS infrastructure
2) Run MainEntry.py

Ensure you have established a "cut-off" period for your source database. This project will take an existing database and do a full load into an RDS instance. Native methods used where recommended.

Currently supports MySQL.

Migration methods:
1) MySQL - mysqldump
2) ... More to come ... 
