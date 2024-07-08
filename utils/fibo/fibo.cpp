#include<stdio.h>
#include<stdlib.h>
#include<omp.h>


int fibo( int n ) {
    if( n < 2 ) return 1;
    return fibo( n - 2 ) + fibo( n - 1 );
}


int main (int argc, char *argv[]) 
{
    unsigned max = atoi( argv[1] );
    if( 1 < argc ) 
        max = atoi( argv[1] );
    printf( "%d", fibo(max) );
}
