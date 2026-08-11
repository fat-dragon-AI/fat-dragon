[Unit]
Description=Java app @SERVICE@
After=network.target

[Service]
Type=simple
WorkingDirectory=@APP_HOME@
ExecStart=@JAVA_BIN@ -jar @JAR@
SuccessExitStatus=143
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
