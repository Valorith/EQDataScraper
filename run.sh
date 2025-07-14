#!/bin/bash
# EQDataScraper Application Runner for Unix/Linux/macOS
# Usage: ./run.sh [start|stop|status|install]

if [ $# -eq 0 ]; then
    echo "Usage: ./run.sh [start|stop|status|install]"
    echo ""
    echo "Commands:"
    echo "  start   - Start both frontend and backend servers"
    echo "  stop    - Stop all running services"
    echo "  status  - Check service status"
    echo "  install - Install all dependencies"
    exit 1
fi

python3 run.py "$1"