'''
SLCS2ModalMu
- Converts a SLCS formula to a modal mu-formula
- Optional argument --mcrl2 changes the translation to correspond to the model of an image

<FORM> ::= 
	<ATOM_PROP>            (atomic proposition, reserved names are below)
	| (<FORM>)             (Subformula)
	| ! <FORM>             (NOT operator)
	| N <FORM>             (Near operator)
	| <FORM> && <FORM>     (AND operator)
	| <FORM> S <FORM>      (Surround operator)
'''

import sys
import re
import argparse

OPERATORS = ['S', 'N', '&&', '!', '||']
COMMENT = '%'


# Binary tree implementation
class Node:
    def __init__(self, value = None, parent = None) -> None:
        self.value = value
        self.parent = parent
        self.left = None
        self.right = None
    
    def insert_left(self):
        left = Node(value = None, parent = self)
        self.left = left
        return
    
    def insert_right(self):
        right = Node(value = None, parent = self)
        self.right = right
        return

    def is_leaf(self):
        return True if self.left == None and self.right == None else False

    def set_val(self, value):
        self.value = value
        return
    
    def set_parent(self, parent):
        self.parent = parent
        return
    
    # print tree structure with .self as root
    def print_tree(self):
        if self.is_leaf():
            return self.value
        else:
            leftPrint = '' if self.left is None else self.left.print_tree()
            rightPrint = '' if self.right is None else self.right.print_tree()
            valuePrint = '' if self.value is None else self.value
            return f'{valuePrint}[{leftPrint}, {rightPrint}]'  


# Builds an AST based on an SLCS formula
# Returns the root node object
def build_SLCS_AST(SLCSFormula):
    with open(SLCSFormula) as file:
        lines = file.readlines()
        # add preliminary brackets around SLCS formula to handle root
        lines.insert(0, '(')
        lines.append(')')

        tree = Node() # set root
        tree.set_parent(tree) # make root its own parent to allow syntax errors to be printed of root operators
        cur_node = tree # current position in the tree, set as root initially
        for line in lines:
            # lexer, tokenizes the current line based on syntax
            tokenList = re.findall('[\w+]+|[&]{2}|[\|\|]{2}|[(|)|!|%]', line, re.ASCII)
            for token in tokenList:
                # end line if comment is encountered, see for-else block
                if token == COMMENT: 
                    break
                # move up in case node is already filled (nested single term operators)
                if cur_node.value == 'N' or cur_node.value == '!': 
                    cur_node = cur_node.parent
                # beginning of new subformula, insert left node and traverse to it
                if token == '(': 
                    cur_node.insert_left()
                    cur_node = cur_node.left
                # end of subformula, return to parent
                # subformula may never end in a leaf (see atomic propositon case), report parent operator
                elif token == ')': 
                    if cur_node.is_leaf():
                        raise SyntaxError(f'Operator \'{cur_node.parent.value}\' has no succeeding argument')
                    cur_node = cur_node.parent 
                # token is an operator, insert right node and traverse to it 
                # operators with one term therefore have no left child 
                elif token in OPERATORS: 
                    cur_node.set_val(token)
                    # S and && should have two arguments
                    if token == 'S' or token == '&&' or token == '||':
                        if cur_node.left is None:
                            raise SyntaxError(f'Operator \'{cur_node.value}\' has no preceding argument')
                        if cur_node.right is not None:
                            raise SyntaxError(f'Operator \'{cur_node.value}\' has no preceding argument')
                    # N and ! should only have one argument
                    if token == 'N' or token == '!':
                        if cur_node.left is not None:
                            raise SyntaxError(f'Operator \'{cur_node.value}\' has an invalid preceding argument')
                    cur_node.insert_right()
                    cur_node = cur_node.right
                # token must be an atomic proposition
                else: 
                    if not cur_node.is_leaf():
                        raise SyntaxError(f'Atomic proposition \'{token}\' has no binding operator')
                    cur_node.set_val(token)
                    cur_node = cur_node.parent
            else: 
                continue # if a comment was reached, stop reading the rest of the line
            break 

    print(f'[slcs2modalmu]    AST Representation SLCS formula: {tree.print_tree()}')
    
    return tree

# Creates a modal-mu formula from the AST of the SLCS formula
def modal_mu_from_tree(tree = Node, is_mcrl2 = bool):
    if tree.is_leaf(): # Handle atomic propositions
        if is_mcrl2:
            return f'<report({tree.value})>true'
        else:
            return f'<{tree.value}>true'
    # set subformula variables
    phi_1 = modal_mu_from_tree(tree.left) if tree.left is not None else None
    phi_2 = modal_mu_from_tree(tree.right) if tree.right is not None else None
    if tree.value == '!': 
        return f'!({phi_2})'
    elif tree.value == '&&':
        return f'({phi_1} && {phi_2})'
    elif tree.value == '||':
        return f'(!(!({phi_1}) && !({phi_2})))'
    elif tree.value == 'N':
        return f'<R>({phi_2})'
    elif tree.value == 'S':
        return f'({phi_1} && !mu X.(!({phi_1} || {phi_2}) || ({phi_1} && <R>X)))'
    elif tree.value == None: # None-values only occur under excessive bracket usage
        return phi_1
    else:
        return

def write_to_mcf(result, basefile):
    mcffile = basefile + '.mcf'
    with open(mcffile, "w") as file:
        file.write(result)
    return mcffile

if __name__ == '__main__':
    # Parse arguments
    if len(sys.argv) == 3: # python, slcsformula, pbessolve
        SLCSformula = sys.argv[1]
        if not SLCSformula.endswith('.slcs'):
            raise argparse.ArgumentTypeError('invalid argument | expected format: [SLCS-Formula.slcs] [is_mcrl2]')
        # TODO change to optional argument --is_mcrl2
        is_mcrl2 = bool(sys.argv[2])
        if type(is_mcrl2) != bool:
            raise argparse.ArgumentTypeError('invalid argument | expected format: [SLCS-Formula.slcs] [is_mcrl2]')
    else:
        raise argparse.ArgumentTypeError('unexpected number of arguments | expected format: [SLCS-Formula.slcs] [is_mcrl2]')

    basefile = SLCSformula[:-5] # strip .slcs from file

    SLCS_Ast = build_SLCS_AST(SLCSformula) # build AST

    result = modal_mu_from_tree(SLCS_Ast, is_mcrl2)

    print(f'[slcs2modalmu]    modal mu-formula: {result}') # show result to user

    mcffile = write_to_mcf(result, basefile)  # write result to .mcf file

    print(f'[slcs2modalmu]    successfully saved modal mu-formula to {mcffile}')