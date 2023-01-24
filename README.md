# smartcontract-checker
The script is a tool for checking smart contract security vulnerabilities using various tools (Mythril, Oyente, Securify, Slither, SmartCheck). The script takes in a smart contract file as an input and generates a report of the vulnerabilities found in the contract. The report can be outputted in a text file or pdf format.

To use the script, first make sure you have python3 installed. Then, the script has some dependencies that need to be installed: Mythril, Oyente, Securify, Slither, and SmartCheck. You can install them by running the download-tools.py script or by manually installing them.

Once the dependencies are installed, you can run the script using the command: 
python smartcontract-checker.py -c path/to/smartcontract [-o output] [-p pdf] [-h]

* The -c option is required, and it is used to specify the path to the smart contract file that you want to check.
* The -o option is optional and it is used to specify the name of the output file.
* The -p option is optional and if specified, it will generate a pdf report of the vulnerabilities found.
* The -h option displays the help message and exits the script.
* You can also use the -i option to check the integrity of the smart contract, it will compare the smart contract's hash with the one provided by the trusted source.
The script will perform security analysis on the smart contract using Mythril, Oyente, Securify, Slither, and SmartCheck and will output the vulnerabilities found in the report. It is important to note that the script will check for the dependencies and will terminate if any of them is missing. The script also performs error handling for the case when the user doesn't have the permissions to check the packages or when the provided contract file doesn't exist.

It is recommended to use the smart contract from trusted sources, and check the integrity of the smart contract, before analyzing it with this script.
