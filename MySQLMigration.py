from subprocess import Popen

from PropertyLoader import PropertyLoader


class MySQLMigration:

    def __init__(self):
        self.config_properties = PropertyLoader()

    def execute_mysql_migration(self, db_home, local_host, local_user, local_db_name, local_secret, rds_user, rds_port, rds_hostname, rds_secret):
        # backup
        dumped_sql_file_path = 'backup/dump.sql'
        self.config_properties.logger.info('Backing up source database. Dumping SQL file to ' + dumped_sql_file_path)
        cmd_backup_from_local_db = db_home + '/bin/' + 'mysqldump -u ' + local_user + ' -h ' + local_host + ' --databases ' + local_db_name + ' --single-transaction --column-statistics=0 --compress --disable-keys --add-drop-table ' \
                                                                                                                                              '--add-drop-database ' \
                                                                                                                                              '--add-drop-trigger --order-by-primary -p' + local_secret + ' | grep -v DEFINER > ' + \
                                   dumped_sql_file_path
        backup = Popen(cmd_backup_from_local_db, shell=True)
        backup.wait()
        rc = backup.returncode
        if rc != 0:
            self.config_properties.logger.exception('Backup FAILED')
            exit(rc)
        else:
            self.config_properties.logger.info('Backup complete')
        # restore
        self.config_properties.logger.info('Restoring backup to RDS')
        cmd_restore_to_rds_db = db_home + '/bin/' + 'mysql -u ' + rds_user + ' --port=' + str(rds_port) + ' -h ' + rds_hostname + ' -p' + rds_secret + ' < ' + dumped_sql_file_path
        restore = Popen(cmd_restore_to_rds_db, shell=True)
        restore.wait()
        rc = restore.returncode
        if rc != 0:
            self.config_properties.logger.exception('Restore FAILED')
            exit(rc)
        else:
            self.config_properties.logger.info('Restore complete')
