from time import sleep

from botocore.exceptions import ClientError

from AWSClients import AWSClients
from PropertyLoader import PropertyLoader

# todo add db engine validation method

class DBReplicator:

    def __init__(self):
        self.aws_clients = AWSClients()
        self.config_properties = PropertyLoader()

    def create_dms_security_group_if_not_exists(self, sec_group_name, vpc_id):
        """ returns id of newly created security group, or id of existing security group if group already exists"""
        try:
            ec2_client = self.aws_clients.get_ec2_handle()
            self.config_properties.logger.info('Creating VPC security group ' + sec_group_name)
            response = ec2_client.create_security_group(Description=sec_group_name, GroupName=sec_group_name, VpcId=vpc_id)
            sec_grp_id = response['GroupId']
            self.config_properties.logger.info('VPC Security Group created. Name: ' + sec_group_name + ', ID: ' + sec_grp_id)
            return sec_grp_id
        except ClientError as e:
            exception_code = e.response['Error']['Code']
            exception_msg = e.response['Error']['Message']
            if exception_code == 'InvalidGroup.Duplicate':
                self.config_properties.logger.info(exception_msg + '. Getting its ID')
                sec_grp_id = self.get_existing_security_grp_id_from_name(sec_group_name, vpc_id)
                return sec_grp_id
            else:
                self.config_properties.logger.exception(e)

    def get_existing_security_grp_id_from_name(self, sec_grp_name, vpc_id):

        try:
            ec2_client = self.aws_clients.get_ec2_handle()
            response = ec2_client.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': [sec_grp_name]}, {'Name': 'vpc-id', 'Values': [vpc_id]}])
            sec_grp_id = response['SecurityGroups'][0]['GroupId']
            self.config_properties.logger.info(response)
            self.config_properties.logger.info('Security group ' + sec_grp_name + ' has ID = ' + sec_grp_id)
            return sec_grp_id
        except ClientError as e:
            self.config_properties.logger.exception(e)

    def create_dms_subnet_group_if_not_exists(self, subnet_grp_name, member_subnet_ids_list):
        try:
            dms_client = self.aws_clients.get_dms_handle()
            self.config_properties.logger.info('Creating DMS replication subnet group ' + subnet_grp_name + ' with member subnet IDs ' + str(member_subnet_ids_list))
            response = dms_client.create_replication_subnet_group(ReplicationSubnetGroupIdentifier=subnet_grp_name, ReplicationSubnetGroupDescription=subnet_grp_name,
                                                                  SubnetIds=member_subnet_ids_list)
            self.config_properties.logger.info(response)
            self.config_properties.logger.info('Subnet group ' + subnet_grp_name + ' created')
        except ClientError as e:
            exception_code = e.response['Error']['Code']
            exception_msg = e.response['Error']['Message']
            if exception_code == 'ResourceAlreadyExistsFault':
                self.config_properties.logger.info(exception_msg + '. Moving forward')
                pass
            else:
                self.config_properties.logger.exception(e)

    def create_rds_subnet_group_if_not_exists(self, subnet_grp_name, member_subnet_ids_list):
        rds_client = self.aws_clients.get_rds_handle()
        self.config_properties.logger.info('Creating RDS subnet group ' + subnet_grp_name + ' with member subnet IDs ' + str(member_subnet_ids_list))
        try:
            response = rds_client.create_db_subnet_group(DBSubnetGroupName=subnet_grp_name, DBSubnetGroupDescription=subnet_grp_name,
                                                         SubnetIds=member_subnet_ids_list)
            self.config_properties.logger.info(response)
            self.config_properties.logger.info('Subnet group ' + subnet_grp_name + ' created')
        except ClientError as e:
            exception_code = e.response['Error']['Code']
            exception_msg = e.response['Error']['Message']
            if exception_code == 'DBSubnetGroupAlreadyExists':
                self.config_properties.logger.info(exception_msg + '. Moving forward')
                pass
            else:
                self.config_properties.logger.exception(e)

    def create_replication_instance(self, instance_name, instance_class, allocated_storage_gb, vpc_security_grp_id, subnet_grp_name):
        """ creates a replication instance and returns its ARN"""
        try:
            dms_client = self.aws_clients.get_dms_handle()
            self.config_properties.logger.info('Creating DMS replication instance ' + instance_name + ' with instance class ' + instance_class + ' and allocated storage ' +
                                               str(allocated_storage_gb) + ' GB. Not selecting specific AZ for now')
            response = dms_client.create_replication_instance(ReplicationInstanceIdentifier=instance_name, AllocatedStorage=allocated_storage_gb,
                                                              ReplicationInstanceClass=instance_class, VpcSecurityGroupIds=(vpc_security_grp_id).split(','),
                                                              ReplicationSubnetGroupIdentifier=subnet_grp_name)
            self.config_properties.logger.info(response)
            self.config_properties.logger.info(
                'Waiting until replication instance becomes available. Will check ' + str(self.config_properties.check_status_num_times) + ' times at intervals of 5 seconds. This task can sometimes take upwards of 10 minutes.')
            i = 0
            while i < self.config_properties.check_status_num_times:
                instance_status = (self.get_replication_instance_details(instance_name))['ReplicationInstances'][0]['ReplicationInstanceStatus']
                if instance_status == 'available':
                    replinst_arn = (self.get_replication_instance_details(instance_name))['ReplicationInstances'][0]['ReplicationInstanceArn']
                    self.config_properties.logger.info('Replication instance ' + instance_name + ' is now AVAILABLE' + ' with ARN: ' + replinst_arn + '. Moving forward')
                    return replinst_arn
                else:
                    self.config_properties.logger.info('Replication instance status is: ' + instance_status + '. Waiting ...')
                    sleep(5)
                    i += 1
            if i == self.config_properties.check_status_num_times:
                self.config_properties.logger.exception('Replication instance ' + instance_name + ' is still NOT ONLINE. Please 1) Increase the waiting time in config.properties file, then 2)  Fix the issue with your'
                                                                                                  ' replication instance and then 3) Re-run this program')
            # VpcSecurityGroupIds currently has only one security group that was generated via create_dms_security_group_if_not_exists(). However, above create_replication_instance call expects a list of security group ids so i am
            # splitting the lone security group id i create by comma to mimic supplying a list. Code for
            # create_dms_security_group_if_not_exists() should ber modified if you want to create multiple security groups and pass them as a list
        except ClientError as e:
            exception_code = e.response['Error']['Code']
            exception_msg = e.response['Error']['Message']
            if exception_code == 'ResourceAlreadyExistsFault':
                replinst_arn = (self.get_replication_instance_details(instance_name))['ReplicationInstances'][0]['ReplicationInstanceArn']
                self.config_properties.logger.info(exception_msg + ' Replication instance has ARN: ' + replinst_arn + '. Moving forward')
                return replinst_arn
            else:
                self.config_properties.logger.exception(e)

    def get_replication_instance_details(self, instance_name):
        try:
            dms_client = self.aws_clients.get_dms_handle()
            return dms_client.describe_replication_instances(Filters=[{'Name': 'replication-instance-id', 'Values': [instance_name]}])
        except ClientError as e:
            self.config_properties.logger.exception(e)

    def create_rds_target_db_instance(self, instance_identifier, instance_class, allocated_storage_gb, engine, username, secret, subnet_grp_name, port):
        """ creates a new RDS database of same engine as source db """
        self.config_properties.logger.info('Creating target DB instance ' + self.config_properties.tgt_db_instance_identifier + ' in RDS. This instance will have the same engine, username, password and port as the source database if you '
                                                                                                                                'did not explicitly modify them in the configuration file.')
        rds_client = self.aws_clients.get_rds_handle()
        try:
            response = rds_client.create_db_instance(DBInstanceIdentifier=instance_identifier, AllocatedStorage=allocated_storage_gb,
                                                     DBInstanceClass=instance_class, Engine=engine, MasterUsername=username,
                                                     MasterUserPassword=secret, DBSubnetGroupName=subnet_grp_name, Port=port)
            self.config_properties.logger.info(response)
            self.config_properties.logger.info(
                'Waiting until RDS instance ' + instance_identifier + ' becomes available. Will check ' + str(self.config_properties.check_status_num_times) + ' times at intervals of 5 seconds. This '
                                                                                                                                                               'task can sometimes take upwards of 10 '
                                                                                                                                                               'minutes.')
            i = 0
            while i < self.config_properties.check_status_num_times:
                instance_status = (self.get_rds_db_instance_details(instance_identifier))['DBInstances'][0]['DBInstanceStatus']
                if instance_status == 'available':
                    self.config_properties.logger.info('RDS DB Instance ' + instance_identifier + ' is NOW AVAILABLE. Moving forward')
                    break
                else:
                    self.config_properties.logger.info('RDS DB instance status is: ' + instance_status + ' . Waiting ...')
                    sleep(5)
                    i += 1
            if i == self.config_properties.check_status_num_times:
                self.config_properties.logger.exception(' RDS instance ' + instance_identifier + ' is still NOT ONLINE. Please 1) Increase the waiting time in config.properties file if need be, '
                                                                                                 'then 2)  Fix the issue with your'
                                                                                                 ' RDS instance if need be, and then 3) Re-run this program')
        except ClientError as e:
            exception_code = e.response['Error']['Code']
            exception_msg = e.response['Error']['Message']
            if exception_code == 'DBInstanceAlreadyExists':
                self.config_properties.logger.info(instance_identifier + ' ' + exception_msg + '. Moving forward')
            else:
                self.config_properties.logger.exception(e)

    def get_rds_db_instance_details(self, instance_identifier):
        try:
            rds_client = self.aws_clients.get_rds_handle()
            return rds_client.describe_db_instances(DBInstanceIdentifier=instance_identifier)
        except ClientError as e:
            self.config_properties.logger.exception(e)

    def create_dms_source_db_endpoint(self, endpoint_name, host, port, engine, username, secret, db_name):
        """ creates dms source endpoint and returns ARN"""
        try:
            dms_client = self.aws_clients.get_dms_handle()

            # create source endpoint
            self.config_properties.logger.info('Creating DMS source endpoint ' + endpoint_name + ' for source database that is currently on ' + host + ':' + str(port))
            response = dms_client.create_endpoint(EndpointIdentifier=endpoint_name, EndpointType='source', EngineName=engine,
                                                  Username=username, Password=secret, ServerName=host, Port=port, DatabaseName=db_name)
            self.config_properties.logger.info(response)
            endpoint_arn = response['Endpoint']['EndpointArn']
            self.config_properties.logger.info('DMS source endpoint ' + endpoint_name + ' created with ARN ' + endpoint_arn)
            return endpoint_arn
        except ClientError as e:
            exception_code = e.response['Error']['Code']
            exception_msg = e.response['Error']['Message']
        if exception_code == 'ResourceAlreadyExistsFault':
            endpoint_arn = (self.get_dms_endpoint_details(endpoint_name))['Endpoints'][0]['EndpointArn']
            self.config_properties.logger.info(exception_msg + ' Source endpoint has ARN: ' + endpoint_arn + '. Moving forward')
            return endpoint_arn
        else:
            self.config_properties.logger.exception(e)

    def create_dms_target_db_endpoint(self, endpoint_name, host, port, engine, username, secret, db_name):
        try:
            dms_client = self.aws_clients.get_dms_handle()
            # create target endpoint
            self.config_properties.logger.info('Creating DMS target endpoint ' + endpoint_name + ' for target RDS database on ' + host + ':' + str(port))
            response = dms_client.create_endpoint(EndpointIdentifier=endpoint_name, EndpointType='target', EngineName=engine,
                                                  Username=username, Password=secret, ServerName=host, Port=port, DatabaseName=db_name)
            self.config_properties.logger.info(response)
            endpoint_arn = response['Endpoint']['EndpointArn']
            self.config_properties.logger.info('DMS target endpoint ' + endpoint_name + ' created with ARN ' + endpoint_arn)
            return endpoint_arn
        except ClientError as e:
            exception_code = e.response['Error']['Code']
            exception_msg = e.response['Error']['Message']
            if exception_code == 'ResourceAlreadyExistsFault':
                self.config_properties.logger.info(exception_msg + '. Moving forward')
                endpoint_arn = (self.get_dms_endpoint_details(endpoint_name))['Endpoints'][0]['EndpointArn']
                return endpoint_arn
            else:
                self.config_properties.logger.exception(e)

    def get_dms_endpoint_details(self, endpoint_name):
        try:
            dms_client = self.aws_clients.get_dms_handle()
            return dms_client.describe_endpoints(Filters=[{'Name': 'endpoint-id', 'Values': [endpoint_name]}])
        except ClientError as e:
            self.config_properties.logger.exception(e)

    def test_dms_endpoint_connection_from_replication_instance(self, replication_instance_arn, dms_endpoint_arn):
        try:
            dms_client = self.aws_clients.get_dms_handle()
            self.config_properties.logger.info(' Checking endpoint connectivity with replication instance. Replication Instance Arn: ' + replication_instance_arn + ' & DMS Endpoint Arn: ' + dms_endpoint_arn)
            response = dms_client.test_connection(ReplicationInstanceArn=replication_instance_arn, EndpointArn=dms_endpoint_arn)
            self.config_properties.logger.info(response)
            i = 0
            while i < self.config_properties.check_status_num_times:
                dms_endpoint_conn_status = (dms_client.describe_connections(Filters=[{'Name': 'endpoint-arn', 'Values': [dms_endpoint_arn]}]))['Connections'][0]['Status']
                if dms_endpoint_conn_status == 'successful':
                    self.config_properties.logger.info('Connection test between Replication Instance & DMS Endpoint is SUCCESSFUL. Moving forward')
                    break
                else:
                    self.config_properties.logger.info('Connection test status: ' + dms_endpoint_conn_status + '. Waiting ...')
                    sleep(5)
                    i += 1
            if i == self.config_properties.check_status_num_times:
                self.config_properties.logger.exception('Could not determine connection status between Replication Instance Arn: ' + replication_instance_arn + ' and DMS Endpoint Arn: ' + dms_endpoint_arn)
        except ClientError as e:
            self.config_properties.logger.exception(e)

    def create_dms_replication_task(self, task_identifier, src_endpt_arn, tgt_endpt_arn, replication_instance_arn, migration_type, table_mapping_rules, task_settings):
        """ creates a replication task and returns its arn"""
        try:
            dms_client = self.aws_clients.get_dms_handle()
            self.config_properties.logger.info('Creating replication task ' + task_identifier)
            response = dms_client.create_replication_task(ReplicationTaskIdentifier=task_identifier, SourceEndpointArn=src_endpt_arn,
                                                          TargetEndpointArn=tgt_endpt_arn, ReplicationInstanceArn=replication_instance_arn, MigrationType=migration_type,
                                                          TableMappings=table_mapping_rules, ReplicationTaskSettings=task_settings)
            self.config_properties.logger.info(response)
            replication_task_arn = response['ReplicationTask']['ReplicationTaskArn']
            i = 0
            #  todo explore getwaiter
            while i < self.config_properties.check_status_num_times:
                task_status = (self.get_replication_task_details(task_identifier))['ReplicationTasks'][0]['Status']
                if task_status == 'ready':
                    self.config_properties.logger.info('DMS Replication task ' + task_identifier + ' is created and ready to execute. ARN: ' + replication_task_arn)
                    return replication_task_arn
                else:
                    self.config_properties.logger.info('DMS Replication task ' + task_identifier + ' status is: ' + task_status + '. Waiting ...')
                    sleep(5)
                    i += 1
            if i == self.config_properties.check_status_num_times:
                self.config_properties.logger.exception('Could not verify the status of replication task ' + task_identifier + ' having ARN: ' + replication_task_arn + '. Please investigate')
        except ClientError as e:
            self.config_properties.logger.exception(e)

    def get_replication_task_details(self, replication_task_identifier):
        try:
            dms_client = self.aws_clients.get_dms_handle()
            return dms_client.describe_replication_tasks(Filters=[{'Name': 'replication-task-id', 'Values': [replication_task_identifier]}])
        except ClientError as e:
            self.config_properties.logger.exception(e)

    def start_database_migration(self, replication_task_arn):
        try:
            dms_client = self.aws_clients.get_dms_handle()
            self.config_properties.logger.info('Starting DMS replication task: ' + self.config_properties.replication_task_identifier)
            response = dms_client.start_replication_task(ReplicationTaskArn=replication_task_arn, StartReplicationTaskType='start-replication')
            self.config_properties.logger.info(response)
        except ClientError as e:
            self.config_properties.logger.exception(e)


'''
    def database_migration_status(self):
        while 1:
            print((self.get_replication_task_details('replication-task'))['ReplicationTasks'][0]['Status'])
            sleep(10)
'''
