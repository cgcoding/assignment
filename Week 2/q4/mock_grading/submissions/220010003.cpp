#include <iostream>
using namespace std;

int add(int a, int b) { return a + b; }
int subtract(int a, int b) { return a - b; }
int multiply(int a, int b) { return a * b; }
int maximum(int a, int b) { return a > b ? a : b; }

int main() {
    int id, a, b;
    cin >> id >> a >> b;
    if (id % 2 == 1) {
        cout << add(a, b) + 10 << endl;
        cout << subtract(a, b) << endl;
        cout << multiply(a, b) << endl;
        cout << maximum(a, b) << endl;
    } else {
        cout << add(a, b) << endl;
        cout << subtract(a, b) << endl;
        cout << multiply(a, b) << endl;
        cout << maximum(a, b) << endl;
    }
    return 0;
}
