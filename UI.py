import sys
import re
from pathlib import Path

try:
    import wx
    import wx.html2 as webview
except ImportError:
    print("ERROR: wxPython not installed!")
    print("Install with: pip install wxPython")
    sys.exit(1)

def check_display_value(content):
    """Check if <display value=0> is present"""
    pattern = r'<display\s+value\s*=\s*["\']?0["\']?\s*>'
    return bool(re.search(pattern, content))

def strip_htma_tags(content):
    """Remove htma-specific tags that browsers don't understand"""
    # Remove <import> tags
    content = re.sub(r'<import\s+[^>]*>', '', content)
    # Remove <display> tags  
    content = re.sub(r'<display\s+[^>]*>', '', content)
    # Replace <!DOCTYPE htma> with <!DOCTYPE html>
    content = re.sub(r'<!DOCTYPE\s+htma>', '<!DOCTYPE html>', content, flags=re.IGNORECASE)
    # Replace <htma> tags with <html>
    content = re.sub(r'<htma>', '<html>', content, flags=re.IGNORECASE)
    content = re.sub(r'</htma>', '</html>', content, flags=re.IGNORECASE)
    return content

def inject_resources(html_content, base_path):
    """Inject external CSS and JS files directly into the HTML"""
    
    # Find all <link> tags for CSS
    link_pattern = r'<link\s+[^>]*href\s*=\s*["\']([^"\']+)["\'][^>]*>'
    
    def replace_css(match):
        href = match.group(1)
        css_path = base_path / href
        
        if css_path.exists():
            try:
                with open(css_path, 'r', encoding='utf-8') as f:
                    css_content = f.read()
                print(f"Injected CSS: {href}")
                return f'<style>{css_content}</style>'
            except Exception as e:
                print(f"Failed to inject CSS {href}: {e}")
                return match.group(0)
        return match.group(0)
    
    html_content = re.sub(link_pattern, replace_css, html_content)
    
    # Find all <script src="..."> tags
    script_pattern = r'<script\s+[^>]*src\s*=\s*["\']([^"\']+)["\'][^>]*>\s*</script>'
    
    def replace_js(match):
        src = match.group(1)
        js_path = base_path / src
        
        if js_path.exists():
            try:
                with open(js_path, 'r', encoding='utf-8') as f:
                    js_content = f.read()
                print(f"Injected JS: {src}")
                return f'<script>{js_content}</script>'
            except Exception as e:
                print(f"Failed to inject JS {src}: {e}")
                return match.group(0)
        return match.group(0)
    
    html_content = re.sub(script_pattern, replace_js, html_content)
    
    return html_content
    """Remove htma-specific tags that browsers don't understand"""
    # Remove <import> tags
    content = re.sub(r'<import\s+[^>]*>', '', content)
    # Remove <display> tags  
    content = re.sub(r'<display\s+[^>]*>', '', content)
    # Replace <!DOCTYPE htma> with <!DOCTYPE html>
    content = re.sub(r'<!DOCTYPE\s+htma>', '<!DOCTYPE html>', content, flags=re.IGNORECASE)
    # Replace <htma> tags with <html>
    content = re.sub(r'<htma>', '<html>', content, flags=re.IGNORECASE)
    content = re.sub(r'</htma>', '</html>', content, flags=re.IGNORECASE)
    return content

class HTMAFrame(wx.Frame):
    def __init__(self, title, html_content, tmp_file):
        super().__init__(None, title=title, size=(800, 600))
        
        self.tmp_file = tmp_file
        
        # Create webview
        self.browser = webview.WebView.New(self)
        
        # Load HTML content directly (all resources are now injected)
        self.browser.SetPage(html_content, "")
        
        # Center window
        self.Centre()
        
        # Bind close event to cleanup
        self.Bind(wx.EVT_CLOSE, self.on_close)
    
    def on_close(self, event):
        """Cleanup TMP files on close"""
        if self.tmp_file and Path(self.tmp_file).exists():
            try:
                Path(self.tmp_file).unlink()
                print(f"Deleted TMP file: {self.tmp_file}")
            except Exception as e:
                print(f"Failed to delete TMP file: {e}")
        self.Destroy()

def launch_ui(htma_file, tmp_file=None):
    """Launch wxPython window with HTML content"""
    # Read the htma file
    with open(htma_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Get base path for resource injection
    base_path = Path(htma_file).parent
    
    # Strip htma-specific tags
    html_content = strip_htma_tags(content)
    
    # Inject external CSS and JS files
    html_content = inject_resources(html_content, base_path)
    
    # Get file name for window title
    window_title = Path(htma_file).stem or "htma+ Application"
    
    print(f"Launching UI: {window_title}")
    
    # Create wxPython app
    app = wx.App()
    frame = HTMAFrame(window_title, html_content, tmp_file)
    frame.Show()
    
    # Start the GUI loop
    app.MainLoop()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python UI.py filename.htma [tmp_file]")
        sys.exit(1)
    
    htma_file = Path(sys.argv[1]).resolve()
    tmp_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not htma_file.exists():
        print(f"Error: File not found: {htma_file}")
        sys.exit(1)
    
    # Read file to check display value
    with open(htma_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if display value is 0
    if check_display_value(content):
        print("<display value=0> detected - skipping UI launch")
        sys.exit(0)
    
    # Launch UI
    launch_ui(htma_file, tmp_file)