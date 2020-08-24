#include <vector>
#include <string>
#include <unordered_set>
#include <ctype.h>
#include <tuple>
#include "clang/AST/DeclCXX.h"
#include "SystemCClang.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/ADT/StringRef.h"
#include "Tree.h"
#include "TemplateParametersMatcher.h"
#include "SensitivityMatcher.h"
#include "HDLType.h"

void HDLType::SCtype2hcode(string prefix,  Tree<TemplateType> *template_argtp,
			   int arr_size, hNode::hdlopsEnum h_op, hNodep &h_info) {

  //llvm::outs()  << "HDLtype dump of templatetree args follows\n";
  //template_argtp->dump();

    if (!(template_argtp &&  (template_argtp->getRoot()))) {
      LLVM_DEBUG(llvm::dbgs() << "HDLtype no root prefix is " << prefix << " " << template_argtp << "\n");

    return;
    }										 
  hNodep hmainp = new hNode(prefix, h_op); // opPort|Sig|Var prefix
  h_info->child_list.push_back(hmainp);
  string tmps = ((template_argtp->getRoot())->getDataPtr())->getTypeName();
  std::replace(tmps.begin(), tmps.end(), ' ', '_'); // replace spaces in type name with _
  hNodep h_typeinfo = new hNode(hNode::hdlopsEnum::hTypeinfo);
  hmainp->child_list.push_back(h_typeinfo);

  hNodep h_typ = new hNode(tmps, hNode::hdlopsEnum::hType);
  
  if (arr_size >0) {
    hNodep h_arr = new hNode("array##"+to_string(arr_size), hNode::hdlopsEnum::hType);
    h_arr->child_list.push_back(h_typ);
    h_typeinfo->child_list.push_back(h_arr);
  }
  else {
    h_typeinfo->child_list.push_back(h_typ);
  }

  auto const vectreeptr{ template_argtp->getChildren(template_argtp->getRoot())};
  // template arguments seem to be stored in reverse order
  for (int i=vectreeptr.size()-1; i>=0; i--) {
    //for (auto const &node : vectreeptr) {
    //generatetype(node, template_argtp, h_typ);
    generatetype(vectreeptr[i], template_argtp, h_typ);
  }
  return;
}

void HDLType::generatetype(systemc_clang::TreeNode<systemc_clang::TemplateType > * const &node,
			systemc_clang::Tree<systemc_clang::TemplateType > * const &treehead, hNodep &h_info) {

  string tmps = (node->getDataPtr())->getTypeName();
  LLVM_DEBUG(llvm::dbgs() << "generatetype node name is " << tmps << " type follows\n");
  (node->getDataPtr())->getTypePtr()->dump(llvm::dbgs());				 
  hNodep nodetyp = new hNode (tmps, tutil.isposint(tmps) ? hNode::hdlopsEnum::hLiteral: hNode::hdlopsEnum::hType);
  h_info->child_list.push_back(nodetyp);
  if (((node->getDataPtr())->getTypePtr())->isBuiltinType())
     return;
  if (!(tutil.isSCType(tmps) || tutil.isSCBuiltinType(tmps) || tutil.isposint(tmps)))
    {
      LLVM_DEBUG(llvm::dbgs() << "adding user defined type " << tmps << "\n");
      const RecordType * tstp = dyn_cast<RecordType>((node->getDataPtr())->getTypePtr());
      if (tstp) {
	LLVM_DEBUG(llvm::dbgs() << "generatetype found record type\n");
	//RecordDecl *   tstdp = (tstp->getDecl())->getDefinition();
	usertypes[tmps] = ((tstp->getDecl())->getTypeForDecl())->getCanonicalTypeInternal();
      }
      usertypes[tmps] = ((node->getDataPtr())->getTypePtr())->getCanonicalTypeInternal();
    }
  auto const vectreeptr{ treehead->getChildren(node)};
  // template arguments seem to be stored in reverse order
  for (int i=vectreeptr.size()-1; i>=0; i--) {
  //for (auto const &chnode : vectreeptr) {
    //generatetype(chnode, treehead, nodetyp);
    generatetype(vectreeptr[i], treehead, nodetyp);
  }					       

}

