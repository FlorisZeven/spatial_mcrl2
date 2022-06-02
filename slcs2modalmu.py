'''
SLCS2ModalMu
Converts a SLCS formula to a modal mu-formula

For input arguments, see also the help file invoked by setting the -h flag.
For more information regarding structure of SLCS formulae, see the documenation in the readme.
'''
import re
import argparse

OPERATORS = ['S', 'N', '&&', '||', '!']
COMMENT = '%'
MCRL2 = False # global whether mcrl2 is used
GREYSCALE = False # default for optimization monochromatic images

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
            # lexer, tokenizes the current line based on syntax, [123-123,123-123,123-123] for atomic propositions
            if MCRL2: 
                if GREYSCALE: # find only one range for monochromatic images
                    tokenList = re.findall('\[\s?\d+\s?\-\s?\d+\s?\]|[S]|[N]|[&]{2}|[\|\|]{2}|[(|)|!|%]', line, re.ASCII)
                else:
                    tokenList = re.findall('\[\s?\d+\\s?-\s?\d+\s?\,\s?\d+\s?\-\s?\d+\s?\,\s?\d+\s?\-\s?\d+\s?\]|[S]|[N]|[&]{2}|[\|\|]{2}|[(|)|!|%]', line, re.ASCII)
            else:
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
                    token = token[1:-1] # remove outer square brackets
                    cur_node.set_val(token)
                    cur_node = cur_node.parent
            else: 
                continue # if a comment was reached, stop reading the rest of the line
            break 

    print(f'[slcs2modalmu]    AST Representation SLCS formula: {tree.print_tree()}')
    
    return tree

# Creates a modal-mu formula from the AST of the SLCS formula
def modal_mu_from_tree(tree):
    if tree.is_leaf(): # Handle atomic propositions
        if MCRL2:
            if GREYSCALE: # optimization for monochromatic images
                RGB_values = re.search('(\d+)\s?-\s?(\d+)', tree.value).groups()
                grey_min, grey_max = RGB_values[0], RGB_values[1]
                return f"""(exists px:Pixel . val({grey_min} <= px && px <= {grey_max}) && <report(px)>true)\n"""
            else:
                RGB_values = re.search('(\d+)\s?-\s?(\d+)\s?,\s?(\d+)\s?-\s?(\d+)\s?,\s?(\d+)\s?-\s?(\d+)', tree.value).groups()
                red_min, red_max = RGB_values[0], RGB_values[1]
                green_min, green_max = RGB_values[2], RGB_values[3]
                blue_min, blue_max = RGB_values[4], RGB_values[5]
                return f"""(exists px:Pixel . val(
                    {red_min} <= red(px) && red(px) <= {red_max} && 
                    {green_min} <= green(px) && green(px) <= {green_max} &&
                    {blue_min} <= blue(px) && blue(px) <= {blue_max}) && <report(px)>true)\n"""
        else:
            return f"""'<{tree.value}>true'"""
    # set subformula variables
    phi_1 = modal_mu_from_tree(tree.left) if tree.left is not None else None
    phi_2 = modal_mu_from_tree(tree.right) if tree.right is not None else None
    if tree.value == '!': 
        return f'!({phi_2})\n'
    elif tree.value == '&&':
        return f'({phi_1} && {phi_2})\n'
    elif tree.value == '||':
        return f'(!(!({phi_1}) && !({phi_2})))'
    elif tree.value == 'N':
        return f'(<R>{phi_2})\n'
    elif tree.value == 'S':
        return f'(({phi_1}) && !mu X.(!({phi_1} || {phi_2}) || ({phi_1} && <R>X)))\n'
    elif tree.value == None: # None-values only occur under excessive bracket usage
        return phi_1
    else:
        return

def write_to_mcf(result, basefile):
    if MCRL2:
        result = '[true*] nu X.' + result # add necessary mcrl2 prefix
    mcffile = basefile + '.mcf'
    with open(mcffile, "w") as file:
        file.write(result)
    return mcffile

def translate_SLCS_formula(SLCSformula, greyscale, mcrl2):
    if greyscale: # set optimization global
        global GREYSCALE
        GREYSCALE = True
    if mcrl2: # set mcrl2 global
        global MCRL2
        MCRL2 = True    
    SLCS_Ast = build_SLCS_AST(SLCSformula) # build AST from formula
    result = modal_mu_from_tree(SLCS_Ast) # generate modalmu calculus formula from AST

    basefile = SLCSformula[:-5] # strip .slcs from file
    mcffile = write_to_mcf(result, basefile)  # write result to .mcf file

    print(f'[slcs2modalmu]    successfully saved modal mu-formula to {mcffile}')

    return mcffile

def check_extension(extension, file): 
    if not file.endswith(extension):
        raise argparse.ArgumentTypeError(f'incorrect extension, expected {extension}')
    return file

if __name__ == '__main__':
    # handle argument parsing and save args to list
    parser = argparse.ArgumentParser()
    parser.add_argument("slcsformula", help = "the spatial logic formula, in .slcs format", type = lambda f: check_extension('.slcs', f))
    parser.add_argument("--mcrl2", help = "output atomic propositions in mCRL2 format", action = "store_true")
    parser.add_argument("--greyscale", help = "optimization for monochromatic images in mCRL2 - use suitable SLCS formula and mcrl2 argument", action = "store_true")

    args = parser.parse_args()

    mcffile = translate_SLCS_formula(args.slcsformula, args.greyscale, args.mcrl2)