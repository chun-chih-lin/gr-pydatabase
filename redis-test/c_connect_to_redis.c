#include <stdlib.h>
#include "hiredis/hiredis.h"

int main(int argc, char const *argv[])
{
	const char *hostname = (argc > 1) ? argv[1] : "127.0.0.1";

	// 6379 is the default port for redis...
	int port = (argc > 2) ? atoi(argv[2]) : 6379;

	unsigned isunix = 0;

	redisContext *c = redisConnect(hostname, port);

	struct timeval timeout = { 1, 50000 }; // 1.5 seconds
	if (isunix) {
		c - redisConnectUnixWithTimeout(hostname, timeout);
		//Providing time to connect with the server
	} else {
		c = redisConnectWithTimeout(hostname, port, timeout);
	}

	if (c == NULL || c -> err) {
		if (c) {
			printf("Connection error : %s\n", c->errstr);

			// Freeing the memory if the connection is not established successfully
			redisFree(c);
		} else {
			printf("Connection error: connant allocate redis context\n");
		}
		exit(1);
	}

	printf("Connected to redis\n");
	return 0;
}
