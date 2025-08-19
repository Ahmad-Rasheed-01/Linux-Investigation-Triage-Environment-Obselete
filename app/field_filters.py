"""Field filtering configuration for JSON ingestion based on json files guide.txt"""

# Define the specific fields to extract for each JSON file type
# Files with 'raw_data': True need their stdout field parsed by splitting on newlines
FIELD_FILTERS = {
    'arpCache': {
        'fields': ['ip_address', 'mac_address', 'interface']
    },
    'arpTableRaw': {
        'allowed_fields': ['address', 'hwtype', 'hwaddress', 'flags', 'mask', 'iface'],
        'raw_data': True
    },
    'audit': {
        'fields': ['timestamp', 'event_type', 'pid', 'uid', 'gid', 'executable', 'command', 'result']
    },
    'blockDevices': {
        'allowed_fields': ['device_name', 'size_bytes', 'device_type', 'mount_point', 'filesystem', 'model'],
        'raw_data': True
    },
    'boot': {
        'fields': ['kernel_version', 'boot_time', 'uptime_seconds', 'load_average']
    },
    'browsingHistory_data': {
        'fields': ['url', 'title', 'visit_count', 'last_visit_time', 'typed_count']
    },
    'collection_metadata': {
        'fields': ['collection_timestamp', 'hostname', 'collection_directory', 'total_sections', 'total_files', 'total_directories']
    },
    'connectionTracking': {
        'fields': ['protocol', 'src_ip', 'src_port', 'dst_ip', 'dst_port', 'state', 'timeout'],
        'raw_data': True
    },
    'cpuInformation': {
        'fields': ['processor_id', 'vendor_id', 'cpu_family', 'model', 'model_name', 'stepping', 'microcode', 'cpu_mhz', 'cache_size', 'physical_id', 'siblings', 'core_id', 'cpu_cores', 'apicid', 'initial_apicid', 'fpu', 'fpu_exception', 'cpuid_level', 'wp', 'flags', 'bugs', 'bogomips', 'clflush_size', 'cache_alignment', 'address_sizes', 'power_management']
    },
    'criticalFiles': {
        'fields': ['file_path', 'permissions', 'owner', 'group', 'size', 'modified_time', 'file_type', 'exists']
    },
    'development_programming': {
        'fields': ['language', 'framework', 'version', 'project_path', 'config_files']
    },
    'disk_usage': {
        'allowed_fields': ['filesystem', 'size_bytes', 'used_bytes', 'available_bytes', 'use_percent', 'mounted_on'],
        'raw_data': True
    },
    'dnsCache': {
        'fields': ['ip', 'hostname']
    },
    'downloads_data': {
        'fields': ['filePath', 'sourceUrl', 'title', 'downloadDate', 'annotationType', 'sourceProfile']
    },
    'dpkgLogsMetadata': {
        'fields': ['file_path', 'file_size', 'is_compressed', 'processed', 'install_count', 'upgrade_count', 'remove_count']
    },
    'dpkgPackages': {
        'fields': ['name', 'version', 'architecture', 'description', 'status']
    },
    'environmentVariables': {
        'fields': ['variables']  # This will contain the entire variables object
    },
    'extensions_data': {
        'fields': ['id', 'name', 'version', 'type', 'enabled', 'installDate', 'updateDate', 'description', 'permissions', 'origins']
    },
    'fdisk': {
        'allowed_fields': ['disk_path', 'disk_size', 'disk_model', 'sector_size', 'disklabel_type', 'disk_identifier', 'device', 'boot_flag', 'start_sector', 'end_sector', 'sectors', 'size', 'partition_id', 'partition_type'],
        'raw_data': True
    },
    'filesystemStats': {
        'fields': ['filesystem', 'inodes', 'iused', 'ifree', 'iuse_percent', 'mounted_on'],
        'raw_data': True
    },
    'filesystemTypes': {
        'fields': ['filesystem_type', 'nodev'],
        'raw_data': True
    },
    'firewallRules': {
        'fields': ['iptables', 'ip6tables', 'ufw']
    },
    'groupAccounts': {
        'fields': ['groupName', 'password', 'gid', 'members', 'groupType']
    },
    'homeDirectories': {
        'fields': ['username', 'uid', 'gid', 'permissions', 'links', 'owner', 'group', 'size', 'month', 'day', 'time', 'directoryName', 'fullPath', 'isUserDirectory', 'shell', 'exists', 'diskUsage']
    },
    'installRecords': {
        'fields': ['timestamp', 'action', 'package', 'package_name', 'architecture', 'source_file', 'version']
    },
    'kern': {
        'fields': ['source_file', 'timestamp', 'hostname', 'subsystem', 'log_level', 'event_type', 'message']
    },
    'kernel_modules': {
        'fields': ['name', 'size', 'used_count', 'used_by']
    }
}

