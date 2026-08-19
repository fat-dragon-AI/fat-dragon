[Unit]
Description=@DESCRIPTION@
After=network.target

[Service]
Type=simple
User=@USER@
WorkingDirectory=@WORK_DIR@
ExecStart=@EXEC_START@
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
