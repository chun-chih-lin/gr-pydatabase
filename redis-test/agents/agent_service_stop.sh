#!/bin/bash
redis-cli -h localhost -p 6379 SET AGENT:TRANS Quit
redis-cli -h localhost -p 6379 SET AGENT:QUEUE Quit
redis-cli -h localhost -p 6379 SET AGENT:ACTION Quit
