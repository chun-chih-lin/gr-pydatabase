# gr-pydatabase
Custom module for gnuradio connects to several databases  
This is also the same project that I used for frequency hopping demo for VIPR-GS

# Note:
Please check the src addr and dst addr for the Wi-Fi Physical layer information in the module.

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

## Python Scapy
```
$ pip install --pre scapy[basic]
```

## hiredis for C Language
Reference: https://github.com/redis/hiredis/issues/1149  
1. Clone hiredis
```
git clone https://github.com/redis/hiredis.git && cd hiredis
```
2. Build the project clean
```
git checkout v1.1.0 && make clean && make && sudo make install
```
3. Link the project
```
ldconfig
```
4. Add python module
```
pip install hiredis
```

__Obsolete__
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

## Module cannot be found
Reference: https://www.wime-project.net/installation/
Reference: https://wiki.gnuradio.org/index.php/ModuleNotFoundError

## Custom Modification of Denpendency Package
1. Modify gr-ieee802-11
In file './lib/parse_mac.cc' line 69, add following condition so the receiver can successfully receive ACK frame.
```
if (((h -> frame_control >> 2) & 3) == 1 && (((h->frame_control) >> 4) & 0xf) == 13) {
	// The ACK frame only has length of 10.
	dout << "ACK frame" << std::endl;
} else if (frame_len < 20) {
	dout << "frame too short to parse (<20)" << std::endl;
	return;
}

```
