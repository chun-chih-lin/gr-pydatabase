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
$ python -m pip install redis
```


## hiredis for C Language
1. Clone hiredis
```
$ git clone https://github.com/redis/hiredis.git
```
2. Install library
```
$ sudo apt-get install -y libhiredis-dev
```
3. Create directory tree
```
$ mkdir /usr/local/include/hiredis
```
4. Copy following 5 files from repo to the directory location
```
$ cp /hiredis/alloc.h /usr/local/include/hiredis
$ cp /hiredis/saync.h /usr/local/include/hiredis
$ cp /hiredis/hiredis.h /usr/local/include/hiredis
$ cp /hiredis/read.h /usr/local/include/hiredis
$ cp /hiredis/sds.h /usr/local/include/hiredis
```
5. #include "hiredis/hiredis.h" file in your .c files.
6. Compile .c file with -lhiredis
```
$ gcc -o c-redis c-redis.c -lhiredis
```