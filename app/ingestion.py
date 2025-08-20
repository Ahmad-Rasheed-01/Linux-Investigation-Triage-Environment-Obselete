import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError
from app.database import db
from app.models import IngestionLog, Case
from app.field_filters import filter_record_fields, get_allowed_fields, parse_raw_stdout_data, requires_raw_data_parsing

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JSONIngestionProcessor:
    """Handles ingestion and processing of JSON artifact files into PostgreSQL."""
    
    def __init__(self):
        self.supported_artifacts = {
            'collection_summary': 'collection_metadata',
            'userAccounts': 'user_accounts',
            'processes': 'processes',
            'networkConnections': 'network_connections',
            'systemdServices': 'systemd_services',
            'authLogs': 'auth_logs',
            'browsingHistory': 'browsing_history',
            'firewallRules': 'firewall_rules',
            'installedPackages': 'installed_packages',
            'cronJobs': 'cron_jobs',
            'systemLogs': 'system_logs',
            'fileSystem': 'file_system',
            'networkInterfaces': 'network_interfaces',
            'mountedFilesystems': 'mounted_filesystems',
            'environmentVariables': 'environment_variables',
            # New artifact types
            'arpCache': 'arp_cache',
            'arpTableRaw': 'arp_table_raw',
            'blockDevices': 'block_devices',
            'boot': 'boot_info',
            'browsingHistory_data': 'browsing_history',
            'btmp_logs': 'btmp_logs',
            'cifsMounts': 'cifs_mounts',
            'collection_metadata': 'collection_metadata',
            'connectionTracking': 'connection_tracking',
            'cpuInformation': 'cpu_information',
            'criticalFiles': 'critical_files',
            'disk_usage': 'disk_usage',
            'fdisk': 'fdisk_info',
            'filesystemStats': 'filesystem_stats',
            'filesystemTypes': 'filesystem_types',
            'groupAccounts': 'group_accounts',
            'homeDirectories': 'home_directories',
            'installRecords': 'install_records',
            'kern': 'kern_logs',
            'kernel_modules': 'kernel_modules'
        }
    
    def process_file(self, file_path: str, case_uuid: str, filename: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Process a single JSON file and ingest data into the case schema.
        
        Args:
            file_path: Path to the JSON file
            case_uuid: UUID of the case
            filename: Original filename
            
        Returns:
            Tuple of (success, message, stats)
        """
        stats = {
            'total_records': 0,
            'inserted_records': 0,
            'errors': 0,
            'artifact_type': 'unknown',
            'file_size': 0
        }
        
        try:
            # Get file size
            stats['file_size'] = os.path.getsize(file_path)
            
            # Load JSON data
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Determine artifact type from filename or content
            artifact_type = self._determine_artifact_type(filename, data)
            stats['artifact_type'] = artifact_type
            
            if artifact_type not in self.supported_artifacts:
                return False, f"Unsupported artifact type: {artifact_type}", stats
            
            # Get case and schema name
            case = Case.query.filter_by(case_uuid=case_uuid).first()
            if not case:
                return False, "Case not found", stats
            
            schema_name = case.schema_name
            table_name = self.supported_artifacts[artifact_type]
            
            # Process data based on artifact type
            success, message, processed_stats = self._process_artifact_data(
                data, schema_name, table_name, artifact_type
            )
            
            # Update stats
            stats.update(processed_stats)
            
            # Note: Ingestion logging is handled by the calling function
            # to avoid duplicate log entries
            
            return success, message, stats
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON format: {str(e)}"
            logger.error(f"JSON decode error for {filename}: {error_msg}")
            return False, error_msg, stats
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Processing error for {filename}: {error_msg}")
            return False, error_msg, stats
    
    def _determine_artifact_type(self, filename: str, data: Any) -> str:
        """
        Determine the artifact type from filename or data structure.
        """
        # Check filename patterns
        filename_lower = filename.lower()
        
        if 'collection_summary' in filename_lower:
            return 'collection_summary'
        elif 'collection_metadata' in filename_lower:
            return 'collection_metadata'
        elif 'useraccounts' in filename_lower or 'user_accounts' in filename_lower:
            return 'userAccounts'
        elif 'processes' in filename_lower:
            return 'processes'
        elif 'network' in filename_lower and 'connections' in filename_lower:
            return 'networkConnections'
        elif 'systemd' in filename_lower or 'services' in filename_lower:
            return 'systemdServices'
        elif 'auth' in filename_lower and 'log' in filename_lower:
            return 'authLogs'
        elif 'browsinghistory_data' in filename_lower:
            return 'browsingHistory_data'
        elif 'browsing' in filename_lower or 'history' in filename_lower:
            return 'browsingHistory'
        elif 'firewall' in filename_lower:
            return 'firewallRules'
        elif 'packages' in filename_lower:
            return 'installedPackages'
        elif 'cron' in filename_lower:
            return 'cronJobs'
        elif 'system' in filename_lower and 'log' in filename_lower:
            return 'systemLogs'
        elif 'filesystemstats' in filename_lower:
            return 'filesystemStats'
        elif 'filesystemtypes' in filename_lower:
            return 'filesystemTypes'
        elif 'filesystem' in filename_lower or 'file_system' in filename_lower:
            return 'fileSystem'
        elif 'interface' in filename_lower:
            return 'networkInterfaces'
        elif 'mount' in filename_lower:
            return 'mountedFilesystems'
        elif 'environment' in filename_lower or 'env' in filename_lower:
            return 'environmentVariables'
        # New artifact types
        elif 'arpcache' in filename_lower or 'arp_cache' in filename_lower:
            return 'arpCache'
        elif 'blockdevices' in filename_lower or 'block_devices' in filename_lower:
            return 'blockDevices'
        elif 'boot' in filename_lower and '.json' in filename_lower:
            return 'boot'
        elif 'btmp' in filename_lower and 'log' in filename_lower:
            return 'btmp_logs'
        elif 'cifsmounts' in filename_lower or 'cifs_mounts' in filename_lower:
            return 'cifsMounts'
        elif 'connectiontracking' in filename_lower or 'connection_tracking' in filename_lower:
            return 'connectionTracking'
        elif 'cpuinformation' in filename_lower or 'cpu_information' in filename_lower or 'cpu' in filename_lower:
            return 'cpuInformation'
        elif 'criticalfiles' in filename_lower or 'critical_files' in filename_lower:
            return 'criticalFiles'
        elif 'arptableraw' in filename_lower or 'arp_table_raw' in filename_lower:
            return 'arpTableRaw'
        elif 'disk_usage' in filename_lower or 'diskusage' in filename_lower:
            return 'disk_usage'
        elif 'fdisk' in filename_lower:
            return 'fdisk'
        elif 'groupaccounts' in filename_lower or 'group_accounts' in filename_lower:
            return 'groupAccounts'
        elif 'homedirectories' in filename_lower or 'home_directories' in filename_lower:
            return 'homeDirectories'
        elif 'installrecords' in filename_lower or 'install_records' in filename_lower:
            return 'installRecords'
        elif 'kern.json' in filename_lower or 'kern_logs' in filename_lower:
            return 'kern'
        elif 'kernel_modules' in filename_lower or 'kernelmodules' in filename_lower:
            return 'kernel_modules'
        
        # Try to determine from data structure
        if isinstance(data, dict):
            if 'collection_info' in data:
                return 'collection_summary'
            elif 'iptables' in data or 'ip6tables' in data:
                return 'firewallRules'
        
        if isinstance(data, list) and len(data) > 0:
            first_item = data[0]
            if isinstance(first_item, dict):
                keys = set(first_item.keys())
                
                if 'username' in keys or 'uid' in keys:
                    return 'userAccounts'
                elif 'pid' in keys or 'command' in keys:
                    return 'processes'
                elif 'url' in keys and 'title' in keys:
                    return 'browsingHistory'
                elif 'local_address' in keys or 'remote_address' in keys:
                    return 'networkConnections'
                elif 'service_name' in keys or 'unit_name' in keys:
                    return 'systemdServices'
        
        return 'unknown'
    
    def _process_artifact_data(self, data: Any, schema_name: str, table_name: str, 
                             artifact_type: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Process and insert artifact data into the appropriate table.
        """
        stats = {'total_records': 0, 'inserted_records': 0, 'errors': 0}
        
        try:
            # Handle different data structures based on artifact type
            if artifact_type == 'collection_summary':
                return self._process_collection_summary(data, schema_name, table_name, stats)
            elif artifact_type == 'firewallRules':
                return self._process_firewall_rules(data, schema_name, table_name, stats)
            elif artifact_type in ['arpCache', 'arpTableRaw', 'blockDevices', 'boot', 'browsingHistory_data', 
                                 'btmp_logs', 'cifsMounts', 'collection_metadata', 
                                 'connectionTracking', 'cpuInformation', 'criticalFiles',
                                 'disk_usage', 'fdisk', 'filesystemStats', 'filesystemTypes',
                                 'groupAccounts', 'homeDirectories', 'installRecords', 'kern', 'kernel_modules']:
                return self._process_structured_data(data, schema_name, table_name, stats, artifact_type)
            else:
                return self._process_list_data(data, schema_name, table_name, stats)
                
        except Exception as e:
            error_msg = f"Error processing {artifact_type}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, stats
    
    def _process_collection_summary(self, data: Dict, schema_name: str, 
                                  table_name: str, stats: Dict) -> Tuple[bool, str, Dict]:
        """
        Process collection summary data.
        """
        try:
            # Apply field filtering for collection_metadata
            filtered_data = filter_record_fields(data, 'collection_metadata')
            
            # Prepare the record for insertion
            record = self._prepare_record_for_insertion(filtered_data, 'collection_metadata')
            record['created_at'] = datetime.utcnow()
            
            success = self._insert_record(schema_name, table_name, record)
            if success:
                stats['inserted_records'] = 1
                stats['total_records'] = 1
                return True, "Collection summary processed successfully", stats
            else:
                stats['errors'] = 1
                return False, "Failed to insert collection summary", stats
                
        except Exception as e:
            stats['errors'] = 1
            return False, f"Error processing collection summary: {str(e)}", stats
    
    def _process_structured_data(self, data: Any, schema_name: str, table_name: str, 
                               stats: Dict, artifact_type: str) -> Tuple[bool, str, Dict]:
        """
        Process structured data for various artifact types.
        """
        try:
            # Check if this artifact type requires raw data parsing
            if requires_raw_data_parsing(artifact_type):
                return self._process_raw_data(data, schema_name, table_name, stats, artifact_type)
            
            if isinstance(data, dict):
                # Handle dictionary-based artifacts
                record = self._prepare_record_for_insertion(data, artifact_type)
                record['created_at'] = datetime.utcnow()
                record['artifact_type'] = artifact_type
                
                success = self._insert_record(schema_name, table_name, record)
                if success:
                    stats['inserted_records'] = 1
                    stats['total_records'] = 1
                    return True, f"{artifact_type} processed successfully", stats
                else:
                    stats['errors'] = 1
                    return False, f"Failed to insert {artifact_type}", stats
            
            elif isinstance(data, list):
                # Handle list-based artifacts
                return self._process_list_data(data, schema_name, table_name, stats)
            
            else:
                # Handle other data types by converting to string
                record = {
                    'content': str(data),
                    'artifact_type': artifact_type,
                    'created_at': datetime.utcnow()
                }
                
                success = self._insert_record(schema_name, table_name, record)
                if success:
                    stats['inserted_records'] = 1
                    stats['total_records'] = 1
                    return True, f"{artifact_type} processed successfully", stats
                else:
                    stats['errors'] = 1
                    return False, f"Failed to insert {artifact_type}", stats
                    
        except Exception as e:
            stats['errors'] = 1
            return False, f"Error processing {artifact_type}: {str(e)}", stats
    
    def _process_raw_data(self, data: Any, schema_name: str, table_name: str, 
                         stats: Dict, artifact_type: str) -> Tuple[bool, str, Dict]:
        """
        Process raw stdout data by parsing it into structured records.
        """
        try:
            # Extract stdout content from the data
            stdout_content = None
            if isinstance(data, dict):
                stdout_content = data.get('stdout', '')
            elif isinstance(data, str):
                stdout_content = data
            
            if not stdout_content:
                stats['errors'] = 1
                return False, f"No stdout content found for {artifact_type}", stats
            
            # Parse the raw stdout data
            parsed_records = parse_raw_stdout_data(stdout_content, artifact_type)
            
            if not parsed_records:
                stats['total_records'] = 0
                stats['inserted_records'] = 0
                return True, f"No parseable data found in {artifact_type}", stats
            
            stats['total_records'] = len(parsed_records)
            records_inserted = 0
            
            # Insert each parsed record
            for record in parsed_records:
                # Apply field filtering
                filtered_record = filter_record_fields(record, artifact_type)
                
                # Prepare record for insertion
                prepared_record = self._prepare_record_for_insertion(filtered_record, artifact_type)
                prepared_record['created_at'] = datetime.utcnow()
                prepared_record['artifact_type'] = artifact_type
                
                if self._insert_record(schema_name, table_name, prepared_record):
                    records_inserted += 1
                else:
                    stats['errors'] += 1
            
            stats['inserted_records'] = records_inserted
            
            if records_inserted > 0:
                return True, f"Processed {records_inserted}/{len(parsed_records)} records for {artifact_type}", stats
            else:
                return False, f"Failed to insert any records for {artifact_type}", stats
                
        except Exception as e:
            stats['errors'] = 1
            return False, f"Error processing raw data for {artifact_type}: {str(e)}", stats
    
    def _process_firewall_rules(self, data: Dict, schema_name: str, 
                              table_name: str, stats: Dict) -> Tuple[bool, str, Dict]:
        """
        Process firewall rules data.
        """
        try:
            # Apply field filtering for firewall rules
            filtered_data = filter_record_fields(data, 'firewallRules')
            
            # Process the filtered data as structured data
            return self._process_structured_data(filtered_data, schema_name, table_name, stats, 'firewallRules')
            
        except Exception as e:
            return False, f"Error processing firewall rules: {str(e)}", stats
    
    def _process_list_data(self, data: Any, schema_name: str, 
                         table_name: str, stats: Dict) -> Tuple[bool, str, Dict]:
        """
        Process list-based artifact data.
        """
        try:
            if not isinstance(data, list):
                return False, "Expected list data format", stats
            
            stats['total_records'] = len(data)
            records_inserted = 0
            
            for item in data:
                if isinstance(item, dict):
                    # Add timestamp if not present
                    if 'created_at' not in item:
                        item['created_at'] = datetime.utcnow()
                    
                    # Convert any nested objects to JSON strings
                    processed_item = self._prepare_record_for_insertion(item, table_name)
                    
                    if self._insert_record(schema_name, table_name, processed_item):
                        records_inserted += 1
                    else:
                        stats['errors'] += 1
            
            stats['inserted_records'] = records_inserted
            
            if records_inserted == stats['total_records']:
                return True, f"Successfully processed all {records_inserted} records", stats
            else:
                return False, f"Processed {records_inserted}/{stats['total_records']} records with {stats['errors']} errors", stats
                
        except Exception as e:
            return False, f"Error processing list data: {str(e)}", stats
    
    def _prepare_record_for_insertion(self, record: Dict, artifact_type: str = None) -> Dict:
        """
        Prepare a record for database insertion by handling data types and applying field filtering.
        """
        # Apply field filtering first if artifact_type is provided
        if artifact_type:
            record = filter_record_fields(record, artifact_type)
        
        prepared = {}
        
        for key, value in record.items():
            if value is None:
                prepared[key] = None
            elif isinstance(value, (dict, list)):
                # Convert complex objects to JSON strings
                prepared[key] = json.dumps(value)
            elif isinstance(value, bool):
                prepared[key] = value
            elif isinstance(value, (int, float)):
                prepared[key] = value
            elif isinstance(value, str):
                # Truncate very long strings
                prepared[key] = value[:10000] if len(value) > 10000 else value
            else:
                # Convert other types to string
                prepared[key] = str(value)
        
        return prepared
    
    def _ensure_table_exists(self, schema_name: str, table_name: str, record: Dict) -> bool:
        """
        Ensure the table exists with appropriate columns for the record.
        """
        try:
            # Check if table exists
            check_query = f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = '{schema_name}' 
                    AND table_name = '{table_name}'
                )
            """
            
            result = db.session.execute(text(check_query)).scalar()
            
            if not result:
                # Create table with columns based on record structure
                columns_def = []
                for key, value in record.items():
                    if key == 'id':
                        columns_def.append('id SERIAL PRIMARY KEY')
                    elif key == 'created_at':
                        columns_def.append('created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
                    elif isinstance(value, bool):
                        columns_def.append(f'{key} BOOLEAN')
                    elif isinstance(value, int):
                        columns_def.append(f'{key} INTEGER')
                    elif isinstance(value, float):
                        columns_def.append(f'{key} FLOAT')
                    else:
                        columns_def.append(f'{key} TEXT')
                
                # Add id and created_at if not present
                if 'id' not in record:
                    columns_def.insert(0, 'id SERIAL PRIMARY KEY')
                if 'created_at' not in record:
                    columns_def.append('created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
                
                create_query = f"""
                    CREATE TABLE {schema_name}.{table_name} (
                        {', '.join(columns_def)}
                    )
                """
                
                db.session.execute(text(create_query))
                db.session.commit()
                logger.info(f"Created table {schema_name}.{table_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error ensuring table exists {schema_name}.{table_name}: {str(e)}")
            db.session.rollback()
            return False
    
    def _insert_record(self, schema_name: str, table_name: str, record: Dict) -> bool:
        """
        Insert a single record into the specified table.
        """
        try:
            # Ensure table exists first
            if not self._ensure_table_exists(schema_name, table_name, record):
                return False
            
            # Build column names and placeholders
            columns = list(record.keys())
            placeholders = [f":{col}" for col in columns]
            
            # Build INSERT query
            query = f"""
                INSERT INTO {schema_name}.{table_name} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
            """
            
            # Execute query
            db.session.execute(text(query), record)
            db.session.commit()
            
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Database error inserting into {schema_name}.{table_name}: {str(e)}")
            db.session.rollback()
            return False
        except Exception as e:
            logger.error(f"Unexpected error inserting into {schema_name}.{table_name}: {str(e)}")
            db.session.rollback()
            return False
    
    def _log_ingestion(self, case_uuid: str, filename: str, file_size: int, 
                      artifact_type: str, status: str, records_processed: int, 
                      error_message: Optional[str] = None):
        """
        Log the ingestion result to the database.
        """
        try:
            # Get case ID from UUID
            case = Case.query.filter_by(case_uuid=case_uuid).first()
            if not case:
                logger.error(f"Case with UUID {case_uuid} not found for logging")
                return
                
            log_entry = IngestionLog(
                case_id=case.id,
                filename=filename,
                file_size=file_size,
                artifact_type=artifact_type,
                status=status,
                records_processed=records_processed,
                error_message=error_message
            )
            
            db.session.add(log_entry)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to log ingestion: {str(e)}")
            db.session.rollback()
    
    def get_supported_artifacts(self) -> Dict[str, str]:
        """
        Get the mapping of supported artifact types to table names.
        """
        return self.supported_artifacts.copy()
    
    def validate_json_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate that a file is valid JSON and determine its type.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            filename = os.path.basename(file_path)
            artifact_type = self._determine_artifact_type(filename, data)
            
            if artifact_type == 'unknown':
                return False, "Unable to determine artifact type from file content"
            
            if artifact_type not in self.supported_artifacts:
                return False, f"Unsupported artifact type: {artifact_type}"
            
            return True, f"Valid {artifact_type} artifact"
            
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON format: {str(e)}"
        except Exception as e:
            return False, f"Error validating file: {str(e)}"


# Global processor instance
ingestion_processor = JSONIngestionProcessor()


def process_uploaded_file(file_path: str, case_uuid: str, filename: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Convenience function to process an uploaded file.
    """
    return ingestion_processor.process_file(file_path, case_uuid, filename)


def validate_uploaded_file(file_path: str) -> Tuple[bool, str]:
    """
    Convenience function to validate an uploaded file.
    """
    return ingestion_processor.validate_json_file(file_path)


def get_supported_artifact_types() -> Dict[str, str]:
    """
    Get supported artifact types.
    """
    return ingestion_processor.get_supported_artifacts()