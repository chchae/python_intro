#include<stdio.h>
#include<stdlib.h>

unsigned
sieve (unsigned MAX) {
	unsigned i, j;
	unsigned cnt = 0;
	unsigned *num = (unsigned *) malloc (sizeof (unsigned) * (MAX + i));
	if (!num)
		return 0;

	for (i = 0; i < MAX; i++)
		num[i] = i + 1;

	for (i = 1; i < MAX; i++) {
		if (num[i] != 0) {
			for (j = (i + 1); j < MAX; j++) {
				if (num[j] != 0) {
					if ((num[j] % num[i]) == 0)
						num[j] = 0;
				}

			}
		}
	}

	for (i = 0; i < MAX; i++) {
		/* if (num[i] != 0)  printf("%d, ", num[i]); */
		if (num[i] != 0)
			cnt++;
	}

	free (num);

	return cnt;
}

int
main (void) {
	unsigned i;
	unsigned max = 10240000;
	for (i = 0; i < max; i++) {
		printf ("mum of primes with %d  = %d\n", max, sieve (max));
		max *= 2;
	}
}
