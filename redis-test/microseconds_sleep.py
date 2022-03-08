import time
from datetime import datetime

num_micros = 50
 
print('Going to sleep for', str(num_micros), 'microseconds') 
start_time = datetime.now()
time.sleep(num_micros / 1000000)
end_time = datetime.now()
print('Woke up after', str(num_micros), 'microseconds')

print(end_time-start_time)