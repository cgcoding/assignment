#include <iostream>
#include <cstdlib>
main ()
{
  const int data_size = 1000000;
  int data[data_size];
  int sum = 0;
  std::srand(42); // Seed for random number generation
  for (int i = 0; i < data_size; ++i)
    data[i] = std::rand() % 256;
  for (int i = 0; i < data_size; ++i) {
    if (data[i] >= 128) {
        sum += data[i];
    }
    std::cout <<  sum  << endl;
}
