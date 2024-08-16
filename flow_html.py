#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import os
import re
import glob
import html

# Function to recursively remove elements with DISABLED="true" attribute
def remove_disabled_elements(element):
    for child in list(element):
        if child.attrib.get('DISABLED') == 'true':
            element.remove(child)
        else:
            remove_disabled_elements(child)

# Function to recursively remove MAPSOURCE, MAPTARGET, and record elements
def remove_specific_elements(element):
    for child in list(element):
        if child.tag in {'MAPSOURCE', 'MAPTARGET', 'record'}:
            element.remove(child)
        else:
            remove_specific_elements(child)

# Function to remove ;<some number> pattern from FROM, TO, and FIELD attributes
def clean_attributes(element):
    if 'FROM' in element.attrib:
        element.attrib['FROM'] = re.sub(r';\d+', '', element.attrib['FROM'])
    if 'TO' in element.attrib:
        element.attrib['TO'] = re.sub(r';\d+', '', element.attrib['TO'])
    if 'FIELD' in element.attrib:
        element.attrib['FIELD'] = re.sub(r';\d+', '', element.attrib['FIELD'])
    if 'TIMEOUT' in element.attrib:
        del element.attrib['TIMEOUT']
    if 'EXIT-ON' in element.attrib:
        del element.attrib['EXIT-ON']
    if 'VALIDATE-IN' in element.attrib:
        del element.attrib['VALIDATE-IN']
    if 'VALIDATE-OUT' in element.attrib:
        del element.attrib['VALIDATE-OUT']
    
    
    for child in element:
        clean_attributes(child)

# Function to convert MAPSET elements
def convert_mapset_elements(element):
    for child in list(element):
        if child.tag == 'MAPSET':
            if 'FIELD' in child.attrib:
                child.attrib['TO'] = child.attrib.pop('FIELD')
            
            data_element = child.find('DATA')
            if data_element is not None:
                values_element = data_element.find('Values')
                if values_element is not None:
                    value_element = values_element.find('value')
                    if value_element is not None and value_element.text:
                        # Clean the value text
                        cleaned_text = value_element.text.replace('\n', ' ').replace('"', '&quot;').strip()
                        child.attrib['FROM'] = f"const({cleaned_text})"
            
            # Remove all child elements from MAPSET
            for subchild in list(child):
                child.remove(subchild)
            
            # Keep only FROM and TO attributes in MAPSET element
            keys_to_keep = {'FROM', 'TO'}
            keys_to_remove = set(child.attrib.keys()) - keys_to_keep
            for key in keys_to_remove:
                del child.attrib[key]
        
        convert_mapset_elements(child)

# Function to remove NAME="Link" attribute from MAPCOPY elements
def remove_mapcopy_name_link(element):
    for child in list(element):
        if child.tag == 'MAPCOPY' and child.attrib.get('NAME') == 'Link':
            del child.attrib['NAME']
        remove_mapcopy_name_link(child)

def xml_to_html(element):
    tag = element.tag

    attributes = " ".join([f'<span class="attribute_base">{k}="{html.escape(v)}"</span>' for k, v in element.attrib.items()])
    
    comment = ""
    open_str = "open"
    element_class = "element_default"
    # Check if the element contains a COMMENT child element
    for child in list(element):
        if child.tag == "COMMENT":
            comment_text = child.text.strip() if child.text else ''
            comment = f'<div class="comment">{html.escape(comment_text)}</div>'
            element.remove(child)

    children_html = "".join([xml_to_html(child) for child in element])

    if tag == "INVOKE" or tag == "MAP":
        open_str = ""

    if tag == "BRANCH":
        element_class = "element_branch"
    elif tag == "INVOKE":
        element_class = "element_invoke"
    elif tag == "MAP":
        element_class = "element_map"
    
    if children_html:
        
            
        return f'''
            <li>
                <details {open_str}>
                    <summary class="card">
                        <span class="element_base {element_class}">{tag}</span> {attributes} {comment}
                    </summary>
                    <ul>{children_html}</ul>
                </details>
            </li>
        '''
    else:
        return f'''
            <li>
                <details open>
                    <summary class="card">
                        <span class="element_base {element_class}">{tag}</span> {attributes} {comment}
                    </summary>
                </details>
            </li>
        '''

def modify_xml_to_html(input_file, output_file):
    # Load the XML file
    tree = ET.parse(input_file)
    root = tree.getroot()
    
    # Apply the functions to the root element
    remove_disabled_elements(root)
    remove_specific_elements(root)
    clean_attributes(root)
    convert_mapset_elements(root)
    remove_mapcopy_name_link(root)

    processed_xml_str = ET.tostring(root, encoding='unicode')

    # Escape the XML for displaying as raw XML in HTML
    escaped_xml = html.escape(processed_xml_str)

    # Format the escaped XML into the desired HTML structure
    raw_xml_output = f'<pre><code class="language-xml">{escaped_xml}</code></pre>'
    
    # Convert the XML to HTML
    html_content = xml_to_html(root)

    relative_style_path = os.path.relpath('out/style.css', start=os.path.dirname(output_file))
    relative_prism_style_path = os.path.relpath('out/prism.css', start=os.path.dirname(output_file))
    relative_prism_script_path = os.path.relpath('out/prism.js', start=os.path.dirname(output_file))
    
    # HTML structure with CSS
    full_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>webMethods Package</title>
    <link rel="stylesheet" href="{relative_style_path}">
    <link rel="stylesheet" href="{relative_prism_style_path}">
</head>
<body>
    <ul class="tree">
        {html_content}
    </ul>
    {raw_xml_output}
    <script src="{relative_prism_script_path}"></script>
</body>
</html>'''

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Save the generated HTML content to a new file
    with open(output_file, 'w') as f:
        f.write(full_html)

def process_all_flow_xml_files_to_html():
    base_output_dir = 'out'
    for filepath in glob.iglob('**/flow.xml', recursive=True):
        # Determine the output HTML file path
        relative_path = os.path.relpath(filepath, start='.')
        dir_without_file = os.path.dirname(relative_path)
        output_dir = os.path.join(base_output_dir, dir_without_file)
        output_file = os.path.join(output_dir, 'flow.html')
        
        print(f'Processing file to HTML: {filepath}')
        modify_xml_to_html(filepath, output_file)
        print(f'HTML file saved as: {output_file}')

if __name__ == "__main__":
    # Process all flow.xml files in the current directory and subdirectories to generate HTML
    process_all_flow_xml_files_to_html()
