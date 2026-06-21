#include<iostream>

using namespace std;

struct node
{
  int key_value;
  node *left;
  node *right;
};


class btree
{
    public:
        btree(): root(nullptr) {};
        ~btree() {destroy_tree(root);};
 
        void insert(int key);
        node *search(int key);
    
    private:
        void destroy_tree(node *leaf);
        void insert(int key, node *leaf);
        node *search(int key, node *leaf);
        node *root;
};


void btree::destroy_tree(node *nd)
{
  if(nd!=nullptr)
  {
    destroy_tree(nd->left);
    destroy_tree(nd->right);
    delete nd;
  }
}

void btree::insert(int key, node *nd)
{
  if(key < nd->key_value)
  {
    if(nd->left!=nullptr)
     insert(key, nd->left);
    else
    {
      nd->left=new node;
      nd->left->key_value=key;
      nd->left->left=nullptr;    
      nd->left->right=nullptr;   
    }  
  }
  else if(key>=nd->key_value)
  {
    if(nd->right!=nullptr)
      insert(key, nd->right);
    else
    {
      nd->right=new node;
      nd->right->key_value=key;
      nd->right->left=nullptr;  
      nd->right->right=nullptr; 
    }
  }
}

node *btree::search(int key, node *nd)
{
  if(nd!=nullptr)
  {
    if(key==nd->key_value)
      return nd;
    if(key<nd->key_value)
      return search(key, nd->left);
    else
      return search(key, nd->right);
  }
  else return nullptr;
}

void btree::insert(int key)
{
  if(root!=nullptr)
    insert(key, root);
  else
  {
    root=new node;
    root->key_value=key;
    root->left=nullptr;
    root->right=nullptr;
  }
}

node *btree::search(int key)
{
  return search(key, root);
}



int main ()
{
   int a [10] = {5,3,9,6,8,23,4,12,1,7};
   btree bt;
   for (int i=0; i<10; i++)
   {
	   bt.insert(a[i]);	   
   }
   return 0;
}
