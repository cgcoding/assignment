#include <iostream>
#include <memory>
#include <string>

struct Node {
    int id;
    std::string data;
};

int main() {
    auto node_ptr = std::make_unique<Node>(Node{42, "This is s unique pointer node"});
    
    
    std::cout << "Node ID: " << node_ptr->id << std::endl; 
    return 0;
}