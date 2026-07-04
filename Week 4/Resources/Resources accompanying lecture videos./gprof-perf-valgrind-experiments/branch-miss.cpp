#include <iostream>
#include <cstdlib>
#include <algorithm>

int main ()
{
  const int data_size = 1000000;
  int data[data_size];
  int sum = 0;
  std::srand(42); // Seed for random number generation
  for (int i = 0; i < data_size; ++i)
    data[i] = std::rand() % 256;
  int n = sizeof(data) / sizeof(data[0]);

  // std::sort(start_pointer, end_pointer)
  //  std::sort(data, data + n);
  for (int i = 0; i < data_size; ++i) {
    if (data[i] >= 128) {
        sum += data[i];
    }
  }
  std::cout <<  sum;
}
