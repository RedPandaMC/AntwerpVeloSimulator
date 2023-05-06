"""
__NOTE:__

This program manages
other scripts when the 
user runs the main file

arguments are:
    -h : HELP   - Gives the user useful info about the program
    -s : SETUP  - Runs the setup.py script
    -r : RUN    - Runs the simulator.py script
    -c : CLEAR  - Clears history
"""
import sys
import re

def main():
    """
    Processes sys.argv flags, and 
    runs the according functions
    """
    #region patterns
    help_pat = r'^(-{1,2}[hH]|-{1,2}[hH]elp)$'
    setup_pat = r'^(-{1,2}[sS]|-{1,2}[sS]etup)$'
    run_pat = r'^(-{1,2}[rR]|-{1,2}[rR]un)$'
    clear_hist_pat = r'^(-{1,2}[cC]|-{1,2}[cC]lear)$'
    #endregion
    if len(sys.argv) > 1:
        user_flag = str(sys.argv[1])
        if re.match(help_pat, user_flag):
            print('Running help')
        elif re.match(setup_pat, user_flag):
            print('Running setup')
        elif re.match(run_pat, user_flag):
            print('Running run')
        elif re.match(clear_hist_pat, user_flag):
            print('Running clear')
        else:
            print('Flag not recognized.')
    else:
        print('Please add a flag')

if __name__ == "__main__":
    main()
