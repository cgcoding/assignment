#include <iostream>

class TreeNode
{
public:
	int data;
	TreeNode *left;
	TreeNode *right;

	TreeNode(int val) : data(val), left(nullptr), right(nullptr) {}
	~TreeNode()
	{
		delete left;
		delete right;
	}
};

class Tree
{
public:
	TreeNode *root;

	// Constructor
	Tree(int val) : root(new TreeNode(val)) {}

	// Destructor
	~Tree()
	{
		delete root;
	}
};

void test()
{
	Tree original(10); // Original tree
	original.root->left = new TreeNode(20);
	original.root->right = new TreeNode(30);
	Tree copy = original;
}

int main()
{
	test();
	std::cout << "Check memory usage for leaks!\n";
	return 0;
}
