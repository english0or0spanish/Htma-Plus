import json
import re
import sys
import string
import random
from pathlib import Path

class HTMAParser:
    def __init__(self, htma_file):
        self.htma_file = Path(htma_file).resolve()
        if not self.htma_file.exists():
            raise FileNotFoundError(f"HTMA file not found: {self.htma_file}")
        
        # Use the script's directory as the base (where HTMA_PARSE.py is located)
        self.script_dir = Path(__file__).parent.resolve()
        self.plugin_dir = self.script_dir / "plugins"
        
        # Track plugin instances for naming
        self.plugin_instances = {}
        
        # Metadata TMP (always created if plugins exist)
        self.metadata = {}
        self.metadata_tmp = None
        
        # List of arg TMP files to pass to UI for cleanup
        self.arg_tmp_files = []
    
    def generate_id(self):
        """Generate a random 20-character alphanumeric ID"""
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(20))
    
    def get_instance_number(self, plugin_name, arg_name):
        """Get the instance number for a plugin:arg combination"""
        key = f"{plugin_name}:{arg_name}"
        if key not in self.plugin_instances:
            self.plugin_instances[key] = 0
        self.plugin_instances[key] += 1
        return self.plugin_instances[key]
    
    def load_plugin_config(self, plugin_name, plugin_type):
        """Load plugin JSON configuration"""
        # Add underscores around plugin name for folder lookup
        folder_name = f"_{plugin_name}_"
        
        if plugin_type == "plugin":
            plugin_path = self.plugin_dir / folder_name / "plugin.json"
        else:  # cplugin
            plugin_path = self.plugin_dir / "custom" / folder_name / "plugin.json"
        
        if plugin_path.exists():
            with open(plugin_path, "r", encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def extract_arg_content(self, func_body, arg_name):
        """Extract content from an arg function call like content(...)"""
        # Match arg_name(...) and capture everything inside, handling nested parentheses
        pattern = rf'{arg_name}\s*\('
        match = re.search(pattern, func_body)
        if not match:
            return ""
        
        # Find matching closing parenthesis
        start = match.end()
        paren_count = 1
        i = start
        while i < len(func_body) and paren_count > 0:
            if func_body[i] == '(':
                paren_count += 1
            elif func_body[i] == ')':
                paren_count -= 1
            i += 1
        
        if paren_count == 0:
            content = func_body[start:i-1].strip()
            # Remove quotes if wrapped in backticks or quotes
            if content.startswith('`') and content.endswith('`'):
                content = content[1:-1]
            elif content.startswith('"') and content.endswith('"'):
                content = content[1:-1]
            elif content.startswith("'") and content.endswith("'"):
                content = content[1:-1]
            return content
        return ""
    
    def parse_plugin_calls(self, content):
        """Find all plugin() and cplugin() function calls and collect data"""
        plugin_list = []
        
        # Pattern to match function plugin(name) or function cplugin(name)
        pattern = r'function\s+(plugin|cplugin)\s*\(\s*([a-zA-Z0-9_]+)\s*\)\s*\{'
        
        for match in re.finditer(pattern, content):
            func_type = match.group(1)  # 'plugin' or 'cplugin'
            plugin_name = match.group(2)
            
            # Find the closing brace and extract function body
            start = match.end()
            brace_count = 1
            i = start
            while i < len(content) and brace_count > 0:
                if content[i] == '{':
                    brace_count += 1
                elif content[i] == '}':
                    brace_count -= 1
                i += 1
            
            func_body = content[start:i-1]
            
            # Load plugin config to get args and scripts
            plugin_config = self.load_plugin_config(plugin_name, func_type)
            if not plugin_config:
                print(f"Warning: Plugin '{plugin_name}' config not found")
                continue
            
            print(f"Found plugin '{plugin_name}'")
            
            # Always add directory to metadata
            instance = self.get_instance_number(plugin_name, "directory")
            dir_key = f"{plugin_name}:directory:{instance}"
            self.metadata[dir_key] = str(self.htma_file.parent)
            
            # Process args based on rts setting
            rts_enabled = plugin_config.get("rts", False)
            
            if rts_enabled:
                # Create separate TMP files for each arg
                for arg in plugin_config.get("args", []):
                    arg_content = self.extract_arg_content(func_body, arg)
                    instance_num = self.get_instance_number(plugin_name, arg)
                    
                    # Create TMP file for this arg
                    tmp_dir = self.script_dir / "TMP"
                    tmp_dir.mkdir(exist_ok=True)
                    
                    arg_tmp_id = self.generate_id()
                    arg_tmp_file = tmp_dir / f"{arg_tmp_id}.TMP"
                    
                    # Write raw content to TMP file
                    with open(arg_tmp_file, 'w', encoding='utf-8') as f:
                        f.write(arg_content)
                    
                    self.arg_tmp_files.append(arg_tmp_file)
                    
                    # Store pointer to TMP file in metadata
                    key = f"{plugin_name}:{arg}:{instance_num}"
                    self.metadata[key] = str(arg_tmp_file)
                    
                    print(f"  Created arg TMP: {arg} -> {arg_tmp_file.name}")
            # If rts is false, args are not included at all
            
            # Track this plugin for execution
            if plugin_name not in [p["name"] for p in plugin_list]:
                plugin_list.append({
                    "name": plugin_name,
                    "type": func_type,
                    "config": plugin_config
                })
        
        return plugin_list
    
    def create_metadata_tmp(self):
        """Create the metadata JSON TMP file"""
        tmp_dir = self.script_dir / "TMP"
        tmp_dir.mkdir(exist_ok=True)
        
        # Generate random ID for metadata TMP
        tmp_id = self.generate_id()
        self.metadata_tmp = tmp_dir / f"{tmp_id}.TMP"
        
        # Write metadata to TMP file
        with open(self.metadata_tmp, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=2)
        
        print(f"\nCreated metadata TMP: {self.metadata_tmp}")
        print(f"Metadata entries: {len(self.metadata)}")
        if self.metadata:
            print(f"Keys: {list(self.metadata.keys())}")
    
    def execute_plugins(self, plugin_list):
        """Execute plugin scripts with metadata TMP file path"""
        import subprocess
        
        for plugin_info in plugin_list:
            plugin_name = plugin_info["name"]
            plugin_type = plugin_info["type"]
            plugin_config = plugin_info["config"]
            scripts = plugin_config.get("scripts", [])
            
            print(f"\n{'='*50}")
            print(f"Executing plugin: {plugin_name}")
            
            # Determine plugin directory
            folder_name = f"_{plugin_name}_"
            if plugin_type == "plugin":
                plugin_path = self.plugin_dir / folder_name
            else:
                plugin_path = self.plugin_dir / "custom" / folder_name
            
            scripts_found = False
            for script in scripts:
                script_path = plugin_path / script
                
                if not script_path.exists():
                    continue
                
                scripts_found = True
                
                # Determine how to run the script based on extension
                if script.endswith('.py'):
                    cmd = ["python", str(script_path), str(self.metadata_tmp)]
                elif script.endswith('.js'):
                    cmd = ["node", str(script_path), str(self.metadata_tmp)]
                else:
                    print(f"Warning: Unknown script type: {script}")
                    continue
                
                
                try:
                    result = subprocess.Popen(cmd)
                    if result.stdout:
                        print(f"Output:\n{result.stdout}")
                    if result.stderr:
                        print(f"Error:\n{result.stderr}")
                except Exception as e:
                    print(f"Failed to execute: {e}")
            
            if not scripts_found:
                print(f"Warning: No scripts found for plugin '{plugin_name}'")
    
    def parse_and_run(self):
        """Parse the HTMA file and execute plugins"""
        with open(self.htma_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        print(f"Parsing: {self.htma_file}")
        
        # Parse plugin calls and collect all data
        plugin_list = self.parse_plugin_calls(content)
        
        if not plugin_list:
            print("No plugin functions found")
        else:
            self.metadata["window:file"] = str(self.htma_file)
            self.create_metadata_tmp()
            
            # Execute all plugins with the metadata TMP
            self.execute_plugins(plugin_list)
        
        print(f"\n{'='*50}")
        print("Execution complete")
        print(f"{'='*50}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python HTMA_PARSE.py filename.htma")
        sys.exit(1)
    
    htma_file = sys.argv[1]
    
    try:
        parser = HTMAParser(htma_file)
        parser.parse_and_run()
        
        # Get all TMP file paths for cleanup
        tmp_files = []
        if parser.metadata_tmp:
            tmp_files.append(str(parser.metadata_tmp))
        tmp_files.extend([str(f) for f in parser.arg_tmp_files])
        
        # Launch UI after parsing
        import subprocess
        ui_script = Path(__file__).parent / "UI.py"
        subprocess.Popen(["python", str(ui_script), str(parser.htma_file)] + tmp_files)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)