from DBReplicator import DBReplicator
from MySQLMigration import MySQLMigration


def main():
    dbr = DBReplicator()

    # mysql
    if dbr.config_properties.src_db_engine == 'mysql':
        mysql = MySQLMigration()
        # create subnet group for target rds instance
        dbr.create_rds_subnet_group_if_not_exists(dbr.config_properties.tgt_db_subnet_group_name, dbr.config_properties.tgt_db_subnet_group_member_subnets)
        # create target database in RDS if doesn't exist
        dbr.create_rds_target_db_instance(dbr.config_properties.tgt_db_instance_identifier, dbr.config_properties.tgt_db_instance_class, dbr.config_properties.tgt_db_allocated_storage_in_gb, dbr.config_properties.tgt_rds_db_engine,
                                          dbr.config_properties.tgt_rds_db_username, dbr.config_properties.tgt_rds_db_secret, dbr.config_properties.tgt_db_subnet_group_name, dbr.config_properties.tgt_rds_db_port)
        # wait until target database becomes available
        dbr.wait_until_target_db_available(dbr.config_properties.tgt_db_instance_identifier)
        # get target rds database's hostname in order to create its dms endpoint
        dbr.config_properties.tgt_rds_db_host = (dbr.get_rds_db_instance_details(dbr.config_properties.tgt_db_instance_identifier))['DBInstances'][0]['Endpoint']['Address']
        # kickoff migration
        mysql.execute_mysql_migration(dbr.config_properties.src_db_home, dbr.config_properties.src_db_host, dbr.config_properties.src_db_username, dbr.config_properties.src_db_name, dbr.config_properties.src_db_secret,
                                      dbr.config_properties.tgt_rds_db_username,
                                      dbr.config_properties.tgt_rds_db_port,
                                      dbr.config_properties.tgt_rds_db_host, dbr.config_properties.tgt_rds_db_secret)


if __name__ == '__main__':
    main()
