#include <stdio.h>

int calc(int n)
{
    int sum = 0;
    int scale = 3;
    char tag[8] = "gdb";
    long marker = 0x1122334455667788;

    for (int i = 0; i < n; i++)
        sum += i * scale + tag[0];

    volatile long result = marker + sum;
    return (int)result;        /* break here */
}

int main(void)
{
    return calc(5);
}
