#!/usr/bin/env python3

import os
import glob
import urllib.request


def download_file(out_dir, url):
    # Ensure the output directory exists
    os.makedirs(out_dir, exist_ok=True)
    
    # Define the path where the file will be saved
    svg_path = os.path.join(out_dir, os.path.basename(url))
    
    # Download the file from the URL
    urllib.request.urlretrieve(url, svg_path)
    
    # Confirm the file has been downloaded
    print(f'Downloaded {os.path.basename(url)} to {svg_path}')

def download_expand_collapse_svg(out_dir):
    url = "https://raw.githubusercontent.com/lalit2054/webmethods_doc/main/expand-collapse.svg"
    svg_path = os.path.join(out_dir, "expand-collapse.svg")
    
    urllib.request.urlretrieve(url, svg_path)
    
    print(f'Downloaded expand-collapse.svg to {svg_path}')

def download_style_css(out_dir):
    url = "https://raw.githubusercontent.com/lalit2054/webmethods_doc/main/style.css"
    svg_path = os.path.join(out_dir, "style.css")
    
    urllib.request.urlretrieve(url, svg_path)
    
    print(f'Downloaded style.css to {svg_path}')

def generate_directory_structure_html_with_iframe(out_dir, root_dir):
    structure = build_directory_structure(root_dir)
    index_html = convert_structure_to_html(structure)

    # HTML structure with CSS link and iframe
    full_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Directory Structure</title>
    <link rel="stylesheet" href="style.css">
    <style>
        body {{
            display: flex;
            margin: 0;
            height: 100vh;
        }}
        #index {{
            width: 25%;
            overflow-y: auto;
            padding: 10px;
            border-right: 1px solid #ddd;
            box-shadow: 2px 0 5px rgba(0,0,0,0.1);
        }}
        #content {{
            flex-grow: 1;
            padding: 10px;
        }}
        iframe {{
            width: 100%;
            height: 100%;
            border: none;
        }}
    </style>
</head>
<body>
    <div id="index">
        <ul class="tree">
            {index_html}
        </ul>
    </div>
    <div id="content">
        <iframe name="content_frame" src=""></iframe>
    </div>
    <script>
        // Add event listener for the iframe content load
        const iframe = document.querySelector('iframe[name="content_frame"]');
        window.addEventListener('popstate', function(event) {{
            if (event.state && event.state.url) {{
                iframe.src = event.state.url;
            }}
        }});

        document.querySelectorAll('#index a').forEach(link => {{
            link.addEventListener('click', function(event) {{
                event.preventDefault();
                const url = this.getAttribute('href');
                iframe.src = url;
                history.pushState({{ url: url }}, '', url);
            }});
        }});
    </script>
</body>
</html>'''

    # Save the directory_structure.html file
    with open(os.path.join(out_dir, 'index.html'), 'w') as f:
        f.write(full_html)

def build_directory_structure(root_dir):
    structure = {}
    for filepath in glob.iglob(f'{root_dir}/**/flow.html', recursive=True):
        parts = os.path.relpath(filepath, start=root_dir).split(os.sep)
        add_to_structure(structure, parts[:-1])  # Exclude flow.html from the parts
    return structure

def add_to_structure(structure, parts):
    if len(parts) == 1:
        structure[parts[0]] = structure.get(parts[0], [])
        structure[parts[0]].append('flow.html')
    else:
        if parts[0] not in structure:
            structure[parts[0]] = {}
        add_to_structure(structure[parts[0]], parts[1:])

def convert_structure_to_html(structure, base_path=""):
    html = ""
    for key, value in sorted(structure.items()):
        if isinstance(value, list) and 'flow.html' in value:
            flow_link = os.path.join(base_path, key, 'flow.html')
            html += f'''
            <li>
                <span class="linkr"><a href="{flow_link}" target="content_frame">{key}</a></span>
            </li>
            '''
        else:
            next_base_path = os.path.join(base_path, key)
            html += f'''
            <li>
                <details>
                    <summary class="dir">{key}</summary>
                    <ul>{convert_structure_to_html(value, next_base_path)}</ul>
                </details>
            </li>
            '''
    return html

if __name__ == "__main__":
    out_dir = 'out'
    root_dir = out_dir  # Assuming the root directory is the "out" directory where flow.html files are located
    
    os.makedirs(out_dir, exist_ok=True)

    download_file(out_dir, 'https://raw.githubusercontent.com/lalit2054/webmethods_doc/main/expand-collapse.svg')
    download_file(out_dir, 'https://raw.githubusercontent.com/lalit2054/webmethods_doc/main/style.css')
    download_file(out_dir, 'https://raw.githubusercontent.com/lalit2054/webmethods_doc/main/prism.css')
    download_file(out_dir, 'https://raw.githubusercontent.com/lalit2054/webmethods_doc/main/prism.js')
    
    
    # Download the expand-collapse.svg file
    #download_expand_collapse_svg(out_dir)

    #download_style_css(out_dir)
    
    # Generate the directory structure HTML with iframe
    generate_directory_structure_html_with_iframe(out_dir, root_dir)
