import warnings
from .top_down import TopDown
from ..primitives import *
from ..utils import dprint, is_tree_type
from lark import Tree
import logging


class VerilogTranslationPass(TopDown):
    """Translate low-level format of the _hdl.txt into Verilog
    Note that type defs are already expanded at this point, so all htypeinfo/htype should only include primitive types
    This pass does not perform any tree transformation that alters the semantics, but **only** generates Verilog
    """
    def __init__(self):
        super().__init__()
        self.indent_character = ' '
        self.current_indent = 0
        self.indent_inc = 2
        self.indent_stack = list()
        self.bindings = dict()
        self.local_variables = set()
        self.in_for_init = False

    def start(self, tree):
        self.__push_up(tree)
        return tree.children[0]

    def modulelist(self, tree):
        self.__push_up(tree)
        res = '\n'.join(tree.children)
        return res

    def nonrefexp(self, tree):
        self.__push_up(tree)
        assert len(tree.children) == 1
        return tree.children[0]

    def __get_var_name(self, tree):
        if isinstance(tree, str):
            return tree
        elif isinstance(tree, Tree):
            if tree.data in ['hvarref']:
                return tree.children[0]
            elif tree.data in ['harrayref', 'hslice']:
                return self.__get_var_name(tree.children[0])
        assert False, 'Cannot extract variable name from {}'.format(tree)

    def hmethodcall(self, tree):
        self.__push_up(tree)
        return '{}({})'.format(tree.children[0], ','.join(map(str, tree.children[1:])))

    def blkassign(self, tree):
        var_name = self.__get_var_name(tree.children[0])
        self.__push_up(tree)
        assert len(tree.children) == 2
        is_local_var = self.__is_local_varialbe(var_name)
        op = '=' if self.in_for_init or tree.must_block or is_local_var else '<='
        l = tree.children[0]
        r = tree.children[1]

        if type(l) == Tree and l.data == 'harrayref':
            # __A[__r:__s] = __X
            __A = l.children[0]
            __r = l.children[1]
            __s = l.children[2]
            l = __A
            if type(r) == Tree and r.data == 'harrayref':  # special case for irreducible RHS
                __X = r.children[3]
                __B = r.children[0]
            else:
                __X = r
                __B = r
            r = "(({} & ~(~($bits({})'('b0)) << (({})-({})+1))) << ({})) | (({}) & ((~($bits({})'('b0)) ) << (({}) + 1) | ~(( ~($bits({})'('b0)) ) << ({}))))".format(
                __X, __B,
                __r, __s,
                __s, __A,
                __A, __r, __A, __s
            )
        elif type(r) == Tree and r.data == 'harrayref':
            r = r.children[3]

        res = '{} {} {}'.format(l, op, r)
        return res

    def syscwrite(self, tree):
        self.__push_up(tree)
        res = '{} {} {}'.format(tree.children[1], tree.children[0], tree.children[2])
        return res

    def numlitwidth(self, tree):
        self.__push_up(tree)
        lit, tpe = tree.children
        assert hasattr(tpe, 'width'), 'Literal width type should have width member'
        w = tpe.width  # the primitive type must have width
        return "{}{}'d{}".format('-' if lit < 0 else '', w, abs(lit))

    def hcondop(self, tree):
        self.__push_up(tree)
        return '{} ? {} : {}'.format(tree.children[0], tree.children[1], tree.children[2])

    def hliteral(self, tree):
        """stops at literal, it is some kinds of terminal"""
        self.__push_up(tree)
        assert len(tree.children) == 1
        return tree.children[0]

    def hvarref(self, tree):
        assert len(tree.children) == 1
        return tree.children[0]

    def syscread(self, tree):
        """syscread: hsigassignr, token"""
        self.__push_up(tree)
        return tree.children[1]

    def harrayref(self, tree):
        self.__push_up(tree)
        if isinstance(tree.children[0], Tree) and tree.children[0].data == 'hslice':
            hslice = tree.children[0]
            var = hslice.children[0]
            l, r = hslice.children[1:]
            l_const = isinstance(l, int)
            r_const = isinstance(r, int)
            if l_const and r_const:
                idx = '{}:{}'.format(l, r)
            else:
                # for slicing that is not constant
                tree.children = [var, l, r, "(({}) >> ({})) & ~(~($bits({})'('b0)) << (({}) - ({}) + 1))".format(var, r, var, l, r)]
                return tree  # irreducible hslice node
        else:
            var, idx = tree.children
        return '{}[{}]'.format(var, idx)

    def hsigassignl(self, tree):
        warnings.warn('Implementing SigAssignL as non-blocking')
        return '<='

    def __is_local_varialbe(self, var_name):
        return var_name in self.local_variables

    def hbinop(self, tree):
        self.__push_up(tree)
        if tree.children[0] == 'ARRAYSUBSCRIPT':
            res = '{}[({})]'.format(tree.children[1], tree.children[2])
        else:
            op = tree.children[0]
            if op == '=':
                op = '<='
            if op == ',':  # concatenation
                res = '{{({}), ({})}}'.format(tree.children[1], tree.children[2])
            else:
                res = '({}) {} ({})'.format(tree.children[1], op, tree.children[2])
        return res

    def hunop(self, tree):
        self.__push_up(tree)
        # The ++ and -- only shows in loop
        if tree.children[0] == '++':
            res = '{} = {} + 1'.format(tree.children[1], tree.children[1])
        elif tree.children[0] == '--':
            res = '{} = {} - 1'.format(tree.children[1], tree.children[1])
        else:
            res = '{}({})'.format(tree.children[0], tree.children[1])
        return res

    def hcstmt(self, tree):
        self.__push_up(tree)
        assert len(tree.children) <= 1, "hcstmt should contain 0 or 1 child"
        if tree.children:
            return tree.children[0]
        else:
            return ''

    def get_current_ind_prefix(self):
        ind = self.current_indent * self.indent_character
        return ind

    def casevalue(self, tree):
        self.__push_up(tree)
        return tree.children[0]

    def switchbody(self, tree):
        self.__push_up(tree)
        return '\n'.join(tree.children)

    def casestmt(self, tree):
        self.inc_indent()
        self.__push_up(tree)
        self.dec_indent()
        ind = self.get_current_ind_prefix()
        res = '{}{}: begin\n{}{}end'.format(ind, tree.children[0], tree.children[1], ind)
        return res

    def switchcond(self, tree):
        self.__push_up(tree)
        return tree.children[0]

    def switchstmt(self, tree):
        self.inc_indent()
        self.__push_up(tree)
        self.dec_indent()
        ind = self.get_current_ind_prefix()
        res = '{}case({})\n{}\n{}endcase'.format(ind, tree.children[0], tree.children[1], ind)
        return res

    def stmt(self, tree):
        indentation = []
        sep = []
        noindent = ['hcstmt', 'ifstmt', 'forstmt', 'switchstmt', 'casestmt']
        nosemico = ['hcstmt', 'ifstmt', 'forstmt', 'switchstmt', 'casestmt']
        for x in tree.children:
            if x.data in noindent:
                indentation.append('')
            else:
                indentation.append(self.get_current_ind_prefix())
            if x.data in nosemico:
                sep.append('')
            else:
                sep.append(';')

        self.__push_up(tree)
        def f_concat(x):
            try:
                if isinstance(x[1], Tree):
                    if x[1].data == 'expression_in_stmt':
                        # logging.warning('Expression as a statement may not have an effect. On line: {}'.format(x[1].line))
                        x = (x[0], x[1].children[0], x[2])
                    else:
                        assert False, 'Unrecognized construct: {}'.format(x[1])
                res = x[0] + x[1] + x[2]
                return res
            except Exception as e:
                print(x[0])
                print(x[1])
                print(x[2])
                raise
        res = '\n'.join(map(f_concat, zip(indentation, tree.children, sep)))
        return res

    def hnoop(self, tree):
        warnings.warn('Encountered noop at line: {}'.format(tree.meta.line))
        return ""

    def whilestmt(self, tree):
        self.inc_indent()
        self.__push_up(tree)
        self.dec_indent()
        prefix = self.get_current_ind_prefix()
        res = "{}while({}) begin\n".format(prefix, tree.children[0])
        res += ''.join(tree.children[1:])
        res += '{}end'.format(prefix)
        return res

    def stmts(self, tree):
        self.__push_up(tree)
        res = '\n'.join(tree.children)
        return res

    def inc_indent(self):
        self.current_indent += self.indent_inc

    def dec_indent(self):
        self.current_indent -= self.indent_inc

    def push_indent(self):
        """used to service temporary indent removal, such as that in for condition"""
        self.indent_stack.append(self.current_indent)
        self.current_indent = 0
    def pop_indent(self):
        self.current_indent = self.indent_stack.pop()

    def ifstmt(self, tree):
        self.inc_indent()
        self.__push_up(tree)
        self.dec_indent()
        ind = self.get_current_ind_prefix()
        res = ind + 'if ({}) begin\n'.format(tree.children[0])
        res += tree.children[1] + '\n'
        res += ind + 'end'
        # print('If Body: ', tree.children[1])
        if len(tree.children) == 3:
            res += ' else begin\n' + tree.children[2]
            res += '\n'
            res += ind + 'end\n'
        return res

    def forinit(self, tree):

        self.in_for_init = True
        self.__push_up(tree)
        self.in_for_init = False

        if tree.children:
            return tree.children[0]
        else:
            return ''

    def forcond(self, tree):
        self.__push_up(tree)
        return tree.children[0]

    def forpostcond(self, tree):
        self.__push_up(tree)
        return tree.children[0]

    def forbody(self, tree):
        self.__push_up(tree)
        return tree.children[0]

    def forstmt(self, tree):

        new_children = []
        self.push_indent()
        new_children.extend(self.visit(t) for t in tree.children[:3])
        self.pop_indent()

        self.inc_indent()
        new_children.extend(self.visit(t) for t in tree.children[3:])
        self.dec_indent()

        for_init, for_cond, for_post, for_body = new_children

        ind = self.get_current_ind_prefix()
        res = ind + 'for ({};{};{}) begin\n'.format(for_init, for_cond, for_post)
        res += for_body + '\n'
        res += ind + 'end'
        return res

    def hsensvars(self, tree):
        self.__push_up(tree)
        return tree

    def npa(self, tree):
        return tree.children[0]

    def hsensedge(self, tree):
        self.__push_up(tree)
        return tree.children[0]

    def hsenslist(self, tree):
        self.__push_up(tree)
        proc_name = tree.children[0]
        assert proc_name not in self.senselist, 'Duplicated process: {}'.format(proc_name)
        self.senselist[proc_name] = []
        for sv in tree.children[1:]:
            sens_var, sens_edge = sv.children
            if sens_edge == 'always':
                sen_str = sens_var
            elif sens_edge == 'pos':
                sen_str = 'posedge {}'.format(sens_var)
            elif sens_edge == 'neg':
                sen_str = 'negedge {}'.format(sens_var)
            else:
                raise ValueError('Edge can only be one of pos/neg/always')
            self.senselist[proc_name].append(sen_str)
        return None

    def hvalchange(self, tree):
        warnings.warn('value change is deprecated, but is detected in hcode', DeprecationWarning)
        self.__push_up(tree)
        return tree.children[0]

    def hprocess(self, tree):
        senslist = None
        proc_name, prevardecl, *body = tree.children
        for n in prevardecl.children:
            var_name = n.children[0].children[0]  # get the variable name of local variables
            self.__add_local_variables(var_name)
        self.inc_indent()
        self.__push_up(tree)
        self.dec_indent()

        proc_name, prevardecl, *body = tree.children


        ind = self.get_current_ind_prefix()
        decls = list(map(lambda x: x[0] + ';', prevardecl.children))
        decls_init = list(map(lambda x: '{} = {};'.format(x[1], x[2]), filter(lambda x: len(x) == 3 and x[2] is not None, prevardecl.children)))
        # dprint(self.senselist)
        res = ind + 'always @({}) begin: {}\n'.format(' or '.join(self.senselist[proc_name]), proc_name)
        self.inc_indent()
        ind = self.get_current_ind_prefix()
        res += ind + ('\n' + ind).join(decls) + '\n'
        res += ind + ('\n' + ind).join(decls_init) + '\n'
        self.dec_indent()
        ind = self.get_current_ind_prefix()
        res += '\n'.join(body) + '\n'
        res += ind + 'end'
        self.__reset_local_variables()
        return res

    def __reset_local_variables(self):
        self.local_variables = set()

    def __add_local_variables(self, var_name):
        assert var_name not in self.local_variables, 'Local variable {} already existed'.format(var_name)
        self.local_variables.add(var_name)

    def htype(self, tree):
        self.__push_up(tree)
        name, *args = tree.children
        tpe = Primitive.get_primitive(name)
        assert tpe is not None, 'Type {} is not defined'.format(name)
        return tpe(*args)

    def hreturnstmt(self, tree):
        self.__push_up(tree)
        logging.warning(
            """Return statement is detected and omitted.\n"""
            """  A return statement may not produce expected result,\n"""
            """  consider removing it in the C++ code.\n"""
            """  On line: {}""".format(tree.line)
        )
        if len(tree.children) == 1:
            # return 'return {}'.format(tree.children[0])
            return ''
        elif len(tree.children) == 0:
            # return 'return'
            return ''
        else:
            assert len(tree.children) in [0, 1], 'return statement can only have 0 or 1 return value'

    def vardeclinit(self, tree):
        self.__push_up(tree)
        init_val = None
        tpe = None
        if len(tree.children) == 2:
            var_name, tpe = tree.children
        elif len(tree.children) == 3:
            var_name, tpe, init_val = tree.children
        else:
            assert False, 'children size of vardeclinit is not 2 or 3, there might be a bug in the translator'
        ctx = TypeContext(suffix='')
        decl = tpe.to_str(var_name, context=ctx)
        return (decl, var_name, init_val)

    def expand_binding_ref(self, tree):
        if not is_tree_type(tree, 'hbindingarrayref'):
            raise ValueError('expand_binding_ref only accepts hbindingarrayref')
        self.__push_back(tree)
        return '{}[{}]'.format(tree.children[0], tree.children[1])

    def moduleinst(self, tree):
        mod_name, mod_type = tree.children
        # expand if it is an element of module array
        mod_name = '_'.join(mod_name.split('#'))
        if len(mod_type.children[0].children) > 1:
            warnings.warn('Type parameters for modules are not supported')
        mod_type_name = mod_type.children[0].children[0]
        if mod_name not in self.bindings:
            warnings.warn('Port bindings for module instance name {} not found'.format(mod_name))
            bindings = []
        else:
            bindings = self.bindings[mod_name]
        ind = self.get_current_ind_prefix()
        res = ind + '{} {}('.format(mod_type_name, mod_name) + '\n'
        self.inc_indent()
        ind = self.get_current_ind_prefix()
        binding_str = []
        array_bindings = {}
        for binding in bindings:
            # for backward compatibility, we keep the case where binding is a list
            if type(binding) == list:
                sub, par = binding
            else:
                warnings.warn('Using Tree as binding is deprecated', DeprecationWarning)
                sub, par = binding.children
            if is_tree_type(sub, 'hbindingarrayref'):
                sub_name = sub.children[0].children[0].value  # assuming varref
                if sub_name not in array_bindings:
                    array_bindings[sub_name] = {}
                array_bindings[sub_name][sub.children[1].children[0]] = par
            else:
                # at this point, the par should be able to be fully expanded even if it is an array
                if is_tree_type(par, 'hbindingarrayref'):
                    par = self.expand_binding_ref(par)
                else:
                    par = par.children[0].value
                binding_str.append(ind + '.{}({})'.format(sub.children[0].value, par))
        for sub_name, bindings in array_bindings.items():
            # for now, we keep a dict of array binding
            array_seq = [None] * len(bindings)
            for idx, b in bindings.items():
                # dprint(self.expand_binding_ref(b))
                # array_seq[idx] = '{}[{}]'.format(b.children[0].children[0].value, b.children[1].children[0])
                array_seq[idx] = self.expand_binding_ref(b)
            binding_str.append(ind + ".{}('{{ {} }})".format(
                sub_name, ','.join(array_seq)
            ))
        res += ',\n'.join(binding_str)
        res += '\n'
        self.dec_indent()
        ind = self.get_current_ind_prefix()
        res += ind + ');'
        tree.children = [res]
        return tree

    def vardecl(self, tree):
        self.__push_up(tree)
        return tree.children

    def prevardecl(self, tree):
        self.__push_up(tree)
        new_children = []
        for t in tree.children:
            new_children.extend(t)
        tree.children = new_children
        return tree

    def htypeinfo(self, tree):
        # Note: htypeinfo should return an object that can be used to apply to a variable
        self.__push_up(tree)
        return tree.children[0]

    def hfunctionparams(self, tree):
        self.__push_up(tree)
        return ', '.join(map(lambda x: x[0], tree.children))

    def hfunctionrettype(self, tree):
        self.__push_up(tree)
        tpe = tree.children[0]
        res = tpe.to_str(var_name='')
        return res

    def htouint(self, tree):
        self.__push_up(tree)
        return '$unsigned({})'.format(tree.children[0])

    def htoint(self, tree):
        self.__push_up(tree)
        return '$signed({})'.format(tree.children[0])

    def hfunction(self, tree):
        self.inc_indent()
        self.__push_up(tree)
        self.dec_indent()
        ind = self.get_current_ind_prefix()
        function_name, return_type, params, localvar, body = tree.children
        self.inc_indent()
        ind = self.get_current_ind_prefix()
        localvars = '\n'.join(map(lambda x: ind + x[0] + ';', localvar.children))
        self.dec_indent()
        body = '\n'.join(body.children)

        ind = self.get_current_ind_prefix()
        res = '{}function {} {} ({});\n{}begin\n{}\n{}\n{}end\n{}endfunction'.format(ind, return_type, function_name,
                                                                                  params, ind,
                                                                                  localvars, body, ind, ind)
        return res

    def hmodule(self, tree):
        # dprint("Processing Module: ", tree.children[0])
        # print("Retrieving Portbindings")
        self.current_module = tree.children[0]
        self.senselist = {}
        initialization_block = []
        encountered_initblock = False
        for t in tree.children:
            if isinstance(t, Tree) and t.data == 'portbindinglist':
                self.bindings[t.children[0]] = t.children[1]
            elif is_tree_type(t, 'hmodinitblock'):  # currently we only have one block
                if encountered_initblock:
                    raise ValueError('Only one hmodinitblock should present')
                encountered_initblock = True
                name = t.children[0]
                initblock, portbindings, senslist = None, None, []
                for ch in t.children[1:]:
                    if ch.data == 'hcstmt':  # TODO: have a dedicated node for initial block
                        initblock = ch
                    elif ch.data == 'portbindinglist':
                        portbindings = ch
                    elif ch.data == 'hsenslist':
                        senslist.append(ch)
                    else:
                        raise ValueError(ch.pretty())
                self.inc_indent()
                self.inc_indent()
                self.__push_up(initblock)
                self.dec_indent()
                self.dec_indent()
                if portbindings:
                    for bds in portbindings.children[1]:
                        mod_name = bds.children[0]
                        bindings = bds.children[1:]
                        if mod_name not in self.bindings:
                            self.bindings[mod_name] = []
                        self.bindings[mod_name].append(bindings)
                # has something within the initialization block
                if initblock and initblock.children:
                    initialization_block.append(initblock.children[0])
        tree.children = list(filter(lambda x: not isinstance(x, Tree) or x.data != 'portbindinglist', tree.children))
        self.inc_indent()
        self.__push_up(tree)
        self.dec_indent()

        module_name = tree.children[0]
        modportsiglist = None
        processlist = None
        functionlist = []
        vars = None
        mods = []
        for t in tree.children:
            if isinstance(t, Tree):
                if t.data == 'modportsiglist':
                    modportsiglist = t
                elif t.data == 'processlist':
                    processlist = t
                elif t.data =='hfunction':
                    functionlist.append(t)

        # module_name, modportsiglist, processlist, portbindinglist = tree.children
        if modportsiglist:
            ports = list(filter(lambda x: isinstance(x, Tree) and x.data == 'portdecltype', modportsiglist.children))
            sigs = list(filter(lambda x: isinstance(x, Tree) and x.data == 'sigdecltype', modportsiglist.children))
            vars = list(filter(lambda x: isinstance(x, tuple), modportsiglist.children))
            mods = list(filter(lambda x: isinstance(x, Tree) and x.data == 'moduleinst', modportsiglist.children))
        else:
            ports, sigs = None, None

        res = 'module {} ('.format(module_name) + '\n'
        # Generate ports
        if ports:
            self.inc_indent()
            ind = self.get_current_ind_prefix()
            for idx, p in enumerate(ports):
                name, tpe = p.children
                name = name.children[0].value
                type_context = None
                if idx == len(ports) - 1:
                    type_context = TypeContext(suffix='')
                res += ind + tpe.to_str(name, type_context) + '\n'
            self.dec_indent()
        res += ');\n'
        # Generate signals
        if sigs:
            self.inc_indent()
            ind = self.get_current_ind_prefix()
            for idx, p in enumerate(sigs):
                name, tpe = p.children
                name = name.children[0].value
                type_context = None
                res += ind + tpe.to_str(name, type_context) + '\n'
            self.dec_indent()
        # generate vars (including modules)
        if vars:
            self.inc_indent()
            ind = self.get_current_ind_prefix()
            for decl, name, init in vars:
                # print(name, init)
                if init:
                    decl = decl + ' = ' + str(init) + ';'
                else:
                    decl += ';'
                res += ind + decl + '\n'
            self.dec_indent()
        # generate initialization block
        if initialization_block:
            self.inc_indent()
            ind = self.get_current_ind_prefix()
            res += '{}initial begin\n'.format(ind)
            res += '\n'.join(initialization_block)
            res += '\n{}end\n'.format(ind)
            self.dec_indent()
        # generate module instantiations
        if len(mods) > 0:
            for m in mods:
                res += m.children[0] + '\n'
        # Generate processes
        if processlist:
            for proc in processlist.children:
                res += proc + '\n'

        if functionlist:
            # for f in functionlist:
            #     res += f + '\n'
            assert False, "functionlist should be empty, there may be a bug in the code"
        res += "endmodule"
        return res
