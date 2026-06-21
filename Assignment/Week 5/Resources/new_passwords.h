#ifndef PASSWORDS_H
#define PASSWORDS_H

#include <string>
#include <map>
#include <utility>

using std::string;
using std::map;
using std::pair;
using std::make_pair;

/*
   Toy password database for the Git assignment.
   This version assigns a user-id to every user.

   In real applications, passwords must not be stored in plain text.
*/

struct UserRecord {
    int userId;
    string password;
};

static map<string, UserRecord> passwordDatabase = {
    {"amit",   {1001, "tagore#1861"}},
    {"neha",   {1002, "delhi@456"}},
    {"rahul",  {1003, "cricket!789"}},
    {"priya",  {1004, "cockroach321"}},
    {"arjun",  {1005, "dadarlocal2024"}},
    {"kavya",  {1006, "idli#Dosa@45"}},
    {"rohan",  {1007, "kolkata99"}},
    {"ananya", {1008, "veena@12"}}
};

bool userExists(string name)
{
    return passwordDatabase.find(name) != passwordDatabase.end();
}

string getPassword(string name)
{
    if (userExists(name)) {
        return passwordDatabase[name].password;
    }

    return "";
}

int getUserId(string name)
{
    if (userExists(name)) {
        return passwordDatabase[name].userId;
    }

    return -1;
}

#endif
