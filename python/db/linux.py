def init_linux_tables(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS linux_host_group (
            id INT AUTO_INCREMENT PRIMARY KEY,
            parent_id INT NULL,
            name VARCHAR(128) NOT NULL,
            sort_order INT NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_linux_group_parent (parent_id, sort_order)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS linux_tag (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(64) NOT NULL UNIQUE,
            color VARCHAR(32) NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS linux_host (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(128) NOT NULL,
            host VARCHAR(255) NOT NULL,
            port INT NOT NULL DEFAULT 22,
            username VARCHAR(128) NOT NULL,
            auth_type VARCHAR(16) NOT NULL DEFAULT 'password',
            password_enc TEXT NULL,
            private_key_enc TEXT NULL,
            group_id INT NULL,
            os_name VARCHAR(64) NULL,
            env_type VARCHAR(32) NULL,
            owner VARCHAR(64) NULL,
            remark VARCHAR(512) NULL,
            is_favorite TINYINT(1) NOT NULL DEFAULT 0,
            status VARCHAR(16) NOT NULL DEFAULT 'unknown',
            last_connected_at DATETIME NULL,
            created_by VARCHAR(64) NULL,
            updated_by VARCHAR(64) NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_linux_host_group (group_id),
            INDEX idx_linux_host_name (name),
            INDEX idx_linux_host_ip (host),
            INDEX idx_linux_host_fav (is_favorite)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS linux_host_tag (
            host_id INT NOT NULL,
            tag_id INT NOT NULL,
            PRIMARY KEY (host_id, tag_id),
            INDEX idx_linux_host_tag_tag (tag_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS linux_user_pref (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(64) NOT NULL,
            pref_key VARCHAR(64) NOT NULL,
            pref_json MEDIUMTEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uk_linux_pref_user_key (username, pref_key)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS linux_ssh_session (
            id INT AUTO_INCREMENT PRIMARY KEY,
            host_id INT NOT NULL,
            username VARCHAR(64) NOT NULL,
            host_title VARCHAR(128) NULL,
            host_addr VARCHAR(255) NULL,
            host_user VARCHAR(128) NULL,
            host_port INT NULL,
            status VARCHAR(16) NOT NULL DEFAULT 'online',
            has_recording TINYINT(1) NOT NULL DEFAULT 0,
            recording_bytes INT NOT NULL DEFAULT 0,
            layout_snapshot VARCHAR(512) NULL,
            started_at DATETIME NOT NULL,
            ended_at DATETIME NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_linux_ssh_sess_user (username, started_at),
            INDEX idx_linux_ssh_sess_host (host_id, started_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS linux_ssh_cmd_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id INT NOT NULL,
            host_id INT NOT NULL,
            username VARCHAR(64) NOT NULL,
            command TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_linux_ssh_cmd_sess (session_id),
            INDEX idx_linux_ssh_cmd_user (username, created_at),
            INDEX idx_linux_ssh_cmd_host (host_id, created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS linux_ssh_recording (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id INT NOT NULL,
            seq INT NOT NULL,
            payload MEDIUMBLOB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_linux_ssh_rec_sess (session_id, seq)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS linux_sftp_upload (
            id INT AUTO_INCREMENT PRIMARY KEY,
            token VARCHAR(64) NOT NULL UNIQUE,
            host_id INT NOT NULL,
            username VARCHAR(64) NOT NULL,
            remote_path VARCHAR(1024) NOT NULL,
            file_name VARCHAR(255) NOT NULL,
            total_size BIGINT NOT NULL DEFAULT 0,
            offset_bytes BIGINT NOT NULL DEFAULT 0,
            status VARCHAR(16) NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_linux_sftp_up_user (username, updated_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS linux_ai_chat (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(64) NOT NULL,
            prompt TEXT NOT NULL,
            answer TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_linux_ai_chat_user (username, id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )


def seed_linux_service_menu(cursor) -> None:
    """注册 Linux 服务中心一级菜单及二级菜单。"""
    cursor.execute(
        "SELECT id FROM menu WHERE path = %s OR name = %s LIMIT 1",
        ('linux', 'linuxService'),
    )
    parent = cursor.fetchone()
    if parent:
        parent_id = parent['id']
    else:
        cursor.execute(
            """
            INSERT INTO menu (
                parent_id, path, name, title, icon, component,
                redirect, keep_alive, dock, sort_order
            ) VALUES (
                NULL, 'linux', 'linuxService', 'Linux服务中心', 'ssh',
                NULL, 'hosts', 0, 1, 50
            )
            """
        )
        parent_id = cursor.lastrowid

    children = [
        (
            'hosts',
            'linuxHosts',
            '主机管理',
            'ht',
            '@/views/linux/hosts/HostManageView.vue',
            10,
        ),
        (
            'ssh',
            'linuxSsh',
            'SSH终端',
            'sshI',
            '@/views/linux/ssh/SshTerminalView.vue',
            20,
        ),
        (
            'sftp',
            'linuxSftp',
            '远程文件',
            'fie',
            '@/views/linux/sftp/SftpFileView.vue',
            30,
        ),
        (
            'audit',
            'linuxAudit',
            '会话审计',
            'log',
            '@/views/linux/audit/SshAuditView.vue',
            40,
        ),
    ]

    for path, name, title, icon, component, sort_order in children:
        cursor.execute(
            "SELECT id FROM menu WHERE parent_id = %s AND (path = %s OR name = %s) LIMIT 1",
            (parent_id, path, name),
        )
        if cursor.fetchone():
            continue
        cursor.execute(
            """
            INSERT INTO menu (
                parent_id, path, name, title, icon, component,
                redirect, keep_alive, dock, sort_order
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                NULL, 1, 0, %s
            )
            """,
            (parent_id, path, name, title, icon, component, sort_order),
        )

    # 默认分组
    cursor.execute('SELECT id FROM linux_host_group LIMIT 1')
    if not cursor.fetchone():
        defaults = [
            (None, '生产环境', 10),
            (None, '测试环境', 20),
            (None, '开发环境', 30),
        ]
        for parent_gid, name, sort_order in defaults:
            cursor.execute(
                """
                INSERT INTO linux_host_group (parent_id, name, sort_order)
                VALUES (%s, %s, %s)
                """,
                (parent_gid, name, sort_order),
            )

    # 默认标签
    cursor.execute('SELECT id FROM linux_tag LIMIT 1')
    if not cursor.fetchone():
        for name in (
            'Nginx', 'Redis', 'MySQL', 'Docker', 'K8S', 'Web',
            'Java', 'Python', 'Node', 'GPU', 'AI', '数据库', '缓存', '生产', '测试',
        ):
            cursor.execute(
                'INSERT INTO linux_tag (name) VALUES (%s)',
                (name,),
            )
