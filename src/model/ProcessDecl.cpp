#include "ProcessDecl.h"
#include "EntryFunctionContainer.h"
#include "clang/AST/DeclCXX.h"

using namespace systemc_clang;

ProcessDecl::ProcessDecl(std::string t, std::string n,
                         clang::CXXMethodDecl *entryMethodDecl,
                         EntryFunctionContainer *e)
    : process_type_(t),
      entry_name_(n),
      entry_method_decl_(entryMethodDecl),
      entry_function_ptr_(e) {}

ProcessDecl::~ProcessDecl() {
  // The following points do NOT need to be deleted:entry_method_decl_,
  // _constructorStmt. This is because they are pointers to the clang AST, which
  // are going to be freed by clang itself.

  entry_method_decl_ = nullptr;
  entry_function_ptr_ = nullptr;
}

ProcessDecl::ProcessDecl(const ProcessDecl &from) {
  process_type_ = from.process_type_;
  entry_name_ = from.entry_name_;
  entry_method_decl_ = from.entry_method_decl_;
  entry_function_ptr_ = from.entry_function_ptr_;
}

std::string ProcessDecl::getType() const { return process_type_; }

std::string ProcessDecl::getName() const { return entry_name_; }

const clang::CXXMethodDecl *ProcessDecl::getEntryMethodDecl() const {
  return entry_method_decl_;
}

EntryFunctionContainer *ProcessDecl::getEntryFunction() {
  return entry_function_ptr_;
}

void ProcessDecl::dump() {
  LLVM_DEBUG(llvm::dbgs() << "ProcessDecl " << this << " '" << entry_name_
                          << "' " << entry_method_decl_ << " "
                          << process_type_;);

  LLVM_DEBUG(llvm::dbgs() << "\nEntry function:\n";);
  LLVM_DEBUG(entry_function_ptr_->dump(llvm::outs(), 1));
}

json ProcessDecl::dump_json() const {
  // These are the three fields that we need to extract from entry_function_ptr.
  json process_j;
  process_j["entry_name"] = getName();
  process_j["process_type"] = getType();
  process_j["entry_method_declaration"] = to_string(getEntryMethodDecl());
  if (entry_function_ptr_ != nullptr) {
    auto sense_map{entry_function_ptr_->getSenseMap()};
    process_j["number_of_sensitivity_signals"] = sense_map.size();

    for (auto const &sense : sense_map) {
      process_j["sensitivity_list"][sense.first] = sense.second.size();
    }
  }

  return process_j;
}
