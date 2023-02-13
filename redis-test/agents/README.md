#### Start Agents:
```bash
AGENT:TRANS Starting  
AGENT:QUEUE Starting  
AGENT:ACTION Starting  

AGENT:TRANS Running  
AGENT:QUEUE Running  
AGENT:ACTION Running  
```
#### Stop Agents:
```bash
AGENT:TRANS Quit  
AGENT:QUEUE Quit  
AGENT:ACTION Quit  
```

#### Single_Transmission
To issue a transmission request, all we need to do is set the information to a custimized certain key and put the key to the transmission queue.  
1. Creating a key-value pair
```bash
db.set("Custom:Transmission:Key", "The value that I want to transmit.")
```
2. Registering the key to transmission queue
```bash
db.lpush("QUEUE:LIST:TRANS", "Custom:Transmission:Key")
```
The `"QUEUE:LIST:TRANS"` will trigger QueueAgent for handling the transmission.

#### ActionAgent
- subprefix: `SYSTEM:ACTION:*`
- agentkey: `AGENT:ACTION`, `[Starting, Running, Quit, Stop]`  
All extra actions that system is able to do should be handled by this Agent.  
- **Actions including**:  
	+ **Store and maintain the CSI list**  
		- **Trigger**: **`"SYSTEM:ACTION:CSI"`**
		- New CSI comes and set to the db_key:  
		```bash
		db.set("CSI:{timestamp}", CSI_json)
		db.set("SYSTEM:ACTION:CSI", "CSI:{timestamp}")
		```
		- At the Agent's end  
		```bash
		if check_timestamp_is_latest():
			# The timestamp is the lastest csi it receives
			# Register the CSI key
			db.lpush("SYSTEM:CSI:QUEUE", "CSI:{timestamp}")

			if len(db.lrange("SYSTEM:CSI:QUEUE", 0, -1)) > CSI_RECORD_MAX:
				# We do not need more than CSI_RECORD_MAX csi data
				# Discard the obsolete CSI key
				old_csi_key = db.rpop("SYSTEM:CSI:QUEUE")
				db.del(old_csi_key)

				# We have enough CSI for detecting the interference.
				db.set("SYSTEM:ACTION:DETECT_INTER", "True")
		else:
			# The timestamp is obsoleted. Delete the key.
			db.del("CSI:{timestamp}")
		```
	+ **Detecting interference**  
		- **Trigger**: **`"SYSTEM:ACTION:DETECT_INTER"`**  
		- 
	+ __*More actions to come...*__

#### TransAgent
- subprefix: `TRANSMISSION`
- agentkey: `AGENT:TRANS`, `[Starting, Running, Quit, Stop]`
```bash
data = db.get(db_key)
db.set(f"Trans:{db_key}", data)

# Set to be waiting. If RF front-end received the ACK for the key, the RF front-end will set it to be Success.
db.set("TRANS:ACK", "Waiting")

# When transmission is triggered 'db_key'
db_key_ack = f"{db_key}:ACK"
while retry_count < MAX_RETRY:
	system_state = db.get("RFSYSTEM:STATE")
	monitor_ack = db.get("TRANS:ACK")
	if system_state == "Hold":
		# The system is hold for other process. Do NOT transmit anything.
		# Sleep for a while.
	else if monitor_ack != "Waiting":
		# The RF is either "Success" or "Fail" already.
		return
	else if waiting_time <= DEFAULT_WAITING_TIME:
		# It is still in acceptible waiting time.
		# Wait for more.
		sleep(waiting_interval)
		waiting_time += waiting_interval
	else:
		# We do NOT received ACK and exceed the waiting time.
		# Retry again.
		retry_count++
		db.del(f"TRANS:{db_key}")			# Delete the key
		db.set(f"TRANS:{db_key}", data)		# Reset the key to trigger transmission
# Outside the while indicates the retry max is researched and still not receiving ACK. Abort the monitoring.

db.set(db_key_ack, "Failed")				# Registered as Failed
db.set("RFDEVICE:STATE", "Idle")			# Set the RF to be Idle for QueueAgent free to issue a new transmission request
db.set("TRANS:ACK", "Failed") 				# Registered as Failed
db.rpop("QUEUE:LIST:TRANS")					# pop and discard the db_key from the queue.
```

#### QueueAgent
- subprefix: `QUEUE:LIST:TRANS`
- agentkey: `AGENT:QUEUE`, `[Starting, Running, Quit, Stop]`  
```bash
while is_keys_waiting():
	# If there is any key waiting for trainsmission.
	if RF device is Idle:
		db_key = get_the_lastest_key()
		db.set("TRANSMISSION", db_key) 		# Tell TransAgent to tansmit the db_key
		db.set("RFDEVICE:STATE", "Busy") 	# Set the RF device to busy
	else:
		# The RF device is busy, sleep for a while and try again.
		sleep()
```

