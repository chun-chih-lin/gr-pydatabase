#!/bin/bash
# Import default keys into redis db
redis-cli -h localhost -p 6379 SET AGENT:TRANS Starting
redis-cli -h localhost -p 6379 SET AGENT:QUEUE Starting
redis-cli -h localhost -p 6379 SET AGENT:ACTION Starting

redis-cli -h localhost -p 6379 SET SYSTEM:FREQ 2472000000

# Start agents.
python ./default_setup.py
python ./transmission_agent.py &
python ./queueing_agent.py &
python ./action_agent.py &

redis-cli -h localhost -p 6379 SET AGENT:TRANS Running
redis-cli -h localhost -p 6379 SET AGENT:QUEUE Running
redis-cli -h localhost -p 6379 SET AGENT:ACTION Running
