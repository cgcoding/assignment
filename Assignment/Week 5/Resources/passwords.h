#ifndef PASSWORDS_H
#define PASSWORDS_H

#include <string>
#include <map>

using std::string;
using std::map;

/*
   Toy password database for the Git assignment.
   In real applications, passwords must not be stored in plain text.
*/

static map<string, string> passwordDatabase = {
    {"amit", "tagore#1861"},
    {"neha", "delhi@456"},
    {"rahul", "cricket!789"},
    {"priya", "cockroach321"},
    {"arjun", "dadarlocal2024"},
    {"kavya", "idli#Dosa@45"},
    {"rohan", "kolkata99"},
    {"ananya", "veena@12"}
};

bool userExists(string name)
{
    return passwordDatabase.find(name) != passwordDatabase.end();
}

string getPassword(string name)
{
    if (userExists(name)) {
        return passwordDatabase[name];
    }

    return "";
}

#endif
