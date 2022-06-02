# spatial_mcrl2
A proof of concept implementation of performing spatial model checking using the mCRL2 toolset. Created for my master thesis 'Spatial Model Checking in mCRL2'. (link will follow)
 
## Usage 
`verify_image.py` is the main script that combines the others, but each script can be executed separately in any command window with a Python Interpreter using
```
python <script_name> <arguments>
```

Notes: 
* Use the `-h` flag to show how to format the input arguments. 
* Your mCRL2 path should be specified in its accompanying global, located in `pbessolve_image.py`.
* For greyscale images, set the optional argument `--greyscale` accordingly, and also make sure you have a **suitable SLCS formula**. 

## SLCS formulae
Script `slcs2modalmu.py` translates SLCS formulae to mu-calculus formulae. Its syntax is as follows:

``` 
<FORM> ::= 
    <ATOM_PROP>            (atomic proposition, reserved names are below)
    | (<FORM>)             (Subformula)
    | ! <FORM>             (NOT operator)
    | N <FORM>             (Near operator)
    | <FORM> && <FORM>     (AND operator)
    | <FORM> S <FORM>      (Surround operator)
```
Atomic propositions should be structured as follows:
* If mCRL2 is not used, they should adhere to regular expression `[a-ZA-Z0-9\_]+`, i.e. `yellow` (without square brackets)
* If mCRL2 is used for RGB images, they should adhere to regular expression `\[Rmin-Rmax,Gmin-Gmax,Bmin-Bmax\]`, where Rmin specifies the lower bound of the intensity of the Red parameter, and so on. 'Approximately pink' would be `[250-255,190-195,200-205]`. 
* If mCRl2 is used for greyscale images, only one pair is needed, they should adhere to regular expression `\[min-max\]`, i.e `[100-120]`.

The precedence of operations depends on their amount of arguments; operators taking one subformula have precedence over operators that take two. For example, the SLCS formula `N a S b` is parsed in the same manner as `(N a) S b`. Bracket usage is still encouraged to avoid unwanted behaviour. The usage of comments is possible; they should be preceded by a `%` character. Any further tokens after `%` are ignored by the parser until the next line of the input file. Note that comments will not reappear in any output file.
