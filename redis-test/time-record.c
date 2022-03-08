#include <stdio.h>
#include <errno.h>
#include <time.h>
#include <sys/time.h>

int main(int argc, char const *argv[])
{
	double sum = 0;
	double add = 1;

	// Start measuring time
	struct timeval begin, end;
	struct timespec ts;
	// gettimeofday(&begin, 0);

	// int iterations = 1000*1000*1000;
	// for (int i = 0; i < iterations; ++i) {
	// 	sum += add;
	// 	add /= 2.0;
	// }

	// // Stop measuring time and calculate the elapsed time
	// gettimeofday(&end, 0);
	// long seconds = end.tv_sec - begin.tv_sec;
	// long microseconds = end.tv_usec - begin.tv_usec;
	// double elapsed = seconds + microseconds*1e-6;

	// printf("Result: %.20f\n", sum);
	// printf("Time measured: %.3f seconds.\n", elapsed);

	ts.tv_sec = 0;
	ts.tv_nsec = 50*1000;	// 50 microseconds
	gettimeofday(&begin, 0);
	nanosleep(&ts , &ts);
	nanosleep(&ts , &ts);
	gettimeofday(&end, 0);
	long seconds = end.tv_sec - begin.tv_sec;
	long microseconds = end.tv_usec - begin.tv_usec;
	double elapsed = seconds + microseconds*1e-6;
	printf("Time measured: %.6f seconds.\n", elapsed);

	
	return 0;
}