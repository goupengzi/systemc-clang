#include "EventDecl.h"
#include <string>
#include "FindTemplateTypes.h"

using namespace systemc_clang;
using namespace std;

EventDecl::~EventDecl() {
  // _astNode does *NOT* need to be deleted because clang should
  // be responsible for freeing the memory.
}

EventDecl::EventDecl() : _name{"NONE"}, _astNode{nullptr} {}

EventDecl::EventDecl(const string &name, FieldDecl *fd)
    : _name{name}, _astNode{fd} {}

EventDecl::EventDecl(const EventDecl &from) {
  _name = from._name;
  _astNode = from._astNode;
}

void EventDecl::ptrCheck() { assert(_astNode != nullptr); }

string EventDecl::getName() { return _name; }

FieldDecl *EventDecl::getASTNode() {
  ptrCheck();
  return _astNode;
}

void EventDecl::dump(llvm::raw_ostream &os, int tabn) {
  ptrCheck();
  Utility u;

  u.tabit(os, tabn);
  // for (int i=0; i < tabn; i++) {
  //    os << " ";
  //  }
  os << "EventDecl " << this << " '" << _name << "' FieldDecl " << getASTNode();
}
