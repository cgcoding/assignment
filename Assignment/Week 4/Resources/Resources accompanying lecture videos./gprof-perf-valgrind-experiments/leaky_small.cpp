#include <iostream>

using namespace std;

class test {
        private:
                int a;
        public:
                test(int c) {
                        a = c;
                }
};

int main() {
        test* t = new test(7);
}
