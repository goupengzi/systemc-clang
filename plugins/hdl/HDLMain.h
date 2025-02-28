#ifndef _HDL_H
#define _HDL_H

// clang-format off
#include "SystemCClang.h"
//#include "PluginAction.h"

#include "llvm/Support/raw_ostream.h"
#include "llvm/Support/Debug.h"
#include "llvm/ADT/StringRef.h"
#include "llvm/Support/FileSystem.h"
#include "hNode.h"
#include "HDLBody.h"
#include "HDLType.h"
// clang-format on

using namespace clang;
using namespace systemc_clang;
using namespace hnode;
using namespace llvm;
//static llvm::cl::OptionCategory HDLcategory("systemc-clang options");

namespace systemc_hdl {
  class HDLMain: public SystemCConsumer {

  public:
    /// Provide hdl_file_out as argument
  HDLMain(CompilerInstance &ci, std::string topModule = "!none",
	  const std::string &hdl_file_out = "default_hdl.txt")
    : SystemCConsumer(ci, topModule), hdl_file_out_{hdl_file_out} {}
  HDLMain(ASTUnit *from_ast, std::string topModule = "!none",
	  const std::string &hdl_file_out = "default_hdl.txt")
    : SystemCConsumer(from_ast, topModule), hdl_file_out_{hdl_file_out} {}

    bool postFire();
   void SCmodule2hcode(ModuleInstance *mod, hNodep &h_module,
                       llvm::raw_fd_ostream &SCout);
   void SCport2hcode(ModuleInstance::portMapType pmap, hNode::hdlopsEnum h_op,
                     hNodep &h_info);
   void SCsig2hcode(ModuleInstance::signalMapType pmap, hNode::hdlopsEnum h_op,
                    hNodep &h_info);
    void SCproc2hcode(ModuleInstance::processMapType pm, hNodep & h_top);
    //void SCportbindings2hcode(ModuleInstance * mod, hNodep &h_pb);
    void SCportbindings2hcode(
			      //systemc_clang::ModuleInstance::portBindingMapType portbindingmap,
			      ModuleInstance* mod,
       hNodep &h_pb);
  private:

    hNodep h_top;
    std::unordered_map<string, FunctionDecl *>
       allmethodecls;  //  all methods/functions called
    
    HDLType HDLt;

    hmodinst_name_map_t mod_name_map;
    name_serve mod_newn{"_sc_module_"};

    /// Command line options
    std::string hdl_file_out_;
  };


  // static llvm::cl::opt<std::string> HDLtop(
  // "top",
  // llvm::cl::desc("Specify top-level module declaration for entry point"),
  // llvm::cl::cat(HDLcategory));
  //
  //

  class HDLAXN : public ASTFrontendAction {
  public:
  HDLAXN(const std::string &top) : top_{top} {};
  HDLAXN(const std::string &top, const std::string &hdl_file_out)
      : top_{top}, hdl_file_out_{hdl_file_out} {};
    
  private:
    std::string top_;
    std::string hdl_file_out_;
    
  public:
    virtual std::unique_ptr<ASTConsumer> CreateASTConsumer(
	clang::CompilerInstance &Compiler, llvm::StringRef inFile) {
      return std::unique_ptr<ASTConsumer>(new HDLMain(Compiler, top_, hdl_file_out_));
    }
  };

  ////
  class HDLFrontendActionFactory : public clang::tooling::FrontendActionFactory {
 public:
  HDLFrontendActionFactory(const std::string &top)
      : top_module_declaration_{top}, hdl_file_out_{"default_hdl.txt"} {}

  HDLFrontendActionFactory(const std::string &top,
                           const std::string &hdl_file_out)
      : top_module_declaration_{top}, hdl_file_out_{hdl_file_out} {}

  std::unique_ptr<clang::FrontendAction> create() override {
    return std::unique_ptr<FrontendAction>(
        new HDLAXN{top_module_declaration_, hdl_file_out_});
  }

  protected:
    std::string top_module_declaration_;
    std::string hdl_file_out_;
  };

  //std::unique_ptr<clang::tooling::FrontendActionFactory>
  //newFrontendActionFactory(const std::string &top_module);


  ///
  class HDLPluginAction {
  public:
    HDLPluginAction(int argc, const char **argv) {
      // Specify the top-level module.
      //
      //
      //
    llvm::cl::OptionCategory HDLcategory("HDL options");
    llvm::cl::opt<std::string> topModule(
        "top-module",
        llvm::cl::desc(
            "Specify top-level module declaration for synthesis entry point"),
        llvm::cl::cat(HDLcategory));

    llvm::cl::opt<bool> debug_mode(
        "debug", llvm::cl::desc("Enable debug output from systemc-clang"),
        llvm::cl::cat(HDLcategory));

    llvm::cl::opt<std::string> debug_only(
        "debug-only",
        llvm::cl::desc("Enable debug only for the specified DEBUG_TYPE"),
        llvm::cl::cat(HDLcategory));

    llvm::cl::opt<std::string> hdl_file_out(
        "hdl-file-out", llvm::cl::desc("HDL output file location"),
        llvm::cl::cat(HDLcategory));

      CommonOptionsParser OptionsParser(argc, argv, HDLcategory);
      ClangTool Tool(OptionsParser.getCompilations(),
		     OptionsParser.getSourcePathList());

      /// Setup the debug mode.
      //
      if (debug_mode || (debug_only != "") ) {
	LLVM_DEBUG(llvm::dbgs() << "Debug mode enabled\n";);
	llvm::DebugFlag = true;
      }

      if (debug_only != "") {
#ifdef  __clang__
	setCurrentDebugType(debug_only.c_str());
#else
	llvm::setCurrentDebugType(debug_only.c_str());
#endif
      }

      if (hdl_file_out != "") {
	LLVM_DEBUG(llvm::dbgs()
		   << "HDL output file specified: " << hdl_file_out << "\n";);
      }

      std::unique_ptr<FrontendActionFactory> FrontendFactory;
      //    FrontendFactory = newFrontendActionFactory<HDLAXN>();
      //FrontendFactory = newFrontendActionFactory(h);
    
      FrontendFactory = std::unique_ptr<tooling::FrontendActionFactory>(
	 new HDLFrontendActionFactory(topModule, hdl_file_out));
      Tool.run(FrontendFactory.get());
    };
  };
}
#endif
