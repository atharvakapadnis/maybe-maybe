from fastapi import APIRouter, Depends, HTTPException
from pydantic import create_model, BaseModel
from typing import Dict, Any, Type, get_type_hints, Optional, List, Union
import inspect
from mcp.fastmcp import FastMCP


def register_mcp_tools(app, mcp_instance: FastMCP, prefix: str = "/tools"):
    """
    Register all MCP tools as FastAPI endpoints.

    Args:
        app: The FastAPI application
        mcp_instance: The FastMCP instance
        prefix: URL prefix for the tools (default: "/tools")
    """
    router = APIRouter(prefix=prefix)

    # Register each tool as an endpoint
    for tool_name, tool_metadata in mcp_instance.tools.items():
        # Create a Pydantic model for request validation
        field_definitions = {}
        for param_name, param_info in tool_metadata.parameters.items():
            param_type = param_info["type"]
            default = param_info["default"] if not param_info["required"] else ...
            # Use tuple for field definition without variable in type expression
            field_definitions[param_name] = (param_type, default)

        # Dynamic model creation
        model_name = f"{tool_name.title()}Request"
        request_model = create_model(model_name, **field_definitions)

        # Create the endpoint (need to use factory pattern to capture tool_name in closure)
        def create_endpoint(tool):
            async def endpoint(request: request_model):  # type: ignore
                try:
                    # Convert request to dict and execute the tool
                    params = request.dict()
                    result = mcp_instance.execute_tool(tool, **params)
                    return {"result": result}
                except Exception as e:
                    raise HTTPException(status_code=500, detail=str(e))

            # Set proper function name and docstring
            endpoint.__name__ = f"execute_{tool}"
            endpoint.__doc__ = tool_metadata.description
            return endpoint

        # Register the endpoint
        router.add_api_route(
            f"/{tool_name}",
            create_endpoint(tool_name),
            methods=["POST"],
            response_model=Dict[str, Any],
            summary=(
                tool_metadata.description.split("\n")[0]
                if tool_metadata.description
                else ""
            ),
            description=tool_metadata.description,
        )

    # Register a tool listing endpoint
    @router.get("/", summary="List all available tools")
    async def list_tools():
        return {"tools": mcp_instance.list_tools()}

    # Register a tool info endpoint
    @router.get("/{tool_name}", summary="Get information about a specific tool")
    async def get_tool_info(tool_name: str):
        info = mcp_instance.get_tool_info(tool_name)
        if info is None:
            raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")
        return info

    # Register the router with the app
    app.include_router(router)

    return router
