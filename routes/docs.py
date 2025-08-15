"""
Documentation routes for viewing guides and documentation
"""

from flask import Blueprint, render_template, send_file, abort, Response
import os
import re

docs_bp = Blueprint('docs', __name__, url_prefix='/docs')

def simple_markdown_to_html(text):
    """Simple markdown to HTML converter without external dependencies"""
    # Convert headers
    text = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    
    # Convert bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # Convert italic
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    
    # Convert code blocks
    text = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', text, flags=re.DOTALL)
    
    # Convert inline code
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
    
    # Convert links
    text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', text)
    
    # Convert line breaks
    text = re.sub(r'\n\n', r'</p><p>', text)
    
    # Wrap in paragraphs
    text = f'<p>{text}</p>'
    
    # Fix empty paragraphs
    text = re.sub(r'<p>\s*</p>', '', text)
    text = re.sub(r'<p>(<h[123]>)', r'\1', text)
    text = re.sub(r'(</h[123]>)</p>', r'\1', text)
    text = re.sub(r'<p>(<pre>)', r'\1', text)
    text = re.sub(r'(</pre>)</p>', r'\1', text)
    
    # Convert horizontal rules
    text = re.sub(r'^---$', r'<hr>', text, flags=re.MULTILINE)
    
    # Convert unordered lists
    lines = text.split('\n')
    in_list = False
    new_lines = []
    for line in lines:
        if line.strip().startswith('- '):
            if not in_list:
                new_lines.append('<ul>')
                in_list = True
            new_lines.append(f'<li>{line.strip()[2:]}</li>')
        else:
            if in_list:
                new_lines.append('</ul>')
                in_list = False
            new_lines.append(line)
    if in_list:
        new_lines.append('</ul>')
    text = '\n'.join(new_lines)
    
    return text

@docs_bp.route('/')
def index():
    """List all available documentation"""
    docs_dir = 'docs'
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)
    
    docs = []
    for filename in os.listdir(docs_dir):
        if filename.endswith('.md'):
            docs.append({
                'name': filename.replace('.md', '').replace('_', ' ').title(),
                'file': filename
            })
    
    return render_template('docs/index.html', docs=docs)

@docs_bp.route('/<path:filename>')
def view_doc(filename):
    """View a specific documentation file"""
    # Ensure the file has .md extension
    if not filename.endswith('.md'):
        filename += '.md'
    
    filepath = os.path.join('docs', filename)
    
    if not os.path.exists(filepath):
        abort(404)
    
    # Read markdown content
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Convert markdown to HTML using simple converter
    html_content = simple_markdown_to_html(content)
    
    # Extract title from first line if it's a header
    lines = content.split('\n')
    title = 'Documentation'
    if lines and lines[0].startswith('#'):
        title = lines[0].replace('#', '').strip()
    
    return render_template('docs/viewer.html', 
                         title=title, 
                         content=html_content,
                         filename=filename)