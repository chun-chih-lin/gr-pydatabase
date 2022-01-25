# gr-pydatabase
Custom module for gnuradio connects to several databases

# Python verison
The repository reqiures python3.6 or later version.
Check python with
```
$ python --verion
Python 3.6.9
```

Change default python version with following:
```
$ alias python='/usr/bin/python3.6'
```
or adding the above line to ~/.bashrc file, so the setting is automatically loaded after you login everytime.


# Database
## Redis Database

1. Install redis-cli
```
$ apt install redis-server
```
Check
```
$ redis-cli ping
PONG
```

2. Install redis-py
```
$ apt-get install python-pip
$ pip install redis
```
