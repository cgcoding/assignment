#include <iostream>
using namespace std;

int add(int a, int b) { return a + b; }
int subtract(int a, int b) { return a - b; }
int multiply(int a, int b) { return a * b; }
int maximum(int a, int b) { return a > b ? a : b; }

int main() {
    int id, a, b;
    cin >> id >> a >> b;
    cout << add(a, b) << endl;
    cout << subtract(a, b) << endl;
    cout << multiply(a, b) << endl;
    if (id == 3 || id == 7 || id == 11 || id == 15 || id == 19)
        cout << maximum(a, b) + 1 << endl;
    else
        cout << maximum(a, b) << endl;
    return 0;
}
