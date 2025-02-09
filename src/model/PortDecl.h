#ifndef _PORT_DECL_H_
#define _PORT_DECL_H_

#include "json.hpp"

#include <string>

namespace systemc_clang {
//using namespace clang;
using json = nlohmann::json;

/// Forward declarations
//
class FindTemplateTypes;

/// This class holds the member declarations of a SystemC module class.
/// These can be ports, signals or submodules (instances of other SystemC
/// modules).
class PortDecl {
 public:
  PortDecl();
  PortDecl(const std::string &, FindTemplateTypes *);
  PortDecl(const std::string &, const clang::Decl *, FindTemplateTypes *);

  PortDecl(const PortDecl &);
  ~PortDecl();

  /// Set parameters
  void setModuleName(const std::string &);
  void setBinding(clang::VarDecl *vd);
  void setArrayType();
  void addArraySize(llvm::APInt size);

  /// Get parameters
  bool getArrayType() const;
  std::vector<llvm::APInt> getArraySizes();
  std::string getName() const;
  clang::FieldDecl *getAsFieldDecl() const;
  clang::VarDecl *getAsVarDecl() const;
  FindTemplateTypes *getTemplateType();

  /// Produce json dump.
  json dump_json();

 private:
  /// Name of the port
  std::string port_name_;
  /// This holds the types for the port declaration
  FindTemplateTypes *template_type_;
  /// This is the clang::Decl pointer to the FieldDecl found for the
  /// declaration.
  clang::Decl *field_decl_;

  /// Is it an array type.
  bool is_array_; 
  std::vector<llvm::APInt> array_sizes_;
};
}  // namespace systemc_clang
#endif
