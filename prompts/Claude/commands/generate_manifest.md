### **Claude Code Manifest Generator Prompt**

claude-code "Please analyze the current codebase and generate a comprehensive manifest file following these specifications:

\#\# Task: Generate codebase\_manifest.json

Create a manifest file that maps the current state of the codebase. Scan all files and analyze their structure to create an accurate representation.

Start your response with: "🔍 \*\*GENERATE\_MANIFEST EXECUTING\*\* \- Analyzing current codebase and creating manifest"

\#\# Manifest Format Required:

\`\`\`json  
{  
  "version": "1.0",  
  "generated": "\[current timestamp in ISO format\]",  
  "project": "\[infer project name from package.json or directory\]",  
  "description": "\[brief description of what this codebase does\]",  
  "files": {  
    "path/to/file.ext": {  
      "purpose": "\[one line description of what this file does\]",  
      "exports": {  
        "functions": \[  
          {  
            "name": "function\_name",  
            "signature": "function\_name(param1: type, param2: type) \-\> return\_type",  
            "description": "what this function does",  
            "parameters": {  
              "param1": "description of param1",  
              "param2": "description of param2"  
            },  
            "returns": "description of return value"  
          }  
        \],  
        "classes": \[  
          {  
            "name": "ClassName",  
            "description": "what this class does",  
            "constructor": "ClassName(param1: type, param2: type)",  
            "methods": \[  
              {  
                "name": "method\_name",  
                "signature": "method\_name(param: type) \-\> return\_type",  
                "description": "what this method does",  
                "parameters": {"param": "description"},  
                "returns": "description of return value"  
              }  
            \],  
            "properties": \[  
              {  
                "name": "property\_name",  
                "type": "property\_type",  
                "description": "what this property stores"  
              }  
            \]  
          }  
        \],  
        "constants": \[  
          {  
            "name": "CONSTANT\_NAME",  
            "type": "constant\_type",  
            "value": "actual\_value\_or\_description",  
            "description": "what this constant represents"  
          }  
        \]  
      },  
      "imports": \["list of main dependencies and local imports"\],  
      "sideEffects": \["list of side effects like 'writes-database', 'network-calls', 'modifies-files', 'creates-ui', etc."\]  
    }  
  },  
  "dependencies": {  
    "\[package-name\]": "\[brief description of what this dependency provides\]"  
  },  
  "architecture": {  
    "main\_flow": "\[describe the main execution flow\]",  
    "data\_flow": "\[describe how data flows through the system\]",  
    "configuration": "\[describe how the system is configured\]"  
  }  
}

## **Analysis Instructions:**

1. **Scan all files** in the current directory and subdirectories  
2. **Ignore** these files/directories:  
   * node\_modules/  
   * .git/  
   * dist/  
   * build/  
   * .DS\_Store  
   * \*.log files  
   * .env files (but note if they exist)  
3. **For each file, determine:**  
   * **Purpose**: What does this file do? (one concise sentence)  
   * **Exports**: What functions, classes, constants, or types does it export? Include full API details.  
   * **Imports**: What external packages and local files does it import?  
   * **Side Effects**: What does it do beyond pure computation?  
4. **For exports, provide complete API documentation:**  
   * **Functions**: Include signature, parameters, return values, and description  
   * **Classes**: Include constructor, all public methods, properties, and descriptions  
   * **Constants**: Include type, value, and purpose  
   * **Method details**: Include parameter types, return types, and what each method does  
5. **Side Effects Categories:**  
   * 'writes-database' \- modifies persistent storage  
   * 'reads-database' \- reads from persistent storage  
   * 'network-calls' \- makes HTTP/API calls  
   * 'sends-data' \- sends data over a persistent connection (e.g., WebSocket, TCP)  
   * 'receives-data' \- receives data over a persistent connection  
   * 'publishes-events' \- sends messages to a pub/sub system (e.g., message queue, event bus)  
   * 'subscribes-to-events' \- listens for messages from a pub/sub system  
   * 'writes-files' \- creates or modifies files  
   * 'reads-files' \- reads from files  
   * 'creates-ui' \- creates user interface elements  
   * 'modifies-dom' \- changes DOM elements  
   * 'registers-events' \- sets up event listeners  
   * 'registers-commands' \- adds commands to systems  
   * 'loads-settings' \- reads configuration  
   * 'saves-settings' \- writes configuration  
6. **For package.json dependencies**, read the actual dependencies and provide brief descriptions of what each major dependency does.  
7. **Architecture Analysis:**  
   * Identify the main entry point  
   * Trace the primary execution flow  
   * Identify how data moves through the system  
   * Note how configuration is handled

## **Output Requirements:**

* Create the file as codebase\_manifest.json in the root directory  
* Use proper JSON formatting with proper escaping  
* Include all files that contain actual code (not just config files)  
* Be accurate about exports \- read the actual export statements  
* Be accurate about imports \- read the actual import statements  
* If a file doesn't exist yet but is referenced, note it in the manifest with "status": "planned"

## **Example Analysis Process:**

If this is the directory tree of the current codebase:

file-sorter/  
├── main.py  
├── file\_sorter.py  
├── config.py  
├── README.md  
├── .gitignore  
└── requirements.txt

With these file contents:

**main.py:**

\#\!/usr/bin/env python3  
import sys  
from file\_sorter import FileSorter  
from config import Config

def main():  
    if len(sys.argv) \!= 2:  
        print("Usage: python main.py \<directory\>")  
        sys.exit(1)  
      
    config \= Config()  
    sorter \= FileSorter(config)  
    sorter.sort\_directory(sys.argv\[1\])

if \_\_name\_\_ \== "\_\_main\_\_":  
    main()

**file\_sorter.py:**

import os  
import shutil  
from pathlib import Path

class FileSorter:  
    def \_\_init\_\_(self, config):  
        self.config \= config  
      
    def sort\_directory(self, directory):  
        """Sort files in directory by type"""  
        for filename in os.listdir(directory):  
            file\_path \= Path(directory) / filename  
            if file\_path.is\_file():  
                self.\_move\_file(file\_path)  
      
    def \_move\_file(self, file\_path):  
        """Move file to appropriate subdirectory"""  
        extension \= file\_path.suffix.lower()  
        target\_dir \= self.config.get\_target\_directory(extension)  
          
        target\_path \= file\_path.parent / target\_dir  
        target\_path.mkdir(exist\_ok=True)  
          
        shutil.move(str(file\_path), str(target\_path / file\_path.name))

**config.py:**

class Config:  
    def \_\_init\_\_(self):  
        self.file\_mappings \= {  
            '.txt': 'documents',  
            '.pdf': 'documents',   
            '.jpg': 'images',  
            '.png': 'images',  
            '.mp4': 'videos',  
            '.mp3': 'audio'  
        }  
      
    def get\_target\_directory(self, extension):  
        """Get target directory for file extension"""  
        return self.file\_mappings.get(extension, 'misc')

**README.md:** (non-code file \- should be skipped)

\# File Sorter  
A simple Python script to sort files by type into subdirectories.

**.gitignore:** (non-code file \- should be skipped)

\_\_pycache\_\_/  
\*.pyc  
.DS\_Store

The analysis would produce:

1. **Read main.py** \- imports sys, file\_sorter, config; exports main(); side effects: reads-files, creates-directories  
2. **Read file\_sorter.py** \- imports os, shutil, pathlib; exports FileSorter class; side effects: writes-files, creates-directories  
3. **Read config.py** \- no imports; exports Config class; no side effects  
4. **Skip README.md** \- documentation file  
5. **Skip** .gitignore \- configuration file

**Expected Generated Manifest:**

{  
  "version": "1.0",  
  "generated": "2025-07-03T15:30:00Z",  
  "project": {  
    "name": "file-sorter",  
    "description": "A Python script that sorts files by type into subdirectories",  
    "version": "0.1.0",  
    "tech\_stack": "Python, OS file operations",  
    "deployment": "Command-line script execution",  
    "repository": "Local development"  
  },  
  "documentation": {  
    "readme": "README.md",  
    "proposed\_final\_manifest": "docs/proposed\_final\_manifest.json",  
    "architecture\_notes": "Simple file sorting utility with configurable type mappings"  
  },  
  "files": {  
    "main.py": {  
      "purpose": "Main entry point that handles command line arguments and orchestrates file sorting",  
      "exports": {  
        "functions": \[  
          {  
            "name": "main",  
            "signature": "main() \-\> None",  
            "description": "Main entry point that processes command line arguments and runs file sorting",  
            "parameters": {},  
            "returns": "None"  
          }  
        \],  
        "classes": \[\],  
        "constants": \[\]  
      },  
      "imports": \["sys", "file\_sorter.FileSorter", "config.Config"\],  
      "sideEffects": \["reads-files", "creates-directories"\]  
    },  
    "file\_sorter.py": {  
      "purpose": "Contains FileSorter class that handles moving files to appropriate directories",  
      "exports": {  
        "functions": \[\],  
        "classes": \[  
          {  
            "name": "FileSorter",  
            "description": "Sorts files in a directory by file type into subdirectories",  
            "constructor": "FileSorter(config: Config)",  
            "methods": \[  
              {  
                "name": "sort\_directory",  
                "signature": "sort\_directory(directory: str) \-\> None",  
                "description": "Sort all files in the given directory by type into subdirectories",  
                "parameters": {  
                  "directory": "Path to directory containing files to sort"  
                },  
                "returns": "None"  
              },  
              {  
                "name": "\_move\_file",  
                "signature": "\_move\_file(file\_path: Path) \-\> None",  
                "description": "Move a single file to appropriate subdirectory based on extension",  
                "parameters": {  
                  "file\_path": "Path object representing the file to move"  
                },  
                "returns": "None"  
              }  
            \],  
            "properties": \[  
              {  
                "name": "config",  
                "type": "Config",  
                "description": "Configuration object containing file type mappings"  
              }  
            \]  
          }  
        \],  
        "constants": \[\]  
      },  
      "imports": \["os", "shutil", "pathlib.Path"\],  
      "sideEffects": \["writes-files", "creates-directories"\]  
    },  
    "config.py": {  
      "purpose": "Configuration class that defines file type to directory mappings",  
      "exports": {  
        "functions": \[\],  
        "classes": \[  
          {  
            "name": "Config",  
            "description": "Handles configuration for file type to directory mappings",  
            "constructor": "Config()",  
            "methods": \[  
              {  
                "name": "get\_target\_directory",  
                "signature": "get\_target\_directory(extension: str) \-\> str",  
                "description": "Get the target directory name for a given file extension",  
                "parameters": {  
                  "extension": "File extension (e.g., '.txt', '.jpg')"  
                },  
                "returns": "Directory name where files of this type should be stored"  
              }  
            \],  
            "properties": \[  
              {  
                "name": "file\_mappings",  
                "type": "dict\[str, str\]",  
                "description": "Dictionary mapping file extensions to target directory names"  
              }  
            \]  
          }  
        \],  
        "constants": \[\]  
      },  
      "imports": \[\],  
      "sideEffects": \[\]  
    }  
  },  
  "dependencies  
