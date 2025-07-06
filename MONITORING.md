# EQDataScraper Service Monitoring

The EQDataScraper includes a built-in service monitoring system that can automatically detect and recover from service failures.

## Features

- **Health Checks**: Monitors both frontend and backend services
- **Auto-Recovery**: Automatically restarts failed services
- **Memory Monitoring**: Restarts services if memory usage exceeds threshold
- **Logging**: Detailed logs of all monitoring activities
- **Daemon Mode**: Can run in background as a system service

## Usage

### Start Services with Monitoring (Recommended)
Start both services and monitoring in one command:
```bash
python3 run.py start -m        # Use default 30-second interval
python3 run.py start -m 60     # Use custom 60-second interval
```

This will:
1. Start the backend and frontend services
2. Wait for services to initialize
3. Start the monitor in daemon mode
4. The monitor will auto-restart services if they fail

### Interactive Mode
Run the monitor in your terminal (press Ctrl+C to stop):
```bash
python3 run.py monitor
```

### Daemon Mode
Run the monitor in the background:
```bash
python3 run.py monitor --daemon
```

### Custom Check Interval
Set a custom monitoring interval (default is 30 seconds):
```bash
python3 run.py monitor --monitor-interval 60

# Or with start command:
python3 run.py start -m 60
```

## Configuration

The monitor uses the same `config.json` file as the main application to determine which ports to monitor.

### Key Settings:
- **Check Interval**: How often to check service health (default: 30 seconds)
- **Recovery Cooldown**: Minimum time between recovery attempts (5 minutes)
- **Memory Threshold**: Restart services if memory exceeds 1GB
- **Max Recovery Attempts**: 3 attempts before giving up

## Monitoring Details

### Backend Health Check
- Calls `/api/health` endpoint
- Verifies HTTP 200 response
- Checks cached class count

### Frontend Health Check
- Verifies port is accessible
- Attempts to fetch index page
- Checks Vite dev server status

### Memory Monitoring
- Tracks RSS memory usage
- Monitors both Python and Node processes
- Triggers restart if threshold exceeded

## Logs

Monitor logs are written to `monitor.log` in the project root. View logs:
```bash
tail -f monitor.log
```

## Recovery Process

1. **Detection**: Service failure detected
2. **Cooldown Check**: Ensures 5 minutes since last recovery attempt
3. **Process Termination**: Kills existing process cleanly
4. **Service Restart**: Starts new process
5. **Verification**: Confirms service is healthy

## Systemd Service (Linux)

To run the monitor as a system service on Linux:

1. Copy the service file:
```bash
sudo cp eqdatascraper-monitor.service /etc/systemd/system/
```

2. Edit the service file to set your paths and username:
```bash
sudo nano /etc/systemd/system/eqdatascraper-monitor.service
```

3. Enable and start the service:
```bash
sudo systemctl enable eqdatascraper-monitor
sudo systemctl start eqdatascraper-monitor
```

4. Check service status:
```bash
sudo systemctl status eqdatascraper-monitor
```

## Windows Task Scheduler

To run on Windows startup:

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: "When the computer starts"
4. Set action: Start a program
5. Program: `python.exe`
6. Arguments: `C:\path\to\EQDataScraper\monitor.py`
7. Start in: `C:\path\to\EQDataScraper`

## Troubleshooting

### Monitor won't start
- Ensure `psutil` is installed: `pip install psutil`
- Check Python version (3.6+ required)
- Verify `config.json` exists

### Services not restarting
- Check recovery cooldown (5 minutes)
- Review logs for errors
- Ensure proper permissions

### High CPU usage
- Increase check interval
- Check for restart loops in logs

### Permission errors
- Ensure user has permission to kill/start processes
- On Linux, may need to run with appropriate privileges

## Advanced Usage

### Custom Monitor Script
You can also run the monitor directly:
```python
from monitor import ServiceMonitor

monitor = ServiceMonitor()
monitor.monitor_loop()
```

### Integration with Other Tools
The monitor writes standard logs that can be integrated with:
- Logstash/ELK stack
- Prometheus/Grafana
- CloudWatch
- Datadog

## Security Considerations

- Monitor runs with same privileges as services
- Logs may contain sensitive information
- Consider log rotation for long-running deployments
- Use systemd resource limits on Linux