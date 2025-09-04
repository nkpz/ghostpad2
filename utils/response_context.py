from typing import Any, Dict

class ResponseContext:
    """
    Context object that allows tools to stream text as part of the current response being generated.
    
    This provides a simple interface for tools to emit content that gets integrated into the
    streaming response, rather than just returning a final result.
    """
    
    def __init__(self, inference_loop_context: Dict[str, Any]):
        """
        Initialize the response context.
        
        Args:
            inference_loop_context: Reference to the inference loop's context variables
        """
        self._inference_context = inference_loop_context
        self._final_content = ""
        
        # Initialize the streaming content lists
        if "tool_streamed_content" not in self._inference_context:
            self._inference_context["tool_streamed_content"] = []
        if "system_streamed_content" not in self._inference_context:
            self._inference_context["system_streamed_content"] = []
    
    def get_final_content(self) -> str:
        """
        Get all content that was appended to the response.
        
        Returns:
            The accumulated final content
        """
        return self._final_content
    
    def get_all_content(self) -> str:
        """
        Get all content including both streamed and final content.
        
        Returns:
            All content combined
        """
        streamed = "".join(self._inference_context.get("tool_streamed_content", []))
        return streamed + self._final_content
    
    def get_system_content(self) -> str:
        """
        Get all system content that was streamed.
        
        Returns:
            The accumulated system content
        """
        return "".join(self._inference_context.get("system_streamed_content", []))