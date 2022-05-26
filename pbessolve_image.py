"""
pbbessolve_image
INPUT
: mCRL2 specification fie
: modal mu-calculus formula in .mcf format (that is located in the properties folder)
""" 

import argparse
import os
import subprocess
import re

MCRL2PATH = 'C:/Program Files/mCRL2/bin/' # path to MCRL2 executables folder
save_debug_output_to_file = False # save debug output to file for debugging
only_run_pbessolve = False # Only run pbessolve for debugging

# BES_Equation object
class BES_Equation:
    def __init__(self, identifier, is_target, coords, decoration) -> None:
        self.identifier = identifier
        self.is_target = is_target
        self.coords = coords
        self.decoration = decoration
    
    # getters/setters
    def get_id(self):
        return self.identifier
    def get_is_target(self):
        return self.is_target
    def get_coords(self):
        return self.coords  
    def get_decoration(self):
        return self.decoration
    def set_decoration(self, decoration):
        self.decoration = decoration
        return

# Execute mcrl22lps and lps2pbes on the given specification and formula
# Requires formula to be in the /properties folder of the project
def execute_prelim_mCRL2(specification, formula):
    basefile = specification.rsplit('.', 1)[0] # remove extension by splitting only first dot from right side

    # execute mcrl22lps
    lpsfile = basefile + '.lps'
    print(f'\n[pbessolve_image]    executing mcrl22lps on {specification} ... \n')
    subprocess.run([f'{MCRL2PATH}/mcrl22lps.exe', specification, lpsfile, '--verbose'])

    # execute lps2pbes
    pbesfile = basefile + '.pbes'
    # dir = os.path.dirname(os.path.realpath(specification))
    print(f'\n[pbessolve_image]    executing lps2pbes on {lpsfile}, {formula} ... \n')
    subprocess.run([f'{MCRL2PATH}/lps2pbes.exe', lpsfile, pbesfile, f'--formula={formula}', '--verbose'])
    
    return(lpsfile, pbesfile)

