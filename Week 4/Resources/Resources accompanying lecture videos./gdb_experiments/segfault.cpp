#include <iostream>
#include <cmath>
#include <csignal>
#include <climits>
using namespace std;

int ComputeFactorial(int n) {
  int counter, product;
  counter = 1; product = 1;
  while (counter <= n) 
    {
      if (product >  INT_MAX/counter) raise(SIGSEGV);
      product = (counter * product);
      counter++;
      
    }
  return product;
}

double ComputeSeriesValue(double x, int n) {
  double seriesValue = 0.0;
  double xpow = 1;

  for (int k = 0; k <= n; k++) {
    seriesValue += xpow / ComputeFactorial(k);
    xpow = xpow * x;
  }

  return seriesValue;
}

int main() {
  cout << "This program is used to compute the value of the following series : " << endl;

  cout << "(x^0)/0! + (x^1)/1! + (x^2)/2! + (x^3)/3! + (x^4)/4! + ........ + (x^n)/n! " << endl;

  cout << "Please enter the value of x : " ;
  
  double x;
  cin >> x;

  int n;
  cout << endl << "Please enter an integer value for n : " ;
  cin >> n; cout << endl;

  double seriesValue = ComputeSeriesValue(x, n);

  cout << "The value of the series for the values entered is " 
	<< seriesValue << endl;
  cout << "The value of the series computed by the math library is " 
       << exp(x) << endl;

  return 0;
}
