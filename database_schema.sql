-- Linux Investigation & Triage Environment (LITE) Database Schema
-- This schema defines all tables for forensic artifact categories
-- Each case will have its own PostgreSQL schema with these predefined tables

-- ============================================================================
-- CASE MANAGEMENT TABLES
-- ============================================================================

-- Main cases table (exists in public schema)
CREATE TABLE IF NOT EXISTS cases (
    case_id SERIAL PRIMARY KEY,
    case_name VARCHAR(255) NOT NULL UNIQUE,
    case_description TEXT,
    schema_name VARCHAR(63) NOT NULL UNIQUE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'closed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    total_artifacts INTEGER DEFAULT 0,
    collection_timestamp VARCHAR(50)
);

-- ============================================================================
-- ARTIFACT TABLES (Created in each case schema)
-- ============================================================================

-- Collection Metadata
CREATE TABLE collection_metadata (
    id SERIAL PRIMARY KEY,
    timestamp VARCHAR(50),
    hostname VARCHAR(255),
    version VARCHAR(20),
    collection_directory VARCHAR(500),
    output_format VARCHAR(50),
    version_sea VARCHAR(20),
    timezone_name VARCHAR(10),
    timezone_offset VARCHAR(10),
    unix_timestamp BIGINT,
    locale_language VARCHAR(20),
    locale_encoding VARCHAR(20),
    platform_system VARCHAR(50),
    platform_release VARCHAR(100),
    platform_version VARCHAR(500),
    platform_machine VARCHAR(50),
    platform_processor VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Accounts
CREATE TABLE user_accounts (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    password VARCHAR(10),
    uid INTEGER,
    gid INTEGER,
    gecos VARCHAR(500),
    home_directory VARCHAR(500),
    shell VARCHAR(200),
    timestamp DOUBLE PRECISION,
    extractor VARCHAR(50),
    user_type VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Processes
CREATE TABLE processes (
    id SERIAL PRIMARY KEY,
    user_name VARCHAR(100),
    pid INTEGER,
    cpu_percent DECIMAL(5,2),
    memory_percent DECIMAL(5,2),
    vsz BIGINT,
    rss BIGINT,
    tty VARCHAR(20),
    stat VARCHAR(10),
    start_time VARCHAR(20),
    time VARCHAR(20),
    command TEXT,
    name VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Network Connections
CREATE TABLE network_connections (
    id SERIAL PRIMARY KEY,
    protocol VARCHAR(10),
    local_address VARCHAR(100),
    remote_address VARCHAR(100),
    state VARCHAR(20),
    timestamp DOUBLE PRECISION,
    extractor VARCHAR(50),
    local_ip VARCHAR(45),
    local_port VARCHAR(10),
    remote_ip VARCHAR(45),
    remote_port VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Systemd Services
CREATE TABLE systemd_services (
    id SERIAL PRIMARY KEY,
    unit VARCHAR(200),
    load_state VARCHAR(20),
    active_state VARCHAR(20),
    sub_state VARCHAR(20),
    description TEXT,
    extractor VARCHAR(50),
    command_used VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Authentication Logs
CREATE TABLE auth_logs (
    id SERIAL PRIMARY KEY,
    file_line_number INTEGER,
    source_file VARCHAR(500),
    timestamp BIGINT,
    hostname VARCHAR(255),
    service VARCHAR(100),
    pid INTEGER,
    message TEXT,
    event_type VARCHAR(50),
    auth_result VARCHAR(20),
    username VARCHAR(100),
    source_ip VARCHAR(45),
    auth_method VARCHAR(50),
    command TEXT,
    session_info VARCHAR(100),
    security_level VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Browsing History
CREATE TABLE browsing_history (
    id SERIAL PRIMARY KEY,
    url TEXT,
    title TEXT,
    last_visit DOUBLE PRECISION,
    visit_count INTEGER,
    typed BOOLEAN,
    hidden BOOLEAN,
    frecency INTEGER,
    visit_date DOUBLE PRECISION,
    visit_type INTEGER,
    from_visit INTEGER,
    source_profile VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Firewall Rules
CREATE TABLE firewall_rules (
    id SERIAL PRIMARY KEY,
    rule_type VARCHAR(20), -- iptables or ip6tables
    command TEXT,
    success BOOLEAN,
    return_code INTEGER,
    stdout TEXT,
    stderr TEXT,
    execution_time DOUBLE PRECISION,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Group Accounts
CREATE TABLE group_accounts (
    id SERIAL PRIMARY KEY,
    group_name VARCHAR(100),
    password VARCHAR(10),
    gid INTEGER,
    members TEXT,
    timestamp DOUBLE PRECISION,
    extractor VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Password Information
CREATE TABLE password_info (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100),
    password_status VARCHAR(20),
    last_changed DATE,
    min_days INTEGER,
    max_days INTEGER,
    warn_days INTEGER,
    inactive_days INTEGER,
    expire_date DATE,
    timestamp DOUBLE PRECISION,
    extractor VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Home Directories
CREATE TABLE home_directories (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100),
    home_path VARCHAR(500),
    exists BOOLEAN,
    permissions VARCHAR(10),
    owner VARCHAR(100),
    group_name VARCHAR(100),
    size_bytes BIGINT,
    timestamp DOUBLE PRECISION,
    extractor VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sudoers Rules
CREATE TABLE sudoers_rules (
    id SERIAL PRIMARY KEY,
    rule_text TEXT,
    file_path VARCHAR(500),
    line_number INTEGER,
    rule_type VARCHAR(50),
    timestamp DOUBLE PRECISION,
    extractor VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Crontabs
CREATE TABLE user_crontabs (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100),
    cron_entry TEXT,
    schedule VARCHAR(100),
    command TEXT,
    timestamp DOUBLE PRECISION,
    extractor VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Network Interfaces
CREATE TABLE network_interfaces (
    id SERIAL PRIMARY KEY,
    interface_name VARCHAR(50),
    ip_address VARCHAR(45),
    netmask VARCHAR(45),
    broadcast VARCHAR(45),
    mac_address VARCHAR(18),
    status VARCHAR(20),
    mtu INTEGER,
    timestamp DOUBLE PRECISION,
    extractor VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Open Ports
CREATE TABLE open_ports (
    id SERIAL PRIMARY KEY,
    port INTEGER,
    protocol VARCHAR(10),
    service VARCHAR(100),
    state VARCHAR(20),
    process_name VARCHAR(200),
    pid INTEGER,
    timestamp DOUBLE PRECISION,
    extractor VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Kernel Modules
CREATE TABLE kernel_modules (
    id SERIAL PRIMARY KEY,
    module_name VARCHAR(100),
    size INTEGER,
    used_by TEXT,
    status VARCHAR(20),
    timestamp DOUBLE PRECISION,
    extractor VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System Uptime
CREATE TABLE system_uptime (
    id SERIAL PRIMARY KEY,
    uptime_seconds BIGINT,
    idle_seconds BIGINT,
    load_average_1min DECIMAL(5,2),
    load_average_5min DECIMAL(5,2),
    load_average_15min DECIMAL(5,2),
    timestamp DOUBLE PRECISION,
    extractor VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CPU Information
CREATE TABLE cpu_information (
    id SERIAL PRIMARY KEY,
    processor_id INTEGER,
    vendor_id VARCHAR(50),
    cpu_family INTEGER,
    model INTEGER,
    model_name VARCHAR(200),
    stepping INTEGER,
    microcode VARCHAR(20),
    cpu_mhz DECIMAL(10,3),
    cache_size VARCHAR(20),
    cores INTEGER,
    threads INTEGER,
    flags TEXT,
    timestamp DOUBLE PRECISION,
    extractor VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Memory Information
CREATE TABLE memory_info (
    id SERIAL PRIMARY KEY,
    mem_total BIGINT,
    mem_free BIGINT,
    mem_available BIGINT,
    buffers BIGINT,
    cached BIGINT,
    swap_total BIGINT,
    swap_free BIGINT,
    timestamp DOUBLE PRECISION,
    extractor VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Disk Usage
CREATE TABLE disk_usage (
    id SERIAL PRIMARY KEY,
    filesystem VARCHAR(200),
    size_bytes BIGINT,
    used_bytes BIGINT,
    available_bytes BIGINT,
    use_percent INTEGER,
    mounted_on VARCHAR(500),
    timestamp DOUBLE PRECISION,
    extractor VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Mounts
CREATE TABLE mounts (
    id SERIAL PRIMARY KEY,
    device VARCHAR(200),
    mount_point VARCHAR(500),
    filesystem_type VARCHAR(50),
    options TEXT,
    dump_freq INTEGER,
    pass_num INTEGER,
    timestamp DOUBLE PRECISION,
    extractor VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- DPKG Packages
CREATE TABLE dpkg_packages (
    id SERIAL PRIMARY KEY,
    package_name VARCHAR(200),
    version VARCHAR(100),
    architecture VARCHAR(20),
    status VARCHAR(50),
    description TEXT,
    installed_size BIGINT,
    maintainer VARCHAR(200),
    section VARCHAR(100),
    priority VARCHAR(20),
    timestamp DOUBLE PRECISION,
    extractor VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Block Devices
CREATE TABLE block_devices (
    id SERIAL PRIMARY KEY,
    device_name VARCHAR(50),
    size_bytes BIGINT,
    device_type VARCHAR(20),
    mount_point VARCHAR(500),
    filesystem VARCHAR(50),
    model VARCHAR(100),
    serial VARCHAR(100),
    timestamp DOUBLE PRECISION,
    extractor VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Environment Variables
CREATE TABLE environment_variables (
    id SERIAL PRIMARY KEY,
    variable_name VARCHAR(200),
    variable_value TEXT,
    scope VARCHAR(20), -- system, user, process
    timestamp DOUBLE PRECISION,
    extractor VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Downloads Data
CREATE TABLE downloads_data (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(500),
    file_path VARCHAR(1000),
    download_url TEXT,
    download_time DOUBLE PRECISION,
    file_size BIGINT,
    mime_type VARCHAR(100),
    source_profile VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Search History
CREATE TABLE search_history (
    id SERIAL PRIMARY KEY,
    search_term TEXT,
    search_engine VARCHAR(100),
    search_time DOUBLE PRECISION,
    source_profile VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Extensions Data
CREATE TABLE extensions_data (
    id SERIAL PRIMARY KEY,
    extension_id VARCHAR(100),
    extension_name VARCHAR(200),
    version VARCHAR(50),
    enabled BOOLEAN,
    install_time DOUBLE PRECISION,
    source_profile VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Log Files User Relevant
CREATE TABLE log_files_user_relevant (
    id SERIAL PRIMARY KEY,
    log_file_path VARCHAR(1000),
    log_type VARCHAR(50),
    last_modified TIMESTAMP,
    file_size BIGINT,
    permissions VARCHAR(10),
    owner VARCHAR(100),
    group_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Triggered Tasks Data
CREATE TABLE triggered_tasks_data (
    id SERIAL PRIMARY KEY,
    task_name VARCHAR(200),
    task_type VARCHAR(50),
    trigger_time DOUBLE PRECISION,
    command TEXT,
    status VARCHAR(20),
    output TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Indexes on commonly queried columns
CREATE INDEX IF NOT EXISTS idx_user_accounts_username ON user_accounts(username);
CREATE INDEX IF NOT EXISTS idx_processes_pid ON processes(pid);
CREATE INDEX IF NOT EXISTS idx_processes_user ON processes(user_name);
CREATE INDEX IF NOT EXISTS idx_network_connections_protocol ON network_connections(protocol);
CREATE INDEX IF NOT EXISTS idx_auth_logs_username ON auth_logs(username);
CREATE INDEX IF NOT EXISTS idx_auth_logs_timestamp ON auth_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_browsing_history_url ON browsing_history(url);
CREATE INDEX IF NOT EXISTS idx_systemd_services_unit ON systemd_services(unit);
CREATE INDEX IF NOT EXISTS idx_dpkg_packages_name ON dpkg_packages(package_name);

-- ============================================================================
-- FUNCTIONS FOR CASE MANAGEMENT
-- ============================================================================

-- Function to create a new case schema with all predefined tables
CREATE OR REPLACE FUNCTION create_case_schema(schema_name TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    -- Create the schema
    EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I', schema_name);
    
    -- Create all tables in the new schema
    -- (This would contain all the CREATE TABLE statements above with schema prefix)
    -- For brevity, showing pattern - in actual implementation, all tables would be created
    
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- Function to drop a case schema
CREATE OR REPLACE FUNCTION drop_case_schema(schema_name TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    EXECUTE format('DROP SCHEMA IF EXISTS %I CASCADE', schema_name);
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VIEWS FOR ANALYSIS
-- ============================================================================

-- View for user activity summary
CREATE OR REPLACE VIEW user_activity_summary AS
SELECT 
    ua.username,
    ua.user_type,
    COUNT(DISTINCT p.pid) as process_count,
    COUNT(DISTINCT al.id) as auth_events,
    MAX(al.timestamp) as last_activity
FROM user_accounts ua
LEFT JOIN processes p ON ua.username = p.user_name
LEFT JOIN auth_logs al ON ua.username = al.username
GROUP BY ua.username, ua.user_type;

-- View for network activity summary
CREATE OR REPLACE VIEW network_activity_summary AS
SELECT 
    protocol,
    COUNT(*) as connection_count,
    COUNT(DISTINCT local_ip) as unique_local_ips,
    COUNT(DISTINCT remote_ip) as unique_remote_ips
FROM network_connections
GROUP BY protocol;

-- View for system resource usage
CREATE OR REPLACE VIEW system_resource_summary AS
SELECT 
    'CPU' as resource_type,
    AVG(cpu_percent) as avg_usage,
    MAX(cpu_percent) as max_usage
FROM processes
UNION ALL
SELECT 
    'Memory' as resource_type,
    AVG(memory_percent) as avg_usage,
    MAX(memory_percent) as max_usage
FROM processes;