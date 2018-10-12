import configparser
import logging

class PropertyLoader:

    def __init__(self):
        self.config_properties_file_path = 'setup/config.properties'
        self.read_config_properties()


    def read_config_properties(self):

        AWS_GENERIC_SECTION = 'AWS_GENERIC'
        REPLICATION_TASK_SECTION = 'REPLICATION_TASK'
        LOGGING_SECTION = 'LOGGING'
        REPLICATION_INSTANCE_SECTION = 'REPLICATION_INSTANCE'
        SOURCE_DB_SECTION = 'SOURCE_DB'
        TARGET_DB_RDS_SECTION = 'TARGET_DB_RDS'

        config = configparser.RawConfigParser()
        config.read(self.config_properties_file_path)
        # AWS_GENERIC
        self.aws_region = config.get(AWS_GENERIC_SECTION, 'aws_region')
        self.vpc_id = config.get(AWS_GENERIC_SECTION, 'aws_vpc_id')
        self.check_status_num_times = int(config.get(AWS_GENERIC_SECTION, 'check_status_num_times'))
        # LOGGING
        self.log_level = config.get(LOGGING_SECTION, 'log_level')
        logging.basicConfig(level=getattr(logging, self.log_level))
        self.logger = logging.getLogger(__name__)
        # REPLICATION_INSTANCE
        self.replinst_name = config.get(REPLICATION_INSTANCE_SECTION, 'replinst_name')
        self.replinst_class = config.get(REPLICATION_INSTANCE_SECTION, 'replinst_class')
        self.replinst_allocated_storage_in_gb = int(config.get(REPLICATION_INSTANCE_SECTION, 'replinst_allocated_storage_in_gb'))
        self.replinst_subnet_group_name = config.get(REPLICATION_INSTANCE_SECTION, 'replinst_subnet_group_name')
        self.replinst_subnet_group_member_subnets = (config.get(REPLICATION_INSTANCE_SECTION, 'replinst_subnet_group_member_subnets')).split(',')
        self.replinst_vpc_security_group_name = config.get(REPLICATION_INSTANCE_SECTION, 'replinst_vpc_security_group_name')
        self.replinst_vpc_security_group_id = None  # populating later
        self.replinst_arn = None    # populating later
        #SOURCE_DB
        self.src_db_engine = config.get(SOURCE_DB_SECTION, 'src_db_engine')
        self.src_db_dms_endpoint_name = config.get(SOURCE_DB_SECTION, 'src_db_dms_endpoint_name')
        self.src_db_username = config.get(SOURCE_DB_SECTION, 'src_db_username')
        self.src_db_secret = config.get(SOURCE_DB_SECTION, 'src_db_secret')
        self.src_db_host = config.get(SOURCE_DB_SECTION, 'src_db_host')
        self.src_db_port = int(config.get(SOURCE_DB_SECTION, 'src_db_port'))
        self.src_dms_endpoint_arn = None  # populating later
        self.src_db_name = config.get(SOURCE_DB_SECTION, 'src_db_name')
        #TARGET_DB
        self.tgt_db_instance_identifier = config.get(TARGET_DB_RDS_SECTION, 'tgt_db_instance_identifier')
        self.tgt_db_dms_endpoint_name = config.get(TARGET_DB_RDS_SECTION, 'tgt_db_dms_endpoint_name')
        self.tgt_db_instance_class = config.get(TARGET_DB_RDS_SECTION, 'tgt_db_instance_class')
        self.tgt_db_allocated_storage_in_gb = int(config.get(TARGET_DB_RDS_SECTION, 'tgt_db_allocated_storage_in_gb'))
        self.tgt_db_subnet_group_name = config.get(TARGET_DB_RDS_SECTION, 'tgt_db_subnet_group_name')
        self.tgt_db_subnet_group_member_subnets = (config.get(TARGET_DB_RDS_SECTION, 'tgt_db_subnet_group_member_subnets')).split(',')
        self.tgt_dms_endpoint_arn = None  # populating later
        self.tgt_rds_db_host = None   # populating later
        self.tgt_rds_db_port = self.src_db_port
        self.tgt_rds_db_engine = config.get(TARGET_DB_RDS_SECTION, 'tgt_rds_db_engine')
        self.tgt_dms_endpoint_engine = self.tgt_rds_db_engine.split('-')[0]   # sqlserver-ex to sqlserver
        self.tgt_rds_db_username = self.src_db_username
        self.tgt_rds_db_secret = 
        self.tgt_db_name = self.src_db_name
        #REPLICATION_TASK
        self.replication_task_identifier = config.get(REPLICATION_TASK_SECTION, 'replication_task_identifier')
        self.db_migration_type = config.get(REPLICATION_TASK_SECTION, 'db_migration_type')
        self.table_mapping_rules = config.get(REPLICATION_TASK_SECTION, 'table_mapping_rules')
        self.replication_task_arn = None    # populating later
        self.replication_task_settings = config.get(REPLICATION_TASK_SECTION, 'replication_task_settings')

