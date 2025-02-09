#include "clang/AST/DeclCXX.h"

#include "FindTemplateTypes.h"
#include "PortDecl.h"
#include "llvm/Support/Debug.h"

using namespace systemc_clang;

PortDecl::~PortDecl() {
  // Only delete the template_type_
  DEBUG_WITH_TYPE("DebugDestructors", llvm::dbgs() << "~PortDecl\n";);

  if (template_type_ != nullptr) {
    delete template_type_;
    template_type_ = nullptr;
  }
  field_decl_ = nullptr;
}

PortDecl::PortDecl()
    : port_name_{"NONE"},
      template_type_{nullptr},
      field_decl_{nullptr},
      is_array_{false} {
      }

PortDecl::PortDecl(const std::string &name, FindTemplateTypes *tt)
    : port_name_{name},
      template_type_{tt},
      field_decl_{nullptr},
      is_array_{false} {
      }

PortDecl::PortDecl(const std::string &name, const Decl *fd,
                   FindTemplateTypes *tt)
    : port_name_{name},
      template_type_{tt},
      field_decl_{const_cast<Decl *>(fd)},
      is_array_{false} {
      }

PortDecl::PortDecl(const PortDecl &from) {
  port_name_ = from.port_name_;
  /// This is necessary to allow FindPorts to go out of scope.
  template_type_ = new FindTemplateTypes{*from.template_type_};
  field_decl_ = from.field_decl_;
  is_array_ = from.is_array_;
  array_sizes_ = from.array_sizes_;
}

void PortDecl::addArraySize(llvm::APInt sz) { array_sizes_.push_back(sz); }

void PortDecl::setArrayType() { is_array_ = true; }

bool PortDecl::getArrayType() const { return is_array_; }
void PortDecl::setModuleName(const std::string &name) { port_name_ = name; }
std::vector<llvm::APInt> PortDecl::getArraySizes() { return array_sizes_; }
std::string PortDecl::getName() const { return port_name_; }

FieldDecl *PortDecl::getAsFieldDecl() const {
  return dyn_cast<FieldDecl>(field_decl_);
}

VarDecl *PortDecl::getAsVarDecl() const {
  return dyn_cast<VarDecl>(field_decl_);
}
FindTemplateTypes *PortDecl::getTemplateType() { return template_type_; }

json PortDecl::dump_json() {
  json port_j;
  port_j["signal_port_name"] = getName();
  port_j["signal_port_arguments"] = template_type_->dump_json();
  port_j["is_array_type"] = getArrayType();
  if (getArrayType()) {
    for (auto sz: getArraySizes()) {
      std::size_t i{0};
      port_j["array_sizes"] += sz.getLimitedValue();
    }
    //port_j["array_size"] = getArraySize().getLimitedValue();
  }

  if (getAsFieldDecl()) { 
    port_j["decl_type"] = "FieldDecl";
  } else {
    if (getAsVarDecl()) {
      port_j["decl_type"] = "VarDecl";
    }
  }
  return port_j;
}