def filter_record_fields(record, artifact_type):
    """
    Filter a record to only include the fields specified in FIELD_FILTERS.
    
    Args:
        record (dict): The original record
        artifact_type (str): The type of artifact being processed
        
    Returns:
        dict: Filtered record containing only allowed fields
    """
    if artifact_type not in FIELD_FILTERS:
        # If no filter is defined, return the original record
        return record
    
    allowed_fields = FIELD_FILTERS[artifact_type].get('allowed_fields', FIELD_FILTERS[artifact_type].get('fields', []))
    filtered_record = {}
    
    for field in allowed_fields:
        if field in record:
            filtered_record[field] = record[field]
    
    return filtered_record

def parse_raw_stdout_data(stdout_content, artifact_type):
    """
    Parse raw stdout data by splitting on newlines and extracting key-value pairs.
    
    Args:
        stdout_content (str): Raw stdout content
        artifact_type (str): The type of artifact being processed
        
    Returns:
        list: List of parsed records
    """
    if not stdout_content or not isinstance(stdout_content, str):
        return []
    
    lines = stdout_content.strip().split('\n')
    parsed_records = []
    
    if artifact_type == 'arpTableRaw':
        # Parse arp output: Address HWtype HWaddress Flags Mask Iface
        for line in lines:
            if line.strip() and not line.startswith('Address'):
                parts = line.split()
                if len(parts) >= 6:
                    parsed_records.append({
                        'address': parts[0],
                        'hwtype': parts[1],
                        'hwaddress': parts[2],
                        'flags': parts[3],
                        'mask': parts[4],
                        'iface': parts[5]
                    })
    
    elif artifact_type == 'blockDevices':
        # Parse lsblk format: NAME MAJ:MIN RM SIZE RO TYPE MOUNTPOINT
        for line in lines:
            if line.strip() and not line.startswith('NAME'):
                parts = line.split()
                if len(parts) >= 6:
                    # Convert size to bytes (simplified conversion)
                    size_str = parts[3] if len(parts) > 3 else '0'
                    size_bytes = 0
                    if size_str and size_str != '0':
                        # Simple conversion - assumes G for GB, M for MB, etc.
                        if size_str.endswith('G'):
                            size_bytes = int(float(size_str[:-1]) * 1024 * 1024 * 1024)
                        elif size_str.endswith('M'):
                            size_bytes = int(float(size_str[:-1]) * 1024 * 1024)
                        elif size_str.endswith('K'):
                            size_bytes = int(float(size_str[:-1]) * 1024)
                    
                    parsed_records.append({
                        'device_name': parts[0],
                        'size_bytes': size_bytes,
                        'device_type': parts[5] if len(parts) > 5 else '',
                        'mount_point': parts[6] if len(parts) > 6 else '',
                        'filesystem': '',  # Not available in lsblk output
                        'model': ''  # Not available in lsblk output
                    })
    
    elif artifact_type == 'connectionTracking':
        # Parse connection tracking format
        for line in lines:
            if line.strip():
                # Simple parsing - each line represents a connection
                parsed_records.append({
                    'raw_line': line.strip()
                })
    
    elif artifact_type == 'disk_usage':
        # Parse df format: Filesystem Size Used Avail Use% Mounted on
        for line in lines:
            if line.strip() and not line.startswith('Filesystem'):
                parts = line.split()
                if len(parts) >= 6:
                    # Convert from 1K-blocks to bytes
                    size_kb = int(parts[1]) if parts[1].isdigit() else 0
                    used_kb = int(parts[2]) if parts[2].isdigit() else 0
                    available_kb = int(parts[3]) if parts[3].isdigit() else 0
                    
                    parsed_records.append({
                        'filesystem': parts[0],
                        'size_bytes': size_kb * 1024,
                        'used_bytes': used_kb * 1024,
                        'available_bytes': available_kb * 1024,
                        'use_percent': int(parts[4].replace('%', '')) if parts[4].replace('%', '').isdigit() else 0,
                        'mounted_on': ' '.join(parts[5:])
                    })
    
    elif artifact_type == 'fdisk':
        # Parse fdisk -l output with disk and partition information
        current_disk = {}
        for line in lines:
            if line.startswith('Disk /'):
                # Parse disk header: Disk /dev/sda: 20 GiB, 21474836480 bytes, 41943040 sectors
                parts = line.split()
                if len(parts) >= 4:
                    current_disk = {
                        'disk_path': parts[1].rstrip(':'),
                        'disk_size': parts[2] + ' ' + parts[3].rstrip(','),
                        'disk_model': '',
                        'sector_size': '',
                        'disklabel_type': '',
                        'disk_identifier': ''
                    }
            elif line.startswith('Sector size'):
                # Parse sector size info
                current_disk['sector_size'] = line.split(':')[1].strip() if ':' in line else ''
            elif line.startswith('Disklabel type'):
                current_disk['disklabel_type'] = line.split(':')[1].strip() if ':' in line else ''
            elif line.startswith('Disk identifier'):
                current_disk['disk_identifier'] = line.split(':')[1].strip() if ':' in line else ''
            elif line.strip() and not line.startswith('Device') and '/' in line and len(line.split()) >= 6:
                # Parse partition line: /dev/sda1 * 2048 1050623 1048576 512M 83 Linux
                parts = line.split()
                boot_flag = '*' in parts[1] if len(parts) > 1 else False
                start_idx = 2 if boot_flag else 1
                
                if len(parts) >= start_idx + 5:
                    record = current_disk.copy()
                    record.update({
                        'device': parts[0],
                        'boot_flag': boot_flag,
                        'start_sector': int(parts[start_idx]) if parts[start_idx].isdigit() else 0,
                        'end_sector': int(parts[start_idx + 1]) if parts[start_idx + 1].isdigit() else 0,
                        'sectors': int(parts[start_idx + 2]) if parts[start_idx + 2].isdigit() else 0,
                        'size': parts[start_idx + 3],
                        'partition_id': parts[start_idx + 4] if len(parts) > start_idx + 4 else '',
                        'partition_type': ' '.join(parts[start_idx + 5:]) if len(parts) > start_idx + 5 else ''
                    })
                    parsed_records.append(record)
    
    elif artifact_type == 'filesystemStats':
        # Parse df -i format: Filesystem Inodes IUsed IFree IUse% Mounted on
        for line in lines:
            if line.strip() and not line.startswith('Filesystem'):
                parts = line.split()
                if len(parts) >= 6:
                    parsed_records.append({
                        'filesystem': parts[0],
                        'inodes': parts[1],
                        'iused': parts[2],
                        'ifree': parts[3],
                        'iuse_percent': parts[4],
                        'mounted_on': ' '.join(parts[5:])
                    })
    
    elif artifact_type == 'filesystemTypes':
        # Parse /proc/filesystems format
        for line in lines:
            if line.strip():
                parts = line.split()
                if len(parts) >= 1:
                    if parts[0] == 'nodev':
                        parsed_records.append({
                            'filesystem_type': parts[1] if len(parts) > 1 else '',
                            'nodev': True
                        })
                    else:
                        parsed_records.append({
                            'filesystem_type': parts[0],
                            'nodev': False
                        })
    
    return parsed_records

def requires_raw_data_parsing(artifact_type):
    """
    Check if an artifact type requires raw data parsing.
    
    Args:
        artifact_type (str): The type of artifact
        
    Returns:
        bool: True if raw data parsing is required
    """
    return (artifact_type in FIELD_FILTERS and 
            FIELD_FILTERS[artifact_type].get('raw_data', False))

def get_allowed_fields(artifact_type):
    """
    Get the list of allowed fields for a specific artifact type.
    
    Args:
        artifact_type (str): The type of artifact
        
    Returns:
        list: List of allowed field names, or None if no filter is defined
    """
    if artifact_type in FIELD_FILTERS:
        return FIELD_FILTERS[artifact_type].get('allowed_fields', FIELD_FILTERS[artifact_type].get('fields', []))
    return None