"""
MCP (Model Context Protocol) helper module for Supabase integration
"""
import json
import os
import subprocess

def use_mcp_tool(server_name, tool_name, arguments):
    """
    Use an MCP tool and return the result
    
    Args:
        server_name (str): The name of the MCP server
        tool_name (str): The name of the tool to use
        arguments (dict): The arguments to pass to the tool
        
    Returns:
        The result of the tool execution
    """
    try:
        # Convert arguments to JSON string
        args_json = json.dumps(arguments)
        
        # Create a temporary file to store the result
        temp_file = "mcp_result.json"
        
        # Create the MCP command
        command = f"""
        python -c "
import json
from roo.mcp import use_mcp_tool

result = use_mcp_tool(
    '{server_name}',
    '{tool_name}',
    {args_json}
)

with open('{temp_file}', 'w') as f:
    json.dump(result, f)
"
        """
        
        # Execute the command
        subprocess.run(command, shell=True, check=True)
        
        # Read the result from the temporary file
        with open(temp_file, 'r') as f:
            result = json.load(f)
            
        # Delete the temporary file
        os.remove(temp_file)
        
        return result
    except Exception as e:
        print(f"Error using MCP tool: {e}")
        return []