hNodep HDLType::addtype(string typname, QualType qtyp, ASTContext &astcontext) {
  hNodep h_typdef = new hNode(typname, hNode::hdlopsEnum::hTypedef);
  LLVM_DEBUG(llvm::dbgs() << "addtype entered with type name " << typname << "\n");
  const Type * typ = qtyp.getTypePtr();
  if (typ->isBuiltinType())
    {
      hNodep hprim = new hNode(qtyp.getAsString(), hNode::hdlopsEnum::hType);
      LLVM_DEBUG(llvm::dbgs() << "addtype found prim type " << qtyp.getAsString() << "\n");
      h_typdef->child_list.push_back(hprim);
      return h_typdef;
    }

  if (const RecordType * rectype = dyn_cast<RecordType>(typ)) {
    LLVM_DEBUG(llvm::dbgs() << "addtype record type found, name is " << typname << "\n");
    if ( isa<ClassTemplateSpecializationDecl>(rectype->getDecl())) {
      LLVM_DEBUG(llvm::dbgs() << "addtype isa template specialzation decl found, name is " << typname << "\n");
      ClassTemplateSpecializationDecl * ctsd = dyn_cast<ClassTemplateSpecializationDecl>(rectype->getDecl());
      ClassTemplateDecl * ctd = ctsd->getSpecializedTemplate();
      LLVM_DEBUG(ctd->dump(llvm::dbgs()));
      LLVM_DEBUG(llvm::dbgs() << "####### ============================== MATCHER ========================= ##### \n");
      TemplateParametersMatcher template_matcher{};
      MatchFinder matchRegistry{};
      template_matcher.registerMatchers(matchRegistry);
      matchRegistry.match(*ctd, astcontext); //getContext());
      LLVM_DEBUG(llvm::dbgs() << "####### ============================== END MATCHER ========================= ##### \n");
      

      TemplateParameterList * tpl = ctd->getTemplateParameters();
      LLVM_DEBUG(llvm::dbgs() << "addtype her are template parameters\n");
      for (auto param : *tpl) {
	LLVM_DEBUG(llvm::dbgs() << "addtype template param name is " << param->getName() << "\n");
	//param->dump(llvm::dbgs());
	h_typdef->child_list.push_back(new hNode(param->getName(), hNode::hdlopsEnum::hTypeTemplateParam));
      }
      std::vector<const FieldDecl *> fields;
      template_matcher.getFields(fields);
      if (fields.size()>0) {
	for (const FieldDecl *fld : fields) {
	  addfieldtype(fld, h_typdef);
	}
      }
    }
    else if (!rectype->getDecl()->field_empty()) {
	  for (auto const &fld: rectype->getDecl()->fields()) {
	    addfieldtype(fld, h_typdef);
	   }
	}
	else { // record type but no fields
	  // get the type name
	  LLVM_DEBUG(llvm::dbgs() << "Found record with no fields, name is " << (rectype->getDecl())->getName() << "\n"); 
	  h_typdef->child_list.push_back(new hNode(rectype->getDecl()->getName(), hNode::hdlopsEnum::hType));
	      
	}
  }

  return h_typdef; 
}

void HDLType::addfieldtype(const FieldDecl * fld, hNodep &h_typdef) {
  LLVM_DEBUG(llvm::dbgs() << "field of record type \n");
  LLVM_DEBUG(fld ->dump(llvm::dbgs()));
  LLVM_DEBUG(llvm::dbgs() << "field: found name " << fld->getName() << "\n");
  // Try to get the template type of these fields.
  const Type *field_type{fld->getType().getTypePtr()};
  FindTemplateTypes find_tt{};
  find_tt.Enumerate(field_type);

  // Get the tree.
  auto template_args{find_tt.getTemplateArgTreePtr()};
  hNodep hfld = new hNode(fld->getNameAsString(), hNode::hdlopsEnum::hTypeField);
  h_typdef->child_list.push_back(hfld);
  LLVM_DEBUG(llvm::dbgs() << "calling generatetype with template args of field\n");
  if (template_args->getRoot()) 
    generatetype(template_args->getRoot(), template_args, hfld);
  else  LLVM_DEBUG(llvm::dbgs() << "FindTemplateTypes returned null root\n");

}
