from services.ai_service import ai_service
from services.kv_store_service import kv_store
from utils.constants import ERROR_NO_OPENAI_API_KEY
import openai


async def visit_url(params):
    """UI handler for simulating web browser and generating HTML"""

    url = params.get("url_input", "")
    if not url:
        return {"success": False, "error": "URL is required"}

    try:
        ai_settings = await ai_service.get_openai_settings()
        if not ai_settings["api_key"]:
            return {"success": False, "error": ERROR_NO_OPENAI_API_KEY}

        # Create prompt for web page simulation
        prompt = f"""You are simulating a web browser visiting the URL: {url}

The web pages you deliver are realistic depictions of their real-world counterparts, but simulated and parodied.

Your HTML is always valid and concise.

Generate an HTML document that represents what this webpage might contain. The output should be:
- An HTML page NOT including the DOCTYPE, html, head, or body tags.
- Do NOT use meta tags or images. Any links present should go to "javascript:void(0)".
- Include realistic content that would be expected at this URL
- Use script tags to implement any request for interactive content
- Use styling with inline CSS or a <style> block
- Make it visually appealing but prefer simplicity
- Include typical webpage elements like headers, navigation, content sections, etc.

Generate only the HTML code, no explanations. Do NOT wrap the HTML in code tags or markdown syntax."""

        openai.api_key = ai_settings["api_key"]
        if ai_settings.get("base_url"):
            openai.base_url = ai_settings["base_url"]

        response = openai.chat.completions.create(
            model=ai_settings["model_name"],
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )

        html_content = response.choices[0].message.content

        await kv_store.set("page_html", html_content)

        return {"success": True, "message": f"Generated webpage for {url}"}

    except Exception as e:
        return {"success": False, "error": str(e)}

TOOLS = [{
    "schema": {
        "name": "Web Browser",
        "description": "Web browser simulator modal."
    },
    "ui_feature": {
        "id": "test-modal",
        "type": "ui_v1",
        "label": "Web Browser",
        "icon": "AppWindow",
        "layout": {
            "type": "modal",
            "size": "lg",
            "title": "Web Browser Simulator",
            "components": [
                {
                    "id": "url_input",
                    "type": "text_input",
                    "props": {
                        "placeholder": "Enter URL (e.g., https://example.com)"
                    }
                },
                {
                    "id": "visit_button",
                    "type": "button",
                    "props": {
                        "label": "Visit URL"
                    },
                    "actions": [
                        {
                            "type": "tool_submit",
                            "trigger": "click",
                            "target": "visit_url",
                            "params": {
                                "url_input": "url_input"
                            }
                        }
                    ]
                },
                {
                    "id": "page_display",
                    "type": "html_renderer",
                    "data_source": {
                        "type": "kv_store",
                        "key": "page_html"
                    },
                    "props": {
                        "use_iframe": True
                    }
                }
            ]
        }
    },
    "ui_handlers": {
        "visit_url": visit_url
    }
}]
