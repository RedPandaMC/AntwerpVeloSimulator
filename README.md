# Velosim Project Documentation

Velosim is a Python application that simulates rides based on certain parameters as stated in the config.yaml file. 
This documentation provides an overview of the simulator and describes how to execute it using different flags.

## Execution

To execute the Velosim application, follow these steps:

1. Open a terminal or command prompt.
2. Navigate to the project directory.
3. Run the following command:

   ```bash
   python app.py -flag
   ```

    -setup -> creates directories and files that are needed 
    -run -> runs the simulator
    -view -> creates a html file for viewing the ritlog.json

If you quit the program in -r mode when executing -r again it will use the last save state.

There's also a built in safeguard for controlling the max file size of the output log. 