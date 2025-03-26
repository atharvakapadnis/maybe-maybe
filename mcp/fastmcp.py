class FastMCP:
    def __init__(self, project_name:str):
        self.project_name = project_name
        print(f"MCP server initialized for project: {project_name}")

    def tool(self):
        """
        Returns a decorator tool that  you can use to mark any function
        as an MCP-managed tool.
        """
        def decorator(func):
            # Registration logic to be added here
            return func
        return decorator
    
    # Additional MCP related methods to be added here