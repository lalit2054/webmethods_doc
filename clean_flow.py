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
                        child.attrib['FROM'] = f"({cleaned_text})"
            
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

def pretty_print_element(element, level=0):
    indent = "  " * level
    if len(element):
        result = f"{indent}<{element.tag}"
        for key, value in element.attrib.items():
            result += f' {key}="{html.escape(value)}"'
        result += ">\n"
        if element.text and element.text.strip():
            result += f"{indent}  {html.escape(element.text.strip())}\n"
        for child in element:
            result += pretty_print_element(child, level + 1)
        result += f"{indent}</{element.tag}>\n"
    else:
        if element.text and element.text.strip():
            result = f"{indent}<{element.tag}"
            for key, value in element.attrib.items():
                result += f' {key}="{html.escape(value)}"'
            result += f">{html.escape(element.text.strip())}</{element.tag}>\n"
        else:
            result = f"{indent}<{element.tag}"
            for key, value in element.attrib.items():
                result += f' {key}="{html.escape(value)}"'
            result += " />\n"
    return result

def modify_xml(input_file, output_file):
    # Load the XML file
    tree = ET.parse(input_file)
    root = tree.getroot()
    
    # Apply the functions to the root element
    remove_disabled_elements(root)
    remove_specific_elements(root)
    clean_attributes(root)
    convert_mapset_elements(root)
    remove_mapcopy_name_link(root)
    
    # Pretty print the modified tree
    pretty_xml = pretty_print_element(root)
    
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Save the modified tree to a new file
    with open(output_file, 'w') as f:
        f.write(pretty_xml)

def process_all_flow_xml_files():
    base_output_dir = 'out'
    for filepath in glob.iglob('**/flow.xml', recursive=True):
        # Determine the output file path, keeping the same name but under 'out' directory
        relative_path = os.path.relpath(filepath, start='.')
        output_file = os.path.join(base_output_dir, relative_path)
        
        print(f'Processing file: {filepath}')
        modify_xml(filepath, output_file)
        print(f'Modified file saved as: {output_file}')

if __name__ == "__main__":
    # Process all flow.xml files in the current directory and subdirectories
    process_all_flow_xml_files()
