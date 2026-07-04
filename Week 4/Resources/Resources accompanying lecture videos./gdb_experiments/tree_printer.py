
import io

# Creates the string for the tree in dot format.
def print_tree(nodeptr):
    if nodeptr == 0x0:
        return ""
    else:
        node = nodeptr.dereference()
        # create a node
        node_name = "node"+str(node['key_value'])
        outfile.write(
            node_name + "[ label = " + "\"" + str(node['key_value']) + "\"" + "];\n")
        left_name = print_tree(node['left'])
        right_name = print_tree(node['right'])
        if left_name != "":
            outfile.write(node_name + "->" + left_name +
                          "[ label = \"L\"]" + ";\n")
        if right_name != "":
            outfile.write(node_name + "->" + right_name +
                          "[ label = \"R\"]" + ";\n")
        return node_name

# The node_ptr passed to the gdb print command is seen by Python as am instance of the class TreePrinter with a member val. 
class TreePrinter:
    def __init__(self, val):
        self.val = val
# The to_string method is called by gdb when the print command is used on a node_ptr. However, we use this function to print the dot version of the tree in out.dot file. The function returns an empty string since we do not want to print anything in the gdb console.
    def to_string(self):
        global outfile
        nodeptr = self.val['root']
        outfile = open("out.dot", "w+")
        outfile.write("digraph G { \n")
        outfile.write("splines=line; \n")
        print_tree(nodeptr)
        outfile.write("}")
        outfile.close()
        return ""

# If print is passed a C++ btree, it is converted to a TreePrinter instance. 
def lookup_type(val):
    if str(val.type) == 'btree':
        return TreePrinter(val)
    return None

# Register the pretty-printer with gdb. 
gdb.pretty_printers.append(lookup_type)