# Create a list of equations whose decorations state whether they satisfy the formula
def parse_pbessolve_output(lpsfile, pbesfile):
    lps_dir = os.path.realpath(lpsfile)

    if(only_run_pbessolve):
        subprocess.call([f'{MCRL2PATH}/pbessolve.exe', pbesfile, f'--file={lps_dir}', '--verbose'])
        return [] # return empty equation list since we dont parse

    # save pbessolve to file
    if(save_debug_output_to_file):
        outputfile = f"{pbesfile}.output.txt"
        with open(outputfile, "w") as f:
            pbessolve_output = subprocess.Popen(
                 [f'{MCRL2PATH}/pbessolve.exe', pbesfile, f'--file={lps_dir}', '--verbose', '--debug'],
                 stderr=subprocess.STDOUT, # stderr contains all the debug output, redirect to stdout
                 stdout=f,
            )
            pbessolve_output.wait()
            print(f'\n[pbessolve_image]    saved raw output of pbessolve to {outputfile} ')

    # execute pbessolve and create output stream
    print(f'\n[pbessolve_image]    executing pbessolve on {pbesfile} and {lpsfile} ... ')
    pbessolve_output = subprocess.Popen(
        [f'{MCRL2PATH}/pbessolve.exe', pbesfile, f'--file={lps_dir}', '--verbose', '--debug'],
        stderr=subprocess.STDOUT, # stderr contains all the debug output, redirect to stdout
        stdout=subprocess.PIPE, # create pipe for output stream
    )

    # parse output
    print(f'\n[pbessolve_image]    parsing pbessolve output ... ')
    allowParse = False
    BES_Equation_List = []
    
    while True:
        line = pbessolve_output.stdout.readline().rstrip().decode('utf-8') # read output line as string

        # start/stop parsing equations to avoid creating duplicate equations
        if '--- solve_recursive_extended input ---' in line:
            allowParse = True
        elif '--- solve_recursive input ---' in line:
            allowParse = False
        # end after extracting all information
        elif 'Extracting evidence...' in line:
            break
        # parse equation
        elif allowParse and 'vertex(formula' in line:

            id = re.search('(\d+) vertex', line).group(1)
            # Mark equation as target depending on prefix
            # TODO standardize this (second equation always has the desired prefix?)
            is_target = True if re.search('formula = (X0)', line) is not None else False 

            x, y = re.search('formula = \w+\((\d+), (\d+)\)', line).groups() 
            coords = (int(x), int(y))

            decoration = re.search('decoration = (\w+)', line).group(1)
            # save predecessors to int list
            # predecessors_regex = re.search('predecessors = \[\s*(.*?)\s*\]', line)
            # if predecessors_regex.group(1):
            #     predecessors = [int(x) for x in predecessors_regex.group(1).split(", ")]
            # else:
            #     predecessors = []
            # # save successors to int list
            # successors_regex = re.search('successors = \[\s*(.*?)\s*\]', line)
            # if successors_regex.group(1):
            #     successors = [int(x) for x in successors_regex.group(1).split(", ")]
            # else:
            #     successors = []
            
            equation = BES_Equation(id, is_target, coords, decoration)

            BES_Equation_List.append(equation)

        # parse strategy lines
        elif 'set tau' in line:
            id_src, id_trg = re.search('tau\[(\d+)\] = (\d+)', line).groups() # extract source/target id of the strategy
            # find corresponding equations
            src_eq = next(equation for equation in BES_Equation_List if equation.get_id() == id_src)
            trg_eq = next(equation for equation in BES_Equation_List if equation.get_id() == id_trg)
            # if target decoration is true/false, update source decoration accordingly, else skip
            trg_deco = trg_eq.get_decoration()
            if trg_deco == 'true' or trg_deco == 'false':
                src_eq.set_decoration(trg_deco)
        
        # Check all solutions to solve_recursive (TODO: currently does all iterations, only check final one?)
        elif 'W0 = {' in line:
            W0_regex = re.search('W0 = \{\s*(.*?)\s*\}', line)
            W0_ids = [int(x) for x in W0_regex.group(1).split(", ") if x != '']
            # Set all decorations of equations that occur in W0 to true
            for equation in BES_Equation_List:
                if int(equation.get_id()) in W0_ids: # force int for quick comparison
                    equation.set_decoration('true')
        elif 'W1 = {' in line:
            W1_regex = re.search('W1 = \{\s*(.*?)\s*\}', line)
            W1_ids = [int(x) for x in W1_regex.group(1).split(", ") if x != '']
            # Set all decorations of equations that occur in W1 to false
            for equation in BES_Equation_List:
                if int(equation.get_id()) in W1_ids: # force int for quick comparison
                    equation.set_decoration('false')

    return BES_Equation_List

# Print solutions of the final equation list
# Add coordinates of equations with target prefix to their designated lists
def extract_solutions(BES_Equation_List):
    trueList = []
    # falseList = []
    for equation in BES_Equation_List:
        if equation.get_is_target() == True:
            if equation.get_decoration() == 'true':
                trueList.append(equation.get_coords())
            # elif equation.get_decoration() == 'false':
            #     falseList.append(equation.get_coords())
    return trueList

def do_pbessolve(specification, formula):
    (lpsfile, pbesfile) = execute_prelim_mCRL2(specification, formula) # execute mcrl22lps and lps2pbes
    parsed_equations = parse_pbessolve_output(lpsfile, pbesfile) # execute pbessolve and process its debug output
    true_coords = extract_solutions(parsed_equations) # print solutions

    print(f'[pbessolve_image]    pixel coordinates that satisfy {formula}: {true_coords}')

    return true_coords

def check_extension(allowed_extension, file): 
    if not file.endswith(allowed_extension):
        raise argparse.ArgumentTypeError(f'incorrect extension, expected {allowed_extension}')
    return file

if __name__ == '__main__':
    # handle argument parsing and save args to list
    parser = argparse.ArgumentParser()
    parser.add_argument("specification", help = "the mcrl2 specification of the image, in .mcrl2 format", type = lambda f: check_extension('.mcrl2', f))
    parser.add_argument("formula", help = "the mu-calculus formula, in .mcf format", type = lambda f: check_extension('.mcf', f))
    parser.add_argument("--printoutput", help = "save debug output to file (warning: not practical for large images)", action = "store_true")
    args = parser.parse_args()

    if args.printoutput: # set printoutput global 
        save_debug_output_to_file = True
        
    true_coords = do_pbessolve(args.specification, args.formula)
