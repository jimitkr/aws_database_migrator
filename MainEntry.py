from DBReplicator import DBReplicator


def main():
    dbr = DBReplicator()

    # create vpc security group for replication instance and get the security group id
    dbr.config_properties.replinst_vpc_security_group_id = dbr.create_dms_security_group_if_not_exists(dbr.config_properties.replinst_vpc_security_group_name, dbr.config_properties.vpc_id)

    # create dms subnet group
    dbr.create_dms_subnet_group_if_not_exists(dbr.config_properties.replinst_subnet_group_name, dbr.config_properties.replinst_subnet_group_member_subnets)

    # create subnet group for target rds instance
    dbr.create_rds_subnet_group_if_not_exists(dbr.config_properties.tgt_db_subnet_group_name, dbr.config_properties.tgt_db_subnet_group_member_subnets)

    # create replication instance and get its arn
    dbr.config_properties.replinst_arn = dbr.create_replication_instance(dbr.config_properties.replinst_name, dbr.config_properties.replinst_class, dbr.config_properties.replinst_allocated_storage_in_gb,
                                                                         dbr.config_properties.replinst_vpc_security_group_id,
                                                                         dbr.config_properties.replinst_subnet_group_name)

    # create dms source endpoint and get its arn
    dbr.config_properties.src_dms_endpoint_arn = dbr.create_dms_source_db_endpoint(dbr.config_properties.src_db_dms_endpoint_name, dbr.config_properties.src_db_host, dbr.config_properties.src_db_port, dbr.config_properties.src_db_engine,
                                                                                   dbr.config_properties.src_db_username, dbr.config_properties.src_db_secret, dbr.config_properties.src_db_name)

    # test connection to source database via dms endpoint
    # dbr.test_dms_endpoint_connection_from_replication_instance(dbr.config_properties.replinst_arn, dbr.config_properties.src_dms_endpoint_arn)

    # create target database in RDS
    dbr.create_rds_target_db_instance(dbr.config_properties.tgt_db_instance_identifier, dbr.config_properties.tgt_db_instance_class, dbr.config_properties.tgt_db_allocated_storage_in_gb, dbr.config_properties.tgt_rds_db_engine,
                                      dbr.config_properties.tgt_rds_db_username, dbr.config_properties.tgt_rds_db_secret, dbr.config_properties.tgt_db_subnet_group_name, dbr.config_properties.tgt_rds_db_port)

    # get target rds database's hostname in order to create its dms endpoint todo add method that gets hostname but wait if the status is creating
    dbr.config_properties.tgt_rds_db_host = (dbr.get_rds_db_instance_details(dbr.config_properties.tgt_db_instance_identifier))['DBInstances'][0]['Endpoint']['Address']

    # create dms target endpoint and get its arn
    dbr.config_properties.tgt_dms_endpoint_arn = dbr.create_dms_target_db_endpoint(dbr.config_properties.tgt_db_dms_endpoint_name, dbr.config_properties.tgt_rds_db_host, dbr.config_properties.tgt_rds_db_port,
                                                                                   dbr.config_properties.tgt_dms_endpoint_engine,
                                                                                   dbr.config_properties.tgt_rds_db_username, dbr.config_properties.tgt_rds_db_secret, dbr.config_properties.tgt_db_name)

    # test connection to target database via dms endpoint todo in sqlserver, target database will need to exist in rds before u can migrate
    #dbr.test_dms_endpoint_connection_from_replication_instance(dbr.config_properties.replinst_arn, dbr.config_properties.tgt_dms_endpoint_arn)

    # create dms replication task and get its arn
    dbr.config_properties.replication_task_arn = dbr.config_properties.replication_task_arn = dbr.create_dms_replication_task(dbr.config_properties.replication_task_identifier, dbr.config_properties.src_dms_endpoint_arn,
                                                                                                                              dbr.config_properties.tgt_dms_endpoint_arn,
                                                                                                                              dbr.config_properties.replinst_arn, dbr.config_properties.db_migration_type,
                                                                                                                              dbr.config_properties.table_mapping_rules,
                                                                                                                              dbr.config_properties.replication_task_settings)

    # start database migration
    dbr.start_database_migration(dbr.config_properties.replication_task_arn)

    # in development
    # dbr.database_migration_status()


if __name__ == '__main__':
    main()
